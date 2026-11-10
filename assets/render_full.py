"""Render the full Office Tower animation with Eevee (GPU) or Cycles.

Usage (Kaggle T4 / Colab T4):
    blender -b office-tower.blend --python render_full.py -- \
        --out /kaggle/working/frames --engine EEVEE --samples 32
Usage (local test, a few frames):
    blender -b office-tower.blend --python render_full.py -- \
        --out /tmp/frames --engine CYCLES --samples 16 --frames 1-120

Defaults: Eevee, 1920x1280, frames 1-3990 (66.5 s @ 60 fps), PNG sequence.
Encode afterwards with ffmpeg:
    ffmpeg -framerate 60 -i frames/frame_%04d.png -c:v libx264 \
        -pix_fmt yuv420p -crf 18 office-tower-blender.mp4
"""
import argparse
import os
import sys

import bpy

FPS = 60
TOTAL_FRAMES = 3990  # 66.5 s @ 60 fps


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="frames",
                   help="output directory for the PNG sequence")
    p.add_argument("--engine", default="EEVEE", choices=["EEVEE", "CYCLES"],
                   help="render engine (Eevee for GPU, Cycles for CPU)")
    p.add_argument("--samples", type=int, default=32,
                   help="samples per frame (Eevee: TAA samples; Cycles: paths)")
    p.add_argument("--frames", default=f"1-{TOTAL_FRAMES}",
                   help="frame range, e.g. 1-120 or 871-871")
    p.add_argument("--res", default="1920x1280",
                   help="resolution WxH")
    return p.parse_args(argv)


def main():
    args = parse_args()
    sc = bpy.context.scene
    w, h = (int(v) for v in args.res.lower().split("x"))
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    a, b = args.frames.split("-")
    sc.frame_start = int(a)
    sc.frame_end = int(b)
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    os.makedirs(args.out, exist_ok=True)
    sc.render.filepath = os.path.join(args.out, "frame_")

    if args.engine == "EEVEE":
        sc.render.engine = "BLENDER_EEVEE_NEXT"
        ee = sc.eevee
        ee.taa_render_samples = args.samples
        ee.use_bloom = True
        ee.bloom_threshold = 0.8
        ee.bloom_radius = 6.0
        ee.use_gtao = True
        ee.gtao_distance = 0.5
        ee.use_raytracing = False  # keep it fast/deterministic on T4
    else:
        sc.render.engine = "CYCLES"
        cy = sc.cycles
        cy.samples = args.samples
        cy.device = "CPU"
        cy.use_denoising = True
        cy.denoiser = "OPENIMAGEDENOISE"

    n = sc.frame_end - sc.frame_start + 1
    print(f"render_full: engine={args.engine} samples={args.samples} "
          f"res={w}x{h} frames={sc.frame_start}-{sc.frame_end} ({n}) "
          f"out={args.out}")
    bpy.ops.render.render(animation=True)
    print("render_full: done")


if __name__ == "__main__":
    main()
