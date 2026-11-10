import bpy, json, sys
sc = bpy.context.scene
d = {"scene": sc.name, "frames": [sc.frame_start, sc.frame_end], "fps": sc.render.fps,
     "engine": sc.render.engine, "res": [sc.render.resolution_x, sc.render.resolution_y],
     "view_transform": sc.view_settings.view_transform, "look": sc.view_settings.look,
     "exposure": sc.view_settings.exposure, "camera": sc.camera.name if sc.camera else None,
     "markers": [(m.name, m.frame, m.camera.name if m.camera else None) for m in sc.timeline_markers],
     "use_nodes": sc.use_nodes}
w = sc.world
if w:
    d["world"] = {"name": w.name, "nodes": [(n.type, n.name) for n in w.node_tree.nodes] if w.use_nodes else None}
    if w.use_nodes:
        for n in w.node_tree.nodes:
            if n.type == "BACKGROUND":
                d["world"]["bg"] = [list(n.inputs[0].default_value), n.inputs[1].default_value]
def anim(o):
    a = o.animation_data
    if not a or not a.action: return None
    out = {}
    for fc in a.action.fcurves:
        kp = fc.keyframe_points
        out[f"{fc.data_path}[{fc.array_index}]"] = [(round(k.co[0],1), round(k.co[1],3)) for k in kp][:40] + ([f"...{len(kp)}"] if len(kp) > 40 else [])
    return out
cols = {}
def walk(c, depth=0):
    cols[c.name] = {"objects": len(c.objects), "children": [x.name for x in c.children], "hide_render": c.hide_render}
    for x in c.children: walk(x, depth+1)
walk(sc.collection)
d["collections"] = cols
objs = []
for o in bpy.data.objects:
    e = {"n": o.name, "t": o.type, "p": o.parent.name if o.parent else None,
         "col": [c.name for c in o.users_collection], "loc": [round(v,2) for v in o.location],
         "hide_render": o.hide_render}
    an = anim(o)
    if an: e["anim"] = an
    if o.type == "CAMERA":
        cd = o.data
        e["cam"] = {"type": cd.type, "lens": cd.lens, "ortho": cd.ortho_scale, "rot": [round(v,3) for v in o.rotation_euler],
                    "clip": [cd.clip_start, cd.clip_end], "data_anim": anim(cd) if cd.animation_data else None}
    if o.type == "LIGHT":
        e["light"] = {"type": o.data.type, "energy": o.data.energy, "color": list(o.data.color)}
    if o.type == "FONT":
        e["text"] = o.data.body[:80]
    objs.append(e)
d["n_objects"] = len(objs)
d["objects_animated_or_special"] = [e for e in objs if "anim" in e or e["t"] in ("CAMERA","LIGHT","FONT","EMPTY")]
d["objects_by_type"] = {}
for e in objs: d["objects_by_type"][e["t"]] = d["objects_by_type"].get(e["t"],0)+1
d["object_names"] = [ (e["n"], e["t"], e["col"][0] if e["col"] else None) for e in objs]
d["materials"] = [(m.name, m.users) for m in bpy.data.materials]
d["images"] = [(i.name, i.filepath) for i in bpy.data.images]
d["texts"] = [t.name for t in bpy.data.texts]
d["drivers_handlers"] = [str(h) for h in bpy.app.handlers.frame_change_pre]
json.dump(d, open(sys.argv[-1], "w"), indent=1, default=str)
print("ok", d["n_objects"])
