"""Adjust office-tower.blend to match source.mp4 (run before render_full.py)."""
import bpy, math, os
from mathutils import Vector
sc = bpy.context.scene
P = dict(EL=float(os.environ.get("M_EL", 30)), AZ=float(os.environ.get("M_AZ", -45)),
         DIST=float(os.environ.get("M_DIST", 1.6)), LENS=float(os.environ.get("M_LENS", 56)))
cam = sc.camera
tgt = bpy.data.objects["CamTarget"]
# 1. camera: fixed iso-like direction, per-shot distance scale and target drop
el, az = math.radians(P["EL"]), math.radians(P["AZ"])
dirv = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
# shot start frame -> (distance scale, target z offset)
SHOTS = [(1, float(os.environ.get("M_OV", 1.25)), 0), (151, float(os.environ.get("M_EX", 0.8)), 0),
         (646, float(os.environ.get("M_IN", 1.7)), -3), (1741, float(os.environ.get("M_EX", 0.8)), 0),
         (2041, float(os.environ.get("M_IN", 1.7)), -3), (2461, float(os.environ.get("M_UG", 1.2)), 0),
         (3616, float(os.environ.get("M_OV", 1.25)), 0)]
def shot(f):
    r = SHOTS[0]
    for x in SHOTS:
        if f >= x[0]: r = x
    return r
fc_c = {fc.array_index: fc for fc in cam.animation_data.action.fcurves if fc.data_path == "location"}
fc_t = {fc.array_index: fc for fc in tgt.animation_data.action.fcurves if fc.data_path == "location"}
keys = sorted({round(k.co[0]) for fc in fc_c.values() for k in fc.keyframe_points})
tkeys = sorted({round(k.co[0]) for fc in fc_t.values() for k in fc.keyframe_points})
orig_t = {f: Vector([fc_t[i].evaluate(f) for i in range(3)]) for f in sorted(set(keys) | set(tkeys))}
orig_c = {f: Vector([fc_c[i].evaluate(f) for i in range(3)]) for f in keys}
def setkey(fcs, f, v):
    for i in range(3):
        for k in fcs[i].keyframe_points:
            if round(k.co[0]) == f:
                d = v[i] - k.co[1]; k.co[1] = v[i]; k.handle_left[1] += d; k.handle_right[1] += d
for f in tkeys:
    setkey(fc_t, f, orig_t[f] + Vector((0, 0, shot(f)[2])))
for f in keys:
    t = orig_t[f]; m, dz = shot(f)[1], shot(f)[2]
    setkey(fc_c, f, t + Vector((0, 0, dz)) + dirv * (orig_c[f] - t).length * m)
for fc in list(fc_c.values()) + list(fc_t.values()): fc.update()
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
bg = N["Background"]; bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = float(os.environ.get("M_SKY", 0.2))
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
sun = bpy.data.objects["Sun"].data; sun.energy = float(os.environ.get("M_SUN", 4.0)); sun.angle = math.radians(8)
print("match.py applied", P)

# 3. explode floors at liftoff (up) and basements in overview (down)
def rig(colname, keys):
    e = bpy.data.objects.new("Rig_" + colname, None); sc.collection.objects.link(e)
    for o in bpy.data.collections[colname].all_objects:
        if o.parent is None:
            o.parent = e; o.matrix_parent_inverse.identity()
    for f, z in keys:
        e.location.z = z; e.keyframe_insert("location", index=2, frame=f)
    for fc in e.animation_data.action.fcurves:
        for k in fc.keyframe_points: k.interpolation = "BEZIER"; k.easing = "EASE_IN_OUT"
G = float(os.environ.get("M_GAP", 1.6))
for i, c in enumerate(["F2", "F3", "F4", "Roof"]):
    z = G * (i + 1)
    rig(c, [(372, 0), (430, z), (540, z), (590, 0)])
BG = float(os.environ.get("M_BGAP", 2.5))
for i, c in enumerate(["B1", "B2", "B3"]):
    z = -BG * (i + 1)
    rig(c, [(1, z), (120, z), (160, 0), (3600, 0), (3660, z)])
# elevator shaft out of the way in basement shots
e = bpy.data.objects.new("Rig_Elevator", None); sc.collection.objects.link(e)
for o in bpy.data.collections["Elevator"].all_objects:
    if o.parent is None: o.parent = e; o.matrix_parent_inverse.identity()
for f, z in [(1, 0), (2461, 500), (3616, 0)]:
    e.location.z = z; e.keyframe_insert("location", index=2, frame=f)
for k in e.animation_data.action.fcurves[0].keyframe_points: k.interpolation = "CONSTANT"
# hide the camera-facing void walls so the stacked basements show
for n in ("VoidWallFront", "VoidWallRight"):
    o = bpy.data.objects[n]
    if o.animation_data: o.animation_data.action = None
    o.hide_render = True
# lighting / colour
sc.eevee.use_shadows = True
try:
    sc.eevee.use_raytracing = True; sc.eevee.ray_tracing_method = "SCREEN"
    sc.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
except Exception as ex: print("rt", ex)
print("match v3 done")
