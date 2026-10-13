# -*- coding: utf-8 -*-
"""
Lumina Commons - 本地预览服务器（健壮版，兼容 Python 3.6+ / 含 3.7）

设计目标：让"双击 启动服务器.bat"一次就能成功；万一失败，窗口也不会静默关闭，能看清原因。

要点：
  1. 自动挑选可用端口：8000 优先，被占用就依次 8080 / 8088 / 8888 / 9000 / 3000 / 系统随机
     —— 不再去 kill 别人的进程，从根上避免"僵尸服务器占着端口"把页面搞坏
  2. 端口确认可用后，自动打开浏览器到**正确地址**（可用 SERVE_NO_BROWSER=1 关闭，供自动化测试用）
  3. 多线程：32MB 视频 / 38MB 3D 模型不会阻塞其它请求
  4. 关键 MIME 显式指定：.js / .mjs 必须是 JS 类型，否则 ES Module 会被浏览器拒绝
     （老版本 Python 在 Windows 上对 .mjs / .glb 返回 None，会退化成 octet-stream）
  5. 任何异常都打印完整 traceback + 写 server.log，绝不静默退出
  6. 全部访问记录写 server.log

用法：  python serve.py
可选环境变量：
  SERVE_PORT=8000        指定首选端口（被占用仍会自动往后挑）
  SERVE_HOST=127.0.0.1   绑定地址
  SERVE_NO_BROWSER=1     不自动打开浏览器
"""

import os
import sys
import time
import socket
import logging
import threading
import re
import traceback
import webbrowser

try:
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
except Exception:  # pragma: no cover - 极老的 Python 兜底
    from http.server import SimpleHTTPRequestHandler, HTTPServer as ThreadingHTTPServer

# ------------------------------------------------------------------ 基本配置
ROOT = os.path.dirname(os.path.abspath(__file__))
HOST = os.environ.get("SERVE_HOST", "127.0.0.1")
NO_BROWSER = os.environ.get("SERVE_NO_BROWSER") == "1"

PREFERRED = os.environ.get("SERVE_PORT")
PORT_PREFS = []
if PREFERRED:
    try:
        PORT_PREFS.append(int(PREFERRED))
    except ValueError:
        pass
for _p in (8000, 8080, 8088, 8888, 9000, 3000):
    if _p not in PORT_PREFS:
        PORT_PREFS.append(_p)
PORT_PREFS.append(0)  # 0 = 交给系统随便给一个空闲端口（保底一定能成功）

LOG_PATH = os.path.join(ROOT, "server.log")

# 控制台输出：即使控制台不支持中文也绝不让程序崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def say(msg=""):
    """安全打印（编码异常时自动降级为 ASCII，绝不抛错）"""
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass
    try:
        sys.stdout.flush()
    except Exception:
        pass


# ------------------------------------------------------------------ 日志
log = logging.getLogger("serve")
try:
    logging.basicConfig(
        filename=LOG_PATH,
        filemode="w",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
except Exception:
    logging.basicConfig(level=logging.INFO)


# ------------------------------------------------------------------ HTTP Range 支持
class _RangeFile(object):
    """只允许读取前 length 字节的包装器，用于 HTTP 206 分段响应。"""

    def __init__(self, fp, length):
        self.fp = fp
        self.remaining = length

    def read(self, n=-1):
        if self.remaining <= 0:
            return b""
        if n is None or n < 0:
            n = self.remaining
        data = self.fp.read(min(n, self.remaining))
        self.remaining -= len(data)
        return data

    def close(self):
        try:
            self.fp.close()
        except Exception:
            pass


# ------------------------------------------------------------------ 请求处理
class Handler(SimpleHTTPRequestHandler):
    # 关键：显式钉死 MIME，避免老 Python / Windows 注册表把 .js 判成 text/plain
    extensions_map = dict(getattr(SimpleHTTPRequestHandler, "extensions_map", {}))
    extensions_map.update({
        "": "application/octet-stream",
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".html": "text/html",
        ".htm": "text/html",
        ".svg": "image/svg+xml",
        ".glb": "model/gltf-binary",
        ".gltf": "model/gltf+json",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".webp": "image/webp",
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".wasm": "application/wasm",
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    @staticmethod
    def _parse_range(header, file_len):
        """解析 Range 头；返回 (start, end) / None(无 Range) / "invalid"(越界)。"""
        if not header:
            return None
        m = re.match(r"bytes=(\d*)-(\d*)", header.strip())
        if not m or (m.group(1) == "" and m.group(2) == ""):
            return None
        if m.group(1) == "":
            suffix = int(m.group(2))
            if suffix <= 0:
                return "invalid"
            start = max(0, file_len - suffix)
            end = file_len - 1
        else:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else file_len - 1
        if start >= file_len or start > end:
            return "invalid"
        return (start, min(end, file_len - 1))

    def send_head(self):
        """支持 HTTP Range —— 音视频拖动进度条 / seek 必需。
        标准库默认只返回 200 整文件，没有 206，浏览器就跳不到未缓冲的位置，
        表现成「点了快进，视频却回到开头 / 只有背景」。"""
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return SimpleHTTPRequestHandler.send_head(self)

        ctype = self.guess_type(path)
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            file_len = fs.st_size
            rng = self._parse_range(self.headers.get("Range"), file_len)

            if rng == "invalid":
                self.send_response(416)
                self.send_header("Content-Range", "bytes */%d" % file_len)
                self.send_header("Content-Length", "0")
                self.end_headers()
                f.close()
                return None

            if rng is None:
                self.send_response(200)
                self.send_header("Content-type", ctype)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(file_len))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                return f

            start, end = rng
            length = end - start + 1
            f.seek(start)
            self.send_response(206)
            self.send_header("Content-type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, file_len))
            self.send_header("Content-Length", str(length))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return _RangeFile(f, length)
        except Exception:  # noqa: BLE001
            f.close()
            raise

    def log_message(self, fmt, *args):
        try:
            log.info("%s - %s", self.address_string(), fmt % args)
        except Exception:
            pass

    def handle_one_request(self):
        # 单条请求出错（客户端断开 / 坏连接 / 浏览器取消加载）绝不拖垮整个服务器
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError) as e:
            log.warning("client disconnect: %s", e)
        except Exception as e:  # noqa: BLE001
            log.warning("request error: %s", e)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        SimpleHTTPRequestHandler.end_headers(self)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


# ------------------------------------------------------------------ 端口探测
def port_is_taken(port):
    """端口上是否已有别的程序在监听（只探测，不动别人的进程）"""
    if port == 0:
        return False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.3)
    try:
        s.connect((HOST, port))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def pick_and_bind():
    """按优先级找一个真正可用的端口并绑定；返回 (server, port) 或 (None, None)"""
    tried = []
    for port in PORT_PREFS:
        if port_is_taken(port):
            tried.append("%d(occupied)" % port)
            say("  [i] port %d is occupied by another program -> try next" % port)
            continue
        try:
            httpd = Server((HOST, port), Handler)
        except OSError as e:
            tried.append("%d(%s)" % (port, e))
            say("  [i] port %d cannot bind (%s) -> try next" % (port, e))
            continue
        real = httpd.server_address[1]
        log.info("port chosen: %d (tried: %s)", real, ", ".join(tried) if tried else "none")
        return httpd, real
    log.error("no usable port, tried: %s", ", ".join(tried))
    return None, None


# ------------------------------------------------------------------ 主流程
def open_later(url, delay=1.0):
    def _go():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            log.info("browser opened: %s", url)
        except Exception as e:  # noqa: BLE001
            log.warning("cannot open browser: %s", e)
    t = threading.Thread(target=_go)
    t.daemon = True
    t.start()


def main():
    try:
        os.chdir(ROOT)
    except Exception as e:  # noqa: BLE001
        say("[X] cannot enter project folder: %s" % e)
        return 1

    log.info("serving directory: %s", ROOT)
    log.info("python: %s", sys.version.replace("\n", " "))

    say("")
    say("============================================================")
    say("  Lumina Commons  --  local preview server")
    say("============================================================")
    say("  Python : %s" % sys.version.split()[0])
    say("  Folder : %s" % ROOT)
    say("  Log    : %s" % LOG_PATH)
    say("------------------------------------------------------------")

    httpd, port = pick_and_bind()
    if httpd is None:
        say("[X] No usable port found (8000/8080/8088/8888/9000/3000 all busy).")
        say("    Close some programs and run this script again.")
        say("    See server.log for details.")
        return 3

    home = "http://%s:%d/index.html" % (HOST, port)
    sand = "http://%s:%d/sandbox.html" % (HOST, port)
    say("  Port   : %d   <- FREE, server is now running" % port)
    say("------------------------------------------------------------")
    say("  >>> OPEN THIS ADDRESS  (a browser tab opens automatically)")
    say("        %s" % home)
    say("      3D sandbox : %s" % sand)
    say("------------------------------------------------------------")
    say("  KEEP THIS WINDOW OPEN.  Press Ctrl+C to stop the server.")
    say("============================================================")
    say("")

    if not NO_BROWSER:
        open_later(home, 1.0)
    else:
        say("  (SERVE_NO_BROWSER=1 -> browser not opened)")

    log.info("listening on %s", home)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        say("")
        say("[i] stopped by user (Ctrl+C).")
        log.info("interrupted by user, shutting down")
    except Exception as e:  # noqa: BLE001
        say("[X] server loop crashed: %s" % e)
        say(traceback.format_exc())
        log.exception("server loop error: %s", e)
        return 2
    finally:
        try:
            httpd.server_close()
        except Exception:
            pass
        log.info("server closed")
    return 0


if __name__ == "__main__":
    EXIT = 0
    try:
        EXIT = main()
    except Exception:  # noqa: BLE001  最后一道防线：任何异常都打出来，绝静默退出
        say("[X] unexpected error:")
        say(traceback.format_exc())
        try:
            log.exception("unexpected error")
        except Exception:
            pass
        EXIT = 9
    if EXIT:
        say("")
        say("[i] serve.py exited with code %d." % EXIT)
    sys.exit(EXIT)
