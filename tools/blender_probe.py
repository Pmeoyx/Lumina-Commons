import bpy, json, os, sys

SRC = r"C:/Users/pmeoyx/WorkBuddy/2026-10-04-12-15-33/assets/lumina/lumina_commons_src.glb"

# clean
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

objs = [o for o in bpy.data.objects]
out = {
  "blender": bpy.app.version_string,
  "n_objects": len(objs),
  "object_types": {},
  "sample_names": [],
  "n_materials": len(bpy.data.materials),
  "material_names": [m.name for m in bpy.data.materials],
  "n_meshes": len(bpy.data.meshes),
  "collections": [c.name for c in bpy.data.collections],
}
for o in objs:
    out["object_types"][o.type] = out["object_types"].get(o.type,0)+1
names = sorted(o.name for o in objs)
out["sample_names"] = names[:40]
# print any object whose name suggests parents/empties
out["empties"] = [o.name for o in objs if o.type=='EMPTY'][:60]
out["roots"] = [o.name for o in objs if o.parent is None][:60]

# geometry sanity for one hero
for nm in ["Z01_study_tower","Z01_study_tower_day","U_tile_Z01","U_plaza_disc","U_fence_01"]:
    o = bpy.data.objects.get(nm)
    if o:
        out.setdefault("probe",{})[nm] = {
          "loc": list(o.location), "scale": list(o.scale),
          "dims": list(o.dimensions),
          "parent": o.parent.name if o.parent else None,
          "mats": [ms.material.name if ms.material else None for ms in o.material_slots],
          "verts": len(o.data.vertices) if o.type=='MESH' else None,
        }

print("===PROBE_JSON_START===")
print(json.dumps(out, ensure_ascii=False, indent=1))
print("===PROBE_JSON_END===")
