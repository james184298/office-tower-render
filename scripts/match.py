"""Adjust office-tower.blend to match source.mp4 (run before render_full.py)."""
import bpy, math, os
from mathutils import Vector
sc = bpy.context.scene
P = dict(EL=float(os.environ.get("M_EL", 30)), AZ=float(os.environ.get("M_AZ", -45)),
         DIST=float(os.environ.get("M_DIST", 1.0)), LENS=float(os.environ.get("M_LENS", 56)))
cam = sc.camera
tgt = bpy.data.objects["CamTarget"]
# 1. camera: fixed iso-like direction, keep each key's distance (scaled)
el, az = math.radians(P["EL"]), math.radians(P["AZ"])
dirv = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
fc_c = {fc.array_index: fc for fc in cam.animation_data.action.fcurves if fc.data_path == "location"}
fc_t = {fc.array_index: fc for fc in tgt.animation_data.action.fcurves if fc.data_path == "location"}
keys = sorted({round(k.co[0]) for fc in fc_c.values() for k in fc.keyframe_points})
new = {}
for f in keys:
    c = Vector([fc_c[i].evaluate(f) for i in range(3)])
    t = Vector([fc_t[i].evaluate(f) for i in range(3)])
    new[f] = t + dirv * (c - t).length * P["DIST"]
for f, v in new.items():
    for i in range(3):
        for k in fc_c[i].keyframe_points:
            if round(k.co[0]) == f:
                k.co[1] = v[i]; k.handle_left[1] = v[i]; k.handle_right[1] = v[i]
for fc in fc_c.values(): fc.update()
cam.data.lens = P["LENS"]
# 2. no ocean; bright neutral world like the web app
for o in bpy.data.collections["Coast"].all_objects: o.hide_render = True; o.animation_data_clear() if False else None
bpy.data.collections["Coast"].hide_render = True
w = sc.world; bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.87, 0.87, 0.87, 1); bg.inputs[1].default_value = 1.0
sc.view_settings.view_transform = os.environ.get("M_VT", "Standard")
sc.view_settings.look = "None"
sc.view_settings.exposure = float(os.environ.get("M_EXP", 0.0))
sun = bpy.data.objects["Sun"].data; sun.energy = float(os.environ.get("M_SUN", 3.0)); sun.angle = math.radians(8)
print("match.py applied", P)
