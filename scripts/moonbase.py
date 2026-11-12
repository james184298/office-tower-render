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
    bpy.ops.object.transform_apply(scale=True)
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
M_slab = mat("slab", (0.66,0.67,0.69), 0.28)
M_dark = mat("dark", (0.025,0.027,0.03), 0.35)
M_desk = mat("desk", (0.035,0.038,0.045), 0.25)
M_chair = mat("chair", (0.015,0.015,0.018), 0.5)
M_wall = mat("wall", (0.035,0.036,0.04), 0.6)
M_panel = mat("panel", (0.75,0.76,0.78), 0.4)
M_wood = mat("wood", (0.55,0.4,0.24), 0.45)
M_metal = mat("metal", (0.6,0.62,0.65), 0.25, 1.0)
M_gold = mat("gold", (0.95,0.68,0.15), 0.3, 1.0)
M_glass = mat("glass", (0.75,0.85,0.9), 0.02, 0, alpha=0.18)
M_screen = emis("screen", (0.2,0.5,1.0), 3.0)
M_screenG = emis("screenG", (0.2,0.9,0.4), 2.0)
M_screenP = emis("screenP", (0.55,0.3,1.0), 2.0)
M_red = emis("redposter", (1.0,0.25,0.1), 1.5)
M_lamp = emis("lamp", (1.0,0.8,0.55), 6.0)
M_leaf = mat("leaf", (0.04,0.3,0.06), 0.55)
M_leaf2 = mat("leaf2", (0.08,0.42,0.1), 0.55)
M_pot = mat("pot", (0.9,0.9,0.9), 0.35)
M_purple = mat("carpet", (0.16,0.06,0.36), 0.9)
M_solar = mat("solar", (0.015,0.02,0.045), 0.12, 0.5)
M_eye = emis("eye", (1,1,1), 2.0)
M_pad = mat("pad", (0.07,0.07,0.075), 0.6)
BOT_COLS = [(0.1,0.9,0.2),(1.0,0.45,0.03),(0.12,0.35,1.0),(0.55,0.12,1.0),(1.0,0.12,0.45),(0.05,0.8,0.85),(1.0,0.82,0.05),(0.95,0.95,0.97)]
M_bots = [mat(f"bot{i}", c, 0.15, emit=c, estr=0.7) for i,c in enumerate(BOT_COLS)]

# ---- rock with soft horizontal strata ----
M_rock = C.materials.new("rock"); M_rock.use_nodes = True
nt = M_rock.node_tree; N = nt.nodes; L = nt.links
bsdf = N["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.92
tc = N.new("ShaderNodeTexCoord")
wav = N.new("ShaderNodeTexWave"); wav.wave_type = 'BANDS'; wav.bands_direction = 'Z'
wav.inputs["Scale"].default_value = 0.55; wav.inputs["Distortion"].default_value = 4.0
wav.inputs["Detail"].default_value = 6; wav.inputs["Detail Scale"].default_value = 0.6
wn = N.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 0.35; wn.inputs["Detail"].default_value = 3
mx = N.new("ShaderNodeMix"); mx.data_type = 'FLOAT'; mx.inputs["Factor"].default_value = 0.3
ramp = N.new("ShaderNodeValToRGB"); r = ramp.color_ramp
r.elements[0].position = 0.0; r.elements[0].color = (0.10,0.10,0.105,1)
r.elements[1].position = 1.0; r.elements[1].color = (0.30,0.30,0.31,1)
for p, v in [(0.2,0.2),(0.4,0.34),(0.55,0.16),(0.75,0.4),(0.88,0.22)]:
    e = r.elements.new(p); e.color = (v,v,v*1.02,1)
L.new(tc.outputs["Object"], wav.inputs["Vector"])
L.new(wav.outputs["Fac"], mx.inputs["A"]); L.new(wn.outputs["Fac"], mx.inputs["B"])
L.new(mx.outputs["Result"], ramp.inputs["Fac"])
L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35
fn = N.new("ShaderNodeTexNoise"); fn.inputs["Scale"].default_value = 8; fn.inputs["Detail"].default_value = 6
L.new(fn.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

# ---- regolith ----
M_reg = C.materials.new("regolith"); M_reg.use_nodes = True
nt = M_reg.node_tree; N = nt.nodes; L = nt.links
b2 = N["Principled BSDF"]; b2.inputs["Roughness"].default_value = 1
n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 0.6; n2.inputs["Detail"].default_value = 8
r2 = N.new("ShaderNodeValToRGB"); er = r2.color_ramp.elements
er[0].position = 0.35; er[0].color = (0.36,0.36,0.37,1); er[1].position = 0.65; er[1].color = (0.56,0.56,0.57,1)
L.new(n2.outputs["Fac"], r2.inputs["Fac"]); L.new(r2.outputs["Color"], b2.inputs["Base Color"])
bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = 0.25
n3 = N.new("ShaderNodeTexNoise"); n3.inputs["Scale"].default_value = 12; n3.inputs["Detail"].default_value = 8
L.new(n3.outputs["Fac"], bp2.inputs["Height"]); L.new(bp2.outputs["Normal"], b2.inputs["Normal"])

# ================= layout constants =================
A, B = 6.5, 6.0              # half extents in x, y
XC, YC = -1.0, -0.6          # cutaway region: x > XC and y < YC
ZB, ZT = -17.0, -11.5        # rock bottom tip / start of taper
FZ_BOT = -11.2               # recess floor
NF = 5; Z0 = -1.8; FH = 2.0  # top slab level and floor pitch
EX, EY = A - 0.8, YC + 1.25  # elevator centre (in a slot on the +x face)
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
        n = noise.fractal(Vector((x*0.22+3, y*0.22, z*0.9)), 0.7, 2.0, 5)
        led = 0.12*math.sin(z*2.6 + 2*noise.noise(Vector((x*0.3, y*0.3, z*0.2))))
        off = 0.28*n + led + 0.1
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
        s = 0.28 + 0.72*smooth(f)**0.6
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
                 ("slot", cutter("slotbox", EX-0.75, A+4, YC-0.1, EY+0.75, FZ_BOT, 6))]:
    bb = blk.modifiers.new(nm, 'BOOLEAN'); bb.object = cobj; bb.solver = 'EXACT'
    try: bb.material_mode = 'TRANSFER'
    except Exception: pass
# recess ground
box("recessfloor", ((XC+A)/2+1, (YC-B)/2-1, FZ_BOT+0.02), (A-XC+2, B+YC+2, 0.04), mat("ledge",(0.3,0.3,0.31),0.9))

# warm lights along the rock edges of the cutaway
for k in range(10):
    zz = -0.9 - k*1.05
    box("wl", (XC-0.35, -B-0.12, zz), (0.16, 0.05, 0.22), M_lamp)
    box("wl", (A+0.12, EY+0.95, zz), (0.05, 0.16, 0.22), M_lamp)
for k in range(9):
    box("wl2", (XC-0.06, -B+0.6+k*0.6, -0.12), (0.06, 0.12, 0.06), M_lamp)
    box("wl3", (XC+0.6+k*0.8, YC+0.06, -0.12), (0.12, 0.06, 0.06), M_lamp)

# ================= interior =================
def bot(x, y, z, m, s=0.33):
    cone("botb", (x, y, z+s*0.45), s*1.05, s*0.75, s*0.9, m, 24)
    sph("bot", (x, y, z+s*0.95), s*0.78, m, (1,1,0.95), 20)
    cd = Vector((0.707, -0.707, 0))
    side = Vector((0.707, 0.707, 0))
    for sgn in (-1, 1):
        p = Vector((x, y, z+s*1.0)) + cd*(s*0.72) + side*(sgn*s*0.26)
        sph("eye", p, s*0.13, M_eye, (1,1,1.4), 10)

def plant(x, y, z, s=1.0, tall=False):
    cyl("pot", (x, y, z+0.16*s), 0.16*s, 0.32*s, M_pot)
    hh = (1.0 if tall else 0.55)*s
    if tall: cyl("stem", (x, y, z+0.32*s+hh*0.4), 0.025, hh*0.8, mat("stem",(0.2,0.12,0.05),0.8), 6, smooth=False)
    for i in range(14 if tall else 9):
        a = random.random()*6.28; rr = random.random()*0.22*s
        zz = z + 0.32*s + (hh*0.55 if tall else 0.12*s) + random.random()*hh*0.45
        ico("leaf", (x+math.cos(a)*rr, y+math.sin(a)*rr, zz), (0.11+random.random()*0.07)*s, random.choice((M_leaf, M_leaf2)), 1)

def console(x, y, z, scr=M_screen):
    box("cbase", (x, y, z+0.33), (0.95, 0.42, 0.66), M_desk)
    box("ctop", (x, y-0.05, z+0.68), (1.05, 0.62, 0.05), M_desk)
    for dx in (-0.25, 0.25):
        box("mon", (x+dx, y+0.18, z+0.92), (0.44, 0.04, 0.3), scr)
        box("monb", (x+dx, y+0.21, z+0.92), (0.47, 0.03, 0.33), M_dark)
    box("seat", (x, y-0.62, z+0.42), (0.38, 0.38, 0.07), M_chair)
    box("back", (x, y-0.8, z+0.65), (0.38, 0.05, 0.42), M_chair)
    cyl("cpost", (x, y-0.62, z+0.2), 0.03, 0.4, M_chair, 6, smooth=False)

def stool(x, y, z, m=M_white):
    cyl("stool", (x, y, z+0.42), 0.14, 0.05, m, 12); cyl("sl", (x, y, z+0.21), 0.025, 0.42, M_metal, 6, smooth=False)

slabs = []
for i in range(NF):
    zf = Z0 - i*FH
    d = 0.15 + 0.45*i
    x0, x1 = XC, A - d
    y0, y1 = -B + d, YC
    W, D = x1-x0, y1-y0
    cx, cy = (x0+x1)/2, (y0+y1)/2
    box(f"slab{i}", (cx, cy, zf-0.11), (W, D, 0.22), M_white, 0.01)
    box(f"floor{i}", (cx, cy, zf+0.002), (W-0.06, D-0.06, 0.004), M_slab)
    # glass railing on the two open edges + top rail
    box("railA", (cx, y0+0.04, zf+0.25), (W, 0.03, 0.5), M_glass)
    box("railB", (x1-0.04, cy, zf+0.25), (0.03, D, 0.5), M_glass)
    box("rtA", (cx, y0+0.04, zf+0.5), (W, 0.04, 0.03), M_metal)
    box("rtB", (x1-0.04, cy, zf+0.5), (0.04, D, 0.03), M_metal)
    # light for the floor
    Lg = C.lights.new(f"fl{i}", 'AREA'); Lg.energy = 90 if i else 60; Lg.shape = 'RECTANGLE'
    Lg.size = W*0.8; Lg.size_y = D*0.8; Lg.color = (1, 0.92, 0.82)
    lo = C.objects.new(f"fl{i}", Lg); sc.collection.objects.link(lo); lo.location = (cx, cy, zf + FH - 0.35)
    zt = zf
    if i == 0:   # ---- mission control ----
        # big wall screen (several panels)
        for k, (xa, xb, m) in enumerate([(0.6, 2.5, M_screen), (2.6, 4.4, M_screen), (4.5, 5.6, M_screen)]):
            box("bezel", ((xa+xb)/2, YC+0.03, zt+1.0), (xb-xa+0.08, 0.04, 1.28), M_dark)
            box("big", ((xa+xb)/2, YC-0.0, zt+1.0), (xb-xa, 0.03, 1.2), m)
        box("bigtrim", (3.1, YC-0.02, zt+0.36), (5.0, 0.02, 0.04), M_lamp)
        for k in range(3):
            box("smallscr", (XC+0.45+k*0.45, YC-0.01, zt+1.1), (0.4, 0.03, 0.9), M_screenG if k == 1 else M_screen)
        # dial panel on left wall
        box("dialpanel", (XC+0.03, -2.4, zt+1.05), (0.03, 2.2, 0.9), M_panel)
        for k in range(4):
            cyl("dial", (XC+0.06, -3.2+k*0.5, zt+1.1), 0.17, 0.02, M_dark, 20, rot=(0, math.pi/2, 0))
        for row, yy in enumerate([-1.55, -2.7, -3.85, -5.0]):
            for s_ in range(5):
                xx = XC + 1.1 + s_*1.15 + (row%2)*0.2
                if xx < x1 - 0.7 and yy > y0 + 0.5: console(xx, yy, zt, M_screen if random.random() < 0.8 else M_screenG)
        plant(XC+0.35, YC-0.35, zt, 1.1, True); plant(x1-0.4, YC-0.4, zt, 1.0, True); plant(XC+0.35, y0+0.5, zt, 0.8)
        bots = [(0.2,-2.1),(1.4,-1.0),(2.3,-2.1),(3.9,-3.2),(1.0,-4.3)]
    elif i == 1:  # ---- engineering: long table ----
        box("poster", (XC+0.03, -1.6, zt+1.15), (0.03, 0.8, 1.1), M_red)
        box("poster2", (XC+0.03, -3.0, zt+1.15), (0.03, 0.8, 1.1), M_panel)
        box("wscr", (2.5, YC-0.01, zt+1.2), (2.0, 0.03, 0.8), M_screenP)
        box("table", (2.0, -2.9, zt+0.72), (5.2, 0.9, 0.06), M_wood)
        for k in range(5):
            box("tleg", (-0.4+k*1.2, -2.9, zt+0.36), (0.06, 0.7, 0.7), M_dark)
            box("laptop", (-0.4+k*1.2, -2.75, zt+0.82), (0.36, 0.25, 0.14), M_screen if k%2 else M_screenG)
            stool(-0.2+k*1.2, -2.2, zt); stool(-0.2+k*1.2, -3.6, zt)
        cyl("engbase", (4.3, -1.5, zt+0.06), 0.8, 0.12, M_dark, 32)
        cyl("engine", (4.3, -1.5, zt+0.75), 0.25, 1.3, M_white, 24)
        cone("bell", (4.3, -1.5, zt+0.35), 0.45, 0.2, 0.5, M_dark)
        plant(XC+0.4, -4.6, zt, 1.0, True); plant(x1-0.4, -1.0, zt, 0.9)
        bots = [(0.4,-1.4),(1.4,-1.6),(2.9,-4.2),(3.6,-3.4),(-0.4,-4.4)]
    elif i == 2:  # ---- lounge: purple carpet + bar + servers ----
        box("carpet", (0.4, -2.8, zt+0.01), (2.6, 3.2, 0.02), M_purple)
        for k in range(3):
            box("sofa", (-0.4, -1.9-k*0.9, zt+0.25), (0.55, 0.75, 0.38), mat("sofa",(0.12,0.12,0.14),0.8))
        box("ctable", (0.6, -2.8, zt+0.3), (0.8, 1.6, 0.06), M_wood)
        box("chartscr", (XC+0.03, -1.8, zt+1.1), (0.03, 1.2, 0.8), M_screenP)
        box("bar", (3.2, -3.9, zt+0.5), (3.2, 0.5, 1.0), M_white, 0.03)
        box("bartop", (3.2, -3.9, zt+1.02), (3.3, 0.6, 0.05), M_wood)
        for k in range(5): stool(1.9+k*0.65, -4.5, zt)
        for k in range(4):
            box("rack", (2.6+k*0.65, YC-0.35, zt+0.85), (0.55, 0.5, 1.7), M_dark)
            for j in range(5): box("rl", (2.6+k*0.65, YC-0.61, zt+0.4+j*0.3), (0.4, 0.02, 0.03), M_screen if j%2 else M_screenG)
        plant(x1-0.4, -1.2, zt, 1.0, True); plant(XC+0.35, -4.7, zt, 0.8)
        bots = [(0.0,-2.2),(1.2,-3.3),(2.4,-2.2),(3.8,-1.7)]
    elif i == 3:  # ---- cafe / lab: wooden tables + plants ----
        box("wpanel", (XC+0.03, -2.2, zt+1.0), (0.03, 1.6, 1.3), M_dark)
        box("wpanel2", (XC+0.04, -2.2, zt+1.0), (0.02, 1.4, 1.1), M_panel)
        for row, yy in enumerate([-2.0, -3.6]):
            box("wtable", (1.8, yy, zt+0.72), (4.4, 0.8, 0.06), M_wood)
            for k in range(4):
                box("wleg", (0.0+k*1.2, yy, zt+0.36), (0.06, 0.6, 0.7), M_dark)
                stool(0.2+k*1.2, yy-0.6, zt)
        # round glass room on the right
        cyl("groom", (3.9, -1.5, zt+0.8), 0.8, 1.6, M_glass, 32)
        cyl("groomb", (3.9, -1.5, zt+0.02), 0.82, 0.04, M_dark, 32)
        for p in [(XC+0.4,-1.0,1.2,True),(XC+0.5,-4.4,1.1,True),(4.6,-3.2,0.9,False),(2.8,-1.0,0.8,False)]:
            plant(p[0], p[1], zt, p[2], p[3])
        bots = [(0.4,-2.8),(2.5,-2.8),(3.4,-3.5),(1.4,-4.5)]
    else:         # ---- bottom: workshop + garden ----
        box("bench", (1.0, -1.6, zt+0.5), (2.6, 0.7, 1.0), M_white, 0.02)
        box("tool", (1.0, -1.6, zt+1.1), (2.0, 0.3, 0.2), M_dark)
        box("mat", (1.2, -4.0, zt+0.01), (2.0, 0.8, 0.02), M_dark)
        text("SPACEX", (1.2, -4.0, zt+0.025), 0.35, M_white, rot=(0, 0, 0))
        for p in [(XC+0.5,-1.0,1.3,True),(3.4,-1.5,1.2,True),(0.0,-3.0,1.0,True),(3.8,-3.8,0.9,False),(2.4,-3.0,0.8,False)]:
            plant(p[0], p[1], zt, p[2], p[3])
        box("server2", (XC+0.4, -3.6, zt+0.8), (0.5, 0.6, 1.6), M_dark)
        bots = [(0.9,-2.6),(2.2,-4.6),(3.0,-2.2),(-0.2,-4.8)]
    for k, (bx, by) in enumerate(bots):
        if bx < x1 - 0.3 and by > y0 + 0.3:
            bot(bx, by, zt, M_bots[(i*5+k) % len(M_bots)])

# under the lowest floor: tank, pillars, crates
zb = Z0 - (NF-1)*FH - 0.22
for px, py in [(XC+0.4,-B+2.1+0.2),(1.5,-B+2.1),(A-2.5,-B+2.1),(A-2.3,-2.0),(A-2.3,YC-0.4)]:
    cyl("pillar", (px, py, (zb+FZ_BOT)/2), 0.09, zb-FZ_BOT, M_white, 12)
cyl("tank", (0.6, -4.9, FZ_BOT+0.62), 0.55, 2.2, mat("tank",(0.02,0.02,0.025),0.2,0.3), 32, rot=(0, math.pi/2, 0))
cyl("tankfan", (1.75, -4.9, FZ_BOT+0.62), 0.5, 0.06, M_metal, 16, rot=(0, math.pi/2, 0))
for k in range(3): box("frame", (-0.7+k*0.18, -4.9, FZ_BOT+0.55), (0.05, 0.7, 1.1), M_metal)
for k in range(3): box("crate", (3.6+k*0.5, -5.2, FZ_BOT+0.18), (0.45, 0.4, 0.32), M_white)

# glass elevator in its slot
eh_top = 1.4
box("elev", (EX, EY, (FZ_BOT+eh_top)/2), (1.15, 1.15, eh_top-FZ_BOT), M_glass)
for dx in (-0.575, 0.575):
    for dy in (-0.575, 0.575):
        box("efr", (EX+dx, EY+dy, (FZ_BOT+eh_top)/2), (0.06, 0.06, eh_top-FZ_BOT), M_dark)
for k in range(7):
    zz = FZ_BOT + 0.2 + k*FH
    box("eh1", (EX, EY-0.575, zz), (1.15, 0.05, 0.05), M_dark); box("eh2", (EX+0.575, EY, zz), (0.05, 1.15, 0.05), M_dark)
box("ecab", (EX, EY, Z0-2*FH+0.55), (0.95, 0.95, 1.0), mat("ecab",(0.9,0.6,0.8),0.2,emit=(1,0.3,0.6),estr=1.2, alpha=0.6))
bot(EX, EY, Z0-2*FH+0.05, M_bots[4], 0.25)
# top glass box on the surface
box("etop", (EX-0.2, EY-0.2, 0.75), (1.7, 1.7, 1.5), M_glass)
for dx in (-0.85, 0.85):
    for dy in (-0.85, 0.85):
        box("etf", (EX-0.2+dx, EY-0.2+dy, 0.75), (0.06, 0.06, 1.5), M_dark)
box("etroof", (EX-0.2, EY-0.2, 1.52), (1.75, 1.75, 0.05), M_dark)
bot(EX-0.2, EY-0.2, 0.0, M_bots[1], 0.25)

# ================= surface =================
PX, PY = -3.5, -1.6
cyl("pad", (PX, PY, 0.05), 2.2, 0.14, M_pad, 64)
bpy.ops.mesh.primitive_torus_add(major_radius=1.95, minor_radius=0.035, location=(PX, PY, 0.13), major_segments=64)
bpy.context.object.data.materials.append(M_white)
bpy.ops.mesh.primitive_torus_add(major_radius=1.25, minor_radius=0.02, location=(PX, PY, 0.13), major_segments=64)
bpy.context.object.data.materials.append(M_white)
# rocket (Starship-like)
RB = 1.0; RR = 0.95
cone("skirt", (PX, PY, RB-0.2), RR*0.75, RR, 0.5, M_dark, 48)
cyl("rocket", (PX, PY, RB+3.9), RR, 7.8, M_white, 64)
cyl("band", (PX, PY, RB+7.3), RR+0.01, 1.0, M_dark, 64)
cd = Vector((0.707, -0.707, 0))
for k in range(6):
    a = -math.pi/4 + (k-2.5)*0.22
    box("win", (PX+math.cos(a)*(RR+0.02), PY+math.sin(a)*(RR+0.02), RB+7.3), (0.07, 0.07, 0.1), M_lamp)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=RR, location=(PX, PY, RB+7.8))
n = bpy.context.object; n.scale.z = 2.7; n.data.materials.append(M_white); bpy.ops.object.shade_smooth()
for k in range(4):
    a = k*math.pi/2 + math.pi/4
    f = box("fin", (PX+math.cos(a)*(RR+0.25), PY+math.sin(a)*(RR+0.25), RB+0.9), (0.55, 0.06, 1.6), M_white)
    f.rotation_euler.z = a
for k in range(6):
    a = k*math.pi/3 + 0.3
    p0 = Vector((PX+math.cos(a)*RR*0.9, PY+math.sin(a)*RR*0.9, RB+1.4)); p1 = Vector((PX+math.cos(a)*1.75, PY+math.sin(a)*1.75, 0.12))
    mid = (p0+p1)/2; dv = p0-p1
    lg = cyl("leg", mid, 0.045, dv.length, M_metal, 8)
    lg.rotation_euler = dv.to_track_quat('Z','Y').to_euler()
    cyl("foot", p1, 0.12, 0.05, M_metal, 12)
# vertical SPACEX on the body, facing camera
Xv = Vector((0,0,1)); Zv = cd.copy(); Yv = Zv.cross(Xv)
t = text("SPACEX", (0,0,0), 0.55, M_dark, extrude=0.005)
t.matrix_world = Matrix.Translation(Vector((PX, PY, RB+4.6)) + cd*(RR+0.012)) @ Matrix((Xv, Yv, Zv)).transposed().to_4x4()
t.data.align_y = 'CENTER'
# giant SPACEX sign on the back edge
sgn = text("SPACEX", (-0.6, B-0.6, 0.55), 2.25, M_white, rot=(math.radians(90), 0, 0), extrude=0.18, spacing=1.15)
for xx in (-4.6, -1.5, 1.5, 4.0):
    box("signpost", (xx, B-0.45, 0.3), (0.08, 0.08, 0.6), M_metal)
box("signbar", (-0.4, B-0.45, 0.55), (9.5, 0.08, 0.08), M_metal)
# solar field
for i in range(6):
    for j in range(7):
        x = 0.0 + j*0.68; y = 2.1 + i*0.52
        o = box("panel", (x, y, 0.42), (0.64, 0.46, 0.03), M_solar); o.rotation_euler.x = 0.45
        cyl("post", (x, y+0.05, 0.2), 0.02, 0.4, M_metal, 6, smooth=False)
# satellite dishes on the right edge
for dx, dy in [(5.7, 3.3), (6.0, 4.4), (5.2, 5.3)]:
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
# crates, rover, surface bots, rocks
for k in range(6):
    box("crate", (-2.4+0.42*(k%2), 4.2+0.42*((k//2)%2), 0.2+0.38*(k//4)), (0.4, 0.4, 0.36), M_white, 0.01)
box("rover", (3.5, 0.9, 0.3), (1.0, 0.55, 0.28), M_white, 0.05)
box("roverwin", (3.6, 0.9, 0.48), (0.5, 0.5, 0.14), M_dark, 0.03)
for dx in (-0.35, 0.35):
    for dy in (-0.3, 0.3):
        cyl("wheel", (3.5+dx, 0.9+dy, 0.14), 0.14, 0.1, M_dark, 12, rot=(math.pi/2, 0, 0))
bot(1.4, 1.2, 0.0, M_bots[6], 0.3); bot(2.0, 1.4, 0.0, M_bots[4], 0.3)
for k in range(40):
    x = random.uniform(-A+0.4, A-0.4); y = random.uniform(-B+0.4, B-0.4)
    if (x > XC-0.3 and y < YC+0.3) or math.hypot(x-PX, y-PY) < 2.4: continue
    o = ico("rock", (x, y, 0.02), random.uniform(0.06, 0.18), mat("srock",(0.2,0.2,0.21),0.9), 1)
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
ne = N.new("ShaderNodeTexNoise"); ne.inputs["Scale"].default_value = 2.2; ne.inputs["Detail"].default_value = 8
re = N.new("ShaderNodeValToRGB"); re.color_ramp.elements[0].color = (0.01,0.06,0.3,1); re.color_ramp.elements[1].color = (0.15,0.3,0.08,1)
re.color_ramp.elements[0].position = 0.55; re.color_ramp.elements[1].position = 0.58
nc = N.new("ShaderNodeTexNoise"); nc.inputs["Scale"].default_value = 5; nc.inputs["Detail"].default_value = 6
rc = N.new("ShaderNodeValToRGB"); rc.color_ramp.elements[0].position = 0.55; rc.color_ramp.elements[1].position = 0.72
mxe = N.new("ShaderNodeMixRGB")
L.new(ne.outputs["Fac"], re.inputs["Fac"]); L.new(nc.outputs["Fac"], rc.inputs["Fac"])
L.new(rc.outputs["Color"], mxe.inputs["Fac"]); L.new(re.outputs["Color"], mxe.inputs[1]); mxe.inputs[2].default_value = (0.9,0.9,0.9,1)
L.new(mxe.outputs["Color"], be.inputs["Base Color"])
earth = sph("earth", target + R @ Vector((220*k, 315*k, -40)), 55*k, M_earth, seg=64)
# stars on a backdrop plane facing the camera
M_star = C.materials.new("stars"); M_star.use_nodes = True
nt = M_star.node_tree; nt.nodes.clear()
so_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
tcs = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 260
rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (1,1,1,1)
rp.color_ramp.elements[1].position = 0.045; rp.color_ramp.elements[1].color = (0.0015,0.0015,0.002,1)
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
sun = C.lights.new("sun", 'SUN'); sun.energy = 3.2; sun.angle = math.radians(3)
so = C.objects.new("sun", sun); sc.collection.objects.link(so); aim(so, (-0.45, -1.0, 0.85))
fill = C.lights.new("fill", 'SUN'); fill.energy = 0.5; fill.angle = math.radians(20)
fo = C.objects.new("fill", fill); sc.collection.objects.link(fo); aim(fo, (1.0, -0.4, 0.6))
fill.use_shadow = False
wd = C.worlds.new("w"); sc.world = wd; wd.use_nodes = True
wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02,0.022,0.026,1)
wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0

# ================= render =================
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = int(os.environ.get("PS", 32))
try:
    sc.eevee.use_raytracing = True; sc.eevee.ray_tracing_method = 'SCREEN'
    sc.eevee.use_shadows = True; sc.eevee.shadow_ray_count = 2; sc.eevee.shadow_step_count = 8
except Exception as ex: print("rt", ex)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = float(os.environ.get("EXP", 0.0))
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
