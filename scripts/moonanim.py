# moonanim.py — animation layer for the moon base remake.
# Builds the still scene by executing scripts/moonbase.py unchanged (its still render and .blend save are
# stripped at load time), then adds every keyframe on top. Scene refinements in moonbase.py flow in automatically.
#
# Env:
#   FRANGE "a-b" (default 1-2012), FSTEP (1), CHUNK/NCHUNK (interleaved split for the matrix), OUTDIR (out/frames),
#   FMT JPEG|PNG, PCT / PS (resolution % and Eevee samples, read by moonbase.py), DRY=1 (build + report, no render),
#   SAVEBLEND=1 (write OUTDIR/moonanim.blend), GLARE=0 (no compositor glow), TIMES=1 (per-frame seconds log).
# Timeline (seconds; frame = round(t*30)+1) is documented in moonbase_notes.md "Animation timeline".
import bpy, os, sys, math, random, time
from mathutils import Vector, Matrix

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "scripts"
MB = os.path.join(_here, "moonbase.py")
if not os.path.exists(MB): MB = "scripts/moonbase.py"
os.environ.setdefault("OUT", "/tmp/moonanim_build/moon_hero.png")
_src = open(MB).read()
_n1 = _src.count("bpy.ops.render.render(write_still=True)")
_src = _src.replace("bpy.ops.render.render(write_still=True)", "pass  # moonanim: still render skipped")
_src = _src.replace("bpy.ops.wm.save_as_mainfile(", "(lambda **_k: None)(")
print("MOONANIM exec moonbase.py (render calls stripped: %d)" % _n1)
exec(compile(_src, MB, "exec"), globals())
ALWAYS_HIDDEN = {o.name for o in bpy.data.objects if o.hide_render}   # boolean cutters etc. must never be unhidden
print("MOONANIM always-hidden", sorted(ALWAYS_HIDDEN)[:12])
G = globals()

FPS = 30
NFR = 2012
def F(t): return int(round(t * FPS)) + 1
sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = NFR
bpy.context.view_layer.update()
rng = random.Random(11)

# ---------------- helpers ----------------
def wbb(o):
    if o.type in ('MESH', 'FONT', 'CURVE') and o.bound_box:
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        return lo, hi
    p = o.matrix_world.translation.copy(); return p, p

def ctr(o):
    lo, hi = wbb(o); return (lo + hi) / 2

def empty(name, loc):
    e = C.objects.new(name, None); sc.collection.objects.link(e); e.location = loc; return e

def parent_keep(child, par):
    child.parent = par
    child.matrix_parent_inverse = par.matrix_basis.inverted()

def kv(idb, path, f, val, index=-1):
    """set attribute path (dot-free) on idb and key it"""
    if index >= 0:
        getattr(idb, path)[index] = val
    else:
        setattr(idb, path, val)
    idb.keyframe_insert(path, index=index, frame=f)

def ksock(sock, f, val):
    sock.default_value = val; sock.keyframe_insert("default_value", frame=f)

def fcurves_of(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    try:
        return list(act.fcurves)
    except Exception:
        out = []
        for lay in act.layers:
            for st in lay.strips:
                cb = st.channelbag(ad.action_slot)
                if cb: out += list(cb.fcurves)
        return out

def fcurve(idb, path, index=0):
    for fc in fcurves_of(idb):
        if fc.data_path == path and fc.array_index == index: return fc
    return None

def set_interp(idb, kind, path=None):
    for fc in fcurves_of(idb):
        if path and fc.data_path != path: continue
        for kp in fc.keyframe_points: kp.interpolation = kind

HIDE = {}   # obj name -> list of (t0, t1) hidden intervals
def hide_iv(o, t0, t1): HIDE.setdefault(o.name, []).append((t0, t1))

def apply_hides():
    for nm, ivs in HIDE.items():
        o = C.objects.get(nm)
        if o is None or nm in ALWAYS_HIDDEN: continue
        ivs = sorted(ivs); merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
            else: merged.append([a, b])
        keys = {}
        keys[1] = merged[0][0] <= 0
        for a, b in merged:
            fa, fb = max(1, F(a)), F(b)
            keys[fa] = True
            if fb <= NFR + 1: keys[fb] = False
        for f in sorted(keys):
            o.hide_render = keys[f]; o.keyframe_insert("hide_render", frame=f)
        o.hide_render = keys[1]
    print("MOONANIM hide keys on", len(HIDE), "objects")

def emit_mat(name, col, strength, alpha_from=None):
    m = C.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs[0]); return m, e

def radial_mat(name, col, strength, profile):
    """camera-facing disc material: emission * profile(d) blended over transparent; d = |object coords| (plane size 2)"""
    m = C.materials.new(name); m.use_nodes = True; nt = m.node_tree; N_ = nt.nodes; L_ = nt.links; N_.clear()
    o = N_.new("ShaderNodeOutputMaterial"); mx = N_.new("ShaderNodeMixShader"); tr = N_.new("ShaderNodeBsdfTransparent")
    e = N_.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = strength
    tc = N_.new("ShaderNodeTexCoord"); ln = N_.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
    L_.new(tc.outputs["Object"], ln.inputs[0])
    out = profile(N_, L_, ln.outputs["Value"])
    cl = N_.new("ShaderNodeClamp"); L_.new(out, cl.inputs["Value"])
    L_.new(cl.outputs[0], mx.inputs["Fac"]); L_.new(tr.outputs[0], mx.inputs[1]); L_.new(e.outputs[0], mx.inputs[2])
    L_.new(mx.outputs[0], o.inputs["Surface"])
    try: m.surface_render_method = 'BLENDED'
    except Exception: pass
    return m, e

def mth(N_, L_, op, a, b=None, bv=None):
    n = N_.new("ShaderNodeMath"); n.operation = op
    if isinstance(a, (int, float)): n.inputs[0].default_value = a
    else: L_.new(a, n.inputs[0])
    if b is not None: L_.new(b, n.inputs[1])
    elif bv is not None: n.inputs[1].default_value = bv
    return n.outputs[0]

def gauss(N_, L_, d, d0, w, amp=1.0):
    x = mth(N_, L_, 'SUBTRACT', d, bv=d0); x = mth(N_, L_, 'DIVIDE', x, bv=w); x = mth(N_, L_, 'MULTIPLY', x, x)
    x = mth(N_, L_, 'MULTIPLY', x, bv=-1.0); x = mth(N_, L_, 'EXPONENT', x)
    return mth(N_, L_, 'MULTIPLY', x, bv=amp)

def disc_plane(name, m, radius, parent, loc):
    bpy.ops.mesh.primitive_plane_add(size=2)
    p = bpy.context.object; p.name = name; p.data.materials.append(m)
    p.parent = parent; p.matrix_parent_inverse = Matrix.Identity(4)
    p.location = loc; p.scale = (radius, radius, 1); p.visible_shadow = False
    try:
        p.visible_diffuse = False; p.visible_glossy = False
    except Exception: pass
    return p

# ================= snapshot memberships BEFORE adding anything =================
base_objs = list(C.objects)
OPEN_Y = -24.0   # plug slide-out offset (fully off frame at hero framing)
def in_cut(x, y):
    return (x > XC - 1.3 and y < YC + 0.02) or (x > EX - 0.7 and y < EY + 2.3)

# rocket parts: near the pad axis, above the pad (feet/legs are on the pad)
rocket_parts = []
for o in base_objs:
    if o.parent is not None or o.type not in ('MESH', 'FONT', 'CURVE'): continue
    nm = o.name.split('.')[0]
    if nm in ('pad', 'Torus', 'block', 'lz') or nm.startswith('Torus'): continue
    lo, hi = wbb(o); c = (lo + hi) / 2
    d = math.hypot(c.x - PX, c.y - PY)
    if d < 2.0 and (lo.z > 0.3 or nm in ('foot', 'leg', 'leg2', 'engbay')):
        rocket_parts.append(o)
print("MOONANIM rocket parts", len(rocket_parts), sorted(set(o.name.split('.')[0] for o in rocket_parts)))

# floors: membership by centre z band inside the cutaway footprint (lights by name)
floor_objs = {i: [] for i in range(NF)}
for o in base_objs:
    nm = o.name.split('.')[0]
    if o.type == 'LIGHT':
        for i in range(NF):
            if nm in (f"fl{i}", f"flb{i}"): floor_objs[i].append(o)
        continue
    if o.parent is not None or o.type not in ('MESH', 'FONT', 'CURVE'): continue
    if nm in ('block',): continue
    c = ctr(o)
    if not (c.x > XC - 0.1 and c.y < YC + 0.05 and c.x < A + 0.2 and c.y > -B - 0.2): continue
    for i in range(NF):
        zf = Z0 - i * FH
        if zf - 0.25 <= c.z < zf + FH - 0.25: floor_objs[i].append(o)
print("MOONANIM floor objs", {i: len(v) for i, v in floor_objs.items()})

# objects hidden while the cutaway lid is closed (inside the lid footprint)
lid_hidden = []
for o in base_objs:
    if o.parent is not None: continue
    nm = o.name.split('.')[0]
    if nm in ('block', 'cutbox', 'slotbox', 'notchbox', 'colbox', 'cam', 'sun', 'fill'): continue
    if o in rocket_parts: continue
    c = ctr(o)
    if in_cut(c.x, c.y) and c.y > -B - 0.05 and c.x < A + 0.1 and c.z > FZ_BOT - 0.6 and c.z < 3.0:
        lid_hidden.append(o)
print("MOONANIM lid-hidden", len(lid_hidden))

# bots (sphere 'bot', cone 'botb', eyes) and elevator cab
bot_spheres = [o for o in base_objs if o.name.split('.')[0] == 'bot']
cz_ = Z0 - 2 * FH
cab_parts = []
for o in base_objs:
    nm = o.name.split('.')[0]
    if nm in ('elev', 'efr', 'eh1', 'eh2', 'ebar', 'eback'): continue
    c = ctr(o)
    if abs(c.x - EX) < 0.45 and abs(c.y - EY) < 0.45 and cz_ - 0.1 < c.z < cz_ + 1.25:
        cab_parts.append(o)
print("MOONANIM cab parts", sorted(set(o.name.split('.')[0] for o in cab_parts)))

# ================= camera =================
OS0 = cam.ortho_scale
T_HERO = target.copy()
T_SOLAR = target + up * float(os.environ.get("SOLAR_UP", 2.6))
OSF = float(os.environ.get("OSF", 6.8)); OSF0 = float(os.environ.get("OSF0", 8.5))
def FT(i, dz=None):
    if dz is None: dz = float(os.environ.get("FTDZ0", 0.7)) if i == 0 else float(os.environ.get("FTDZ", 0.3))
    return Vector((2.9, -3.3, Z0 - i * FH + dz))
CZ = float(os.environ.get("CAVEZ", -30.0))
T_TBM = Vector((2.2, -4.6, FZ_BOT + 1.7)); OS_TBM = 8.0
T_CAVE = Vector((2.7, -3.0, CZ + float(os.environ.get("CAVEDZ", 4.5)))); OS_CAVE = float(os.environ.get("OSCAVE", 12.5))
T_INT = Vector((2.6, -3.4, Z0 - 2.0 * FH)); OS_INT = 11.0
dr = right * 0.35
CAM_KEYS = [
    (0.0, T_HERO, OS0), (10.3, T_HERO, OS0),
    (12.0, FT(0), OSF0), (15.9, FT(0) + dr, OSF0),
    (16.5, FT(1), OSF), (19.9, FT(1) + dr, OSF),
    (20.5, FT(2), OSF), (23.9, FT(2) + dr, OSF),
    (24.5, FT(3), OSF), (30.4, FT(3) + dr, OSF),
    (32.0, T_HERO, OS0), (33.0, T_HERO, OS0),
    (33.6, T_SOLAR, OS0), (44.4, T_SOLAR, OS0),
    (46.5, T_TBM, OS_TBM), (49.9, T_TBM + dr * 0.6, OS_TBM),
    (52.4, T_CAVE, OS_CAVE), (58.36, T_CAVE + dr * 0.5, OS_CAVE * 0.95),
    (58.4, T_INT, OS_INT), (59.6, T_INT + up * 0.6, OS_INT * 1.05),
    (62.0, T_HERO, OS0), (67.1, T_HERO, OS0),
]
for t, tg, osc in CAM_KEYS:
    f = F(t)
    co.location = tg + back * 60; co.keyframe_insert("location", frame=f)
    cam.ortho_scale = osc; cam.keyframe_insert("ortho_scale", frame=f)
cam.clip_end = 400
co_inv = co.matrix_world.inverted()

# sky (earth, halo, stars) rides with the camera so it keeps its screen position while the camera pans
bpy.context.view_layer.update()
CAM0 = co.matrix_world.copy()
# reset camera to frame-1 pose for parenting
co.location = T_HERO + back * 60; bpy.context.view_layer.update(); CAM0 = co.matrix_world.copy()
sky = [earth] + ([G['halo']] if G.get('halo') else []) + ([G['sp']] if G.get('sp') else [])
for o in sky:
    o.parent = co; o.matrix_parent_inverse = CAM0.inverted()
EARTH_L = CAM0.inverted() @ earth.matrix_world.translation
ER = earth.dimensions.x / 2 if earth.dimensions.x > 0 else 2.0
print("MOONANIM earth local", tuple(round(v, 2) for v in EARTH_L), "r", round(ER, 2))

# ================= cutaway lid (4 sliding layers of rock with a regolith top) =================
import bmesh as _bm
def lid_layer(name, z0, z1, top):
    bm = _bm.new()
    boxes = [(XC, A + 0.05, -B - 0.05, YC), (EX - 0.6, A + 0.05, YC - 0.1, EY + 0.6),
             (XC - 1.25, XC + 0.1, -B - 0.05, -B + 0.2)]
    if top: boxes.append((EX - 0.5, A + 0.05, YC, EY + 2.2))
    for (x0, x1, y0, y1) in boxes:
        zz0 = z0 if not (top and x0 == EX - 0.5) else max(z0, Z0 - 0.16)
        r = _bm.ops.create_cube(bm, size=1.0)
        for v in r['verts']:
            v.co.x = x0 if v.co.x < 0 else x1; v.co.y = y0 if v.co.y < 0 else y1; v.co.z = zz0 if v.co.z < 0 else z1
    me = C.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(M_rock); o.data.materials.append(M_reg)
    for p in me.polygons:
        p.material_index = 1 if (top and p.normal.z > 0.5) else 0
    return o
LZ = [(-2.2, 0.0), (-4.3, -2.2), (-6.4, -4.3), (FZ_BOT, -6.4)]
lids = []
for L_i, (z0, z1) in enumerate(LZ):
    o = lid_layer(f"lid{L_i}", z0, z1, L_i == 0); lids.append(o)
    c0 = 2.3 + (3 - L_i) * 0.12; c1 = c0 + 1.3
    o0 = 6.3 + L_i * 0.12; o1 = o0 + 1.2
    for t, y in [(0.0, OPEN_Y), (c0, OPEN_Y), (c1, 0.0), (o0, 0.0), (o1, OPEN_Y)]:
        kv(o, "location", F(t), y, 1)
    hide_iv(o, -1, c0 - 0.05); hide_iv(o, o1 + 0.05, 99)
for o in lid_hidden: hide_iv(o, 4.0, 6.3)

# ================= floors hidden above the focused floor =================
FOCUS = [(16.2, 20.2, {0}), (20.2, 24.2, {0, 1}), (24.2, 30.6, {0, 1, 2}), (45.6, 58.39, {0, 1, 2})]
for t0, t1, fl in FOCUS:
    for i in fl:
        for o in floor_objs[i]: hide_iv(o, t0, t1)

# ================= rocket: launch and landing =================
rig = empty("RocketRig", (PX, PY, 0.0))
for o in rocket_parts: parent_keep(o, rig)
# engine plume (cone pointing down) + light, children of the rig
M_plume, E_plume = emit_mat("plume", (0.78, 0.86, 1.0), 40.0)
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.05, radius2=0.85, depth=2.6, location=(PX, PY, RB - 1.3 - 0.15))
plume = bpy.context.object; plume.name = "plume"; plume.data.materials.append(M_plume); plume.visible_shadow = False
parent_keep(plume, rig)
eL = C.lights.new("englight", 'POINT'); eL.color = (0.8, 0.88, 1.0); eL.shadow_soft_size = 0.8; eL.energy = 0
eLo = C.objects.new("englight", eL); sc.collection.objects.link(eLo); eLo.location = (PX, PY, RB - 0.9); parent_keep(eLo, rig)
ROCK_TOP = float(os.environ.get("ROCKET_OUT", 15.0))

def rocket_z(t):
    if t < 6.5: return 0.0
    if t < 9.0:   # launch: constant acceleration, out of frame by ~8.8 s
        a = 2 * ROCK_TOP / (2.3 ** 2); return 0.5 * a * (t - 6.5) ** 2
    if t < 60.6: return 40.0
    if t < 63.3:  # landing: decelerating to touchdown
        u = (t - 60.6) / 2.7; return (ROCK_TOP + 2.0) * (1 - u) ** 2.2
    return 0.0
for f in range(F(6.4), F(63.5) + 1, 2):
    t = (f - 1) / FPS
    if 9.2 < t < 60.4: continue
    kv(rig, "location", f, rocket_z(t), 2)
kv(rig, "location", 1, 0.0, 2); kv(rig, "location", F(9.1), 40.0, 2); kv(rig, "location", F(60.5), 40.0, 2)
set_interp(rig, 'LINEAR')
for o in rocket_parts + [plume]: hide_iv(o, 9.3, 60.5)
# plume size / strength and light energy
for t, s, e, en in [(0, 0, 0, 0), (6.0, 0.0, 0, 0), (6.15, 0.6, 30, 1500), (6.5, 1.0, 45, 4000), (8.8, 1.2, 45, 4000), (9.1, 1.2, 0, 0),
                    (60.5, 0.0, 0, 0), (60.7, 1.0, 45, 3000), (62.6, 1.0, 45, 4000), (63.2, 0.7, 30, 2000), (63.6, 0.0, 0, 0)]:
    plume.scale = (max(s, 0.001),) * 3; plume.keyframe_insert("scale", frame=F(t))
    ksock(E_plume.inputs["Strength"], F(t), e)
    kv(eL, "energy", F(t), en)

# exhaust trail column above the pad after lift-off
bm = _bm.new(); _bm.ops.create_cone(bm, cap_ends=False, segments=32, radius1=0.75, radius2=0.95, depth=1.0)
for v in bm.verts: v.co.z += 0.5
me = C.meshes.new("trail"); bm.to_mesh(me); bm.free()
trail = C.objects.new("trail", me); sc.collection.objects.link(trail); trail.location = (PX, PY, 0.15); trail.visible_shadow = False
M_trail = C.materials.new("trail"); M_trail.use_nodes = True; nt = M_trail.node_tree; nt.nodes.clear()
_o = nt.nodes.new("ShaderNodeOutputMaterial"); _mx = nt.nodes.new("ShaderNodeMixShader"); _tr = nt.nodes.new("ShaderNodeBsdfTransparent")
E_trail = nt.nodes.new("ShaderNodeEmission"); E_trail.inputs["Color"].default_value = (0.35, 0.55, 1.0, 1)
_mx.inputs["Fac"].default_value = 0.45
nt.links.new(_tr.outputs[0], _mx.inputs[1]); nt.links.new(E_trail.outputs[0], _mx.inputs[2]); nt.links.new(_mx.outputs[0], _o.inputs[0])
try: M_trail.surface_render_method = 'BLENDED'
except Exception: pass
trail.data.materials.append(M_trail)
for f in range(F(6.5), F(9.2) + 1, 2):
    t = (f - 1) / FPS
    trail.scale = (1, 1, max(0.01, rocket_z(t) + RB - 0.3)); trail.keyframe_insert("scale", frame=f)
trail.scale = (1, 1, 40); trail.keyframe_insert("scale", frame=F(9.3))
for t, e in [(0, 0), (6.6, 0), (7.2, 3.0), (8.8, 3.0), (9.9, 0)]:
    ksock(E_trail.inputs["Strength"], F(t), e)
hide_iv(trail, -1, 6.5); hide_iv(trail, 10.0, 99)

# scorched crater on the pad between launch and landing (hot glow fading after lift-off)
M_crat = mat("crater", (0.012, 0.012, 0.014), 0.8, emit=(0.5, 0.7, 1.0), estr=0.0)
crat = cyl("crater", (PX, PY, 0.128), 1.45, 0.012, M_crat, 64)
cb = M_crat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for t, e in [(0, 0), (7.0, 0), (7.6, 6.0), (8.8, 4.0), (9.9, 0.0), (60.4, 0.0), (61.2, 3.0), (63.2, 3.0), (63.4, 0)]:
    ksock(cb, F(t), e)
hide_iv(crat, -1, 7.0); hide_iv(crat, 63.35, 99)

# ================= sun, eclipse =================
M_sun, E_sun = emit_mat("sundisc", (1.0, 0.98, 0.94), 30.0)
sun_disc = sph("sundisc", (0, 0, 0), 0.95, M_sun, seg=32); sun_disc.parent = co; sun_disc.matrix_parent_inverse = Matrix.Identity(4)
sun_disc.visible_shadow = False
M_sh, E_sh = radial_mat("sunhalo", (1.0, 0.95, 0.85), 6.0,
                        lambda N_, L_, d: mth(N_, L_, 'POWER', mth(N_, L_, 'SUBTRACT', 1.0, d), bv=float(os.environ.get("SHP", 3.6))))
sun_halo = disc_plane("sunhalo", M_sh, float(os.environ.get("SHR", 2.6)), sun_disc, (0, 0, -0.5))
S_A = Vector((-7.2, 10.0, -150.0)); S_E = Vector((EARTH_L.x, EARTH_L.y, -150.0)); S_X = Vector((-1.6, 10.2, -150.0))
for t, p, s in [(0, S_A, 0.0), (33.3, S_A, 0.0), (33.8, S_A, 1.0), (36.0, S_A, 1.0), (39.0, S_E, 1.0),
                (61.6, S_E, 1.0), (63.4, S_X, 1.0), (64.2, S_X, 0.0)]:
    sun_disc.location = p; sun_disc.keyframe_insert("location", frame=F(t))
    sun_disc.scale = (max(s, 0.001),) * 3; sun_disc.keyframe_insert("scale", frame=F(t))
for t, e in [(0, 6.0), (38.3, 6.0), (38.9, 0.0), (61.6, 0.0), (62.3, 6.0)]:   # ref: no white glow while the sun is behind the earth, only the thin red ring
    ksock(E_sh.inputs["Strength"], F(t), e)
hide_iv(sun_disc, 38.95, 61.55); hide_iv(sun_halo, 38.95, 61.55)
hide_iv(sun_disc, -1, 33.3); hide_iv(sun_halo, -1, 33.3); hide_iv(sun_disc, 64.25, 99); hide_iv(sun_halo, 64.25, 99)
# corona ring behind the darkened earth
rp = ER * 1.3
RSTR = float(os.environ.get('RSTR', 4.0))
M_ring, E_ring = radial_mat("corona", (1.0, 0.42, 0.1), 0.0,
                            lambda N_, L_, d: mth(N_, L_, 'ADD', gauss(N_, L_, d, ER * 1.01 / rp, float(os.environ.get('RW1', 0.012)), 1.0), gauss(N_, L_, d, ER * 1.03 / rp, float(os.environ.get('RW2', 0.05)), float(os.environ.get('RG2', 0.25)))))
ring = disc_plane("corona", M_ring, rp, co, Vector((EARTH_L.x, EARTH_L.y, EARTH_L.z - ER - 2.0)))
for t, e in [(0, 0), (38.7, 0), (39.3, RSTR), (61.3, RSTR), (61.9, 0)]:
    ksock(E_ring.inputs["Strength"], F(t), e)
hide_iv(ring, -1, 38.6); hide_iv(ring, 62.0, 99)
# earth terminator follows the sun behind it (light direction animated in the earth + halo shaders)
def dot_nodes(mname):
    m = C.materials.get(mname)
    if not m: return []
    return [n for n in m.node_tree.nodes if n.type == 'VECT_MATH' and n.operation == 'DOT_PRODUCT'
            and n.inputs[0].is_linked and n.inputs[0].links[0].from_node.type == 'NEW_GEOMETRY']
LD0 = Vector(dot_nodes("earth")[0].inputs[1].default_value) if dot_nodes("earth") else (-right)
LD1 = (-right * 0.3 - back * 0.95).normalized(); LD2 = (-back).normalized()
for n in dot_nodes("earth") + dot_nodes("halo"):
    for t, v in [(0, LD0), (36.2, LD0), (38.2, LD1), (38.9, LD2), (61.6, LD2), (62.4, LD1), (63.6, LD0)]:
        ksock(n.inputs[1], F(t), v)

# city lights on the night side during the eclipse (ref: dark earth speckled with warm lights)
_me = C.materials.get("earth")
if _me and os.environ.get("ECITY", "1") != "0":
    _n = _me.node_tree.nodes; _l = _me.node_tree.links
    _img = [n for n in _n if n.type == 'TEX_IMAGE']
    _tm = [n for n in _n if n.type == 'MAP_RANGE' and getattr(n, 'interpolation_type', '') == 'SMOOTHSTEP']
    _out = [n for n in _n if n.type == 'OUTPUT_MATERIAL'][0]
    if _img and _tm and _out.inputs["Surface"].is_linked:
        _tc = _n.new("ShaderNodeTexCoord")
        _vo = _n.new("ShaderNodeTexVoronoi"); _vo.inputs["Scale"].default_value = float(os.environ.get("ECSC", 70)); _l.new(_tc.outputs["Object"], _vo.inputs["Vector"])
        _dot = _n.new("ShaderNodeMapRange"); _dot.inputs["From Min"].default_value = 0.0; _dot.inputs["From Max"].default_value = 0.22; _dot.inputs["To Min"].default_value = 1.0; _dot.inputs["To Max"].default_value = 0.0
        _l.new(_vo.outputs["Distance"], _dot.inputs["Value"])
        _cl = _n.new("ShaderNodeTexNoise"); _cl.inputs["Scale"].default_value = 9.0; _l.new(_tc.outputs["Object"], _cl.inputs["Vector"])
        _clr = _n.new("ShaderNodeMapRange"); _clr.inputs["From Min"].default_value = 0.45; _clr.inputs["From Max"].default_value = 0.65; _l.new(_cl.outputs["Fac"], _clr.inputs["Value"])
        _sep = _n.new("ShaderNodeSeparateColor"); _l.new(_img[0].outputs["Color"], _sep.inputs[0])
        _a = _n.new("ShaderNodeMath"); _a.operation = 'ADD'; _l.new(_sep.outputs[0], _a.inputs[0]); _l.new(_sep.outputs[1], _a.inputs[1])
        _b = _n.new("ShaderNodeMath"); _b.operation = 'MULTIPLY_ADD'; _b.inputs[1].default_value = 0.5; _l.new(_a.outputs[0], _b.inputs[0])
        _nb = _n.new("ShaderNodeMath"); _nb.operation = 'MULTIPLY'; _nb.inputs[1].default_value = -1; _l.new(_sep.outputs[2], _nb.inputs[0]); _l.new(_nb.outputs[0], _b.inputs[2])
        _land = _n.new("ShaderNodeMapRange"); _land.inputs["From Min"].default_value = 0.0; _land.inputs["From Max"].default_value = 0.1; _l.new(_b.outputs[0], _land.inputs["Value"])
        _night = _n.new("ShaderNodeMath"); _night.operation = 'SUBTRACT'; _night.inputs[0].default_value = 1.0; _l.new(_tm[0].outputs["Result"], _night.inputs[1])
        _m1 = _n.new("ShaderNodeMath"); _m1.operation = 'MULTIPLY'; _l.new(_dot.outputs["Result"], _m1.inputs[0]); _l.new(_clr.outputs["Result"], _m1.inputs[1])
        _m2 = _n.new("ShaderNodeMath"); _m2.operation = 'MULTIPLY'; _l.new(_m1.outputs[0], _m2.inputs[0]); _l.new(_land.outputs["Result"], _m2.inputs[1])
        _m3 = _n.new("ShaderNodeMath"); _m3.operation = 'MULTIPLY'; _l.new(_m2.outputs[0], _m3.inputs[0]); _l.new(_night.outputs[0], _m3.inputs[1])
        _ce = _n.new("ShaderNodeEmission"); _ce.inputs["Color"].default_value = (1.0, 0.72, 0.35, 1); _l.new(_m3.outputs[0], _ce.inputs["Strength"])
        _sm = _n.new("ShaderNodeMath"); _sm.operation = 'MULTIPLY'; _l.new(_m3.outputs[0], _sm.inputs[0])
        _l.new(_sm.outputs[0], _ce.inputs["Strength"])
        _prev = _out.inputs["Surface"].links[0].from_socket
        _ad = _n.new("ShaderNodeAddShader"); _l.new(_prev, _ad.inputs[0]); _l.new(_ce.outputs[0], _ad.inputs[1]); _l.new(_ad.outputs[0], _out.inputs["Surface"])
        _cs = float(os.environ.get("ECITYS", 6.0))
        for t, e in [(0, 0.0), (37.8, 0.0), (39.0, _cs), (61.4, _cs), (62.4, 0.0)]:
            ksock(_sm.inputs[1], F(t), e)
        print("MOONANIM city lights on")
# cutaway cavity faces: ref close-ups show layered grey rock where ours were flat black
_mw = C.materials.get("wall")
if _mw and _mw.use_nodes and os.environ.get("ROCKWALL", "1") != "0":
    _n = _mw.node_tree.nodes; _l = _mw.node_tree.links
    _bs = [n for n in _n if n.type == 'BSDF_PRINCIPLED'][0]
    _tc = _n.new("ShaderNodeTexCoord")
    _wv = _n.new("ShaderNodeTexWave"); _wv.wave_type = 'BANDS'; _wv.bands_direction = 'Z'
    _wv.inputs["Scale"].default_value = float(os.environ.get("RWS", 0.9)); _wv.inputs["Distortion"].default_value = 6.0; _wv.inputs["Detail"].default_value = 4.0; _wv.inputs["Detail Scale"].default_value = 1.5
    _l.new(_tc.outputs["Generated"] if False else _tc.outputs["Object"], _wv.inputs["Vector"])
    _rr = _n.new("ShaderNodeValToRGB"); _rr.color_ramp.elements[0].color = (0.05, 0.05, 0.055, 1); _rr.color_ramp.elements[1].color = (0.24, 0.24, 0.25, 1)
    _l.new(_wv.outputs["Fac"], _rr.inputs["Fac"])
    _mx = _n.new("ShaderNodeMixRGB"); _mx.inputs["Color1"].default_value = tuple(_bs.inputs["Base Color"].default_value)
    _l.new(_rr.outputs["Color"], _mx.inputs["Color2"]); _l.new(_mx.outputs["Color"], _bs.inputs["Base Color"])
    for t, v in [(0, 0.0), (11.0, 0.0), (12.0, 1.0), (30.6, 1.0), (31.6, 0.0), (45.0, 0.0), (46.0, 1.0), (58.4, 1.0), (58.5, 0.0)]:
        ksock(_mx.inputs["Fac"], F(t), v)
    print("MOONANIM rock cavity walls on")
# red eclipse tint: rock/regolith multiplied toward rust, sun + fill + world go red
TINT = (1.0, 0.42, 0.33, 1.0)
def tint_socket(m):
    if m is None or not m.use_nodes: return None
    nt = m.node_tree; b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None: return None
    s = b.inputs["Base Color"]; mx = nt.nodes.new("ShaderNodeMixRGB"); mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 0.0
    if s.is_linked:
        nt.links.new(s.links[0].from_socket, mx.inputs[1])
    else:
        mx.inputs[1].default_value = s.default_value
    mx.inputs[2].default_value = TINT; nt.links.new(mx.outputs[0], s); return mx.inputs[0]
TT = [(0, 0.0), (38.6, 0.0), (39.4, 1.0), (61.4, 1.0), (62.2, 0.0)]
tinted = set()
for o in base_objs:
    if o.type != 'MESH' or o in rocket_parts: continue
    for sl in o.material_slots:
        m = sl.material
        if m and m.name.split('.')[0] in ('rock', 'regolith', 'boulder', 'recg2') and m.name not in tinted:
            tinted.add(m.name)
for mn in tinted:
    s = tint_socket(C.materials[mn])
    if s is not None:
        for t, v in TT: ksock(s, F(t), v)
print("MOONANIM tinted materials", sorted(tinted))
sunL = so.data; fillL = fo.data
for t, v in TT:
    sunL.color = (1, 1, 1) if v == 0 else (1.0, 0.36, 0.24); sunL.keyframe_insert("color", frame=F(t))
    fillL.color = (1, 1, 1) if v == 0 else (1.0, 0.45, 0.35); fillL.keyframe_insert("color", frame=F(t))
# sun/fill energy: dim red during the eclipse, off while the camera is in the cave (cave is lamp-lit only)
for t, se, fe in [(0, 3.0, 1.0), (38.6, 3.0, 1.0), (39.4, 1.6, 0.7), (51.4, 1.6, 0.7), (52.3, 0.0, 0.0), (58.37, 0.0, 0.0),
                  (58.4, 1.6, 0.7), (61.4, 1.6, 0.7), (62.2, 3.0, 1.0)]:
    kv(sunL, "energy", F(t), se); kv(fillL, "energy", F(t), fe)
bg = wd.node_tree.nodes["Background"].inputs["Color"]
for t, v in TT: ksock(bg, F(t), (0.02, 0.022, 0.026, 1) if v == 0 else (0.035, 0.01, 0.008, 1))

# ================= TBM (the tank under the lowest floor) =================
TB = Vector((1.55 + TX, TY, FZ_BOT + 0.55))
tbm = empty("TBMRig", TB)
for o in base_objs:
    if o.name.split('.')[0] in ('tankfan', 'fanblade'): parent_keep(o, tbm)
tbm.rotation_euler = (0, 0, 0); tbm.keyframe_insert("rotation_euler", index=0, frame=F(47.0))
tbm.rotation_euler = (math.radians(360 * 5), 0, 0); tbm.keyframe_insert("rotation_euler", index=0, frame=F(50.6))
set_interp(tbm, 'LINEAR')
tl = C.lights.new("tbmlight", 'SPOT'); tl.energy = 900; tl.color = (1, 0.97, 0.9); tl.spot_size = math.radians(70); tl.spot_blend = 0.6
tlo = C.objects.new("tbmlight", tl); sc.collection.objects.link(tlo); tlo.location = TB + Vector((0.5, -0.9, 0.5))
tlo.rotation_euler = Vector((0.3, -1.0, -0.15)).normalized().to_track_quat('-Z', 'Y').to_euler()
hide_iv(tlo, -1, 45.5); hide_iv(tlo, 50.8, 99)

# ================= deep rock column + cave + monolith (visible 49.8-58.4 s) =================
pre = set(C.objects.keys())
def rockbox(name, x0, x1, y0, y1, z0, z1, m=None):
    o = box(name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), m or M_rock); return o
CH = 6.0
def strata_mat():
    m = C.materials.new("strata"); m.use_nodes = True
    nt = m.node_tree; b = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'
    wv.inputs["Scale"].default_value = float(os.environ.get("SWS", 3.5)); wv.inputs["Distortion"].default_value = 3.0
    wv.inputs["Detail"].default_value = 5.0; wv.inputs["Detail Scale"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (0.04, 0.02, 0.015, 1); rp.color_ramp.elements[1].color = (0.20, 0.10, 0.06, 1)
    nt.links.new(wv.outputs["Fac"], rp.inputs["Fac"])
    gn = nt.nodes.new("ShaderNodeNewGeometry"); sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(gn.outputs["Normal"], sp.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMixRGB"); mx.blend_type = 'MIX'
    mx.inputs["Color2"].default_value = (0.012, 0.008, 0.008, 1)
    cl = nt.nodes.new("ShaderNodeMath"); cl.operation = 'MULTIPLY'; cl.use_clamp = True; cl.inputs[1].default_value = 3.0
    nt.links.new(sp.outputs["Z"], cl.inputs[0]); nt.links.new(cl.outputs[0], mx.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], mx.inputs["Color1"])
    nt.links.new(mx.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(mx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = float(os.environ.get("SEM", 0.25))
    b.inputs["Roughness"].default_value = 0.95
    return m
M_strata = strata_mat()
rockbox("deep", -A, A, -B, B, CZ + CH, FZ_BOT - 0.4, M_strata)
_W = float(os.environ.get("RWIDE", 3.0))
rockbox("deepwide", -A * _W, A * _W, -B * _W, B * _W, CZ - 16, FZ_BOT - 0.4, M_strata)
rockbox("cavewl", -A, XC - 0.5, -B, B, CZ, CZ + CH)
rockbox("cavewb", XC - 0.5, A, 0.5, B, CZ, CZ + CH)
M_cfl = mat("cavefloor", (0.36, 0.3, 0.29), 0.95, spec=0.2)
rockbox("cavebase", -A, A, -B, B, CZ - 16, CZ, M_strata)
rockbox("cavefl", XC - 0.5, A, -B, 0.5, CZ - 0.05, CZ + 0.02, M_cfl)
M_crock = mat("caverock", (0.11, 0.095, 0.095), 0.95)
for i in range(70):
    x = rng.uniform(XC - 0.3, A - 0.2); y = rng.uniform(-B + 0.2, 0.3)
    if math.hypot(x - 2.9, y + 2.6) < 1.3: continue
    r = rng.uniform(0.08, 0.38) * (1.6 if rng.random() < 0.15 else 1.0)
    o = ico("caverock", (x, y, CZ + r * 0.35), r, M_crock, 1)
    o.scale = (rng.uniform(0.8, 1.4), rng.uniform(0.8, 1.4), rng.uniform(0.5, 0.9)); o.rotation_euler = (rng.random(), rng.random(), rng.random() * 6)
# monolith (1:4:9), wide face toward -y
M_mono = mat("monolith", (0.006, 0.006, 0.007), 0.22, 0.2, emit=(0.08, 1.0, 0.3), estr=0.0)
mono = box("monolith", (2.9, -2.6, CZ + 2.0), (1.8, 0.45, 4.05), M_mono)
ms = M_mono.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for t, v in [(0, 0), (56.3, 0), (56.9, 0.5), (58.4, 0.6)]: ksock(ms, F(t), v)
box("mnote", (3.45, -2.6 - 0.235, CZ + 3.1), (0.32, 0.01, 0.32), mat("note", (0.95, 0.75, 0.1), 0.6, emit=(1, 0.75, 0.1), estr=0.4))
eyes = [sph("monoeye", (2.9 + dx, -2.6 - 0.24, CZ + 1.35), 0.13, emit_mat("monoeye", (1, 1, 1), 5.0)[0], (1, 0.35, 1.35), 16) for dx in (-0.28, 0.28)]
for e in eyes: hide_iv(e, -1, 56.6)
# rover pod with a headlight (top-left of the cave)
pod = sph("pod", (0.1, -0.6, CZ + 0.55), 0.6, mat("podm", (0.05, 0.05, 0.055), 0.35, 0.4), (1.2, 1, 0.9), 24)
sph("podlamp", (0.75, -0.95, CZ + 0.6), 0.14, emit_mat("podlamp", (1, 0.97, 0.9), 12.0)[0], (1, 1, 1), 12)
# bots in the cave
bot(3.75, -3.45, CZ, M_bots[4], 0.3)
bot(1.7, -3.9, CZ, M_bots[6], 0.26)
# lights
def plight(name, loc, col, en, r=0.4, kind='POINT'):
    l = C.lights.new(name, kind); l.color = col; l.energy = en
    if kind == 'POINT': l.shadow_soft_size = r
    o = C.objects.new(name, l); sc.collection.objects.link(o); o.location = loc; return o, l
lo_, lamp = plight("cavelamp", (3.3, -4.3, CZ + 0.5), (1.0, 0.5, 0.13), 1400, 0.5)
go_, glamp = plight("cavegreen", (2.9, -3.6, CZ + 0.6), (0.15, 1.0, 0.35), 0.0, 0.8)
plight("caveamb", (2.0, -2.5, CZ + CH - 0.4), (1.0, 0.75, 0.6), 250, 3.0)
so_, spot = plight("podspot", (0.8, -1.0, CZ + 0.7), (1, 0.97, 0.9), 600, kind='SPOT')
spot.spot_size = math.radians(60); so_.rotation_euler = Vector((1.0, -0.6, -0.25)).normalized().to_track_quat('-Z', 'Y').to_euler()
for t, a, g in [(0, 1400, 0), (56.3, 1400, 0), (56.9, 250, 1800), (58.4, 250, 1800)]:
    kv(lamp, "energy", F(t), a); kv(glamp, "energy", F(t), g)
cave_objs = [C.objects[n] for n in C.objects.keys() if n not in pre]
for o in cave_objs: hide_iv(o, -1, 49.8); hide_iv(o, 58.4, 99)
print("MOONANIM cave objects", len(cave_objs))

# ================= bots: bob + wander =================
BOTFAM = ('bot', 'botb', 'eye')
allbots = [o for o in C.objects if o.name.split('.')[0] == 'bot']
fam = [o for o in C.objects if o.name.split('.')[0] in ('botb', 'eye') and o.parent is None]
nb = 0
for bs in allbots:
    s = bs.dimensions.x / 1.6; p = bs.location.copy(); base = Vector((p.x, p.y, p.z - 0.95 * s))
    parts = [bs] + [o for o in fam if (o.location - p).length < s * 1.2 and o.parent is None]
    in_cab = bs in cab_parts
    r_ = empty("botrig", base)
    for o in parts: parent_keep(o, r_)
    if in_cab: cab_parts.append(r_)
    # inherit visibility keys: a rig is an empty (never renders); parts keep their own hide keys
    r_.keyframe_insert("location", index=2, frame=1)
    fc = fcurve(r_, "location", 2)
    if fc:
        m_ = fc.modifiers.new('FNGENERATOR'); m_.function_type = 'SIN'; m_.amplitude = s * 0.09
        m_.phase_multiplier = 2 * math.pi / rng.uniform(26, 40); m_.phase_offset = rng.uniform(0, 6.28); m_.use_additive = True
    c = base
    if not in_cab and c.x > XC and c.y < YC and c.z < Z0 + 0.3 and c.z > FZ_BOT and rng.random() < 0.6:
        amp = rng.choice((-1, 1)) * rng.uniform(0.25, 0.45); ph = rng.uniform(0, 5.0); per = rng.uniform(5.5, 8.0)
        t = ph
        kv(r_, "location", 1, base.x, 0)
        while t < 67.5:
            for dt, off in [(0, 0), (1.1, amp), (per * 0.5, amp), (per * 0.5 + 1.1, 0)]:
                if t + dt < 67.5: kv(r_, "location", F(t + dt), base.x + off, 0)
            t += per
    nb += 1
print("MOONANIM bot rigs", nb)

# ================= elevator cab =================
cab = empty("CabRig", (EX, EY, cz_))
for o in cab_parts:
    if o.parent is None: parent_keep(o, cab)
seq = [2, 1, 0, 1, 2, 3, 2, 1, 0, 1, 2, 3, 2, 1, 0]
t = 0.0; cur = 2
kv(cab, "location", 1, cz_, 2)
for nxt in seq[1:]:
    t += 3.0
    kv(cab, "location", F(t), cz_ + (2 - cur) * FH, 2)
    t += 1.6
    kv(cab, "location", F(t), cz_ + (2 - nxt) * FH, 2); cur = nxt
    if t > 67: break

# ================= screens flicker =================
for mn in ("conscr", "bigscr", "screen"):
    m = C.materials.get(mn)
    if not m: continue
    e = next((n for n in m.node_tree.nodes if n.type == 'EMISSION'), None)
    if not e: continue
    s0 = e.inputs["Strength"].default_value; ksock(e.inputs["Strength"], 1, s0)
    fc = fcurve(m.node_tree, 'nodes["%s"].inputs[1].default_value' % e.name, 0)
    if fc:
        nm_ = fc.modifiers.new('NOISE'); nm_.scale = 6.0; nm_.strength = s0 * 0.25; nm_.blend_type = 'ADD'

# ================= compositor glow (engine, sun) =================
if os.environ.get("GLARE", "1") == "1":
    try:
        sc.use_nodes = True; tr_ = sc.node_tree
        rl = next(n for n in tr_.nodes if n.type == 'R_LAYERS'); cp = next(n for n in tr_.nodes if n.type == 'COMPOSITE')
        gl = tr_.nodes.new("CompositorNodeGlare"); gl.glare_type = 'FOG_GLOW'
        for attr, val in (("quality", 'MEDIUM'), ("threshold", 6.0), ("size", 8), ("mix", 0.0)):
            try: setattr(gl, attr, val)
            except Exception: pass
        for nm_, val in (("Threshold", 6.0), ("Highlights Threshold", 6.0), ("Size", 0.6), ("Strength", 1.0)):
            if nm_ in gl.inputs: gl.inputs[nm_].default_value = val
        tr_.links.new(rl.outputs["Image"], gl.inputs["Image"]); tr_.links.new(gl.outputs["Image"], cp.inputs["Image"])
        print("MOONANIM glare ok", [i.name for i in gl.inputs])
    except Exception as ex:
        print("MOONANIM glare failed", ex)

apply_hides()
print("MOONANIM BUILD_SECONDS %.1f objects %d" % (time.time() - T0, len(C.objects)))

# ================= render =================
OUTDIR = os.environ.get("OUTDIR", "out/frames"); os.makedirs(OUTDIR, exist_ok=True)
if os.environ.get("SAVEBLEND") == "1":
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, "moonanim.blend"))
a_, b_ = [int(x) for x in os.environ.get("FRANGE", "1-%d" % NFR).split("-")]
STEP = int(os.environ.get("FSTEP", "1")); CHK = int(os.environ.get("CHUNK", "0")); NCH = int(os.environ.get("NCHUNK", "1"))
frames = list(range(a_, b_ + 1, STEP))[CHK::NCH]
FMT = os.environ.get("FMT", "JPEG").upper()
sc.render.image_settings.file_format = FMT
if FMT == "JPEG": sc.render.image_settings.quality = 90
ext = "jpg" if FMT == "JPEG" else "png"
print("MOONANIM frames", len(frames), frames[:5], "...", "res %d%%" % sc.render.resolution_percentage, "samples", sc.eevee.taa_render_samples)
if os.environ.get("DRY") == "1":
    for f in (1, F(7.5), F(14), F(38), F(40), F(48), F(55), F(62)):
        sc.frame_set(f)
        print("DRY frame", f, "cam", tuple(round(v, 2) for v in co.location), "os", round(cam.ortho_scale, 2), "rocket z", round(rig.location.z, 2),
              "sun", tuple(round(v, 2) for v in sun_disc.location), "lid0 y", round(lids[0].location.y, 2))
    sys.exit(0)
tlog = open(os.path.join(OUTDIR, "times_%02d.txt" % CHK), "w")
for f in frames:
    t1 = time.time(); sc.frame_set(f)
    sc.render.filepath = os.path.join(OUTDIR, "f%04d.%s" % (f, ext))
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t1; tlog.write("%d %.1f\n" % (f, dt)); tlog.flush()
    print("FRAME %d SECONDS %.1f" % (f, dt), flush=True)
tlog.close()
print("MOONANIM DONE", len(frames))
