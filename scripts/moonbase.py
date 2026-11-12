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
M_slab = mat("slab", (0.46,0.47,0.49), 0.35)
M_dark = mat("dark", (0.025,0.027,0.03), 0.35)
M_desk = mat("desk", (0.035,0.038,0.045), 0.25)
M_chair = mat("chair", (0.015,0.015,0.018), 0.5)
M_wall = mat("wall", (0.035,0.036,0.04), 0.6)
M_panel = mat("panel", (0.75,0.76,0.78), 0.4)
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
M_pad = mat("pad", (0.07,0.07,0.075), 0.6)
BOT_COLS = [(0.02,0.75,0.08),(1.0,0.32,0.0),(0.03,0.18,1.0),(0.42,0.04,1.0),(1.0,0.04,0.32),(0.0,0.62,0.75),(1.0,0.7,0.0),(0.95,0.95,0.97)]
M_bots = [mat(f"bot{i}", tuple(v*0.8 for v in c), 0.22, emit=c, estr=0.12, spec=0.7) for i,c in enumerate(BOT_COLS)]
M_pupil = mat("pupil",(0.01,0.01,0.01),0.2)

# ---- rock: broad soft strata bands + faint fine striations ----
M_rock = C.materials.new("rock"); M_rock.use_nodes = True
nt = M_rock.node_tree; N = nt.nodes; L = nt.links
bsdf = N["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.92
tc = N.new("ShaderNodeTexCoord")
# broad bands: noise stretched along x/y so it varies mostly with z
mpB = N.new("ShaderNodeMapping"); mpB.inputs["Scale"].default_value = (0.035, 0.035, 0.45)
nB = N.new("ShaderNodeTexNoise"); nB.inputs["Scale"].default_value = 1.0; nB.inputs["Detail"].default_value = 3; nB.inputs["Roughness"].default_value = 0.45
L.new(tc.outputs["Object"], mpB.inputs["Vector"]); L.new(mpB.outputs["Vector"], nB.inputs["Vector"])
# fine striations
wav = N.new("ShaderNodeTexWave"); wav.wave_type = 'BANDS'; wav.bands_direction = 'Z'
wav.inputs["Scale"].default_value = 1.25; wav.inputs["Distortion"].default_value = 1.6
wav.inputs["Detail"].default_value = 4; wav.inputs["Detail Scale"].default_value = 0.25; wav.inputs["Detail Roughness"].default_value = 0.7
L.new(tc.outputs["Object"], wav.inputs["Vector"])
rB = N.new("ShaderNodeValToRGB"); r = rB.color_ramp
r.elements[0].position = 0.28; r.elements[0].color = (0.05,0.05,0.055,1)
r.elements[1].position = 0.75; r.elements[1].color = (0.36,0.36,0.37,1)
e = r.elements.new(0.45); e.color = (0.15,0.15,0.155,1)
e = r.elements.new(0.6); e.color = (0.25,0.25,0.26,1)
L.new(nB.outputs["Fac"], rB.inputs["Fac"])
fineR = N.new("ShaderNodeValToRGB"); fr_ = fineR.color_ramp
fr_.elements[0].position = 0.0; fr_.elements[0].color = (0.45,0.45,0.45,1)
fr_.elements[1].position = 1.0; fr_.elements[1].color = (0.85,0.85,0.85,1)
for p_, v_ in [(0.1,1.0),(0.5,1.15),(0.8,1.05)]:
    e_ = fr_.elements.new(p_); e_.color = (v_,v_,v_,1)
L.new(wav.outputs["Fac"], fineR.inputs["Fac"])
mulc = N.new("ShaderNodeMixRGB"); mulc.blend_type = 'MULTIPLY'; mulc.inputs["Fac"].default_value = 1.0
L.new(rB.outputs["Color"], mulc.inputs["Color1"]); L.new(fineR.outputs["Color"], mulc.inputs["Color2"])
gn = N.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 55; gn.inputs["Detail"].default_value = 2
L.new(tc.outputs["Object"], gn.inputs["Vector"])
gr = N.new("ShaderNodeMapRange"); gr.inputs["From Min"].default_value = 0.3; gr.inputs["From Max"].default_value = 0.7
gr.inputs["To Min"].default_value = 0.7; gr.inputs["To Max"].default_value = 1.2
L.new(gn.outputs["Fac"], gr.inputs["Value"])
mulg = N.new("ShaderNodeMixRGB"); mulg.blend_type = 'MULTIPLY'; mulg.inputs["Fac"].default_value = 1.0
L.new(mulc.outputs["Color"], mulg.inputs["Color1"]); L.new(gr.outputs["Result"], mulg.inputs["Color2"])
sxyz = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sxyz.inputs[0])
mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -1.0; mr.inputs["From Max"].default_value = -0.2
L.new(sxyz.outputs["Z"], mr.inputs["Value"])
crust = N.new("ShaderNodeMixRGB"); crust.inputs["Color2"].default_value = (0.3,0.3,0.31,1)
L.new(mr.outputs["Result"], crust.inputs["Fac"]); L.new(mulg.outputs["Color"], crust.inputs["Color1"])
L.new(crust.outputs["Color"], bsdf.inputs["Base Color"])
bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.5
fn = N.new("ShaderNodeTexNoise"); fn.inputs["Scale"].default_value = 5; fn.inputs["Detail"].default_value = 6
mpF = N.new("ShaderNodeMapping"); mpF.inputs["Scale"].default_value = (0.5, 0.5, 2.0)
L.new(tc.outputs["Object"], mpF.inputs["Vector"]); L.new(mpF.outputs["Vector"], fn.inputs["Vector"])
L.new(fn.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

# ---- regolith ----
M_reg = C.materials.new("regolith"); M_reg.use_nodes = True
nt = M_reg.node_tree; N = nt.nodes; L = nt.links
b2 = N["Principled BSDF"]; b2.inputs["Roughness"].default_value = 1
n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 0.35; n2.inputs["Detail"].default_value = 8; n2.inputs["Roughness"].default_value = 0.6
r2 = N.new("ShaderNodeValToRGB"); er = r2.color_ramp.elements
er[0].position = 0.32; er[0].color = (0.1,0.1,0.105,1); er[1].position = 0.68; er[1].color = (0.34,0.34,0.35,1)
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
M_conimg = imgmat("conscr", console_img(), 0.6)
M_dialimg = imgmat("dialp", dial_panel_img(), 0, emissive=False)
M_poster = imgmat("poster", poster_img(), 1.1)
M_chartimg = imgmat("chartp", chart_panel_img(), 0, emissive=False)
M_aiimg = imgmat("aip", ai_panel_img(), 0.9)

# ================= layout constants =================
A, B = 6.5, 6.0              # half extents in x, y
XC, YC = -1.0, -0.6          # cutaway region: x > XC and y < YC
ZB, ZT = -18.5, -10.8        # rock bottom tip / start of taper
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
        layer = math.floor(z/0.85 + 0.5*noise.noise(Vector((x*0.12, y*0.12, 7.0))))
        led = 0.13*noise.noise(Vector((layer*1.73, 0.5, 2.0)))
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
        f = (z - ZB)/(ZT - ZB)
        s = 0.3 + 0.7*smooth(f)**0.85
        ns = 1 + 0.12*noise.noise(Vector((x*0.3, y*0.3, z*0.3)))
        v.co.x *= s*ns; v.co.y *= s*ns
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
                 ("notch", cutter("notchbox", EX-0.5, A+4, YC-0.1, EY+2.2, Z0-0.16, 6))]:
    bb = blk.modifiers.new(nm, 'BOOLEAN'); bb.object = cobj; bb.solver = 'EXACT'
    try: bb.material_mode = 'TRANSFER'
    except Exception: pass
# rubble / boulders around the tapered bottom of the rock
M_boul = mat("boulder",(0.07,0.07,0.075),0.95)
rb = random.Random(5)
for k in range(26):
    z = rb.uniform(ZB+0.6, ZT-1.0)
    f = (z - ZB)/(ZT - ZB); sc_ = 0.3 + 0.7*smooth(min(1, f))**0.85
    if rb.random() < 0.55: x = rb.uniform(-A, A)*sc_; y = -B*sc_ - rb.uniform(0.0, 0.25)
    else: x = A*sc_ + rb.uniform(0.0, 0.25); y = rb.uniform(-B, B)*sc_
    o = ico("boulder", (x*0.97, y*0.97, z), rb.uniform(0.18, 0.5), M_boul, 2)
    o.scale = (rb.uniform(0.8, 1.4), rb.uniform(0.8, 1.4), rb.uniform(0.5, 0.9)); o.rotation_euler = (rb.random(), rb.random(), rb.random()*6)
    md = o.modifiers.new("d", 'DISPLACE'); tx_ = C.textures.new(f"bt{k}", 'CLOUDS'); tx_.noise_scale = 0.4; md.texture = tx_; md.strength = 0.25
# recess ground
box("recessfloor", ((XC+A)/2, (YC-B)/2, FZ_BOT+0.02), (A-XC-0.1, B+YC-0.1, 0.04), mat("ledge",(0.16,0.16,0.17),0.9))

# warm lights along the rock edges of the cutaway
for k in range(9):
    zz = -0.9 - k*1.05
    box("wn", (XC-0.95, -B-0.47, zz), (0.24, 0.04, 0.24), M_dark)
    box("wl", (XC-0.95, -B-0.5, zz+0.06), (0.14, 0.03, 0.06), M_wlamp)
for k in range(9):
    box("wl2", (XC-0.06, -B+0.6+k*0.6, -0.12), (0.06, 0.12, 0.06), M_lamp)
    box("wl3", (XC+0.6+k*0.8, YC+0.06, -0.12), (0.12, 0.06, 0.06), M_lamp)

# ================= interior =================
M_glow = C.materials.new("glow"); M_glow.use_nodes = True
_nt = M_glow.node_tree; _nt.nodes.clear()
_o = _nt.nodes.new("ShaderNodeOutputMaterial"); _mix = _nt.nodes.new("ShaderNodeMixShader")
_tr = _nt.nodes.new("ShaderNodeBsdfTransparent"); _em = _nt.nodes.new("ShaderNodeEmission")
_em.inputs["Color"].default_value = (0.15, 1.0, 0.3, 1); _em.inputs["Strength"].default_value = 3.0
_tc = _nt.nodes.new("ShaderNodeTexCoord"); _gr = _nt.nodes.new("ShaderNodeTexGradient"); _gr.gradient_type = 'SPHERICAL'
_mp = _nt.nodes.new("ShaderNodeMapping"); _mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
_pw = _nt.nodes.new("ShaderNodeMath"); _pw.operation = 'POWER'; _pw.inputs[1].default_value = 1.6
_nt.links.new(_tc.outputs["Object"], _gr.inputs["Vector"]); _nt.links.new(_gr.outputs["Fac"], _pw.inputs[0])
_nt.links.new(_pw.outputs[0], _mix.inputs["Fac"]); _nt.links.new(_tr.outputs[0], _mix.inputs[1]); _nt.links.new(_em.outputs[0], _mix.inputs[2])
_nt.links.new(_mix.outputs[0], _o.inputs[0])
try: M_glow.surface_render_method = 'BLENDED'
except Exception: pass

def bot(x, y, z, m, s=0.27, glow=True):
    cone("botb", (x, y, z+s*0.42), s*1.08, s*0.72, s*0.84, m, 32)
    sph("bot", (x, y, z+s*0.95), s*0.8, m, (1,1,0.95), 24)
    cd = Vector((0.707, -0.707, 0)); side = Vector((0.707, 0.707, 0))
    for sgn in (-1, 1):
        p = Vector((x, y, z+s*1.02)) + cd*(s*0.7) + side*(sgn*s*0.25)
        sph("eye", p, s*0.15, M_eye, (1,1,1.4), 12)
    if glow:
        g = cyl("glow", (x, y, z+0.012), 1.0, 0.002, M_glow, 32); g.scale = (s*2.6, s*2.6, 1)
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

def chair(x, y, z, face=1, m=None):
    m = m or M_chair
    box("seat", (x, y, z+0.28), (0.22, 0.22, 0.04), m)
    box("back", (x, y-face*0.1, z+0.4), (0.22, 0.03, 0.22), m)
    cyl("cpost", (x, y, z+0.15), 0.02, 0.3, m if m is not M_chair else M_dark, 6, smooth=False)
    cyl("cbase", (x, y, z+0.015), 0.1, 0.03, m if m is not M_chair else M_dark, 8)

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
        o = box("cdesk", (*P(0, 0), z+0.4), (seg-0.02, 0.36, 0.05), M_desk); o.rotation_euler.z = rot
        o = box("cbody", (*P(0, 0.05), z+0.2), (seg-0.06, 0.24, 0.38), M_dark); o.rotation_euler.z = rot
        for dx in (-0.12, 0.12):
            o = box("cmonb", (*P(dx, 0.13), z+0.56), (0.2, 0.025, 0.14), M_dark); o.rotation_euler.z = rot
            o = plane("cmon", (*P(dx, 0.115), z+0.56), 0.18, 0.12, M_conimg); o.rotation_euler.z = rot
        cx_, cy_ = P(0, -0.33); chair(cx_, cy_, z, 1)

slabs = []
for i in range(NF):
    zf = Z0 - i*FH
    d = 0.15
    x0, x1 = XC, A - d
    y0, y1 = -B + d, YC
    W, D = x1-x0, y1-y0
    cx, cy = (x0+x1)/2, (y0+y1)/2
    box(f"slab{i}", (cx, cy, zf-0.07), (W, D, 0.14), M_white, 0.01)
    box(f"floor{i}", (cx, cy, zf+0.002), (W-0.06, D-0.06, 0.004), M_slab)
    # thin glass railing on the two open edges
    box("railA", (cx, y0+0.03, zf+0.18), (W, 0.015, 0.36), M_glass)
    box("railB", (x1-0.03, cy, zf+0.18), (0.015, D, 0.36), M_glass)
    box("rtA", (cx, y0+0.03, zf+0.36), (W, 0.02, 0.015), M_white)
    box("rtB", (x1-0.03, cy, zf+0.36), (0.02, D, 0.015), M_white)
    # side wall panels (white) on the x=XC wall
    box("lwall", (XC+0.02, cy, zf+(0.72 if i == 0 else 1.0)), (0.03, D, 1.3 if i else 1.4), M_panel)
    Lg = C.lights.new(f"fl{i}", 'AREA'); Lg.energy = 150 if i else 90; Lg.shape = 'RECTANGLE'
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
        box("plat", (2.6, -3.2, zt+0.02), (6.4, 4.4, 0.04), mat("plat",(0.36,0.37,0.39),0.4))
        for gx, gy in ((0.75, 0.0), (4.15, -0.35)):
            for r_, yy in enumerate([-1.7, -3.05, -4.4]):
                console_row(gx, yy+gy, zt+0.04, 4, seg=0.56)
        box("frontdesk", (5.3, -5.3, zt+0.35), (1.2, 0.45, 0.7), M_wood)
        cyl("bin", (5.9, -1.3, zt+0.18), 0.14, 0.36, M_dark, 12)
        plant(XC+0.3, -0.95, zt, 0.8, True); plant(XC+0.3, -5.3, zt, 0.7); plant(6.0, -2.4, zt, 0.8, True)
        bots = [(0.0,-2.4,2),(1.2,-1.05,1),(2.45,-2.0,0),(4.1,-3.75,3),(2.5,-3.75,7),(5.6,-2.2,5)]
    elif i == 1:  # ---- engineering: long workbench ----
        plane("poster", (XC+0.04, -5.0, zt+1.0), 0.6, 1.0, M_poster, '+X')
        box("wtable", (2.0, -4.55, zt+0.5), (4.8, 0.45, 0.04), M_wood)
        for k in range(9):
            xx = -0.1 + k*0.53
            box("tleg", (xx, -4.55, zt+0.25), (0.025, 0.025, 0.5), M_metal)
            if k % 2 == 0: box("lap", (xx+0.2, -4.5, zt+0.57), (0.26, 0.18, 0.1), M_dark)
            chair(xx+0.1, -5.05, zt, -1, M_white); chair(xx-0.05, -4.05, zt, 1, M_white)
        for k in range(6):
            chair(4.5+ (k % 2)*0.7, -3.4 - (k//2)*0.7, zt, 1, M_white)
        cyl("rug", (5.0, -2.9, zt+0.008), 0.95, 0.012, mat("rug",(0.18,0.18,0.19),0.9), 48)
        cyl("rtable", (5.0, -2.9, zt+0.42), 0.38, 0.04, M_dark, 32); cyl("rtleg", (5.0, -2.9, zt+0.21), 0.04, 0.42, M_dark, 8)
        for k in range(5): box("tmon", (0.15+k*1.06, -4.38, zt+0.66), (0.3, 0.02, 0.2), M_dark); plane("tmons", (0.15+k*1.06, -4.395, zt+0.66), 0.27, 0.17, M_conimg)
        box("gpart", (4.1, -2.4, zt+0.5), (0.02, 1.6, 1.0), M_glass)
        box("lounge", (5.5, -1.7, zt+0.18), (0.8, 0.5, 0.36), M_dark)
        cyl("engbase", (5.6, -1.0, zt+0.04), 0.45, 0.08, M_dark, 32)
        plant(XC+0.3, -5.5, zt, 0.7); plant(6.0, -5.5, zt, 0.7)
        bots = [(1.1,-3.85,0),(2.7,-3.9,4),(5.2,-4.6,7),(4.4,-3.4,1)]
    elif i == 2:  # ---- lounge: purple carpet + wood bar ----
        plane("chartp", (XC+0.04, -4.8, zt+1.0), 1.1, 0.9, M_chartimg, '+X')
        box("darkscr", (XC+0.04, -3.6, zt+1.1), (0.02, 0.8, 0.6), M_dark)
        box("carpet", (0.5, -4.7, zt+0.01), (2.4, 2.0, 0.02), M_purple)
        box("ltable", (0.4, -4.6, zt+0.2), (1.3, 0.5, 0.04), M_wood)
        for k in range(3): box("cube", (-0.3+k*0.55, -5.3, zt+0.13), (0.28, 0.28, 0.26), M_white, 0.01)
        M_sofa = mat("sofa",(0.03,0.03,0.035),0.8)
        box("sofa", (-0.55, -4.4, zt+0.17), (0.4, 1.0, 0.3), M_sofa)
        box("bar", (3.5, -4.2, zt+0.25), (2.8, 0.7, 0.5), mat("lwood",(0.72,0.58,0.4),0.5), 0.02)
        for k in range(7): stool(2.3+k*0.4, -4.75, zt, M_white)
        for k in range(3): box("pc", (2.6+k*0.8, -4.1, zt+0.56), (0.24, 0.04, 0.16), M_dark)
        cyl("groom", (5.4, -2.6, zt+0.75), 0.75, 1.5, M_glass, 40)
        cyl("groomb", (5.4, -2.6, zt+0.01), 0.77, 0.02, M_dark, 40)
        cyl("groomt", (5.4, -2.6, zt+0.4), 0.3, 0.04, M_white, 24)
        for a in range(5): chair(5.4+0.5*math.cos(a*1.25), -2.6+0.5*math.sin(a*1.25), zt, 1, M_white)
        box("sofa2", (4.6, -5.4, zt+0.17), (0.6, 0.35, 0.3), M_sofa)
        M_bdesk = mat("bdesk",(0.03,0.06,0.2),0.35)
        for k in range(3): box("bdesk", (1.9, -3.6-k*0.55, zt+0.3), (0.5, 0.4, 0.6), M_bdesk, 0.01)
        for p in [(2.4,-5.4),(5.6,-4.4)]:
            cyl("ctab", (p[0], p[1], zt+0.4), 0.22, 0.03, M_dark, 20); cyl("ctl", (p[0], p[1], zt+0.2), 0.025, 0.4, M_dark, 8)
        plant(6.0, -5.3, zt, 0.7, True)
        bots = [(0.3,-4.0,5),(1.2,-5.0,4),(4.6,-5.0,3)]
    else:         # ---- garden / workshop ----
        plane("aip", (XC+0.04, -5.0, zt+0.95), 0.7, 0.95, M_aiimg, '+X')
        box("mat", (2.4, -5.25, zt+0.01), (1.6, 0.6, 0.015), M_dark)
        tx = text("SPACEX", (2.4, -5.3, zt+0.02), 0.25, M_white, extrude=0.0); tx.data.space_character = 1.4
        for p in [(0.2,-4.4,1.1,True),(1.9,-3.7,1.0,True),(3.8,-4.6,1.2,True),(5.6,-3.0,1.0,True),(XC+0.4,-3.8,0.8,False),(4.9,-5.4,0.8,False),(3.0,-4.4,0.7,False)]:
            plant(p[0], p[1], zt, p[2], p[3])
        for p in [(0.6,-5.3),(1.4,-4.2),(4.3,-5.0),(5.0,-4.0),(-0.4,-5.0)]:
            box("bcube", (p[0], p[1], zt+0.12), (0.24, 0.24, 0.24), M_dark, 0.01)
        box("deck", (3.1, -4.5, zt+0.03), (2.2, 1.7, 0.06), mat("deckw",(0.6,0.45,0.28),0.6))
        for k in range(6): box("plank", (3.1, -5.3+k*0.3, zt+0.061), (2.2, 0.01, 0.002), M_dark)
        box("totem", (2.0, -4.4, zt+0.4), (0.16, 0.16, 0.8), M_dark); box("totem2", (0.9, -3.9, zt+0.35), (0.14, 0.14, 0.7), M_dark)
        for k in range(3): chair(4.0+k*0.4, -3.7, zt, 1, M_white)
        cyl("rbench", (1.2, -5.3, zt+0.12), 0.45, 0.24, M_wood, 32)
        box("robase", (5.6, -5.2, zt+0.3), (0.4, 0.4, 0.6), M_white)
        cyl("roarm", (5.6, -5.0, zt+0.85), 0.05, 0.6, M_white, 8).rotation_euler.x = 0.6
        for k in range(2): cyl("barrel", (5.2+k*0.45, -1.4, zt+0.3), 0.18, 0.6, M_dark, 16)
        bots = [(2.6,-4.1,0),(4.6,-5.5,5),(1.0,-5.4,6)]
    for bx, by, ci in bots:
        bot(bx, by, zt, M_bots[ci % len(M_bots)])

# under the lowest floor: tank, pillars, crates
zb = Z0 - (NF-1)*FH - 0.14
for px, py in [(XC+0.4,-B+0.6),(1.6,-B+0.6),(3.6,-B+0.6),(A-0.6,-B+0.6),(A-0.6,-3.0),(A-0.6,YC-0.3)]:
    cyl("pillar", (px, py, (zb+FZ_BOT)/2), 0.09, zb-FZ_BOT, M_white, 12)
M_tank = mat("tank",(0.02,0.02,0.025),0.25,0.3)
cyl("tank", (0.5, -5.3, FZ_BOT+0.62), 0.58, 2.0, M_tank, 40, rot=(0, math.pi/2, 0))
cyl("tankfan", (1.55, -5.3, FZ_BOT+0.62), 0.6, 0.12, M_dark, 24, rot=(0, math.pi/2, 0))
for k in range(8):
    a = k*math.pi/4
    o = box("fanblade", (1.62, -5.3+0.3*math.cos(a), FZ_BOT+0.62+0.3*math.sin(a)), (0.02, 0.08, 0.5), M_metal); o.rotation_euler.x = a - math.pi/2
cyl("tankband", (0.2, -5.3, FZ_BOT+0.62), 0.6, 0.18, mat("yellow",(0.9,0.6,0.02),0.4), 40, rot=(0, math.pi/2, 0))
for k in range(3): box("frame", (-0.85+k*0.16, -5.3, FZ_BOT+0.55), (0.04, 0.8, 1.1), M_metal)
for k in range(4): box("crate", (4.2+k*0.42, -5.4, FZ_BOT+0.12), (0.4, 0.5, 0.2), M_white)
for k in range(3): box("crate", (4.4+k*0.42, -5.4, FZ_BOT+0.32), (0.4, 0.5, 0.2), M_white)

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
TX0, TX1, TY0, TY1, TZ0, TZ1 = EX-0.45, A+0.05, EY-0.45, EY+2.15, Z0, -0.15
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
box("kiosk", (4.95, 2.75, 0.4), (0.7, 0.55, 0.8), M_white, 0.02)
box("kdoor", (4.95, 2.47, 0.33), (0.28, 0.02, 0.55), M_dark)
cyl("kpost", (5.1, 2.8, 0.95), 0.025, 0.3, M_metal, 6)
c_ = sph("kdish", (5.1, 2.8, 1.1), 0.2, M_white, (1, 1, 0.35), 16); c_.rotation_euler = (math.radians(50), 0, math.radians(-45))

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
box("rimA", ((XC+A)/2, YC+0.18, -0.15), (A-XC, 0.36, 0.34), M_rim)
box("rimB", (XC-0.18, (YC-B)/2, -0.15), (0.36, B+YC, 0.34), M_rim)
box("colR", (A+0.1, EY+0.85, (FZ_BOT+Z0-0.2)/2), (0.75, 0.5, Z0-0.2-FZ_BOT), mat("colr",(0.07,0.07,0.075),0.5))
for k in range(8):
    box("wlr", (A+0.49, EY+0.85, -2.2 - k*0.95), (0.05, 0.1, 0.16), M_wlamp)
# dark structural column on the rock face left of the cutaway
box("colL", (XC-0.62, -B-0.075, (FZ_BOT)/2), (1.24, 0.75, -FZ_BOT), mat("col",(0.1,0.1,0.105),0.5))
cyl("colLs", (XC-0.22, -B-0.5, (FZ_BOT)/2), 0.04, -FZ_BOT, M_white, 10)
box("colLe", (XC-0.04, -B-0.47, (FZ_BOT)/2), (0.08, 0.04, -FZ_BOT), M_dark)

# ================= surface =================
PX, PY = -3.5, -1.6
cyl("pad", (PX, PY, 0.05), 2.2, 0.14, M_pad, 64)
bpy.ops.mesh.primitive_torus_add(major_radius=1.95, minor_radius=0.035, location=(PX, PY, 0.13), major_segments=64)
bpy.context.object.data.materials.append(M_white)
bpy.ops.mesh.primitive_torus_add(major_radius=1.25, minor_radius=0.02, location=(PX, PY, 0.13), major_segments=64)
bpy.context.object.data.materials.append(M_white)
# rocket (Starship-like), sized off the ref: r~1.0, ~11.6 tall
RB = 0.9; RR = 0.92; BH = 8.8
cd = Vector((0.707, -0.707, 0)); sd = Vector((0.707, 0.707, 0))
cone("skirt", (PX, PY, RB-0.15), RR*0.8, RR, 0.4, M_dark, 48)
cyl("rocket", (PX, PY, RB+BH/2), RR, BH, M_white, 64)
cyl("band", (PX, PY, RB+BH-0.85), RR+0.008, 1.7, M_dark, 64)
cyl("ring", (PX, PY, RB+2.2), RR+0.006, 0.05, mat("seam",(0.55,0.56,0.58),0.4), 64)
for k in range(5):
    a = -math.pi/4 + (k-2)*0.2
    box("win", (PX+math.cos(a)*(RR+0.01), PY+math.sin(a)*(RR+0.01), RB+BH-1.4), (0.12, 0.12, 0.09), mat("winw",(0.9,0.9,0.92),0.2), rz=a)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=RR, location=(PX, PY, RB+BH))
n = bpy.context.object; n.scale.z = 1.95; n.data.materials.append(M_white); bpy.ops.object.shade_smooth()
# delete lower hemisphere of the nose (inside body anyway)
# forward + aft flaps on the left/right sides of the silhouette
M_flap = mat("flap",(0.45,0.46,0.48),0.4)
for sgn in (-1, 1):
    base = Vector((PX, PY, 0)) + sd*(sgn*(RR+0.12))
    o2 = box("aflap", (base.x - sd.x*sgn*0.02, base.y - sd.y*sgn*0.02, RB+1.0), (0.34, 0.05, 1.1), M_flap); o2.rotation_euler.z = math.radians(45)
# small dark hatches under the band (visible in ref)
for k in (-0.35, 0.35):
    p = Vector((PX, PY, RB+BH-1.95)) + cd*(RR+0.005) + sd*k
    o = box("hatch", (p.x, p.y, p.z), (0.2, 0.02, 0.1), M_dark); o.rotation_euler.z = math.radians(45)
for k in range(6):
    a = k*math.pi/3 + 0.3
    p0 = Vector((PX+math.cos(a)*RR*0.9, PY+math.sin(a)*RR*0.9, RB+1.3)); p1 = Vector((PX+math.cos(a)*1.65, PY+math.sin(a)*1.65, 0.12))
    mid = (p0+p1)/2; dv = p0-p1
    lg = cyl("leg", mid, 0.04, dv.length, M_metal, 8)
    lg.rotation_euler = dv.to_track_quat('Z','Y').to_euler()
    cyl("foot", p1, 0.11, 0.05, M_metal, 12)

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
FR = Matrix.Translation(Vector((PX, PY, RB+3.1)) + cd*(RR+0.012)) @ Matrix((Xv, Yv, Zv)).transposed().to_4x4()
t = text("SPACEX", (0,0,0), 0.5, M_dark, extrude=0.004, align='LEFT', spacing=1.35)
t.scale = (1.15, 1, 1); t.matrix_world = FR @ Matrix.Diagonal((1.15, 1, 1, 1))
t.data.align_y = 'CENTER'
swoosh("rswoosh", (2.0, -0.32), (3.4, 0.55), 0.22, 0.09, M_dark, 0.004, FR @ Matrix.Translation((0, 0, 0.004)))
# giant SPACEX sign on the back edge: chunky extruded letters + swoosh on the X
sgn = text("SPACEX", (-0.45, B-0.6, 0.55), 1.55, M_white, rot=(math.radians(90), 0, 0), extrude=0.22, spacing=1.15)
sgn.data.bevel_depth = 0.03; sgn.data.bevel_resolution = 2
sgn.scale = (1.45, 0.8, 1); sgn.rotation_euler = (math.radians(90), 0, math.radians(22))
bpy.context.view_layer.update()
SF = sgn.matrix_world.copy()
# swoosh in the sign's local frame (text units before scale): from inside the X out to the right
sw = swoosh("sswoosh", (2.7, 0.05), (4.5, 0.75), -0.15, 0.2, M_white, 0.12, SF @ Matrix.Translation((0, 0, 0.05)))
for xx in (-4.6, -1.5, 1.5, 4.0):
    box("signpost", (xx, B-0.45, 0.3), (0.08, 0.08, 0.6), M_metal)
box("signbar", (-0.4, B-0.45, 0.55), (9.5, 0.08, 0.08), M_metal)
# LANDING ZONE 1 painted on the pad (reads along the camera's right axis)
lz = text("LANDING ZONE 1", (0,0,0), 0.2, M_white, extrude=0.0, spacing=1.1)
lz.location = Vector((PX, PY, 0.125)) + cd*1.55; lz.rotation_euler = (0, 0, math.radians(45)); lz.data.align_y = 'CENTER'
# solar field
_nt = M_solar.node_tree; _b = _nt.nodes["Principled BSDF"]
_br = _nt.nodes.new("ShaderNodeTexBrick"); _br.offset = 0.0
_br.inputs["Color1"].default_value = (0.01,0.015,0.04,1); _br.inputs["Color2"].default_value = (0.015,0.022,0.05,1)
_br.inputs["Mortar"].default_value = (0.5,0.52,0.56,1); _br.inputs["Scale"].default_value = 4.0
_br.inputs["Mortar Size"].default_value = 0.012; _br.inputs["Brick Width"].default_value = 0.5; _br.inputs["Row Height"].default_value = 0.42
_tcs = _nt.nodes.new("ShaderNodeTexCoord"); _nt.links.new(_tcs.outputs["Object"], _br.inputs["Vector"])
_nt.links.new(_br.outputs["Color"], _b.inputs["Base Color"])
for i in range(6):
    for j in range(8):
        x = -0.3 + j*0.64; y = 2.35 + i*0.5
        o = box("panel", (x, y, 0.42), (0.58, 0.42, 0.025), M_solar); o.rotation_euler.x = 0.38
        box("pframe", (x, y-0.215, 0.34), (0.58, 0.02, 0.02), M_metal)
        cyl("post", (x, y, 0.2), 0.02, 0.4, M_metal, 6, smooth=False)
# satellite dishes on the right edge
for dx, dy in [(5.8, 3.75), (6.0, 4.7), (5.2, 5.4)]:
    cyl("dpost", (dx, dy, 0.45), 0.04, 0.9, M_metal, 8)
    c = sph("dish", (dx, dy, 1.05), 0.55, M_white, (1, 1, 0.3), 24); c.rotation_euler = (math.radians(55), 0, math.radians(-45))
# gold lander + sign
cyl("lander", (-5.0, -4.4, 0.55), 0.5, 0.45, M_gold, 8, smooth=False)
cyl("landtop", (-5.0, -4.4, 0.82), 0.38, 0.1, M_dark, 16)
for k in range(4):
    a = k*math.pi/2 + 0.4
    lg = cyl("lleg", (-5.0+math.cos(a)*0.55, -4.4+math.sin(a)*0.55, 0.28), 0.03, 0.6, M_gold, 6)
    lg.rotation_euler = (math.sin(a)*0.5, -math.cos(a)*0.5, 0)
box("tboard", (-4.6, -5.6, 0.55), (1.0, 0.05, 0.45), M_white)
box("tred", (-4.6, -5.63, 0.45), (0.8, 0.02, 0.12), emis("red2",(0.9,0.05,0.05),1.0))
for xx in (-5.05, -4.15): box("tpost", (xx, -5.6, 0.2), (0.04, 0.04, 0.4), M_metal)
text("TRANQUILITY BASE", (-4.6, -5.632, 0.6), 0.085, M_dark, rot=(math.radians(90), 0, 0), extrude=0.0)
text("DO NOT TOUCH", (-4.6, -5.645, 0.42), 0.07, M_white, rot=(math.radians(90), 0, 0), extrude=0.0)
M_srock = mat("srock",(0.16,0.16,0.17),0.9)
# crates, rover, surface bots, rocks
M_crate = mat("crate",(0.9,0.9,0.92),0.4)
for k, (cx_, cy_, cz_) in enumerate([(0,0,0),(0.34,0,0),(0,0.34,0),(0.34,0.34,0),(0.17,0.17,1),(0.5,-0.3,0)]):
    box("crate", (-2.6+cx_, 4.2+cy_, 0.15+0.3*cz_), (0.32, 0.32, 0.28), M_crate, 0.01)
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
    o = ico("rock", (x, y, 0.02), random.uniform(0.04, 0.16), M_srock, 1)
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
re = N.new("ShaderNodeValToRGB"); re.color_ramp.elements[0].color = (0.004,0.05,0.32,1); re.color_ramp.elements[1].color = (0.16,0.3,0.06,1)
_e3 = re.color_ramp.elements.new(0.75); _e3.color = (0.42,0.36,0.18,1)
_e4 = re.color_ramp.elements.new(0.45); _e4.color = (0.02,0.14,0.5,1)
re.color_ramp.elements[0].position = 0.5; re.color_ramp.elements[1].position = 0.53
nc = N.new("ShaderNodeTexNoise"); nc.inputs["Scale"].default_value = 3.5; nc.inputs["Detail"].default_value = 8; nc.inputs["Distortion"].default_value = 1.2
rc = N.new("ShaderNodeValToRGB"); rc.color_ramp.elements[0].position = 0.56; rc.color_ramp.elements[1].position = 0.7
mxe = N.new("ShaderNodeMixRGB")
L.new(ne.outputs["Fac"], re.inputs["Fac"]); L.new(nc.outputs["Fac"], rc.inputs["Fac"])
L.new(rc.outputs["Color"], mxe.inputs["Fac"]); L.new(re.outputs["Color"], mxe.inputs[1]); mxe.inputs[2].default_value = (0.9,0.9,0.9,1)
L.new(mxe.outputs["Color"], be.inputs["Base Color"])
# self-lit earth with a terminator (night side on the right) and a thin blue atmosphere rim
eo = N["Material Output"]
ldir = (-right*1.0 + up*0.3 + back*0.5).normalized()
geo = N.new("ShaderNodeNewGeometry"); dp = N.new("ShaderNodeVectorMath"); dp.operation = 'DOT_PRODUCT'
dp.inputs[1].default_value = ldir
L.new(geo.outputs["Normal"], dp.inputs[0])
tm = N.new("ShaderNodeMapRange"); tm.inputs["From Min"].default_value = -0.15; tm.inputs["From Max"].default_value = 0.3
tm.inputs["To Min"].default_value = 0.025; tm.inputs["To Max"].default_value = 1.0
L.new(dp.outputs["Value"], tm.inputs["Value"])
cm = N.new("ShaderNodeMixRGB"); cm.blend_type = 'MULTIPLY'; cm.inputs["Fac"].default_value = 1
L.new(mxe.outputs["Color"], cm.inputs["Color1"]); L.new(tm.outputs["Result"], cm.inputs["Color2"])
e1 = N.new("ShaderNodeEmission"); e1.inputs["Strength"].default_value = 1.15; L.new(cm.outputs["Color"], e1.inputs["Color"])
lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
rp_ = N.new("ShaderNodeMath"); rp_.operation = 'POWER'; rp_.inputs[1].default_value = 2.5
L.new(lw.outputs["Facing"], rp_.inputs[0])
rm = N.new("ShaderNodeMath"); rm.operation = 'MULTIPLY'; L.new(rp_.outputs[0], rm.inputs[0]); L.new(tm.outputs["Result"], rm.inputs[1])
e2 = N.new("ShaderNodeEmission"); e2.inputs["Color"].default_value = (0.35,0.6,1.0,1); L.new(rm.outputs[0], e2.inputs["Strength"])
ad = N.new("ShaderNodeAddShader"); L.new(e1.outputs[0], ad.inputs[0]); L.new(e2.outputs[0], ad.inputs[1])
L.new(ad.outputs[0], eo.inputs["Surface"])
earth = sph("earth", target + R @ Vector((229*k, 308*k, -40)), 64*k, M_earth, seg=64)
# stars on a backdrop plane facing the camera
M_star = C.materials.new("stars"); M_star.use_nodes = True
nt = M_star.node_tree; nt.nodes.clear()
so_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
tcs = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 260
rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (1,1,1,1)
rp.color_ramp.elements[1].position = 0.06; rp.color_ramp.elements[1].color = (0.0015,0.0015,0.002,1)
vn = nt.nodes.new("ShaderNodeTexNoise"); vn.inputs["Scale"].default_value = 40
mm = nt.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'
nt.links.new(tcs.outputs["Object"], vo.inputs["Vector"]); nt.links.new(vo.outputs["Distance"], rp.inputs["Fac"])
nt.links.new(rp.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.2
nt.links.new(em.outputs[0], so_.inputs[0])
bpy.ops.mesh.primitive_plane_add(size=1, location=target - back*120)
sp = bpy.context.object; sp.scale = (OS*1.2, OS*1.6, 1); sp.rotation_euler = co.rotation_euler; sp.data.materials.append(M_star)
sp.visible_shadow = False

# ================= lights =================
def aim(obj, d):
    obj.rotation_euler = Vector(d).normalized().to_track_quat('Z','Y').to_euler()
sun = C.lights.new("sun", 'SUN'); sun.energy = 3.0; sun.angle = math.radians(3)
so = C.objects.new("sun", sun); sc.collection.objects.link(so); aim(so, (-0.18, -1.0, 0.8))
fill = C.lights.new("fill", 'SUN'); fill.energy = 0.5; fill.angle = math.radians(20)
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
