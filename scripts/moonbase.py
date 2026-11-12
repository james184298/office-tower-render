import bpy, bmesh, math, random, os
from mathutils import Vector
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
C = bpy.data

# ---------- helpers ----------
def mat(name, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0):
    m = C.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = estr
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except: pass
    return m

def box(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name
    o.scale = (size[0]/2, size[1]/2, size[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new("b", 'BEVEL'); md.width = bevel; md.segments = 2
    o.data.materials.append(m); return o

def cyl(name, loc, r, h, m, verts=24, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); return o

def sph(name, loc, r, m, sc_=(1,1,1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg//2, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = sc_
    o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o

def cone(name, loc, r1, r2, h, m, verts=24):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=h, location=loc)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); return o

# ---------- materials ----------
M_white = mat("white", (0.85,0.86,0.88), 0.35)
M_floor = mat("floor", (0.78,0.79,0.8), 0.25)
M_dark = mat("dark", (0.03,0.035,0.04), 0.4)
M_desk = mat("desk", (0.06,0.065,0.07), 0.3)
M_wood = mat("wood", (0.55,0.42,0.28), 0.5)
M_metal = mat("metal", (0.6,0.62,0.65), 0.25, 1.0)
M_glass = mat("glass", (0.8,0.9,0.95), 0.02, 0, alpha=0.25)
M_screen = mat("screen", (0,0,0), 0.2, emit=(0.25,0.55,1.0), estr=6.0)
M_screen2 = mat("screen2", (0,0,0), 0.2, emit=(0.6,0.3,1.0), estr=2.5)
M_lamp = mat("lamp", (1,1,1), 0.5, emit=(1.0,0.85,0.6), estr=8)
M_leaf = mat("leaf", (0.06,0.35,0.08), 0.6)
M_pot = mat("pot", (0.9,0.9,0.9), 0.4)
M_purple = mat("carpet", (0.18,0.08,0.38), 0.9)
M_solar = mat("solar", (0.02,0.03,0.07), 0.15, 0.6)
M_eye = mat("eye", (1,1,1), 0.2, emit=(1,1,1), estr=1.5)
M_pupil = mat("pupil", (0.01,0.01,0.01), 0.2)
BOT_COLS = [(0.1,0.85,0.2),(1.0,0.45,0.05),(0.15,0.4,1.0),(0.6,0.15,1.0),(1.0,0.15,0.4),(0.05,0.8,0.8),(1.0,0.8,0.05),(0.9,0.9,0.95)]
M_bots = [mat(f"bot{i}", c, 0.35, emit=c, estr=0.6) for i,c in enumerate(BOT_COLS)]

# rock with horizontal strata
M_rock = C.materials.new("rock"); M_rock.use_nodes = True
nt = M_rock.node_tree; N = nt.nodes; L = nt.links
bsdf = N["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.9
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
noi = N.new("ShaderNodeTexNoise"); noi.inputs["Scale"].default_value = 1.5; noi.inputs["Detail"].default_value = 6
mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY_ADD'; mul.inputs[1].default_value = 0.25
wav = N.new("ShaderNodeTexWave"); wav.wave_type = 'BANDS'; wav.bands_direction = 'Z'
wav.inputs["Scale"].default_value = 1.6; wav.inputs["Distortion"].default_value = 2.5; wav.inputs["Detail"].default_value = 8
ramp = N.new("ShaderNodeValToRGB"); r = ramp.color_ramp
r.elements[0].color = (0.12,0.12,0.125,1); r.elements[1].color = (0.36,0.36,0.37,1)
e = r.elements.new(0.5); e.color = (0.22,0.22,0.23,1)
L.new(tc.outputs["Object"], wav.inputs["Vector"])
L.new(wav.outputs["Color"], ramp.inputs["Fac"])
L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4
L.new(wav.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

M_regolith = C.materials.new("regolith"); M_regolith.use_nodes = True
nt = M_regolith.node_tree; N = nt.nodes; L = nt.links
b2 = N["Principled BSDF"]; b2.inputs["Roughness"].default_value = 1
n2 = N.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 6; n2.inputs["Detail"].default_value = 10
r2 = N.new("ShaderNodeValToRGB"); r2.color_ramp.elements[0].color = (0.32,0.32,0.33,1); r2.color_ramp.elements[1].color = (0.5,0.5,0.5,1); r2.color_ramp.elements[0].position=0.3; r2.color_ramp.elements[1].position=0.7
L.new(n2.outputs["Fac"], r2.inputs["Fac"]); L.new(r2.outputs["Color"], b2.inputs["Base Color"])
bp2 = N.new("ShaderNodeBump"); bp2.inputs["Strength"].default_value = 0.3
L.new(n2.outputs["Fac"], bp2.inputs["Height"]); L.new(bp2.outputs["Normal"], b2.inputs["Normal"])

# ---------- rock block with cutaway ----------
S = 6.0      # half size
TOP = 0.0; BOT = -11.0
bpy.ops.mesh.primitive_cube_add(location=(0,0,(TOP+BOT)/2))
blk = bpy.context.object; blk.name = "block"
blk.scale = (S, S, (TOP-BOT)/2); bpy.ops.object.transform_apply(scale=True)
# irregular sides
md = blk.modifiers.new("sub", 'SUBSURF'); md.levels = 3; md.render_levels = 3; md.subdivision_type = 'SIMPLE'
tex = C.textures.new("rk", 'CLOUDS'); tex.noise_scale = 1.6
d = blk.modifiers.new("disp", 'DISPLACE'); d.texture = tex; d.strength = 0.45; d.mid_level = 0.5
# cut
CUT_X0, CUT_Y1 = -2.2, 2.2          # cut region: x > CUT_X0, y < CUT_Y1
FZ_TOP, FZ_BOT = -0.6, -8.2
bpy.ops.mesh.primitive_cube_add(location=((CUT_X0+S+2)/2, (CUT_Y1-S-2)/2, (FZ_TOP+FZ_BOT)/2))
cut = bpy.context.object
cut.scale = ((S+2-CUT_X0)/2, (CUT_Y1+S+2)/2, (FZ_TOP-FZ_BOT)/2)
bb = blk.modifiers.new("cut", 'BOOLEAN'); bb.object = cut; bb.solver = 'EXACT'
cut.hide_render = True; cut.hide_viewport = True
blk.data.materials.append(M_rock)
bpy.ops.object.shade_smooth()
# taper bottom: lower part narrower (simple: a second, smaller rock chunk underneath)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=(0,0,BOT))
ch = bpy.context.object; ch.scale = (S*0.95, S*0.95, 3.2)
d2 = ch.modifiers.new("disp", 'DISPLACE'); d2.texture = tex; d2.strength = 0.8
ch.data.materials.append(M_rock)

# top regolith skin
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=2*S-0.05, location=(0,0,TOP+0.02))
top = bpy.context.object; top.name = "surface"
tex2 = C.textures.new("rg", 'CLOUDS'); tex2.noise_scale = 0.8
d3 = top.modifiers.new("disp", 'DISPLACE'); d3.texture = tex2; d3.strength = 0.18
top.data.materials.append(M_regolith); bpy.ops.object.shade_smooth()
# craters
for cx, cy, cr in [(-4.0,-1.0,0.9),(2.8,3.5,0.6),(-1.2,4.4,0.4),(4.4,-3.5,0.35)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=cr, minor_radius=cr*0.18, location=(cx,cy,TOP+0.05))
    t = bpy.context.object; t.scale.z = 0.35; t.data.materials.append(M_regolith)
    bpy.ops.mesh.primitive_cylinder_add(radius=cr*0.9, depth=0.02, location=(cx,cy,TOP+0.02))
    bpy.context.object.data.materials.append(mat("crater",(0.08,0.08,0.085),1))

# ---------- floors ----------
NF = 5
fh = (FZ_TOP - FZ_BOT) / NF
X0, X1 = CUT_X0, S - 0.4
Y0, Y1 = -S + 0.4, CUT_Y1
W = X1 - X0; D = Y1 - Y0

def bot(loc, m, s=0.3):
    x,y,z = loc
    b = sph("bot", (x,y,z+s*1.0), s, m, (1,1,1.15))
    # flatten bottom by a skirt cone
    cone("skirt", (x,y,z+s*0.35), s*1.1, s*0.9, s*0.7, m)
    for dx in (-0.35, 0.35):
        ex, ey = x + s*0.92*0.707 + dx*s*0.707, y - s*0.92*0.707 + dx*s*0.707
        sph("eye", (ex, ey, z+s*1.25), s*0.2, M_eye)
        sph("pup", (ex+s*0.1, ey-s*0.1, z+s*1.25), s*0.1, M_pupil)

def plant(loc, s=1.0):
    x,y,z = loc
    cyl("pot", (x,y,z+0.12*s), 0.12*s, 0.24*s, M_pot)
    for i in range(7):
        a = random.random()*6.28; rr = random.random()*0.14*s
        sph("leaf", (x+math.cos(a)*rr, y+math.sin(a)*rr, z+(0.35+random.random()*0.4)*s), (0.08+random.random()*0.06)*s, M_leaf, seg=10)

def desk_row(x, y, z, n, along='x', screens=True):
    for i in range(n):
        px = x + (i*0.75 if along=='x' else 0); py = y + (i*0.75 if along=='y' else 0)
        box("desk", (px, py, z+0.38), (0.7, 0.4, 0.05), M_desk)
        box("leg", (px, py, z+0.19), (0.05, 0.3, 0.38), M_dark)
        if screens:
            box("mon", (px, py+0.12, z+0.6), (0.5, 0.03, 0.3), M_screen if random.random()<0.7 else M_screen2)
        box("chair", (px, py-0.32, z+0.25), (0.3, 0.3, 0.06), M_dark)
        box("chairb", (px, py-0.46, z+0.45), (0.3, 0.04, 0.35), M_dark)

for f in range(NF):
    z = FZ_BOT + f*fh
    box(f"slab{f}", (X0+W/2, Y0+D/2, z+0.08), (W, D, 0.16), M_floor, 0.02)
    box(f"edge{f}", (X0+W/2, Y0+0.03, z+0.08), (W, 0.06, 0.18), M_white)
    # ceiling lights strip
    for k in range(4):
        box("light", (X0+1+k*1.8, Y0+D/2, z+fh-0.05), (1.2, 0.15, 0.03), M_lamp)
    L_ = C.lights.new(f"fl{f}", 'AREA'); L_.energy = 150; L_.size = 4; L_.color = (1,0.93,0.85)
    lo = C.objects.new(f"fl{f}", L_); sc.collection.objects.link(lo); lo.location = (X0+W/2, Y0+D/2, z+fh-0.15)
    # back walls: left wall (x=X0) dark with lights, right wall (y=Y1) screens
    box("wallL", (X0+0.05, Y0+D/2, z+fh/2), (0.1, D, fh), M_white)
    box("wallB", (X0+W/2, Y1-0.05, z+fh/2), (W, 0.1, fh), mat(f"wb{f}", (0.12,0.12,0.13), 0.4))
    # big screen on back wall
    sw = W*0.55
    box("bigscreen", (X0+W*0.55, Y1-0.12, z+fh*0.55), (sw, 0.04, fh*0.45), M_screen if f%2==0 else M_screen2)
    box("bezel", (X0+W*0.55, Y1-0.1, z+fh*0.55), (sw+0.1, 0.03, fh*0.45+0.1), M_dark)
    # glass railing front
    box("glassF", (X0+W/2, Y0+0.05, z+0.16+0.25), (W, 0.03, 0.5), M_glass)
    kind = [ 'lobby','lounge','labs','engineering','mission'][f]
    if kind == 'mission':
        for row in range(3):
            desk_row(X0+0.8, Y0+1.0+row*1.3, z+0.16, 6)
    elif kind == 'engineering':
        desk_row(X0+0.8, Y0+1.0, z+0.16, 5)
        box("bench", (X0+W*0.6, Y0+D*0.6, z+0.55), (2.5, 0.7, 0.08), M_wood)
        cyl("rocketmodel", (X0+W*0.85, Y0+D*0.35, z+0.9), 0.08, 1.4, M_white)
        cone("rmnose", (X0+W*0.85, Y0+D*0.35, z+1.7), 0.08, 0, 0.25, M_white)
        box("glassroom", (X0+1.2, Y0+D*0.7, z+0.7), (1.6, 1.4, 1.1), M_glass)
    elif kind == 'labs':
        box("carpet", (X0+1.6, Y0+D*0.55, z+0.17), (2.4, 2.2, 0.01), M_purple)
        for k in range(3): box("sofa", (X0+1.0+k*0.8, Y0+D*0.6, z+0.3), (0.6, 0.5, 0.25), M_dark)
        box("bar", (X0+W*0.62, Y0+D*0.45, z+0.5), (3.0, 0.4, 0.7), M_wood)
        for k in range(4): box("rack", (X1-0.5, Y0+1+k*0.6, z+0.8), (0.4, 0.4, 1.3), M_dark)
    elif kind == 'lounge':
        desk_row(X0+0.8, Y0+1.2, z+0.16, 4, screens=True)
        box("table", (X0+W*0.6, Y0+D*0.55, z+0.45), (2.8, 0.9, 0.06), M_wood)
    else:  # lobby
        box("reception", (X0+W*0.45, Y0+D*0.45, z+0.5), (2.0, 0.5, 0.7), M_white, 0.03)
        cone("capsule", (X0+W*0.72, Y0+D*0.55, z+0.75), 0.55, 0.25, 1.0, M_white, 32)
        box("tank", (X0+0.9, Y0+0.9, z+0.6), (1.4, 0.8, 0.8), M_dark, 0.3)
    for k in range(4 + random.randint(0,2)):
        plant((X0+0.4+random.random()*(W-0.8), Y0+0.4+random.random()*(D-0.8), z+0.16), 0.8+random.random()*0.6)
    for k in range(6):
        bot((X0+0.6+random.random()*(W-1.2), Y0+0.5+random.random()*(D-1.0), z+0.16), random.choice(M_bots))
    # pillars under bottom floor
    if f == 0:
        for px in (X0+1, X0+W/2, X1-0.5):
            cyl("pillar", (px, Y0+0.4, z-0.5), 0.08, 1.0, M_white)

# glass elevator tower at front-right corner
ex, ey = X1-0.2, Y0+0.6
box("elev", (ex, ey, (FZ_BOT+TOP)/2+0.6), (1.0, 1.0, TOP-FZ_BOT+1.2), M_glass)
for dx in (-0.5,0.5):
    for dy in (-0.5,0.5):
        box("efr", (ex+dx, ey+dy, (FZ_BOT+TOP)/2+0.6), (0.05,0.05,TOP-FZ_BOT+1.2), M_dark)
box("ecab", (ex, ey, FZ_BOT+fh*2+0.6), (0.85,0.85,1.0), mat("ecab",(0.9,0.9,0.95),0.2,emit=(1,0.3,0.6),estr=1.5))

# wall lights on cut faces
for k in range(14):
    zz = FZ_BOT + 0.4 + k*0.5
    sph("wl", (X0-0.25, Y0+0.05, zz), 0.05, M_lamp, seg=8)

# ---------- surface props ----------
# landing pad + rocket
px, py = -3.2, 3.0
cyl("pad", (px,py,TOP+0.08), 1.6, 0.12, mat("pad",(0.15,0.15,0.16),0.5), 48)
bpy.ops.mesh.primitive_torus_add(major_radius=1.4, minor_radius=0.03, location=(px,py,TOP+0.15))
bpy.context.object.data.materials.append(M_white)
RH = 7.0
cyl("rocket", (px,py,TOP+0.6+RH/2), 0.55, RH, M_white, 48)
cyl("band", (px,py,TOP+0.6+RH*0.8), 0.56, 0.7, M_dark, 48)
cyl("band2", (px,py,TOP+0.6+RH*0.18), 0.56, 0.08, M_dark, 48)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.55, location=(px,py,TOP+0.6+RH))
n = bpy.context.object; n.scale.z = 2.2; n.data.materials.append(M_white); bpy.ops.object.shade_smooth()
for a in range(4):
    ang = a*math.pi/2 + math.pi/4
    fx, fy = px+math.cos(ang)*0.7, py+math.sin(ang)*0.7
    box("fin", (fx,fy,TOP+1.3), (0.5,0.06,1.4), M_white).rotation_euler.z = ang
    leg = cyl("leg", (px+math.cos(ang)*0.95, py+math.sin(ang)*0.95, TOP+0.5), 0.04, 1.2, M_metal)
    leg.rotation_euler = (math.sin(ang)*0.4, -math.cos(ang)*0.4, 0)
# solar field
for i in range(6):
    for j in range(7):
        o = box("panel", (0.8+i*0.75, 0.2+j*0.6, TOP+0.35), (0.7, 0.5, 0.03), M_solar)
        o.rotation_euler.x = 0.35
        cyl("post", (0.8+i*0.75, 0.2+j*0.6, TOP+0.18), 0.02, 0.35, M_metal)
# dishes
for dx, dy in [(5.0,-1.5),(5.2,-0.4),(4.7,0.7)]:
    c = cone("dish", (dx,dy,TOP+0.7), 0.4, 0.05, 0.2, M_white, 32); c.rotation_euler = (0.8,0,0.6)
    cyl("dpost", (dx,dy,TOP+0.3), 0.03, 0.6, M_metal)
# lander
cyl("lander", (-4.6,-0.6,TOP+0.5), 0.45, 0.35, mat("gold",(0.9,0.65,0.15),0.3,1.0), 8)
# sign SPACEX
bpy.ops.object.text_add(location=(-0.5, 4.8, TOP+0.1))
t = bpy.context.object; t.data.body = "SPACEX"; t.data.extrude = 0.08; t.data.size = 1.3
t.rotation_euler = (math.radians(90), 0, 0); t.data.materials.append(M_white)
# cargo boxes, rover
for k in range(4): box("crate", (-1.0+0.3*(k%2), 1.8+0.3*(k//2), TOP+0.15+0.0), (0.28,0.28,0.25), M_white)
box("rover", (2.2,-2.5,TOP+0.15), (0.6,0.35,0.15), M_white, 0.04)
for k in range(2): bot((-0.2+k*0.5, -1.2, TOP+0.1), M_bots[1+k*3], 0.18)

# ---------- sky ----------
wd = C.worlds.new("w"); sc.world = wd; wd.use_nodes = True
N = wd.node_tree.nodes; L = wd.node_tree.links
bg = N["Background"]; bg.inputs["Strength"].default_value = 1.0
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 400
vo.feature = 'F1'
rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (1,1,1,1)
rp.color_ramp.elements[1].position = 0.03; rp.color_ramp.elements[1].color = (0.002,0.002,0.003,1)
L.new(tc.outputs["Generated"], vo.inputs["Vector"]); L.new(vo.outputs["Distance"], rp.inputs["Fac"])
L.new(rp.outputs["Color"], bg.inputs["Color"])

# earth
M_earth = C.materials.new("earth"); M_earth.use_nodes = True
N = M_earth.node_tree.nodes; L = M_earth.node_tree.links
be = N["Principled BSDF"]; be.inputs["Roughness"].default_value = 0.6
ne = N.new("ShaderNodeTexNoise"); ne.inputs["Scale"].default_value = 3; ne.inputs["Detail"].default_value = 8
re = N.new("ShaderNodeValToRGB"); re.color_ramp.elements[0].color = (0.01,0.07,0.35,1); re.color_ramp.elements[1].color = (0.12,0.3,0.08,1)
re.color_ramp.elements[0].position = 0.52; re.color_ramp.elements[1].position = 0.56
nc = N.new("ShaderNodeTexNoise"); nc.inputs["Scale"].default_value = 7; nc.inputs["Detail"].default_value = 6
rc = N.new("ShaderNodeValToRGB"); rc.color_ramp.elements[0].position = 0.58; rc.color_ramp.elements[1].position = 0.7
mx = N.new("ShaderNodeMixRGB")
L.new(ne.outputs["Fac"], re.inputs["Fac"]); L.new(nc.outputs["Fac"], rc.inputs["Fac"])
L.new(rc.outputs["Color"], mx.inputs["Fac"]); L.new(re.outputs["Color"], mx.inputs[1]); mx.inputs[2].default_value = (1,1,1,1)
L.new(mx.outputs["Color"], be.inputs["Base Color"])
earth = sph("earth", (14, 6, 12), 2.2, M_earth, seg=64)

# ---------- lights / camera ----------
sun = C.lights.new("sun", 'SUN'); sun.energy = 3.0; sun.angle = 0.02
so = C.objects.new("sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-25), math.radians(-20))
fill = C.lights.new("fill", 'SUN'); fill.energy = 0.6
fo = C.objects.new("fill", fill); sc.collection.objects.link(fo); fo.rotation_euler = (math.radians(70), 0, math.radians(200))

cam = C.cameras.new("cam"); cam.type = 'ORTHO'; cam.ortho_scale = float(os.environ.get("OS", 31))
co = C.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
co.rotation_euler = (math.radians(58), 0, math.radians(45))
dvec = co.rotation_euler.to_matrix() @ Vector((0,0,1))
target = Vector((float(os.environ.get("TX",0.3)), float(os.environ.get("TY",-0.3)), float(os.environ.get("TZ",-1.0))))
co.location = target + dvec*40
cam.clip_end = 200
R = co.rotation_euler.to_matrix()
earth.location = target + R @ Vector((9.0, 12.5, -20))
earth.scale = (1.4,1.4,1.4)

# ---------- render ----------
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = int(os.environ.get("PS", 32))
try:
    sc.eevee.use_raytracing = True; sc.eevee.ray_tracing_method = 'SCREEN'
    sc.eevee.use_shadows = True
except Exception as ex: print("rt", ex)
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1350
sc.render.resolution_percentage = int(os.environ.get("PCT", 100))
sc.render.image_settings.file_format = "PNG"
out = os.environ.get("OUT", "../out/moon_hero.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(out), "moonbase.blend"))
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("DONE", out)
