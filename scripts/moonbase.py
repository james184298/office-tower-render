import bpy, bmesh, math, random, os, time
from mathutils import Vector, Matrix, noise
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
C = bpy.data
T0 = time.time()

# ================= helpers =================
def mat(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, spec=0.5):
    m = C.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    try: b.inputs["Specular IOR Level"].default_value = spec
    except Exception: pass
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    return m

def emis(name, col, s):
    m = C.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1); e.inputs["Strength"].default_value = s
    nt.links.new(e.outputs[0], o.inputs[0]); return m

def box(name, loc, size, m, bevel=0.0, rz=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        md = o.modifiers.new("b", 'BEVEL'); md.width = bevel; md.segments = 2
    o.rotation_euler.z = rz
    o.data.materials.append(m); return o

def cyl(name, loc, r, h, m, verts=24, rot=(0,0,0), smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    if smooth: bpy.ops.object.shade_smooth()
    return o

def sph(name, loc, r, m, s=(1,1,1), seg=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(6, seg//2), radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = s
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o

def ico(name, loc, r, m, sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(m); return o

def cone(name, loc, r1, r2, h, m, verts=24, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); return o

def text(body, loc, size, m, rot=(0,0,0), extrude=0.02, align='CENTER', spacing=1.0):
    bpy.ops.object.text_add(location=loc)
    t = bpy.context.object; t.data.body = body; t.data.size = size; t.data.extrude = extrude
    t.data.align_x = align; t.data.align_y = 'BOTTOM'; t.data.space_character = spacing
    t.rotation_euler = rot; t.data.materials.append(m); return t

# ================= materials =================
M_white = mat("white", (0.82,0.83,0.85), 0.3)
M_slab = mat("slab", (0.27,0.275,0.29), 0.35)
M_dark = mat("dark", (0.025,0.027,0.03), 0.35)
M_desk = mat("desk", (0.035,0.038,0.045), 0.25)
M_chair = mat("chair", (0.015,0.015,0.018), 0.5)
M_wall = mat("wall", (0.035,0.036,0.04), 0.6)
M_panel = mat("panel", (0.75,0.76,0.78), 0.4)
M_lwall = mat("lwallm", (0.42,0.42,0.44), 0.5)
M_wood = mat("wood", (0.55,0.4,0.24), 0.45)
M_metal = mat("metal", (0.62,0.64,0.67), 0.35, 0.2)
M_gold = mat("gold", (0.95,0.68,0.15), 0.3, 1.0)
M_glass = mat("glass", (0.75,0.85,0.9), 0.02, 0, alpha=0.18)
M_screen = emis("screen", (0.06,0.22,0.9), 1.3)
M_big = C.materials.new("bigscreen"); M_big.use_nodes = True
nt = M_big.node_tree; nt.nodes.clear()
_o = nt.nodes.new("ShaderNodeOutputMaterial"); _e = nt.nodes.new("ShaderNodeEmission"); _t = nt.nodes.new("ShaderNodeTexCoord")
_w = nt.nodes.new("ShaderNodeTexWave"); _w.inputs["Scale"].default_value = 1.2; _w.inputs["Distortion"].default_value = 2; _w.bands_direction = 'X'
_n = nt.nodes.new("ShaderNodeTexNoise"); _n.inputs["Scale"].default_value = 3
_r = nt.nodes.new("ShaderNodeValToRGB"); _r.color_ramp.elements[0].position = 0.74; _r.color_ramp.elements[0].color = (0.005,0.02,0.09,1)
_r.color_ramp.elements[1].position = 0.8; _r.color_ramp.elements[1].color = (0.35,0.75,1.0,1)
_m = nt.nodes.new("ShaderNodeMath"); _m.operation = 'MAXIMUM'
nt.links.new(_t.outputs["Object"], _w.inputs["Vector"]); nt.links.new(_t.outputs["Object"], _n.inputs["Vector"])
nt.links.new(_w.outputs["Fac"], _m.inputs[0]); nt.links.new(_n.outputs["Fac"], _m.inputs[1])
nt.links.new(_m.outputs[0], _r.inputs["Fac"]); nt.links.new(_r.outputs["Color"], _e.inputs["Color"])
_e.inputs["Strength"].default_value = 1.6; nt.links.new(_e.outputs[0], _o.inputs[0])
M_navy = emis("navy", (0.02,0.07,0.3), 1.6)
M_cyan = emis("cyan", (0.4,0.85,1.0), 4.0)
M_orange = emis("orange", (1.0,0.5,0.1), 3.0)
M_screenG = emis("screenG", (0.1,0.7,0.25), 1.0)
M_screenP = emis("screenP", (0.35,0.15,0.9), 1.0)
M_red = emis("redposter", (1.0,0.25,0.1), 1.5)
M_lamp = emis("lamp", (1.0,0.8,0.55), 6.0)
M_wlamp = emis("wlamp", (1.0,0.55,0.2), 3.0)
M_leaf = mat("leaf", (0.04,0.3,0.06), 0.55)
M_leaf2 = mat("leaf2", (0.08,0.42,0.1), 0.55)
M_pot = mat("pot", (0.9,0.9,0.9), 0.35)
M_purple = mat("carpet", (0.16,0.06,0.36), 0.9)
M_solar = mat("solar", (0.015,0.02,0.045), 0.12, 0.5)
M_eye = emis("eye", (1,1,1), 2.0)
M_pad = mat("pad", (0.035,0.035,0.04), 0.6)
BOT_COLS = [(0.02,0.75,0.08),(1.0,0.32,0.0),(0.03,0.18,1.0),(0.42,0.04,1.0),(1.0,0.04,0.32),(0.0,0.62,0.75),(1.0,0.7,0.0),(0.95,0.95,0.97)]
M_bots = [mat(f"bot{i}", tuple(v*0.8 for v in c), 0.22, emit=c, estr=0.12, spec=0.7) for i,c in enumerate(BOT_COLS)]
M_pupil = mat("pupil",(0.01,0.01,0.01),0.2)

# ---- rock: discrete sediment layers (per-layer random tone), fine streaks, grain, crisp layer edges ----
M_rock = C.materials.new("rock"); M_rock.use_nodes = True
nt = M_rock.node_tree; N = nt.nodes; L = nt.links
bsdf = N["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.95
try: bsdf.inputs["Specular IOR Level"].default_value = 0.25
except Exception: pass
tc = N.new("ShaderNodeTexCoord")
sx_ = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx_.inputs[0])
def mnode(op, a_=None, b_=None, v0=None, v1=None):
    m_ = N.new("ShaderNodeMath"); m_.operation = op
    if a_ is not None: L.new(a_, m_.inputs[0])
    elif v0 is not None: m_.inputs[0].default_value = v0
    if b_ is not None: L.new(b_, m_.inputs[1])
    elif v1 is not None: m_.inputs[1].default_value = v1
    return m_
# warp: low-frequency noise shifts the layers up/down along the face
wn = N.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 0.12; wn.inputs["Detail"].default_value = 2
mpw = N.new("ShaderNodeMapping"); mpw.inputs["Scale"].default_value = (1.0, 1.0, 0.25)
L.new(tc.outputs["Object"], mpw.inputs["Vector"]); L.new(mpw.outputs["Vector"], wn.inputs["Vector"])
wsc = mnode('MULTIPLY_ADD', wn.outputs["Fac"], None, None, 1.6); wsc.inputs[2].default_value = -0.8
# layer coordinate: z tilted so strata read flatter on screen than the slab edges (as in the ref)
zdot = N.new("ShaderNodeVectorMath"); zdot.operation = 'DOT_PRODUCT'; zdot.inputs[1].default_value = (-0.19, 0.19, 1.0)
L.new(tc.outputs["Object"], zdot.inputs[0]); ZQ = zdot.outputs["Value"]
zl = mnode('MULTIPLY', ZQ, None, None, 3.6)
zw = mnode('ADD', zl.outputs[0], wsc.outputs[0])
lid = mnode('FLOOR', zw.outputs[0])
lfr = mnode('FRACT', zw.outputs[0])
wh = N.new("ShaderNodeTexWhiteNoise"); wh.noise_dimensions = '1D'; L.new(lid.outputs[0], wh.inputs["W"])
tone = N.new("ShaderNodeValToRGB"); tr_ = tone.color_ramp; tr_.interpolation = 'LINEAR'
tr_.elements[0].position = 0.0; tr_.elements[0].color = (0.1,0.1,0.105,1)
tr_.elements[1].position = 1.0; tr_.elements[1].color = (0.285,0.285,0.295,1)
_e = tr_.elements.new(0.3); _e.color = (0.155,0.155,0.16,1)
_e = tr_.elements.new(0.7); _e.color = (0.21,0.21,0.22,1)
L.new(wh.outputs["Value"], tone.inputs["Fac"])
# sub-layer streaks: noise heavily stretched horizontally
sn = N.new("ShaderNodeTexNoise"); sn.inputs["Scale"].default_value = 1.0; sn.inputs["Detail"].default_value = 6; sn.inputs["Roughness"].default_value = 0.65
cxyz = N.new("ShaderNodeCombineXYZ")
_mx = mnode('MULTIPLY', sx_.outputs["X"], None, None, 1.3); _my = mnode('MULTIPLY', sx_.outputs["Y"], None, None, 1.3); _mz = mnode('MULTIPLY', ZQ, None, None, 16.0)
L.new(_mx.outputs[0], cxyz.inputs[0]); L.new(_my.outputs[0], cxyz.inputs[1]); L.new(_mz.outputs[0], cxyz.inputs[2])
L.new(cxyz.outputs[0], sn.inputs["Vector"])
smr = N.new("ShaderNodeMapRange"); smr.inputs["From Min"].default_value = 0.3; smr.inputs["From Max"].default_value = 0.7
smr.inputs["To Min"].default_value = 0.85; smr.inputs["To Max"].default_value = 1.15
L.new(sn.outputs["Fac"], smr.inputs["Value"])
# grain
gn = N.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 28; gn.inputs["Detail"].default_value = 8; gn.inputs["Roughness"].default_value = 0.7
L.new(tc.outputs["Object"], gn.inputs["Vector"])
gmr = N.new("ShaderNodeMapRange"); gmr.inputs["From Min"].default_value = 0.3; gmr.inputs["From Max"].default_value = 0.7
gmr.inputs["To Min"].default_value = 0.55; gmr.inputs["To Max"].default_value = 1.45
L.new(gn.outputs["Fac"], gmr.inputs["Value"])
# broad patches
pn = N.new("ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 0.35; pn.inputs["Detail"].default_value = 3
L.new(tc.outputs["Object"], pn.inputs["Vector"])
pmr = N.new("ShaderNodeMapRange"); pmr.inputs["From Min"].default_value = 0.35; pmr.inputs["From Max"].default_value = 0.65
pmr.inputs["To Min"].default_value = 0.75; pmr.inputs["To Max"].default_value = 1.2
L.new(pn.outputs["Fac"], pmr.inputs["Value"])
# dark crisp line at the base of each layer
edg = N.new("ShaderNodeMapRange"); edg.inputs["From Min"].default_value = 0.0; edg.inputs["From Max"].default_value = 0.06
edg.inputs["To Min"].default_value = 0.55; edg.inputs["To Max"].default_value = 1.0
L.new(lfr.outputs[0], edg.inputs["Value"])
zf2 = mnode('MULTIPLY', ZQ, None, None, 11.0); zf2w = mnode('ADD', zf2.outputs[0], wsc.outputs[0])
lid2 = mnode('FLOOR', zf2w.outputs[0]); wh2 = N.new("ShaderNodeTexWhiteNoise"); wh2.noise_dimensions = '1D'; L.new(lid2.outputs[0], wh2.inputs["W"])
f2 = N.new("ShaderNodeMapRange"); f2.inputs["To Min"].default_value = 0.62; f2.inputs["To Max"].default_value = 1.12
L.new(wh2.outputs["Value"], f2.inputs["Value"])
m0 = mnode('MULTIPLY', smr.outputs["Result"], f2.outputs["Result"])
gn2 = N.new("ShaderNodeTexNoise"); gn2.inputs["Scale"].default_value = 140; gn2.inputs["Detail"].default_value = 2
L.new(tc.outputs["Object"], gn2.inputs["Vector"])
g2r = N.new("ShaderNodeMapRange"); g2r.inputs["From Min"].default_value = 0.3; g2r.inputs["From Max"].default_value = 0.7
g2r.inputs["To Min"].default_value = 0.75; g2r.inputs["To Max"].default_value = 1.2
L.new(gn2.outputs["Fac"], g2r.inputs["Value"])
m0b = mnode('MULTIPLY', m0.outputs[0], g2r.outputs["Result"])
m1 = mnode('MULTIPLY', m0b.outputs[0], gmr.outputs["Result"])
m2 = mnode('MULTIPLY', m1.outputs[0], pmr.outputs["Result"])
m3 = mnode('MULTIPLY', m2.outputs[0], edg.outputs["Result"])
mulc = N.new("ShaderNodeMixRGB"); mulc.blend_type = 'MULTIPLY'; mulc.inputs["Fac"].default_value = 1.0
L.new(tone.outputs["Color"], mulc.inputs["Color1"]); L.new(m3.outputs[0], mulc.inputs["Color2"])
# lighter crust just under the surface
mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.9; mr.inputs["From Max"].default_value = -0.25
L.new(sx_.outputs["Z"], mr.inputs["Value"])
crust = N.new("ShaderNodeMixRGB"); crust.inputs["Color2"].default_value = (0.22,0.22,0.23,1)
L.new(mr.outputs["Result"], crust.inputs["Fac"]); L.new(mulc.outputs["Color"], crust.inputs["Color1"])
L.new(crust.outputs["Color"], bsdf.inputs["Base Color"])
# bump: layer steps + streaks + grain
bh1 = mnode('MULTIPLY', lfr.outputs[0], None, None, 0.6)
bh2 = mnode('MULTIPLY_ADD', sn.outputs["Fac"], None, None, 0.5); L.new(bh1.outputs[0], bh2.inputs[2])
bh3 = mnode('MULTIPLY_ADD', gn.outputs["Fac"], None, None, 0.25); L.new(bh2.outputs[0], bh3.inputs[2])
bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.05
L.new(bh3.outputs[0], bump.inputs["Height"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

# ---- regolith ----
M_reg = C.materials.new("regolith"); M_reg.use_nodes = True
nt = M_reg.node_tree; N = nt.nodes; L = nt.links
b2 = N["Principled BSDF"]; b2.inputs["Roughness"].default_value = 1
n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 0.8; n2.inputs["Detail"].default_value = 8; n2.inputs["Roughness"].default_value = 0.6
r2 = N.new("ShaderNodeValToRGB"); er = r2.color_ramp.elements
er[0].position = 0.3; er[0].color = (0.09,0.09,0.095,1); er[1].position = 0.7; er[1].color = (0.33,0.33,0.34,1)
L.new(n2.outputs["Fac"], r2.inputs["Fac"]); L.new(r2.outputs["Color"], b2.inputs["Base Color"])
bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = 0.25
n3 = N.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 12; n3.inputs["Detail"].default_value = 8
L.new(n3.outputs["Fac"], bp2.inputs["Height"]); L.new(bp2.outputs["Normal"], b2.inputs["Normal"])


# ================= procedural raster images (UI screens, posters) =================
import array
class Canvas:
    def __init__(s, w, h, bg):
        s.w, s.h = w, h
        s.px = array.array('f', [0.0]) * (w*h*4)
        s.rect(0, 0, w, h, bg)
    def rect(s, x0, y0, x1, y1, c):
        w, h, px = s.w, s.h, s.px
        x0 = max(0, int(x0)); x1 = min(w, int(x1)); y0 = max(0, int(y0)); y1 = min(h, int(y1))
        for yy in range(y0, y1):
            b = yy*w
            for xx in range(x0, x1):
                i = (b+xx)*4; px[i] = c[0]; px[i+1] = c[1]; px[i+2] = c[2]; px[i+3] = 1.0
    def dot(s, x, y, r, c):
        s.rect(x-r, y-r, x+r+1, y+r+1, c)
    def circle(s, cx, cy, r, c, th=1.5, fill=None):
        for yy in range(int(cy-r-2), int(cy+r+3)):
            for xx in range(int(cx-r-2), int(cx+r+3)):
                if 0 <= xx < s.w and 0 <= yy < s.h:
                    d = math.hypot(xx-cx, yy-cy)
                    if fill is not None and d < r-th: s.rect(xx, yy, xx+1, yy+1, fill)
                    elif abs(d-r) < th: s.rect(xx, yy, xx+1, yy+1, c)
    def curve(s, f, x0, x1, c, th=1):
        for xx in range(int(x0), int(x1)):
            y = f(xx); s.dot(xx, y, th, c)
    def textbars(s, x0, y0, x1, y1, c, rows=None, rh=3, gap=3, rnd=None):
        rnd = rnd or random
        y = y1 - rh
        while y >= y0:
            x = x0
            while x < x1 - 4:
                wl = rnd.randint(3, 14)
                if x + wl > x1: break
                s.rect(x, y, x+wl, y+rh, c); x += wl + rnd.randint(2, 4)
                if rnd.random() < 0.25: break
            y -= rh + gap
    def image(s, name):
        img = C.images.new(name, s.w, s.h, float_buffer=False)
        img.pixels.foreach_set(s.px)
        try: img.pack()
        except Exception as ex: print("pack", ex)
        return img

def imgmat(name, img, strength=1.4, emissive=True):
    m = C.materials.new(name); m.use_nodes = True; nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    if emissive:
        nt.nodes.clear(); o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
        nt.links.new(t.outputs["Color"], e.inputs["Color"]); e.inputs["Strength"].default_value = strength
        nt.links.new(e.outputs[0], o.inputs[0])
    else:
        b = nt.nodes["Principled BSDF"]; nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.5
    return m

def plane(name, loc, w, h, m, face='-Y'):
    """vertical image plane; face '-Y' (back wall, u along +x) or '+X' (left wall, u along +y);
    'Z' lies flat (u along +x)"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.object; o.name = name
    o.scale = (w, h, 1)
    if face == '-Y': o.rotation_euler = (math.radians(90), 0, 0)
    elif face == '+X': o.rotation_euler = (math.radians(90), 0, math.radians(90))
    o.data.materials.append(m); return o

NAVY = (0.006, 0.016, 0.05); PANEL = (0.012, 0.03, 0.085); EDGE = (0.05, 0.11, 0.26)
WHT = (0.85, 0.9, 1.0); CYAN = (0.25, 0.8, 1.0); ORG = (1.0, 0.45, 0.08); GRN = (0.15, 0.95, 0.35); RED = (1.0, 0.15, 0.1)
rr = random.Random(11)

def big_screen_img():
    cv = Canvas(960, 200, NAVY)
    W, H = cv.w, cv.h
    # header strip
    cv.rect(0, H-14, W, H, (0.02, 0.05, 0.14))
    cv.textbars(6, H-11, 300, H-4, WHT, rh=3, gap=2, rnd=rr)
    panels = [(4, 200), (204, 420), (424, 590), (594, 820), (824, 956)]
    for x0, x1 in panels:
        cv.rect(x0, 4, x1, H-18, EDGE); cv.rect(x0+2, 6, x1-2, H-20, PANEL)
    # A: countdown digits + small gauges + text rows
    x0 = 10
    for k in range(6):
        xx = x0 + k*24
        if k in (2, 4): cv.rect(xx+6, 150, xx+10, 154, WHT); cv.rect(xx+6, 138, xx+10, 142, WHT); continue
        cv.rect(xx, 132, xx+16, 135, WHT); cv.rect(xx, 145, xx+16, 148, WHT); cv.rect(xx, 158, xx+16, 161, WHT)
        cv.rect(xx, 132, xx+3, 161, WHT); cv.rect(xx+13, 132, xx+16, 161, WHT)
    for k in range(3):
        cv.circle(40+k*55, 95, 18, CYAN, 2.0)
        a = rr.uniform(0.3, 2.6); cv.curve(lambda x, k=k: 95 + 0*x, 40+k*55, 40+k*55+1, CYAN)
        cv.rect(40+k*55-1, 95, 40+k*55+1, 95+14, ORG if k == 1 else WHT)
    cv.textbars(10, 12, 190, 70, (0.6, 0.75, 0.95), rh=3, gap=4, rnd=rr)
    # B: trajectory over the earth limb
    cx, cy, R = 312, -260, 300
    for yy in range(6, H-20):
        for xx in range(206, 418):
            d = math.hypot(xx-cx, yy-cy)
            if d < R: 
                t = max(0.0, min(1.0, (R-d)/40))
                cv.rect(xx, yy, xx+1, yy+1, (0.02+0.05*(1-t), 0.1+0.15*(1-t), 0.35+0.4*(1-t)))
    cv.curve(lambda x: 30 + 140*((x-210)/205)**1.6, 212, 410, WHT, 1)
    cv.curve(lambda x: 30 + 110*((x-210)/205)**2.2, 212, 410, (0.4, 0.6, 1.0), 0)
    for k in range(5): cv.dot(230+k*40, 30 + 140*((20+k*40)/205)**1.6, 2, ORG)
    cv.textbars(214, H-34, 400, H-22, WHT, rh=3, gap=2, rnd=rr)
    # C: launch photo — dusk gradient + rocket + plume
    for yy in range(6, H-20):
        t = (yy-6)/(H-26)
        col = (1.0*(1-t)**2 + 0.02, 0.45*(1-t)**2.5 + 0.04*t, 0.1*(1-t) + 0.25*t)
        cv.rect(426, yy, 588, yy+1, col)
    cv.rect(426, 6, 588, 20, (0.03, 0.03, 0.05))
    cv.rect(503, 40, 511, 140, WHT); cv.rect(505, 140, 509, 150, WHT)
    for yy in range(20, 40): cv.rect(507-(40-yy)//3, yy, 508+(40-yy)//3, yy+1, (1.0, 0.85, 0.5))
    # D: telemetry charts
    for g in range(6): cv.rect(600, 20+g*26, 816, 21+g*26, (0.04, 0.09, 0.2))
    for g in range(9): cv.rect(600+g*26, 8, 601+g*26, H-24, (0.04, 0.09, 0.2))
    cv.curve(lambda x: 20 + 140/(1+math.exp(-(x-700)/18)), 600, 816, CYAN, 1)
    cv.curve(lambda x: 100 + 40*math.sin((x-600)/20) * math.exp(-(x-600)/150), 600, 816, ORG, 1)
    for k in range(18): cv.rect(604+k*12, 8, 612+k*12, 8+rr.randint(4, 22), (0.2, 0.55, 1.0))
    # E: status list
    y = H-32
    while y > 12:
        cv.dot(832, y+1, 2, GRN if rr.random() < 0.75 else ORG)
        cv.textbars(840, y, 950, y+3, WHT, rh=3, gap=99, rnd=rr); y -= 11
    return cv.image("bigscreen_img")

def list_screen_img():
    cv = Canvas(160, 120, (0.01, 0.03, 0.03))
    cv.rect(0, 108, 160, 120, (0.03, 0.12, 0.08)); cv.textbars(4, 111, 120, 117, WHT, rh=3, rnd=rr)
    y = 100
    while y > 6:
        cv.dot(8, y+1, 2, GRN); cv.textbars(16, y, 150, y+3, (0.4, 1.0, 0.55), rh=3, gap=99, rnd=rr); y -= 9
    return cv.image("list_img")

def console_img():
    cv = Canvas(64, 40, (0.01, 0.02, 0.06))
    cv.rect(3, 30, 61, 36, (0.05, 0.15, 0.4)); cv.textbars(4, 4, 40, 26, (0.4, 0.6, 0.9), rh=2, gap=3, rnd=rr)
    cv.rect(50, 8, 58, 14, (0.8, 0.12, 0.08))
    return cv.image("console_img")

def dial_panel_img():
    cv = Canvas(220, 90, (0.82, 0.83, 0.86))
    for k in range(3): cv.circle(130+k*30, 62, 11, (0.1, 0.1, 0.12), 2.0, fill=(0.95, 0.95, 0.97))
    for r_ in range(2):
        for k in range(5):
            col = [(0.1, 0.12, 0.2), (0.7, 0.15, 0.25), (0.15, 0.2, 0.5)][(k+r_) % 3]
            cv.rect(8+k*20, 50-r_*22, 24+k*20, 66-r_*22, col)
    cv.rect(120, 8, 212, 40, (0.03, 0.03, 0.05)); cv.textbars(124, 12, 200, 36, (0.4, 0.8, 1.0), rh=2, gap=4, rnd=rr)
    return cv.image("dial_img")

def poster_img():   # dark launch poster
    cv = Canvas(60, 100, (0.03, 0.03, 0.04))
    for yy in range(5, 60):
        t = (yy-5)/55; cv.rect(5, yy, 55, yy+1, (0.9*(1-t)+0.1, 0.35*(1-t)+0.03, 0.05))
    cv.rect(28, 20, 32, 62, (0.9, 0.9, 0.9))
    cv.rect(10, 72, 50, 84, (0.92, 0.92, 0.92)); cv.textbars(10, 64, 50, 69, (0.7, 0.7, 0.7), rh=2, rnd=rr)
    return cv.image("poster_img")

def chart_panel_img():  # white panel with purple charts
    cv = Canvas(120, 100, (0.85, 0.85, 0.9))
    cv.rect(6, 82, 60, 90, (0.25, 0.1, 0.55))
    for k in range(7): cv.rect(10+k*14, 10, 20+k*14, 10+rr.randint(10, 55), (0.35+0.05*k, 0.2, 0.85))
    cv.rect(70, 76, 112, 92, (0.03, 0.03, 0.05))
    return cv.image("chart_img")

def ai_panel_img():   # black panel with large white glyph bars
    cv = Canvas(80, 100, (0.02, 0.02, 0.025))
    for k, (x, h) in enumerate([(10, 70), (22, 70), (40, 70), (55, 40), (64, 70)]):
        cv.rect(x, 15, x+6, 15+h, (0.9, 0.9, 0.9))
    cv.rect(10, 50, 28, 56, (0.9, 0.9, 0.9)); cv.rect(10, 82, 28, 85, (0.9, 0.9, 0.9))
    return cv.image("ai_img")

M_bigimg = imgmat("bigscr", big_screen_img(), 1.6)
M_listimg = imgmat("listscr", list_screen_img(), 1.4)
M_conimg = imgmat("conscr", console_img(), 1.3)
M_dialimg = imgmat("dialp", dial_panel_img(), 0, emissive=False)
M_poster = imgmat("poster", poster_img(), 1.1)
M_chartimg = imgmat("chartp", chart_panel_img(), 0, emissive=False)
M_aiimg = imgmat("aip", ai_panel_img(), 0.9)

# ================= layout constants =================
A, B = 6.5, 6.0              # half extents in x, y
XC, YC = -1.0, -0.6          # cutaway region: x > XC and y < YC
ZB, ZT = -16.9, -8.0         # rock bottom tip / start of taper
# taper (measured off the ref silhouette): scale about a centre offset toward +x+y, so the left side tapers more
TAPER = [(-16.9, 0.15), (-16.5, 0.25), (-15.8, 0.42), (-14.8, 0.72), (-13.5, 0.85), (-11.9, 0.93), (-10.5, 0.96), (-9.3, 0.985), (-8.0, 1.0)]
TCX, TCY = 2.5, 2.5
def taper_s(z):
    if z <= TAPER[0][0]: return TAPER[0][1]
    for (z0, s0), (z1, s1) in zip(TAPER, TAPER[1:]):
        if z <= z1:
            t = (z-z0)/(z1-z0); t = t*t*(3-2*t); return s0 + (s1-s0)*t
    return 1.0
# terrain rises toward the back-right corner (ref: the +x face's top edge reaches v~310 at the right corner)
HH = float(os.environ.get("HILL", 2.6))
def _sm(t): t = max(0.0, min(1.0, t)); return t*t*(3-2*t)
SGN_P = (-4.71, 4.2, 0.85); SGN_A = math.radians(22); SGN_L = 8.2
def TH(x, y):
    h = HH*_sm((x+2)/8.5)*_sm((y-3.8)/2.2)
    # low berm under the sign so the letters stand on the ground (ref)
    ca, sa = math.cos(SGN_A), math.sin(SGN_A)
    t = (x-SGN_P[0])*ca + (y-SGN_P[1])*sa; tc_ = max(0.0, min(SGN_L, t))
    d = math.hypot(x-(SGN_P[0]+ca*tc_), y-(SGN_P[1]+sa*tc_))
    h += max(0.0, SGN_P[2]-0.05-h)*math.exp(-(d/0.75)**2)
    return h
FZ_BOT = -10.2               # recess floor
NF = 4; Z0 = -1.45; FH = 2.1  # top slab level and floor pitch (measured off the ref)
EX, EY = A - 0.6, YC + 1.65  # elevator centre (in a slot on the +x face; measured: shaft centre at ref u~556)
CRATERS = [(-4.6,1.8,1.0),(-1.5,3.0,0.7),(-5.0,4.6,0.5),(2.0,0.6,0.45),(-0.6,0.9,0.35),(4.6,-0.0,0.3),(-3.2,5.3,0.4)]

# ================= rock block =================
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co = Vector((v.co.x*2*A, v.co.y*2*B, ZB + (v.co.z+0.5)*(0-ZB)))
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=70, use_grid_fill=True)
def smooth(t): t = max(0, min(1, t)); return t*t*(3-2*t)
for v in bm.verts:
    x, y, z = v.co
    ontop = z > -0.001
    edge = max(abs(x)/A, abs(y)/B) > 0.999
    if edge:
        n = noise.noise(Vector((x*0.18+3, y*0.18, z*0.45)))
        n2 = noise.noise(Vector((x*0.6, y*0.6, z*1.2)))
        layer = math.floor((z+0.245*(y-x))/0.85 + 0.5*noise.noise(Vector((x*0.12, y*0.12, 7.0))))
        led = 0.05*noise.noise(Vector((layer*1.73, 0.5, 2.0)))
        off = 0.2*n + 0.05*n2 + led + 0.1
        if z > -0.6: off *= max(0.0, -z/0.6)
        if abs(x)/A >= abs(y)/B: v.co.x += math.copysign(off, x)
        else: v.co.y += math.copysign(off, y)
    if ontop:
        h = 0.05*noise.fractal(Vector((x*0.6, y*0.6, 0)), 0.6, 2.0, 4)
        for cx, cy, cr in CRATERS:
            d = math.hypot(x-cx, y-cy)/cr
            if d < 1: h -= 0.22*cr*(1-d*d)
            h += 0.07*cr*math.exp(-((d-1.0)/0.25)**2)
        v.co.z += h
    if z < ZT:
        s = taper_s(z)
        ns = 1 + 0.1*noise.noise(Vector((x*0.3, y*0.3, z*0.3)))
        v.co.x = TCX + (v.co.x - TCX)*s*ns; v.co.y = TCY + (v.co.y - TCY)*s*ns
    if z > -5.0:
        v.co.z += TH(x, y)*smooth(1 + z/5.0)
    if z < ZB + 0.01:
        v.co.z += 0.8*noise.noise(Vector((x*0.5, y*0.5, 5)))
me = C.meshes.new("block"); bm.to_mesh(me); bm.free()
blk = C.objects.new("block", me); sc.collection.objects.link(blk)
blk.data.materials.append(M_rock); blk.data.materials.append(M_reg)
for p in me.polygons:
    p.use_smooth = True
    if p.normal.z > 0.6 and p.center.z > -0.6: p.material_index = 1
def cutter(name, x0, x1, y0, y1, z0, z1):
    bpy.ops.mesh.primitive_cube_add(location=((x0+x1)/2, (y0+y1)/2, (z0+z1)/2))
    c = bpy.context.object; c.name = name; c.scale = ((x1-x0)/2, (y1-y0)/2, (z1-z0)/2)
    bpy.ops.object.transform_apply(scale=True)
    c.data.materials.append(M_wall); c.hide_render = True; c.hide_viewport = True
    return c
for nm, cobj in [("cut", cutter("cutbox", XC, A+4, -B-4, YC, FZ_BOT, 6)),
                 ("slot", cutter("slotbox", EX-0.6, A+4, YC-0.1, EY+0.6, FZ_BOT, 6)),
                 ("notch", cutter("notchbox", EX-0.5, A+4, YC-0.1, EY+2.2, Z0-0.16, 6)),
                 ("colcut", cutter("colbox", XC-1.25, XC+0.1, -B-4, -B+0.2, FZ_BOT, 6))]:
    bb = blk.modifiers.new(nm, 'BOOLEAN'); bb.object = cobj; bb.solver = 'EXACT'
    try: bb.material_mode = 'TRANSFER'
    except Exception: pass
# rubble / boulders around the tapered bottom of the rock
M_boul = mat("boulder",(0.07,0.07,0.075),0.95)
rb = random.Random(5)
for k in range(int(os.environ.get("NBOUL", 0))):
    z = rb.uniform(ZB+0.8, ZT-1.0)
    sc_ = taper_s(z)
    if rb.random() < 0.55: xr = rb.uniform(-A, A); yr = -B - rb.uniform(0.0, 0.25)/max(sc_, 0.3)
    else: xr = A + rb.uniform(0.0, 0.25)/max(sc_, 0.3); yr = rb.uniform(-B, B)
    x = TCX + (xr-TCX)*sc_*0.97; y = TCY + (yr-TCY)*sc_*0.97
    o = ico("boulder", (x, y, z), rb.uniform(0.12, 0.32), M_boul, 2)
    o.scale = (rb.uniform(0.8, 1.4), rb.uniform(0.8, 1.4), rb.uniform(0.5, 0.9)); o.rotation_euler = (rb.random(), rb.random(), rb.random()*6)
    md = o.modifiers.new("d", 'DISPLACE'); tx_ = C.textures.new(f"bt{k}", 'CLOUDS'); tx_.noise_scale = 0.4; md.texture = tx_; md.strength = 0.25
# recess ground
box("recessfloor", ((XC+A)/2, (YC-B)/2, FZ_BOT+0.02), (A-XC-0.1, B+YC-0.1, 0.04), mat("recg",(0.15,0.15,0.155),0.9))

# warm lights along the rock edges of the cutaway
for k in range(9):
    zz = -0.9 - k*1.05
    box("wn", (XC-0.95, -B-0.26, zz), (0.24, 0.04, 0.24), M_dark)
    box("wl", (XC-0.95, -B-0.29, zz+0.06), (0.14, 0.03, 0.06), M_wlamp)
for k in range(9):
    box("wl2", (XC-0.06, -B+0.6+k*0.6, -0.12), (0.06, 0.12, 0.06), M_lamp)
    box("wl3", (XC+0.6+k*0.8, YC+0.06, -0.12), (0.12, 0.06, 0.06), M_lamp)

# ================= interior =================
M_glow = C.materials.new("glow"); M_glow.use_nodes = True
_nt = M_glow.node_tree; _nt.nodes.clear()
_o = _nt.nodes.new("ShaderNodeOutputMaterial"); _mix = _nt.nodes.new("ShaderNodeMixShader")
_tr = _nt.nodes.new("ShaderNodeBsdfTransparent"); _em = _nt.nodes.new("ShaderNodeEmission")
_em.inputs["Color"].default_value = (0.15, 1.0, 0.3, 1); _em.inputs["Strength"].default_value = 1.9
_tc = _nt.nodes.new("ShaderNodeTexCoord"); _gr = _nt.nodes.new("ShaderNodeTexGradient"); _gr.gradient_type = 'SPHERICAL'
_mp = _nt.nodes.new("ShaderNodeMapping"); _mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
_pw = _nt.nodes.new("ShaderNodeMath"); _pw.operation = 'POWER'; _pw.inputs[1].default_value = 1.6
_nt.links.new(_tc.outputs["Object"], _gr.inputs["Vector"]); _nt.links.new(_gr.outputs["Fac"], _pw.inputs[0])
_nt.links.new(_pw.outputs[0], _mix.inputs["Fac"]); _nt.links.new(_tr.outputs[0], _mix.inputs[1]); _nt.links.new(_em.outputs[0], _mix.inputs[2])
_nt.links.new(_mix.outputs[0], _o.inputs[0])
try: M_glow.surface_render_method = 'BLENDED'
except Exception: pass

def bot(x, y, z, m, s=0.25, glow=True):
    cone("botb", (x, y, z+s*0.42), s*1.08, s*0.72, s*0.84, m, 32)
    sph("bot", (x, y, z+s*0.95), s*0.8, m, (1,1,0.95), 24)
    cd = Vector((0.707, -0.707, 0)); side = Vector((0.707, 0.707, 0))
    for sgn in (-1, 1):
        p = Vector((x, y, z+s*1.02)) + cd*(s*0.7) + side*(sgn*s*0.25)
        sph("eye", p, s*0.15, M_eye, (1,1,1.4), 12)
    if glow:
        g = cyl("glow", (x, y, z+0.012), 1.0, 0.002, M_glow, 32); g.scale = (s*2.5, s*2.5, 1)
        g.visible_shadow = False

def plant(x, y, z, s=1.0, tall=False):
    cyl("pot", (x, y, z+0.13*s), 0.12*s, 0.26*s, M_pot, 16)
    hh = (0.95 if tall else 0.45)*s
    if tall: cyl("stem", (x, y, z+0.26*s+hh*0.35), 0.018, hh*0.7, mat("stem",(0.2,0.12,0.05),0.8), 6, smooth=False)
    for i in range(16 if tall else 9):
        a = random.random()*6.28; r_ = random.random()*(0.24 if tall else 0.14)*s
        zz = z + 0.26*s + (hh*0.5 if tall else 0.08*s) + random.random()*hh*0.5
        o = ico("leaf", (x+math.cos(a)*r_, y+math.sin(a)*r_, zz), (0.08+random.random()*0.06)*s, random.choice((M_leaf, M_leaf2)), 1)
        o.scale = (1.3, 0.8, 0.5); o.rotation_euler = (random.random(), random.random(), a)

def chair(x, y, z, face=1, m=None, s=0.85):
    m = m or M_chair
    box("seat", (x, y, z+0.28*s), (0.22*s, 0.22*s, 0.04*s), m)
    box("back", (x, y-face*0.1*s, z+0.4*s), (0.22*s, 0.03*s, 0.22*s), m)
    cyl("cpost", (x, y, z+0.15*s), 0.02*s, 0.3*s, m if m is not M_chair else M_dark, 6, smooth=False)
    cyl("cbase", (x, y, z+0.015), 0.1*s, 0.03, m if m is not M_chair else M_dark, 8)

def stool(x, y, z, m=M_white):
    cyl("stool", (x, y, z+0.36), 0.1, 0.04, m, 12); cyl("sl", (x, y, z+0.18), 0.018, 0.36, M_metal, 6, smooth=False)

def console_row(cx, cy, z, n, R=7.0, seg=0.5):
    """curved row of mission-control workstations; centre of curvature toward +y (the big screen)"""
    for k in range(n):
        th = (k-(n-1)/2)*seg/R
        px = cx + R*math.sin(th); py = cy + R - R*math.cos(th)
        rot = th
        def P(dx, dy):   # local -> world (rotated about z by rot)
            return (px + dx*math.cos(rot) - dy*math.sin(rot), py + dx*math.sin(rot) + dy*math.cos(rot))
        o = box("cdesk", (*P(0, 0), z+0.36), (seg-0.03, 0.3, 0.04), M_desk); o.rotation_euler.z = rot
        o = box("cbody", (*P(0, 0.05), z+0.18), (seg-0.08, 0.18, 0.34), M_dark); o.rotation_euler.z = rot
        for dx in (-0.12, 0.12):
            o = box("cmonb", (*P(dx, 0.11), z+0.52), (0.2, 0.02, 0.135), M_dark); o.rotation_euler.z = rot
            o = plane("cmon", (*P(dx, 0.098), z+0.52), 0.185, 0.12, M_conimg); o.rotation_euler.z = rot
        cx_, cy_ = P(0, -0.3); chair(cx_, cy_, z, 1, s=0.8)

slabs = []
for i in range(NF):
    zf = Z0 - i*FH
    d = 0.15
    x0, x1 = XC, A - d
    y0, y1 = -B + d, YC
    W, D = x1-x0, y1-y0
    cx, cy = (x0+x1)/2, (y0+y1)/2
    box(f"slab{i}", (cx, cy, zf-0.11), (W, D, 0.22), M_white, 0.01)
    box(f"floor{i}", (cx, cy, zf+0.002), (W-0.06, D-0.06, 0.004), M_slab)
    # thin glass railing on the two open edges
    box("railA", (cx, y0+0.03, zf+0.18), (W, 0.015, 0.36), M_glass)
    box("railB", (x1-0.03, cy, zf+0.18), (0.015, D, 0.36), M_glass)
    box("rtA", (cx, y0+0.03, zf+0.36), (W, 0.02, 0.015), M_white)
    box("rtB", (x1-0.03, cy, zf+0.36), (0.02, D, 0.015), M_white)
    # side wall panels (white) on the x=XC wall
    box("lwall", (XC+0.02, cy, zf+(0.72 if i == 0 else 1.0)), (0.03, D, 1.3 if i else 1.4), M_lwall)
    Lg = C.lights.new(f"fl{i}", 'AREA'); Lg.energy = 50 if i else 50; Lg.shape = 'RECTANGLE'
    Lg.size = W*0.8; Lg.size_y = D*0.8; Lg.color = (1, 0.94, 0.86)
    lo = C.objects.new(f"fl{i}", Lg); sc.collection.objects.link(lo); lo.location = (cx, cy, zf + (1.3 if i == 0 else FH - 0.25))
    zt = zf
    if i == 0:   # ---- mission control ----
        box("bezel", (2.3, YC-0.01, zt+0.8), (6.2, 0.04, 1.12), M_dark)
        plane("big", (2.3, YC-0.035, zt+0.8), 6.1, 1.04, M_bigimg)
        box("lsbez", (XC+0.03, -1.85, zt+1.0), (0.04, 1.85, 0.66), M_dark)
        plane("lscr", (XC+0.055, -1.85, zt+1.0), 1.75, 0.58, M_listimg, '+X')
        box("ldesk", (XC+0.3, -1.85, zt+0.3), (0.45, 1.8, 0.6), M_desk)
        plane("dialp", (XC+0.04, -3.75, zt+0.9), 1.9, 0.85, M_dialimg, '+X')
        # darker raised platform under the consoles
        box("plat", (2.6, -3.2, zt+0.02), (6.4, 4.4, 0.04), mat("plat",(0.06,0.062,0.07),0.45))
        for gx, gy in ((0.75, 0.0), (4.15, -0.35)):
            for r_, yy in enumerate([-1.55, -2.6, -3.65, -4.7]):
                console_row(gx, yy+gy, zt+0.04, 5, seg=0.46)
        cyl("bin", (5.9, -1.3, zt+0.18), 0.14, 0.36, M_dark, 12)
        plant(XC+0.3, -0.95, zt, 0.8, True); plant(XC+0.3, -5.3, zt, 0.7); plant(6.0, -2.4, zt, 0.8, True)
        bots = [(0.0,-2.12,2),(1.2,-1.1,1),(2.45,-2.05,0),(4.1,-3.55,3),(2.5,-3.15,7),(5.6,-2.2,5),(3.3,-5.3,4)]
    elif i == 1:  # ---- engineering: long workbench ----
        plane("poster", (XC+0.04, -5.0, zt+1.0), 0.6, 1.0, M_poster, '+X')
        BY = -4.0
        box("wtable", (2.35, BY, zt+0.5), (5.8, 0.5, 0.04), M_wood)
        for k in range(12):
            xx = -0.35 + k*0.5
            box("tleg", (xx, BY, zt+0.25), (0.025, 0.025, 0.5), M_metal)
            box("lap", (xx+0.2, BY+0.03, zt+0.56), (0.24, 0.16, 0.08), M_dark)
            if k % 3 == 1: box("lamp_", (xx+0.05, BY+0.15, zt+0.62), (0.05, 0.05, 0.2), M_dark)
            chair(xx+0.1, BY-0.48, zt, -1, M_white); chair(xx-0.05, BY+0.5, zt, 1, M_white)
        for k in range(6):
            chair(4.5+ (k % 2)*0.7, -3.4 - (k//2)*0.7, zt, 1, M_white)
        cyl("rug", (5.0, -2.9, zt+0.01), 0.85, 0.02, M_dark, 48)
        cyl("podium", (5.0, -2.9, zt+0.55), 0.16, 1.1, M_white, 24); cyl("podb", (5.0, -2.9, zt+0.04), 0.32, 0.05, M_white, 24)
        for a_ in range(6): stool(5.0+0.62*math.cos(a_*1.047), -2.9+0.62*math.sin(a_*1.047), zt, M_white)
        for k in range(5): box("tmon", (0.15+k*1.06, -4.38, zt+0.66), (0.3, 0.02, 0.2), M_dark); plane("tmons", (0.15+k*1.06, -4.395, zt+0.66), 0.27, 0.17, M_conimg)
        box("gpart", (4.1, -2.4, zt+0.5), (0.02, 1.6, 1.0), M_glass)
        for dx_ in (5.2, 5.75): box("pouf", (dx_, -1.75, zt+0.15), (0.34, 0.34, 0.3), M_dark, 0.03)
        cyl("engbase", (5.6, -1.0, zt+0.04), 0.45, 0.08, M_dark, 32)
        plant(XC+0.3, -5.5, zt, 0.7); plant(6.0, -5.5, zt, 0.7)
        bots = [(1.1,-3.85,0),(2.7,-3.9,4),(5.2,-4.6,7),(4.4,-3.4,1),(0.2,-5.45,2)]
    elif i == 2:  # ---- lounge: purple carpet + wood bar ----
        plane("chartp", (XC+0.04, -4.8, zt+1.0), 1.1, 0.9, M_chartimg, '+X')
        box("darkscr", (XC+0.04, -3.6, zt+1.1), (0.02, 0.8, 0.6), M_dark)
        box("carpet", (0.5, -4.7, zt+0.01), (2.4, 2.0, 0.02), M_purple)
        box("ltable", (0.4, -4.6, zt+0.2), (1.3, 0.5, 0.04), M_wood)
        for k in range(3): box("cube", (-0.3+k*0.55, -5.3, zt+0.13), (0.28, 0.28, 0.26), M_white, 0.01)
        M_sofa = mat("sofa",(0.03,0.03,0.035),0.8)
        box("sofa", (-0.55, -4.4, zt+0.17), (0.4, 1.0, 0.3), M_sofa)
        box("bar", (3.4, -4.25, zt+0.42), (3.6, 0.5, 0.06), mat("lwood",(0.72,0.58,0.4),0.5), 0.01)
        box("barb", (3.4, -4.15, zt+0.2), (3.5, 0.25, 0.4), M_white)
        for k in range(9): stool(1.8+k*0.4, -4.75, zt, M_white)
        for k in range(3): box("pc", (2.6+k*0.8, -4.1, zt+0.56), (0.24, 0.04, 0.16), M_dark)
        cyl("groom", (5.4, -2.6, zt+0.75), 0.75, 1.5, M_glass, 40)
        cyl("groomb", (5.4, -2.6, zt+0.01), 0.77, 0.02, M_dark, 40)
        cyl("groomt", (5.4, -2.6, zt+0.4), 0.3, 0.04, M_white, 24)
        for a in range(5): chair(5.4+0.5*math.cos(a*1.25), -2.6+0.5*math.sin(a*1.25), zt, 1, M_white)
        box("sofa2", (4.6, -5.4, zt+0.17), (0.6, 0.35, 0.3), M_sofa)
        M_bdesk = mat("bdesk",(0.03,0.06,0.2),0.35)
        for k in range(4): chair(1.9, -3.5-k*0.5, zt, 1, M_white)
        for p in [(2.4,-5.4),(5.6,-4.4)]:
            cyl("ctab", (p[0], p[1], zt+0.4), 0.22, 0.03, M_dark, 20); cyl("ctl", (p[0], p[1], zt+0.2), 0.025, 0.4, M_dark, 8)
        plant(6.0, -5.3, zt, 0.7, True)
        # extra lounge furniture (ref: dark armchairs, small round tables, more seating)
        for p in [(1.6,-5.5),(2.0,-3.9),(5.9,-3.6),(4.9,-3.4),(-0.2,-3.7)]:
            box("arm", (p[0], p[1], zt+0.16), (0.36, 0.36, 0.32), M_sofa, 0.04)
            box("armb", (p[0], p[1]+0.15, zt+0.34), (0.36, 0.06, 0.3), M_sofa, 0.02)
        for p in [(1.1,-3.6),(5.0,-1.8),(5.9,-1.2)]:
            cyl("wtab", (p[0], p[1], zt+0.36), 0.25, 0.03, M_white, 24); cyl("wtl", (p[0], p[1], zt+0.18), 0.03, 0.36, M_white, 8)
            for a_ in range(3): stool(p[0]+0.42*math.cos(a_*2.1+0.3), p[1]+0.42*math.sin(a_*2.1+0.3), zt, M_dark)
        plant(-0.6, -5.5, zt, 0.6); plant(2.0, -5.6, zt, 0.6, True)
        bots = [(0.3,-4.0,5),(1.2,-5.0,4),(4.6,-5.0,3),(3.0,-5.35,0)]
    else:         # ---- garden / workshop ----
        plane("aip", (XC+0.04, -5.0, zt+0.95), 0.7, 0.95, M_aiimg, '+X')
        box("mat", (2.4, -5.25, zt+0.01), (2.0, 0.62, 0.015), M_dark)
        bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.025, location=(2.6, -4.2, zt+0.01), major_segments=64)
        _t = bpy.context.object; _t.location.z = zt+0.075; _t.scale.z = 0.2; _t.data.materials.append(M_white)
        tx = text("SPACEX", (2.4, -5.3, zt+0.02), 0.25, M_white, extrude=0.0); tx.data.space_character = 1.4
        for p in [(0.2,-4.4,1.1,True),(1.9,-3.7,1.0,True),(3.8,-4.6,1.2,True),(5.6,-3.0,1.0,True),(XC+0.4,-3.8,0.8,False),(4.9,-5.4,0.8,False),(3.0,-4.4,0.7,False)]:
            plant(p[0], p[1], zt, p[2], p[3])
        for p in [(0.6,-5.3),(1.4,-4.2),(4.3,-5.0),(5.0,-4.0),(-0.4,-5.0)]:
            box("bcube", (p[0], p[1], zt+0.12), (0.24, 0.24, 0.24), M_dark, 0.01)
        M_opt = mat("optimus",(0.05,0.05,0.055),0.3,0.6)
        for (ox, oy) in [(5.0, -4.5), (5.55, -4.15), (0.9, -3.9)]:
            for sgn_ in (-1, 1):
                cyl("oleg", (ox+sgn_*0.06, oy, zt+0.22), 0.04, 0.44, M_opt, 10)
            box("otorso", (ox, oy, zt+0.6), (0.24, 0.14, 0.34), M_opt, 0.03)
            for sgn_ in (-1, 1):
                cyl("oarm", (ox+sgn_*0.15, oy, zt+0.56), 0.03, 0.32, M_opt, 8)
            sph("ohead", (ox, oy, zt+0.86), 0.08, M_opt, (1, 1, 1.15), 16)
            box("oface", (ox+0.04, oy-0.05, zt+0.86), (0.08, 0.02, 0.04), M_white)
        for k in range(3): chair(4.0+k*0.4, -3.7, zt, 1, M_white)
        cyl("rbench", (1.2, -5.3, zt+0.12), 0.45, 0.24, M_wood, 32)
        box("robase", (5.6, -5.2, zt+0.3), (0.4, 0.4, 0.6), M_white)
        cyl("roarm", (5.6, -5.0, zt+0.85), 0.05, 0.6, M_white, 8).rotation_euler.x = 0.6
        for k in range(2): cyl("barrel", (5.2+k*0.45, -1.4, zt+0.3), 0.18, 0.6, M_dark, 16)
        # extra garden density: big leafy plants, dark kiosk column, more cubes and planters
        for p in [(-0.3,-3.8,1.3),(1.5,-5.5,1.2),(4.2,-3.6,1.35),(6.0,-4.5,1.1),(5.9,-2.0,1.2),(2.2,-3.5,0.9)]:
            plant(p[0], p[1], zt, p[2], True)
        box("kcol", (1.7, -4.6, zt+0.5), (0.22, 0.22, 1.0), M_dark); box("kcolb", (1.7, -4.6, zt+0.03), (0.4, 0.4, 0.06), M_dark)
        for p in [(0.0,-4.6),(2.9,-3.6),(5.6,-5.6),(4.0,-5.6)]:
            box("bcube", (p[0], p[1], zt+0.12), (0.24, 0.24, 0.24), M_dark, 0.01)
        for p in [(0.6,-3.6),(3.4,-3.7)]:
            cyl("planter", (p[0], p[1], zt+0.2), 0.22, 0.4, M_white, 20)
        bots = [(2.6,-4.1,0),(4.6,-5.5,5),(1.0,-5.4,6),(3.6,-5.45,0)]
    for bx, by, ci in bots:
        bot(bx, by, zt, M_bots[ci % len(M_bots)])

# under the lowest floor: tank, pillars, crates
zb = Z0 - (NF-1)*FH - 0.14
for px, py in [(XC+0.4,-B+0.6),(1.6,-B+0.6),(3.6,-B+0.6),(A-0.6,-B+0.6),(A-0.6,-3.0),(A-0.6,YC-0.3)]:
    cyl("pillar", (px, py, (zb+FZ_BOT)/2), 0.06, zb-FZ_BOT, M_metal, 12)
M_tank = mat("tank",(0.02,0.02,0.025),0.25,0.3)
cyl("tank", (0.2, -5.25, FZ_BOT+0.55), 0.53, 2.6, M_tank, 40, rot=(0, math.pi/2, 0))
cyl("tankfan", (1.55, -5.25, FZ_BOT+0.55), 0.55, 0.12, M_dark, 24, rot=(0, math.pi/2, 0))
for k in range(8):
    a = k*math.pi/4
    o = box("fanblade", (1.63, -5.25+0.26*math.cos(a), FZ_BOT+0.55+0.26*math.sin(a)), (0.02, 0.07, 0.46), M_metal); o.rotation_euler.x = a - math.pi/2
M_yel = mat("yellow",(0.9,0.6,0.02),0.4)
cyl("tankband", (-1.05, -5.25, FZ_BOT+0.55), 0.535, 0.08, M_yel, 40, rot=(0, math.pi/2, 0))
box("tlabel", (-0.35, -5.25-0.5, FZ_BOT+0.3), (0.4, 0.06, 0.16), M_yel)
for k in range(3): box("frame", (-1.75+k*0.18, -5.3, FZ_BOT+0.45), (0.035, 0.7, 0.9), M_metal)
for j in range(2):
    for k in range(3): box("crate", (4.45+k*0.42, -5.45+j*0.52, FZ_BOT+0.12), (0.4, 0.5, 0.2), M_white, 0.01)
    for k in range(2): box("crate", (4.65+k*0.42, -5.45+j*0.52, FZ_BOT+0.32), (0.4, 0.5, 0.2), M_white, 0.01)
Lr = C.lights.new("recessl", 'AREA'); Lr.energy = 36; Lr.shape = 'RECTANGLE'; Lr.size = 6.0; Lr.size_y = 4.0; Lr.color = (1, 0.95, 0.88)
lro = C.objects.new("recessl", Lr); sc.collection.objects.link(lro); lro.location = (2.6, -3.3, Z0 - (NF-1)*FH - 0.35)

# glass elevator shaft in its slot (thin dark frame, white light bars inside)
M_efr = mat("efr",(0.04,0.04,0.045),0.4)
eh_top = Z0
ES = 0.8; eh = ES/2
box("elev", (EX, EY, (FZ_BOT+eh_top)/2), (ES, ES, eh_top-FZ_BOT), mat("eglass",(0.8,0.85,0.9),0.05, emit=(0.55,0.62,0.7), estr=0.12, alpha=0.28))
for dx in (-eh, eh):
    for dy in (-eh, eh):
        box("efr", (EX+dx, EY+dy, (FZ_BOT+eh_top)/2), (0.045, 0.045, eh_top-FZ_BOT), M_efr)
zz = FZ_BOT + 0.05
while zz < eh_top:
    box("eh1", (EX, EY-eh, zz), (ES, 0.035, 0.035), M_efr); box("eh2", (EX+eh, EY, zz), (0.035, ES, 0.035), M_efr)
    zz += 1.05
for k in range(NF):
    box("ebar", (EX+eh-0.08, EY+eh-0.05, Z0-k*FH-0.9), (0.03, 0.03, 0.7), M_lamp)
# cab: glass with white frame, pink glow and a bot inside
cz = Z0 - 2*FH
box("ecab", (EX, EY, cz+0.55), (0.7, 0.7, 1.0), mat("ecab",(0.95,0.7,0.85),0.05,emit=(1,0.35,0.65),estr=0.35, alpha=0.22))
for dx in (-0.35, 0.35):
    for dy in (-0.35, 0.35):
        box("cabf", (EX+dx, EY+dy, cz+0.55), (0.035, 0.035, 1.0), M_white)
box("cabfl", (EX, EY, cz+0.04), (0.72, 0.72, 0.06), M_white); box("cabrf", (EX, EY, cz+1.06), (0.72, 0.72, 0.06), M_white)
pl = C.lights.new("cabl", 'POINT'); pl.energy = 25; pl.color = (1, 0.4, 0.7); pl.shadow_soft_size = 0.3
plo = C.objects.new("cabl", pl); sc.collection.objects.link(plo); plo.location = (EX, EY, cz+0.85)
box("eback", (EX, EY+0.58, (FZ_BOT+Z0)/2), (1.2, 0.04, Z0-FZ_BOT), mat("slotwall",(0.32,0.32,0.34),0.6))
bot(EX, EY, cz+0.07, M_bots[4], 0.2, glow=False)
# top station: glass box recessed into a notch at mission-floor level (ref: ~1.1 x 2.6, top flush with the surface)
TX0, TX1, TY0, TY1, TZ0, TZ1 = EX-0.45, A+0.05, EY-0.45, EY+2.15, Z0, -0.73
box("tfloor", ((TX0+TX1)/2, (TY0+TY1)/2, TZ0-0.05), (TX1-TX0, TY1-TY0, 0.1), M_white)
box("tglass", ((TX0+TX1)/2, (TY0+TY1)/2, (TZ0+TZ1)/2), (TX1-TX0, TY1-TY0, TZ1-TZ0), M_glass)
for xx in (TX0, TX1):
    for yy in (TY0, TY1):
        box("tf", (xx, yy, (TZ0+TZ1)/2), (0.04, 0.04, TZ1-TZ0), M_efr)
for zz in (TZ0, TZ1):
    box("tfx", ((TX0+TX1)/2, TY0, zz), (TX1-TX0, 0.04, 0.04), M_efr); box("tfx", ((TX0+TX1)/2, TY1, zz), (TX1-TX0, 0.04, 0.04), M_efr)
    box("tfy", (TX0, (TY0+TY1)/2, zz), (0.04, TY1-TY0, 0.04), M_efr); box("tfy", (TX1, (TY0+TY1)/2, zz), (0.04, TY1-TY0, 0.04), M_efr)
box("tfm", (TX1, (TY0+TY1)/2, (TZ0+TZ1)/2), (0.03, 0.03, TZ1-TZ0), M_efr)
box("tfm2", ((TX0+TX1)/2, TY0, (TZ0+TZ1)/2), (0.03, 0.03, TZ1-TZ0), M_efr)
box("tpart", (TX0+0.5, EY+0.9, (TZ0+TZ1)/2), (0.03, 0.9, TZ1-TZ0), M_glass)
bot(EX-0.1, EY+0.9, TZ0, M_bots[1], 0.24, glow=False); bot(EX-0.05, EY+1.7, TZ0, M_bots[0], 0.22, glow=False)
pl2 = C.lights.new("topl", 'POINT'); pl2.energy = 20; pl2.color = (1, 0.85, 0.7)
plo2 = C.objects.new("topl", pl2); sc.collection.objects.link(plo2); plo2.location = (EX, EY+1.0, TZ1-0.25)
# white kiosk with a small dish behind the station
KX, KY, KZ = 5.65, 2.65, TZ1+0.02
box("kiosk", (KX, KY, KZ+0.27), (0.5, 0.42, 0.54), M_white, 0.02)
box("kdoor", (KX, KY-0.215, KZ+0.22), (0.2, 0.02, 0.38), M_dark)
cyl("kpost", (KX+0.1, KY+0.05, KZ+0.65), 0.02, 0.24, M_metal, 6)
c_ = sph("kdish", (KX+0.1, KY+0.05, KZ+0.78), 0.15, M_white, (1, 1, 0.35), 16); c_.rotation_euler = (math.radians(50), 0, math.radians(-45))

# thin railing along the cutaway rim on the surface
xx = XC + 0.1
while xx < EX - 0.7:
    cyl("rpost", (xx, YC+0.12, 0.17), 0.012, 0.34, M_metal, 6, smooth=False); xx += 0.45
box("rrail", ((XC+EX-0.7)/2, YC+0.12, 0.34), (EX-0.7-XC, 0.02, 0.02), M_metal)
yy = -B + 0.15
while yy < YC:
    cyl("rpost", (XC-0.12, yy, 0.17), 0.012, 0.34, M_metal, 6, smooth=False); yy += 0.45
box("rrail", (XC-0.12, (YC-B)/2, 0.34), (0.02, B+YC, 0.02), M_metal)
# dark structural rim around the top of the cutaway
M_rim = mat("rim", (0.05,0.05,0.055), 0.6)
box("rimA", ((XC+A)/2, YC+0.18, -0.27), (A-XC, 0.36, 0.58), M_rim)
box("rimB", (XC-0.18, (YC-B)/2, -0.27), (0.36, B+YC, 0.58), M_rim)
box("colR", (A+0.02, EY+0.62, (FZ_BOT+Z0-0.2)/2), (0.34, 0.36, Z0-0.2-FZ_BOT), mat("colr",(0.07,0.07,0.075),0.5))
for k in range(8):
    box("wlr", (A+0.02, EY+0.43, -2.2 - k*0.95), (0.1, 0.05, 0.16), M_wlamp)
# dark structural column on the rock face left of the cutaway
box("colL", (XC-0.62, 0.15-B, (FZ_BOT-0.05)/2), (1.24, 0.8, -FZ_BOT-0.05), mat("col",(0.045,0.045,0.05),0.5))
cyl("colLs", (XC-0.22, -B-0.3, (FZ_BOT)/2), 0.04, -FZ_BOT, M_white, 10)

# ================= surface =================
PX, PY = -3.38, -1.48
cyl("pad", (PX, PY, 0.05), 2.15, 0.14, M_pad, 64)
bpy.ops.mesh.primitive_torus_add(major_radius=1.92, minor_radius=0.03, location=(PX, PY, 0.13), major_segments=64)
bpy.context.object.data.materials.append(M_white)
bpy.ops.mesh.primitive_torus_add(major_radius=1.3, minor_radius=0.018, location=(PX, PY, 0.13), major_segments=64)
bpy.context.object.data.materials.append(M_white)
# rocket, measured off the ref: r=1.07, body bottom z~0.55, black band z 7.45-9.8, ogive nose tip z~11.75
RB = 0.55; RR = 1.07; BT = 9.8; NOSE = 1.95
cd = Vector((0.707, -0.707, 0)); sd = Vector((0.707, 0.707, 0))
M_rbody = mat("rbody", (0.8,0.81,0.83), 0.38)
M_rband = mat("rband", (0.005,0.005,0.007), 0.5, spec=0.3)
M_seam = mat("seam",(0.5,0.51,0.53),0.45)
def lathe(name, prof, m, segs=64, loc=(0,0,0)):
    bm = bmesh.new(); rings = []
    for (r_, z_) in prof:
        ring = []
        for k in range(segs):
            a = 2*math.pi*k/segs
            ring.append(bm.verts.new((loc[0]+r_*math.cos(a), loc[1]+r_*math.sin(a), loc[2]+z_)))
        rings.append(ring)
    for i in range(len(rings)-1):
        for k in range(segs):
            k2 = (k+1) % segs
            bm.faces.new((rings[i][k], rings[i][k2], rings[i+1][k2], rings[i+1][k]))
    me = C.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons: f.use_smooth = True
    o = C.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(m); return o
# tangent-ogive nose
rho = (RR*RR + NOSE*NOSE)/(2*RR)
prof = []
for k in range(25):
    zz = NOSE*k/24
    r_ = math.sqrt(max(0.0, rho*rho - zz*zz)) + RR - rho
    prof.append((max(r_, 0.0005), zz))
lathe("nose", prof, M_rbody, 64, (PX, PY, BT))
cyl("rocket", (PX, PY, (RB+7.45)/2), RR, 7.45-RB, M_rbody, 64)
cyl("band", (PX, PY, (7.45+BT)/2), RR, BT-7.45, M_rband, 64)
cyl("bandring", (PX, PY, 8.95), RR+0.006, 0.035, M_seam, 64)
cyl("ring", (PX, PY, 2.6), RR+0.004, 0.03, M_seam, 64)
cyl("ring2", (PX, PY, 5.2), RR+0.004, 0.025, M_seam, 64)
cyl("engbay", (PX, PY, RB-0.1), RR*0.92, 0.25, M_rband, 48)
# vertical panel seam facing the camera (slightly right of centre, as in the ref)
for ang in (-45+28, -45-50):
    a = math.radians(ang); dv = Vector((math.cos(a), math.sin(a), 0))
    p = Vector((PX, PY, (RB+7.45)/2)) + dv*(RR+0.002)
    o = box("pseam", (p.x, p.y, p.z), (0.012, 0.012, 7.45-RB-0.1), M_seam)
# four light windows in the band and small dark hatches just under it
M_win = emis("winw", (1.0,0.92,0.75), 1.6)
for k in range(4):
    a = -math.pi/4 + (k-1.5)*0.17
    box("win", (PX+math.cos(a)*(RR+0.005), PY+math.sin(a)*(RR+0.005), 8.35), (0.12, 0.12, 0.085), M_win, rz=a)
for k in range(8):
    a = -math.pi/4 + (k-3.5)*0.36
    box("hatch", (PX+math.cos(a)*(RR+0.003), PY+math.sin(a)*(RR+0.003), 7.3), (0.17, 0.17, 0.1), M_rband, rz=a)
# aft strakes (four tall narrow white plates) + splayed landing struts
for k in range(4):
    a = math.radians(-45 + 38 + k*90)
    dvec = Vector((math.cos(a), math.sin(a), 0))
    p = Vector((PX, PY, RB+1.05)) + dvec*(RR+0.1)
    o2 = box("afin", (p.x, p.y, p.z), (0.26, 0.05, 2.1), M_rbody); o2.rotation_euler.z = a
for k in range(6):
    a = math.radians(-45 + 10 + k*60)
    dv = Vector((math.cos(a), math.sin(a), 0))
    p0 = Vector((PX, PY, RB+1.55)) + dv*(RR*0.98); p1 = Vector((PX, PY, 0.14)) + dv*1.85
    mid = (p0+p1)/2; dvv = p0-p1
    lg = cyl("leg", mid, 0.045, dvv.length, M_white, 8)
    lg.rotation_euler = dvv.to_track_quat('Z','Y').to_euler()
    p2 = Vector((PX, PY, RB+0.25)) + dv*(RR*0.95)
    mid = (p2+p1)/2; dvv = p2-p1
    lg = cyl("leg2", mid, 0.03, dvv.length, M_metal, 6)
    lg.rotation_euler = dvv.to_track_quat('Z','Y').to_euler()
    cyl("foot", p1, 0.13, 0.05, M_dark, 12)

def swoosh(name, p0, p1, bulge, thick, m, width=0.04, frame=None, n=24):
    """crescent swoosh from p0 to p1 (2D in the frame's x/y), bulging by `bulge`, thickness tapering"""
    bm = bmesh.new(); top = []; bot = []
    for k in range(n+1):
        t = k/n
        x = p0[0] + (p1[0]-p0[0])*t; y = p0[1] + (p1[1]-p0[1])*t + bulge*math.sin(math.pi*t)
        th = thick*math.sin(math.pi*min(1, t*1.1))**0.7 + 0.004
        top.append(bm.verts.new((x, y + th/2, 0))); bot.append(bm.verts.new((x, y - th/2, 0)))
    for k in range(n):
        bm.faces.new((bot[k], bot[k+1], top[k+1], top[k]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=width)
    me = C.meshes.new(name); bm.to_mesh(me); bm.free()
    o = C.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(m)
    if frame is not None: o.matrix_world = frame
    return o

# vertical SPACEX on the body, facing camera (wide letter spacing like the logo)
Xv = Vector((0,0,1)); Zv = cd.copy(); Yv = Zv.cross(Xv)
FR = Matrix.Translation(Vector((PX, PY, 2.75)) + cd*(RR+0.012)) @ Matrix((Xv, Yv, Zv)).transposed().to_4x4()
t = text("SPACEX", (0,0,0), 0.52, M_dark, extrude=0.004, align='LEFT', spacing=1.12)
t.matrix_world = FR
t.data.align_y = 'CENTER'
bpy.context.view_layer.update()
Wt = t.dimensions.x; Ht = t.dimensions.y
print("rocket text dims", Wt, Ht)
# small logo swoosh: from the middle of the X out past its upper-right arm
swoosh("rswoosh", (Wt-0.42*Ht*1.4, -0.12*Ht), (Wt+0.55*Ht, 0.95*Ht), 0.12*Ht, 0.16*Ht, M_dark, 0.004, FR @ Matrix.Translation((0, 0, 0.004)))
# giant SPACEX sign on the back edge: custom logotype glyphs (thin strokes, A without bar) on a light scaffold
def rounded(pts, r, n=6):
    out = [pts[0]]
    for i in range(1, len(pts)-1):
        p0, p1, p2 = Vector(pts[i-1]), Vector(pts[i]), Vector(pts[i+1])
        d0 = (p0-p1).normalized(); d1 = (p2-p1).normalized()
        rr = min(r, (p0-p1).length*0.42, (p2-p1).length*0.42)
        a0 = p1 + d0*rr; a1 = p1 + d1*rr
        for k in range(n+1):   # quadratic bezier corner
            t = k/n; q = a0*(1-t)**2 + p1*2*t*(1-t) + a1*t*t
            out.append((q.x, q.y))
    out.append(pts[-1])
    ded = [out[0]]
    for q in out[1:]:
        if (Vector(q)-Vector(ded[-1])).length > 1e-4: ded.append(q)
    return ded
def stroke_geom(bm, pts, w, depth):
    vs = [Vector((x, y, 0)) for x, y in pts]
    L_ = []; R_ = []
    for i, v in enumerate(vs):
        if i == 0: t = (vs[1]-v).normalized()
        elif i == len(vs)-1: t = (v-vs[i-1]).normalized()
        else:
            t = ((v-vs[i-1]).normalized() + (vs[i+1]-v).normalized()).normalized()
        nrm = Vector((-t.y, t.x, 0))
        if 0 < i < len(vs)-1:
            t0 = (v-vs[i-1]).normalized(); n0 = Vector((-t0.y, t0.x, 0))
            sc_ = 1.0/max(0.4, nrm.dot(n0))
        else: sc_ = 1.0
        L_.append(v + nrm*w/2*sc_); R_.append(v - nrm*w/2*sc_)
    fr = []; bk = []
    for P_ in L_ + R_[::-1]:
        fr.append(bm.verts.new(P_)); bk.append(bm.verts.new(P_ + Vector((0, 0, -depth))))
    n_ = len(fr)
    half = len(L_)
    for i in range(half-1):
        bm.faces.new((fr[i], fr[i+1], fr[n_-2-i], fr[n_-1-i]))
        bm.faces.new((bk[n_-1-i], bk[n_-2-i], bk[i+1], bk[i]))
    for i in range(n_):
        j = (i+1) % n_
        bm.faces.new((fr[i], bk[i], bk[j], fr[j]))
GW, GH, ST = 0.95, 0.8, 0.25   # glyph width / height / stroke
h_ = ST/2
GLYPHS = {
 'S': [rounded([(GW, GH-h_), (h_, GH-h_), (h_, GH*0.5), (GW-h_, GH*0.5), (GW-h_, h_), (0, h_)], 0.28)],
 'P': [rounded([(h_, 0), (h_, GH-h_), (GW-h_, GH-h_), (GW-h_, GH*0.47), (h_, GH*0.47)], 0.24)],
 'A': [[(0.02, 0), (GW*0.5, GH-0.02), (GW-0.02, 0)]],
 'C': [rounded([(GW, GH-h_), (h_, GH-h_), (h_, h_), (GW, h_)], 0.28)],
 'E': [rounded([(GW, GH-h_), (h_, GH-h_), (h_, h_), (GW, h_)], 0.18), [(h_, GH*0.5), (GW*0.92, GH*0.5)]],
 'X': [[(0.0, 0.0), (GW, GH)], [(0.0, GH), (GW, 0.0)]],
}
bm = bmesh.new(); xo = 0.0
GROT = math.radians(float(os.environ.get("GROT", 16)))   # each glyph turned a bit more toward the camera than the row
for ch in "SPACEX":
    nv0 = len(bm.verts)
    for pl in GLYPHS[ch]:
        stroke_geom(bm, [(x+xo+0.12*y, y) for x, y in pl], ST, 0.34)
    bm.verts.ensure_lookup_table()
    gv = [bm.verts[i] for i in range(nv0, len(bm.verts))]
    bmesh.ops.rotate(bm, verts=gv, cent=Vector((xo+GW*0.6, 0, 0)), matrix=Matrix.Rotation(GROT, 3, 'Y'))
    xo += GW + 0.47
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me_ = C.meshes.new("signglyphs"); bm.to_mesh(me_); bm.free()
M_signw = mat("signw", (0.9,0.9,0.92), 0.35, emit=(1,1,1), estr=0.12)
sgn = C.objects.new("sign", me_); sc.collection.objects.link(sgn); sgn.data.materials.append(M_signw)
md_ = sgn.modifiers.new("b", 'BEVEL'); md_.width = 0.07; md_.segments = 3; md_.limit_method = 'ANGLE'
SIGN_W = xo - 0.47
# frame: x along the sign (rotated 22 deg toward the camera), y up, z toward the camera
SG0 = Vector(SGN_P) + Vector((0, 0, 0.2)); SA = SGN_A
ex_ = Vector((math.cos(SA), math.sin(SA), 0)); ey_ = Vector((0, 0, 1)); ez_ = ex_.cross(ey_)
SF = Matrix.Translation(SG0) @ Matrix((ex_, ey_, ez_)).transposed().to_4x4()
sgn.matrix_world = SF
# swoosh from inside the X sweeping out to the right
sw = swoosh("sswoosh", (SIGN_W-0.75, 0.15), (SIGN_W+1.6, 0.85), -0.12, 0.16, M_signw, 0.1, SF @ Matrix.Translation((0, 0, -0.05)))
# scaffold behind the letters: posts + two rails + diagonal braces
M_scaf = mat("scaf",(0.2,0.2,0.22),0.5,0.2)
def seg_(a_, b_, r_=0.022, m_=M_scaf):
    a_, b_ = Vector(a_), Vector(b_); d_ = b_-a_
    o = cyl("scaf", (a_+b_)/2, r_, d_.length, m_, 6, smooth=False); o.rotation_euler = d_.to_track_quat('Z','Y').to_euler(); return o
back_ = -ez_*0.35
for k in range(6):
    t_ = 0.3 + k*(SIGN_W-0.6)/5
    base_ = SG0 + ex_*t_ + back_
    gz = 0.0
    seg_((base_.x, base_.y, gz), (base_.x, base_.y, SG0.z+0.55), 0.016)
    if k < 5:
        nb = SG0 + ex_*(t_+(SIGN_W-0.6)/5) + back_
        seg_((base_.x, base_.y, gz+0.1), (nb.x, nb.y, SG0.z+0.5), 0.01)
for zz_ in (SG0.z+0.1, SG0.z+0.5):
    p0_ = SG0 + ex_*(0.3) + back_; p1_ = SG0 + ex_*(SIGN_W-0.3) + back_
    seg_((p0_.x, p0_.y, zz_), (p1_.x, p1_.y, zz_), 0.014)
# LANDING ZONE 1 painted on the pad (reads along the camera's right axis)
lz = text("LANDING ZONE 1", (0,0,0), 0.2, M_white, extrude=0.0, spacing=1.1)
lz.location = Vector((PX, PY, 0.125)) + cd*1.55; lz.rotation_euler = (0, 0, math.radians(45)); lz.data.align_y = 'CENTER'
# solar field
_nt = M_solar.node_tree; _b = _nt.nodes["Principled BSDF"]
_br = _nt.nodes.new("ShaderNodeTexBrick"); _br.offset = 0.0
_br.inputs["Color1"].default_value = (0.006,0.008,0.016,1); _br.inputs["Color2"].default_value = (0.009,0.011,0.022,1)
_br.inputs["Mortar"].default_value = (0.09,0.1,0.12,1); _br.inputs["Scale"].default_value = 3.2
_br.inputs["Mortar Size"].default_value = 0.012; _br.inputs["Brick Width"].default_value = 0.5; _br.inputs["Row Height"].default_value = 0.42
_tcs = _nt.nodes.new("ShaderNodeTexCoord"); _nt.links.new(_tcs.outputs["Object"], _br.inputs["Vector"])
_nt.links.new(_br.outputs["Color"], _b.inputs["Base Color"])
for i in range(5):
    for j in range(9):
        x = 0.7 + j*0.6; y = 1.95 + i*0.58
        if x > 4.9 and y < 3.3: continue
        h0 = TH(x, y)
        o = box("panel", (x, y, h0+0.38), (0.5, 0.46, 0.025), M_solar); o.rotation_euler.x = 0.35
        box("pframe", (x, y-0.22, h0+0.3), (0.48, 0.02, 0.02), M_metal)
        cyl("post", (x, y, h0+0.1), 0.018, 0.55, M_metal, 6, smooth=False)
# satellite dishes on the right edge
for dx, dy in [(6.2, 3.4), (6.25, 3.95), (6.3, 4.5)]:
    h0 = TH(dx, dy)
    cyl("dpost", (dx, dy, h0+0.3), 0.035, 0.6, M_metal, 8)
    c = sph("dish", (dx, dy, h0+0.75), 0.4, M_white, (1, 1, 0.28), 24); DN = Vector((0.15, -0.9, 0.42)).normalized(); c.rotation_euler = DN.to_track_quat('Z','Y').to_euler()
    fp = Vector((dx, dy, h0+0.75)) + DN*0.2; cyl("dfeed", fp, 0.012, 0.36, M_dark, 6).rotation_euler = DN.to_track_quat('Z','Y').to_euler()
# gold lander (Apollo-style descent stage) + sign, positions measured off the ref
LX, LY = -4.5, -5.0
cyl("lander", (LX, LY, 0.55), 0.6, 0.42, M_gold, 8, smooth=False)
cyl("landrim", (LX, LY, 0.78), 0.56, 0.05, mat("lfoil",(0.75,0.55,0.12),0.55,0.6), 8, smooth=False)
sph("landtop", (LX, LY, 0.8), 0.42, M_dark, (1, 1, 0.3), 20)
for k in range(4):
    a = k*math.pi/2 + 0.4
    lg = cyl("lleg", (LX+math.cos(a)*0.74, LY+math.sin(a)*0.74, 0.3), 0.03, 0.7, M_gold, 6)
    lg.rotation_euler = (math.sin(a)*0.6, -math.cos(a)*0.6, 0)
    cyl("lfoot", (LX+math.cos(a)*0.92, LY+math.sin(a)*0.92, 0.03), 0.1, 0.03, M_gold, 10)
SGX, SGY = -3.0, -5.9
box("tboard", (SGX, SGY, 0.55), (1.0, 0.05, 0.45), M_white)
box("tred", (SGX, SGY-0.03, 0.45), (0.8, 0.02, 0.12), emis("red2",(0.9,0.05,0.05),1.0))
for xx in (SGX-0.45, SGX+0.45): box("tpost", (xx, SGY, 0.2), (0.04, 0.04, 0.4), M_metal)
text("TRANQUILITY BASE", (SGX, SGY-0.032, 0.6), 0.085, M_dark, rot=(math.radians(90), 0, 0), extrude=0.0)
text("DO NOT TOUCH", (SGX, SGY-0.045, 0.42), 0.07, M_white, rot=(math.radians(90), 0, 0), extrude=0.0)
# posts along the front-left top edge
xx = -A + 0.35
while xx < XC - 1.4:
    cyl("epost", (xx, -B+0.22, 0.12), 0.012, 0.24, M_metal, 6, smooth=False); xx += 0.5
M_srock = mat("srock",(0.16,0.16,0.17),0.9)
# crates, rover, surface bots, rocks
M_crate = mat("crate",(0.9,0.9,0.92),0.4)
for k, (cx_, cy_, cz_) in enumerate([(0,0,0),(0.34,0,0),(0.68,0,0),(0,0.34,0),(0.34,0.34,0),(0.68,0.34,0),(0.17,0.17,1),(0.51,0.17,1),(0.34,-0.36,0)]):
    box("crate", (-2.7+cx_*0.88, 4.1+cy_*0.88, 0.14+0.27*cz_+TH(-2.6,4.2)), (0.29, 0.29, 0.26), M_crate, 0.012)
RVX, RVY = 4.6, 0.75
bm = bmesh.new()
prof = [(-0.55,0.1),(0.55,0.1),(0.55,0.3),(0.05,0.5),(-0.55,0.32)]
vs = [[bm.verts.new((px_, sy, pz_)) for px_, pz_ in prof] for sy in (-0.27, 0.27)]
bm.faces.new(vs[0][::-1]); bm.faces.new(vs[1])
for k_ in range(len(prof)):
    k2 = (k_+1) % len(prof); bm.faces.new((vs[0][k_], vs[0][k2], vs[1][k2], vs[1][k_]))
me_ = C.meshes.new("rover"); bm.to_mesh(me_); bm.free()
rv = C.objects.new("rover", me_); sc.collection.objects.link(rv); rv.location = (RVX, RVY, 0); rv.data.materials.append(mat("roverw",(0.85,0.86,0.88),0.25,0.3))
box("roverwin", (RVX+0.05, RVY, 0.42), (0.5, 0.56, 0.08), M_dark)
for dx in (-0.35, 0.35):
    for dy in (-0.26, 0.26):
        cyl("wheel", (RVX+dx, RVY+dy, 0.12), 0.12, 0.08, M_dark, 12, rot=(math.pi/2, 0, 0))
bot(1.3, 1.25, 0.0, M_bots[6], 0.27); bot(1.85, 1.05, 0.0, M_bots[4], 0.27)
for k in range(140):
    x = random.uniform(-A+0.4, A-0.4); y = random.uniform(-B+0.4, B-0.4)
    if (x > XC-0.3 and y < YC+0.3) or (x > EX-0.8 and y < EY+2.5) or math.hypot(x-PX, y-PY) < 2.4: continue
    o = ico("rock", (x, y, 0.02+TH(x, y)), random.uniform(0.04, 0.16), M_srock, 1)
    o.scale = (1, random.uniform(0.7,1.3), random.uniform(0.5,0.8))

# ================= camera =================
OS = float(os.environ.get("OS", 20.0))
cam = C.cameras.new("cam"); cam.type = 'ORTHO'; cam.ortho_scale = OS; cam.sensor_fit = 'HORIZONTAL'
co = C.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
co.rotation_euler = (math.radians(float(os.environ.get("EL", 60))), 0, math.radians(float(os.environ.get("AZ", 45))))
R = co.rotation_euler.to_matrix()
right = R @ Vector((1,0,0)); up = R @ Vector((0,1,0)); back = R @ Vector((0,0,1))
k = OS/720.0   # world units per reference pixel (ref is 720 px wide)
# block-top centre should sit at ref pixel (380, 395) -> 20 px right, 55 px above frame centre
SX = float(os.environ.get("SX", 20)); SY = float(os.environ.get("SY", 55))
target = Vector((0,0,0)) - right*(SX*k) - up*(SY*k)
co.location = target + back*60
cam.clip_end = 300
# earth upper right (ref pixel ~ (580,135), radius ~55 px)
M_earth = C.materials.new("earth"); M_earth.use_nodes = True
N = M_earth.node_tree.nodes; L = M_earth.node_tree.links
be = N["Principled BSDF"]; be.inputs["Roughness"].default_value = 0.5
ne = N.new("ShaderNodeTexNoise"); ne.inputs["Scale"].default_value = 1.6; ne.inputs["Detail"].default_value = 10; ne.inputs["Roughness"].default_value = 0.6
re = N.new("ShaderNodeValToRGB"); _el = re.color_ramp.elements
_el[0].position = 0.0; _el[0].color = (0.002,0.025,0.18,1); _el[1].position = 1.0; _el[1].color = (0.45,0.38,0.2,1)
for _p, _c in [(0.44,(0.006,0.045,0.27)),(0.5,(0.012,0.08,0.36)),(0.515,(0.1,0.22,0.04)),(0.6,(0.17,0.26,0.06))]:
    _x = _el.new(_p); _x.color = (*_c, 1)
nc = N.new("ShaderNodeTexNoise"); nc.inputs["Scale"].default_value = 3.5; nc.inputs["Detail"].default_value = 8; nc.inputs["Distortion"].default_value = 1.2
rc = N.new("ShaderNodeValToRGB"); rc.color_ramp.elements[0].position = 0.56; rc.color_ramp.elements[1].position = 0.7
mxe = N.new("ShaderNodeMixRGB")
L.new(ne.outputs["Fac"], re.inputs["Fac"]); L.new(nc.outputs["Fac"], rc.inputs["Fac"])
L.new(rc.outputs["Color"], mxe.inputs["Fac"]); L.new(re.outputs["Color"], mxe.inputs[1]); mxe.inputs[2].default_value = (0.9,0.9,0.9,1)
L.new(mxe.outputs["Color"], be.inputs["Base Color"])
# self-lit earth with a terminator (night side on the right) and a thin blue atmosphere rim
eo = N["Material Output"]
ldir = (-right*0.9 + up*0.1 + back*0.44).normalized()
geo = N.new("ShaderNodeNewGeometry"); dp = N.new("ShaderNodeVectorMath"); dp.operation = 'DOT_PRODUCT'
dp.inputs[1].default_value = ldir
L.new(geo.outputs["Normal"], dp.inputs[0])
tm = N.new("ShaderNodeMapRange"); tm.inputs["From Min"].default_value = -0.3; tm.inputs["From Max"].default_value = 0.3
tm.inputs["To Min"].default_value = 0.006; tm.inputs["To Max"].default_value = 1.0
L.new(dp.outputs["Value"], tm.inputs["Value"])
cm = N.new("ShaderNodeMixRGB"); cm.blend_type = 'MULTIPLY'; cm.inputs["Fac"].default_value = 1
L.new(mxe.outputs["Color"], cm.inputs["Color1"]); L.new(tm.outputs["Result"], cm.inputs["Color2"])
e1 = N.new("ShaderNodeEmission"); e1.inputs["Strength"].default_value = 1.4; L.new(cm.outputs["Color"], e1.inputs["Color"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
rp_ = N.new("ShaderNodeMath"); rp_.operation = 'POWER'; rp_.inputs[1].default_value = 2.5
L.new(lw.outputs["Facing"], rp_.inputs[0])
rm = N.new("ShaderNodeMath"); rm.operation = 'MULTIPLY'; L.new(rp_.outputs[0], rm.inputs[0]); L.new(tm.outputs["Result"], rm.inputs[1])
e2 = N.new("ShaderNodeEmission"); e2.inputs["Color"].default_value = (0.55,0.9,1.7,1); L.new(rm.outputs[0], e2.inputs["Strength"])
ad = N.new("ShaderNodeAddShader"); L.new(e1.outputs[0], ad.inputs[0]); L.new(e2.outputs[0], ad.inputs[1])
L.new(ad.outputs[0], eo.inputs["Surface"])
earth = sph("earth", target + R @ Vector((238*k, 315*k, -40)), 69*k, M_earth, seg=64)
EARTH_IMG = os.environ.get("EARTH", "/tmp/earth_land.jpg"); CLOUD_IMG = os.environ.get("CLOUDS", "/tmp/earth_cloud.jpg")
if os.path.exists(EARTH_IMG) and os.path.getsize(EARTH_IMG) > 100000:
    print("EARTH texture", EARTH_IMG)
    tci = N.new("ShaderNodeTexCoord")
    li = N.new("ShaderNodeTexImage"); li.image = bpy.data.images.load(EARTH_IMG); li.projection = 'SPHERE'
    L.new(tci.outputs["Object"], li.inputs["Vector"])
    land_col = li.outputs["Color"]
    hsv = N.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = 1.8; hsv.inputs["Value"].default_value = 1.45
    L.new(land_col, hsv.inputs["Color"]); land_col = hsv.outputs["Color"]
    if os.path.exists(CLOUD_IMG) and os.path.getsize(CLOUD_IMG) > 100000:
        ci = N.new("ShaderNodeTexImage"); ci.image = bpy.data.images.load(CLOUD_IMG); ci.projection = 'SPHERE'
        ci.image.colorspace_settings.name = 'Non-Color'
        L.new(tci.outputs["Object"], ci.inputs["Vector"])
        cmx = N.new("ShaderNodeMixRGB"); cmx.inputs["Color2"].default_value = (0.95,0.96,0.98,1)
        cpow = N.new("ShaderNodeMath"); cpow.operation = 'POWER'; cpow.inputs[1].default_value = 1.5
        cal = N.new("ShaderNodeMath"); cal.operation = 'MULTIPLY'
        cbw = N.new("ShaderNodeRGBToBW"); L.new(ci.outputs["Color"], cbw.inputs[0])
        L.new(cbw.outputs[0], cal.inputs[0]); L.new(ci.outputs["Alpha"], cal.inputs[1])
        L.new(cal.outputs[0], cpow.inputs[0]); L.new(cpow.outputs[0], cmx.inputs["Fac"])
        L.new(land_col, cmx.inputs["Color1"]); land_col = cmx.outputs["Color"]
    L.new(land_col, cm.inputs["Color1"])
    # orient: longitude -65 on the equator faces the camera, north up on screen
    # image sphere projection: u = 0.5 - atan2(x, y)/2pi, so longitude lon sits at (sin(-lon), cos(-lon))
    LON = float(os.environ.get("ELON", -52)); L1 = Vector((math.sin(math.radians(-LON)), math.cos(math.radians(-LON)), 0))
    Lz = Vector((0, 0, 1)); L3 = Lz.cross(L1)
    TL = math.radians(float(os.environ.get("ETILT", 12))); W1 = (back.normalized()*math.cos(TL) - up.normalized()*math.sin(TL)); Wz = (up.normalized()*math.cos(TL) + back.normalized()*math.sin(TL)); W3 = Wz.cross(W1)
    Mw = Matrix((W1, Wz, W3)).transposed(); Ml = Matrix((L1, Lz, L3)).transposed()
    earth.rotation_euler = (Mw @ Ml.inverted()).to_euler()
# stars on a backdrop plane facing the camera
M_star = C.materials.new("stars"); M_star.use_nodes = True
nt = M_star.node_tree; nt.nodes.clear()
so_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
tcs = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 115
vo.inputs["Randomness"].default_value = 0.9
smp = nt.nodes.new("ShaderNodeMapping"); smp.inputs["Scale"].default_value = (1.0, 1.333, 1.0)
nt.links.new(tcs.outputs["Object"], smp.inputs["Vector"]); nt.links.new(smp.outputs["Vector"], vo.inputs["Vector"])
dmr = nt.nodes.new("ShaderNodeMapRange"); dmr.inputs["From Min"].default_value = 0.03; dmr.inputs["From Max"].default_value = 0.11
dmr.inputs["To Min"].default_value = 1.0; dmr.inputs["To Max"].default_value = 0.0
nt.links.new(vo.outputs["Distance"], dmr.inputs["Value"])
srgb = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(vo.outputs["Color"], srgb.inputs[0])
keep = nt.nodes.new("ShaderNodeMath"); keep.operation = 'GREATER_THAN'; keep.inputs[1].default_value = 0.955
nt.links.new(srgb.outputs[0], keep.inputs[0])
bri = nt.nodes.new("ShaderNodeMath"); bri.operation = 'MULTIPLY_ADD'; bri.inputs[1].default_value = 2.2; bri.inputs[2].default_value = 0.35
nt.links.new(srgb.outputs[1], bri.inputs[0])
s1 = nt.nodes.new("ShaderNodeMath"); s1.operation = 'MULTIPLY'; nt.links.new(dmr.outputs[0], s1.inputs[0]); nt.links.new(keep.outputs[0], s1.inputs[1])
s2 = nt.nodes.new("ShaderNodeMath"); s2.operation = 'MULTIPLY'; nt.links.new(s1.outputs[0], s2.inputs[0]); nt.links.new(bri.outputs[0], s2.inputs[1])
s3 = nt.nodes.new("ShaderNodeMath"); s3.operation = 'ADD'; s3.inputs[1].default_value = 0.002; nt.links.new(s2.outputs[0], s3.inputs[0])
em.inputs["Color"].default_value = (0.92,0.95,1.0,1)
nt.links.new(s3.outputs[0], em.inputs["Strength"])
nt.links.new(em.outputs[0], so_.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=1, location=target - back*120)
sp = bpy.context.object; sp.scale = (OS*1.2, OS*1.6, 1); sp.rotation_euler = co.rotation_euler; sp.data.materials.append(M_star)
sp.visible_shadow = False

# ================= lights =================
def aim(obj, d):
    obj.rotation_euler = Vector(d).normalized().to_track_quat('Z','Y').to_euler()
sun = C.lights.new("sun", 'SUN'); sun.energy = 3.0; sun.angle = math.radians(3)
try:
    sun.shadow_maximum_resolution = 0.0005; sun.shadow_filter_radius = 1.5
    sc.eevee.shadow_resolution_scale = 1.0
except Exception as ex: print("shadow", ex)
so = C.objects.new("sun", sun); sc.collection.objects.link(so); aim(so, (-0.18, -1.0, 0.8))
fill = C.lights.new("fill", 'SUN'); fill.energy = 1.0; fill.angle = math.radians(20)
fo = C.objects.new("fill", fill); sc.collection.objects.link(fo); aim(fo, (1.0, -0.4, 0.6))
fill.use_shadow = False
wd = C.worlds.new("w"); sc.world = wd; wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02,0.022,0.026,1)
wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

# ================= render =================
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = int(os.environ.get("PS", 24))
try:
    sc.eevee.use_raytracing = True; sc.eevee.ray_tracing_method = 'SCREEN'
    sc.eevee.use_shadows = True; sc.eevee.shadow_ray_count = 2; sc.eevee.shadow_step_count = 8
except Exception as ex: print("rt", ex)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = os.environ.get('LOOK', 'AgX - Medium High Contrast')
sc.view_settings.exposure = float(os.environ.get("EXP", 0.35))
sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
sc.render.resolution_percentage = int(os.environ.get("PCT", 100))
sc.render.image_settings.file_format = "PNG"
out = os.environ.get("OUT", "../out/moon_hero.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
print("BUILD_SECONDS %.1f objects %d" % (time.time()-T0, len(C.objects)))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(out), "moonbase.blend"))
sc.render.filepath = out
T1 = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER_SECONDS %.1f" % (time.time()-T1))
print("DONE", out)
