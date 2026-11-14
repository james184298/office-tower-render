# floors_v2: lower-floor interiors rebuilt from the ref close-ups (Starship Engineering / Starlink / Lobby).
# exec'd inside moonbase.py's floor loop (globals: i, zt, XC, YC, A, B, box, cyl, cone, sph, plane, text, plant, chair, stool, mat, M_*)
import math as _m

def _mat(n, c, r=0.5, **k):
    return C.materials.get(n) or mat(n, c, r, **k)

M_bwood = _mat("lwood", (0.72, 0.58, 0.4), 0.5)
M_frame = _mat("frm", (0.05, 0.05, 0.055), 0.4)
M_rugL = _mat("rugl", (0.55, 0.555, 0.56), 0.9)
M_sofaW = _mat("sofaw", (0.8, 0.8, 0.8), 0.7)
M_arm = _mat("armd", (0.03, 0.03, 0.035), 0.6)
M_eng = _mat("engcu", (0.45, 0.36, 0.28), 0.35, metal=0.7)
M_red = _mat("redp", (0.55, 0.08, 0.04), 0.6)
M_map = _mat("mapscr", (0.08, 0.03, 0.2), 0.4, emit=(0.32, 0.18, 0.75), estr=1.4)
M_hedge = _mat("hedge", (0.05, 0.25, 0.04), 0.8)
M_rack = _mat("rack", (0.06, 0.06, 0.07), 0.4)

def desk_row(x0, x1, y, z, both=True, mon=True):
    L = x1 - x0; cx = (x0 + x1) / 2
    box("drow", (cx, y, z + 0.38), (L, 0.5, 0.035), M_bwood)
    n = max(2, int(L / 0.62))
    for k in range(n + 1):
        xx = x0 + 0.05 + k * (L - 0.1) / n
        box("dleg", (xx, y, z + 0.19), (0.025, 0.46, 0.38), M_frame)
    for k in range(n):
        xx = x0 + (k + 0.5) * L / n
        if mon:
            box("dmon", (xx - 0.12, y, z + 0.52), (0.2, 0.02, 0.14), M_dark)
            plane("dmons", (xx - 0.12, y - 0.012, z + 0.52), 0.18, 0.12, M_conimg)
            box("dmon", (xx + 0.12, y + 0.02, z + 0.52), (0.2, 0.02, 0.14), M_dark)
        box("kbd", (xx, y - 0.13, z + 0.405), (0.18, 0.06, 0.01), M_dark)
        chair(xx, y - 0.45, z, -1, M_white, 0.75)
        if both: chair(xx, y + 0.45, z, 1, M_white, 0.75)

def glass_room(x0, x1, y0, y1, z, h=1.25):
    # two open sides (front y0, right x1) glazed, with thin dark frames
    box("grw", ((x0 + x1) / 2, y0, z + h / 2), (x1 - x0, 0.02, h), M_glass)
    box("grw", (x1, (y0 + y1) / 2, z + h / 2), (0.02, y1 - y0, h), M_glass)
    for xx in [x0 + k * (x1 - x0) / 4 for k in range(5)]:
        box("grf", (xx, y0, z + h / 2), (0.025, 0.03, h), M_white)
    for yy in [y0 + k * (y1 - y0) / 3 for k in range(4)]:
        box("grf", (x1, yy, z + h / 2), (0.03, 0.025, h), M_white)
    box("grt", ((x0 + x1) / 2, y0, z + h), (x1 - x0, 0.04, 0.03), M_white)
    box("grt", (x1, (y0 + y1) / 2, z + h), (0.04, y1 - y0, 0.03), M_white)
    box("grfl", ((x0 + x1) / 2, (y0 + y1) / 2, z + 0.008), (x1 - x0, y1 - y0, 0.01), M_bwood)

def raptor(x, y, z, s=1.0, stand=True):
    if stand:
        cyl("rpad", (x, y, z + 0.03), 0.42 * s, 0.06, M_dark, 32)
    cone("rbell", (x, y, z + 0.36 * s), 0.26 * s, 0.11 * s, 0.6 * s, M_eng, 32)
    cyl("rbody", (x, y, z + 0.8 * s), 0.13 * s, 0.32 * s, M_eng, 20)
    cyl("rtop", (x, y, z + 1.02 * s), 0.18 * s, 0.14 * s, M_metal, 20)
    for a in range(4):
        cyl("rpipe", (x + 0.15 * s * _m.cos(a * 1.57), y + 0.15 * s * _m.sin(a * 1.57), z + 0.82 * s), 0.025 * s, 0.4 * s, M_white, 8)

def ship_model(x, y, z):
    cyl("spad", (x, y, z + 0.02), 0.85, 0.04, M_white, 48)
    cyl("spad2", (x, y, z + 0.045), 0.38, 0.03, M_dark, 32)
    cyl("sbody", (x, y, z + 0.8), 0.1, 1.3, M_metal, 24)
    cone("snose", (x, y, z + 1.62), 0.1, 0.0, 0.35, M_metal, 24)
    for a in range(2):
        o = box("sfin", (x, y, z + 0.28), (0.36, 0.015, 0.22), M_metal); o.rotation_euler.z = a * 1.57

def lounge(x, y, z, sofa_rot=0.0):
    box("lrug", (x, y, z + 0.006), (1.6, 1.1, 0.01), M_rugL)
    o = box("lsofa", (x + 0.2, y - 0.35, z + 0.14), (1.0, 0.36, 0.26), M_sofaW, 0.03); o.rotation_euler.z = sofa_rot
    o = box("lsofb", (x + 0.2, y - 0.5, z + 0.3), (1.0, 0.08, 0.2), M_sofaW, 0.02); o.rotation_euler.z = sofa_rot
    for dx, dy in [(-0.55, 0.25), (0.6, 0.35)]:
        box("larm", (x + dx, y + dy, z + 0.13), (0.3, 0.3, 0.24), M_arm, 0.03)
        box("larmb", (x + dx, y + dy + 0.12, z + 0.27), (0.3, 0.06, 0.2), M_arm, 0.02)
    cyl("lctab", (x, y + 0.05, z + 0.2), 0.22, 0.03, M_bwood, 24); cyl("lctl", (x, y + 0.05, z + 0.1), 0.03, 0.2, M_dark, 8)

def shelf(x, y, z, w=1.2, h=1.0):
    for dx in (-w / 2, w / 2):
        box("shp", (x + dx, y, z + h / 2), (0.025, 0.3, h), M_frame)
    for k in range(4):
        box("shb", (x, y, z + 0.05 + k * (h - 0.06) / 3), (w, 0.3, 0.025), M_bwood)
    for k in range(5):
        box("shx", (x - w / 2 + 0.15 + k * 0.22, y, z + 0.38 + (k % 3) * 0.31), (0.12, 0.14, 0.1 + 0.04 * (k % 2)), M_white if k % 2 else M_dark)

def stanchions(pts, z):
    for (x, y) in pts:
        cyl("stan", (x, y, z + 0.22), 0.02, 0.44, M_dark, 8); cyl("stanb", (x, y, z + 0.01), 0.07, 0.02, M_dark, 12)

if i == 1:   # ---- Starship Engineering (-13 m) ----
    plane("poster", (XC + 0.04, -4.9, zt + 1.0), 0.7, 1.1, M_poster, '+X')
    plane("chartp", (XC + 0.04, -3.6, zt + 1.05), 1.0, 0.7, M_chartimg, '+X')
    box("wscr", (XC + 0.04, -2.6, zt + 1.15), (0.02, 0.7, 0.45), M_dark)
    glass_room(XC + 0.05, 1.8, -2.3, YC - 0.03, zt)
    box("mtab", (0.4, -1.45, zt + 0.38), (1.4, 0.5, 0.035), M_bwood)
    for k in range(3):
        chair(-0.1 + k * 0.5, -1.85, zt, -1, M_white, 0.7); chair(-0.1 + k * 0.5, -1.05, zt, 1, M_white, 0.7)
    box("mscr", (0.4, YC - 0.04, zt + 1.0), (1.0, 0.02, 0.5), M_dark); plane("mscrs", (0.4, YC - 0.055, zt + 1.0), 0.95, 0.45, M_conimg)
    plant(1.55, -0.9, zt, 0.9, True)
    desk_row(-0.6, 3.6, -3.3, zt)
    desk_row(-0.6, 3.6, -4.65, zt)
    o = box("draft", (2.75, -1.6, zt + 0.62), (1.0, 0.65, 0.025), M_white); o.rotation_euler.x = 0.45
    for dx in (-0.4, 0.4): box("drl", (2.75 + dx, -1.6, zt + 0.3), (0.025, 0.025, 0.6), M_dark)
    shelf(3.9, -0.85, zt)
    raptor(4.9, -2.3, zt, 1.0)
    for dx, dy in [(-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)]:
        box("rfr", (4.9 + dx, -2.3 + dy, zt + 0.6), (0.03, 0.03, 1.2), M_dark)
    ship_model(5.6, -1.4, zt)
    box("dcb", (4.3, -3.6, zt + 0.2), (0.4, 0.4, 0.4), M_dark); box("dcg", (4.3, -3.6, zt + 0.6), (0.38, 0.38, 0.4), M_glass)
    sph("dco", (4.3, -3.6, zt + 0.5), 0.08, _mat("orng", (0.9, 0.35, 0.05), 0.5))
    lounge(5.1, -4.8, zt)
    plant(XC + 0.3, -5.5, zt, 0.8, True); plant(3.9, -5.4, zt, 1.0, True); plant(6.0, -3.2, zt, 0.8)
    bots = [(1.3, -2.65, 5), (2.9, -2.8, 3), (3.9, -3.95, 1), (1.2, -3.95, 0), (2.3, -4.05, 2), (4.4, -4.6, 7)]
elif i == 2:   # ---- Starlink (-21 m) ----
    plane("mapscr", (XC + 0.04, -1.9, zt + 1.05), 2.4, 0.9, M_map, '+X')
    box("mapbz", (XC + 0.03, -1.9, zt + 1.05), (0.02, 2.5, 1.0), M_dark)
    box("statp", (XC + 0.04, -3.6, zt + 0.95), (0.02, 0.8, 0.8), M_dark)
    plane("statps", (XC + 0.055, -3.6, zt + 0.95), 0.75, 0.75, M_listimg, '+X')
    box("carpet", (0.2, -4.6, zt + 0.01), (2.2, 2.0, 0.02), M_purple)
    cyl("ctab2", (0.2, -4.5, zt + 0.3), 0.55, 0.03, M_bwood, 32); cyl("ctab2l", (0.2, -4.5, zt + 0.15), 0.05, 0.3, M_dark, 8)
    for a in range(6): chair(0.2 + 0.8 * _m.cos(a * 1.05), -4.5 + 0.8 * _m.sin(a * 1.05), zt, 1, M_white, 0.7)
    box("hedge", (2.5, YC - 0.25, zt + 0.15), (3.4, 0.3, 0.3), M_hedge)
    for k in range(4):
        o = box("wbd", (1.3 + k * 0.8, -1.25, zt + 0.62), (0.6, 0.02, 0.45), M_white); o.rotation_euler.x = -0.35
        box("wbl", (1.3 + k * 0.8, -1.15, zt + 0.3), (0.02, 0.02, 0.6), M_dark)
    desk_row(1.0, 3.7, -2.4, zt, both=False)
    desk_row(1.4, 3.9, -3.5, zt, both=False)
    shelf(4.6, -0.85, zt, 1.0, 1.0)
    glass_room(4.2, 6.25, -3.5, -1.15, zt, 1.45)
    cyl("srvpad", (5.3, -2.3, zt + 0.03), 0.65, 0.06, M_dark, 40)
    for k in range(3):
        box("srv", (5.15 + k * 0.17, -2.3 + k * 0.1, zt + 0.75), (0.45, 0.45, 1.4), M_rack)
        for q in range(9): box("srvs", (5.15 + k * 0.17 - 0.23, -2.3 + k * 0.1, zt + 0.15 + q * 0.15), (0.01, 0.42, 0.04), M_white)
    for k in range(5): box("vat", (4.5 + k * 0.4, YC - 0.3, zt + 1.62), (0.36, 0.36, 0.2), M_white, 0.03)
    box("crsign", (4.6, -3.52, zt + 1.2), (0.5, 0.02, 0.14), M_white)
    box("bar", (2.6, -4.65, zt + 0.42), (2.8, 0.45, 0.05), M_bwood, 0.01)
    box("barb", (2.6, -4.6, zt + 0.2), (2.7, 0.3, 0.4), M_white)
    for k in range(7): stool(1.4 + k * 0.4, -5.1, zt, M_bwood)
    for k in range(2): box("espm", (2.2 + k * 0.25, -4.55, zt + 0.55), (0.16, 0.16, 0.22), M_dark)
    box("wbw", (3.95, -3.95, zt + 0.7), (0.7, 0.02, 0.5), M_white); box("wbwl", (3.95, -3.95, zt + 0.3), (0.02, 0.02, 0.6), M_dark)
    lounge(4.9, -4.6, zt)
    plant(XC + 0.3, -0.9, zt, 1.1, True); plant(4.6, -5.4, zt, 1.2, True); plant(0.2, -3.2, zt, 0.7, True); plant(3.9, -1.5, zt, 0.7)
    bots = [(3.3, -1.7, 6), (-0.3, -4.2, 4), (0.6, -3.3, 2), (2.8, -2.95, 3), (5.4, -4.0, 0)]
else:   # ---- Lobby (-29 m) ----
    tx = text("SPACEX", (XC + 0.05, -3.0, zt + 1.15), 0.42, M_dark, rot=(_m.pi / 2, 0, _m.pi / 2), extrude=0.01)
    box("nlscr", (XC + 0.04, -1.25, zt + 1.1), (0.02, 0.9, 0.85), M_dark)
    plane("nlscrs", (XC + 0.055, -1.25, zt + 1.1), 0.85, 0.8, M_listimg, '+X')
    box("recep", (0.6, -2.55, zt + 0.25), (2.0, 0.42, 0.5), M_white, 0.03)
    box("recept", (0.6, -2.55, zt + 0.51), (2.05, 0.46, 0.03), M_bwood)
    for k in range(2): box("rmon", (0.2 + k * 0.7, -2.45, zt + 0.66), (0.24, 0.02, 0.16), M_dark)
    box("cbar", (2.8, -1.1, zt + 0.45), (2.6, 0.45, 0.05), M_bwood, 0.01)
    box("cbarb", (2.8, -1.05, zt + 0.22), (2.5, 0.3, 0.44), M_white)
    for k in range(6): stool(1.8 + k * 0.4, -1.55, zt, M_bwood)
    shelf(2.8, YC - 0.2, zt + 0.5, 2.2, 0.9)
    box("menu", (4.3, YC - 0.03, zt + 1.2), (0.6, 0.02, 0.4), M_dark)
    # dragon capsule under a black truss gantry, ring decal on the floor
    CXc, CYc = 2.9, -3.3
    bpy.ops.mesh.primitive_torus_add(major_radius=1.45, minor_radius=0.02, location=(CXc, CYc, zt + 0.012), major_segments=72)
    _t = bpy.context.object; _t.scale.z = 0.2; _t.data.materials.append(M_dark)
    cyl("ringd", (CXc, CYc, zt + 0.008), 0.55, 0.01, M_dark, 48)
    cone("dragon", (CXc, CYc, zt + 0.45), 0.42, 0.22, 0.7, M_white, 40)
    cyl("dragt", (CXc, CYc, zt + 0.86), 0.2, 0.12, M_white, 32)
    cyl("dragh", (CXc, CYc, zt + 0.09), 0.43, 0.06, M_dark, 40)
    for a in range(8):
        sph("dwin", (CXc + 0.33 * _m.cos(a * 0.785), CYc + 0.33 * _m.sin(a * 0.785), zt + 0.4 + 0.15 * (a % 2)), 0.05, M_dark)
    for (px, py) in [(CXc - 1.0, CYc - 0.6), (CXc + 1.0, CYc + 0.6)]:
        box("gpost", (px, py, zt + 0.7), (0.08, 0.08, 1.4), M_dark)
    o = box("gbeam", (CXc, CYc, zt + 1.4), (2.4, 0.09, 0.09), M_dark); o.rotation_euler.z = _m.atan2(1.2, 2.0)
    for (px, py) in [(CXc - 0.9, CYc + 0.4), (CXc + 0.9, CYc - 0.5)]:
        cyl("ltab", (px, py, zt + 0.36), 0.2, 0.03, M_white, 20); cyl("ltabl", (px, py, zt + 0.18), 0.03, 0.36, M_white, 8)
        for a in range(2): stool(px + 0.35 * _m.cos(a * 3.1 + 0.6), py + 0.35 * _m.sin(a * 3.1 + 0.6), zt, M_bwood)
    for k in range(3): raptor(4.5 + k * 0.75, -1.4 - k * 0.45, zt, 1.0)
    stanchions([(4.1, -2.4), (4.9, -2.85), (5.7, -3.3)], zt)
    box("dbench", (5.2, -3.6, zt + 0.2), (1.0, 0.3, 0.04), M_bwood)
    stanchions([(0.0, -3.4), (0.6, -3.7), (1.2, -4.0)], zt)
    box("kcol", (1.0, -4.55, zt + 0.45), (0.2, 0.2, 0.9), M_dark)
    box("smat", (1.7, -5.25, zt + 0.01), (1.9, 0.6, 0.012), M_dark)
    tx2 = text("SPACEX", (1.7, -5.25, zt + 0.022), 0.22, M_white, extrude=0.0)
    lounge(3.3, -5.0, zt)
    for (px, py) in [(-0.3, -4.3), (0.6, -5.3)]:
        box("larm", (px, py, zt + 0.13), (0.3, 0.3, 0.24), M_arm, 0.03)
    cyl("lctab", (0.1, -4.8, zt + 0.2), 0.2, 0.03, M_bwood, 20)
    box("parch", (5.4, -4.9, zt + 0.55), (0.9, 0.12, 1.1), M_white)
    box("parchi", (5.4, -4.9, zt + 0.5), (0.65, 0.14, 0.85), M_dark)
    o = box("grate", (4.6, -4.3, zt + 0.35), (0.4, 0.06, 0.4), M_frame)
    for p in [(XC + 0.35, -1.9, 1.1), (3.9, -0.95, 1.3), (4.4, -2.0, 1.0), (1.8, -4.5, 1.0), (4.3, -5.5, 1.2), (5.9, -4.0, 0.9), (0.3, -1.0, 0.9)]:
        plant(p[0], p[1], zt, p[2], True)
    bots = [(2.1, -3.5, 1), (2.9, -2.6, 4), (3.6, -3.1, 7), (3.4, -4.2, 2), (0.6, -2.0, 6), (2.6, -1.4, 3)]
