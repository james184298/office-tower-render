import bpy, os, sys
sc = bpy.context.scene
frames = [int(x) for x in os.environ.get("PF", "1,240,420,520,700,870,1100,1500,1800,1950,2250,2600,2950,3400,3620,3900").split(",")]
out = os.environ.get("POUT", "../out/prev")
os.makedirs(out, exist_ok=True)
sc.render.resolution_x, sc.render.resolution_y = 480, 320
sc.render.resolution_percentage = 100
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = int(os.environ.get("PS", 16))
sc.render.image_settings.file_format = "JPEG"
for f in frames:
    sc.frame_set(f)
    sc.render.filepath = f"{out}/f{f:04d}.jpg"
    bpy.ops.render.render(write_still=True)
print("preview done", len(frames))
