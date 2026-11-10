"""Adjust office-tower.blend to match source.mp4 (run before render_full.py)."""
import bpy, math, os
from mathutils import Vector
sc = bpy.context.scene
P = dict(EL=float(os.environ.get("M_EL", 30)), AZ=float(os.environ.get("M_AZ", -45)),
         DIST=float(os.environ.get("M_DIST", 1.6)), LENS=float(os.environ.get("M_LENS", 56)))
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
cam.data.clip_end = 2000
# 2. no ocean; bright neutral world like the web app
# 0. visibility keys must be stepped (linear bool curves flip mid-shot)
nfix = 0
for o in bpy.data.objects:
    ad = o.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path in ("hide_render", "hide_viewport"):
                for k in fc.keyframe_points: k.interpolation = "CONSTANT"; nfix += 1
print("stepped vis keys", nfix)
for name in [o.name for o in bpy.data.collections["Coast"].all_objects]:
    o = bpy.data.objects[name]
    if o.animation_data: o.animation_data.action = None
    o.hide_render = True
bpy.data.collections["Coast"].hide_render = True
# world: camera sees flat backdrop, scene lit by soft neutral sky
w = sc.world; nt = w.node_tree; N = nt.nodes
bg = N["Background"]; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = float(os.environ.get("M_SKY", 0.5))
cb = N.new("ShaderNodeBackground"); lp = N.new("ShaderNodeLightPath"); mx = N.new("ShaderNodeMixShader")
cb.inputs[1].default_value = 1.0
nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(bg.outputs[0], mx.inputs[1]); nt.links.new(cb.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], N["World Output"].inputs[0])
light_bg, dark_bg = (0.84, 0.84, 0.84, 1), (0.004, 0.002, 0.003, 1)
for f, col in [(1, light_bg), (2461, dark_bg), (3616, light_bg)]:
    cb.inputs[0].default_value = col; cb.inputs[0].keyframe_insert("default_value", frame=f)
for fc in nt.animation_data.action.fcurves:
    for k in fc.keyframe_points: k.interpolation = "CONSTANT"
sc.view_settings.view_transform = os.environ.get("M_VT", "Standard")
sc.view_settings.look = "None"
sc.view_settings.exposure = float(os.environ.get("M_EXP", 0.0))
sun = bpy.data.objects["Sun"].data; sun.energy = float(os.environ.get("M_SUN", 3.0)); sun.angle = math.radians(8)
print("match.py applied", P)
