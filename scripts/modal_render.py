"""Render office-tower.blend on Modal GPUs in parallel chunks.

Put this file in the folder with office-tower.blend, tex.zip, render_full.py, source.mp4, then:
  pip install modal && modal token new
  modal run modal_render.py::probe     # 1 test frame (871) -> probe_0871.png, ~5 min incl. image build
  modal run modal_render.py::full      # all 3990 frames in 20 parallel chunks -> office-tower-render.mp4
Output matches source.mp4: 1920x1280, 60 fps, 3990 frames, H.264 High yuv420p ~7.4 Mbps, source audio copied.
Re-running full skips frames already rendered. GPU: L4 (set RENDER_GPU=T4 to use T4).
"""
import os
import subprocess
import modal

BL = "blender-4.5.0-linux-x64"
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "wget", "curl", "ca-certificates", "xz-utils", "ffmpeg", "libegl1", "libgl1", "libglvnd0", "libglx0",
        "libxi6", "libxxf86vm1", "libxfixes3", "libxrender1", "libxkbcommon0",
        "libsm6", "libice6", "libx11-6", "libxext6", "libvulkan1", "unzip",
    )
    .run_commands(
        f"cd /opt && (for m in https://download.blender.org/release https://mirrors.ocf.berkeley.edu/blender/release https://mirror.clarkson.edu/blender/release https://ftp.halifax.rwth-aachen.de/blender/release; do "
        f"curl -fL --retry 3 -A 'Mozilla/5.0' -o {BL}.tar.xz $m/Blender4.5/{BL}.tar.xz && break; done)"
        f" && tar -xf {BL}.tar.xz && rm {BL}.tar.xz && ls /opt/{BL}/blender",
        "mkdir -p /usr/share/glvnd/egl_vendor.d && printf '{\"file_format_version\":\"1.0.0\",\"ICD\":{\"library_path\":\"libEGL_nvidia.so.0\"}}' > /usr/share/glvnd/egl_vendor.d/10_nvidia.json",
    )
    .env({"NVIDIA_DRIVER_CAPABILITIES": "all"})
)
vol = modal.Volume.from_name("office-tower", create_if_missing=True)
app = modal.App("office-tower-render", image=image)
GPU = os.environ.get("RENDER_GPU", "L4")


def _prep():
    os.makedirs("/work", exist_ok=True)
    if not os.path.exists("/work/office-tower.blend"):
        subprocess.run("cp /vol/office-tower.blend /vol/render_full.py /work/ && cd /work && unzip -o -q /vol/tex.zip", shell=True, check=True)
        # Blender 4.5 EEVEE Next has no scene-level bloom/gtao props: guard them.
        src = open("/work/render_full.py").read()
        for prop in ["use_bloom", "bloom_threshold", "bloom_radius", "use_gtao", "gtao_distance", "use_raytracing"]:
            src = src.replace(f"        ee.{prop} =", f"        if hasattr(ee, '{prop}'): ee.{prop} =")
        open("/work/render_full.py", "w").write(src)


@app.function(gpu=GPU, volumes={"/vol": vol}, timeout=3600, retries=1)
def render(a: int, b: int, engine: str = "EEVEE", samples: int = 32):
    _prep()
    out = "/vol/frames"
    os.makedirs(out, exist_ok=True)
    missing = [f for f in range(a, b + 1) if not os.path.exists(f"{out}/frame_{f:04d}.png")]
    if not missing:
        return (a, b, "skip", "")
    a2 = missing[0]
    cmd = (f"cd /work && /opt/{BL}/blender -b office-tower.blend --python render_full.py -- "
           f"--out /tmp/fr --engine {engine} --samples {samples} --frames {a2}-{b}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    subprocess.run(f"cp /tmp/fr/*.png {out}/ 2>/dev/null", shell=True)
    vol.commit()
    log = (r.stdout + r.stderr)[-2500:]
    n = len([f for f in range(a, b + 1) if os.path.exists(f"{out}/frame_{f:04d}.png")])
    return (a, b, n, log)


@app.function(gpu=GPU, volumes={"/vol": vol}, timeout=900)
def probe_fn(frame: int = 871, engine: str = "EEVEE"):
    _prep()
    smi = subprocess.run("nvidia-smi --query-gpu=name,driver_version --format=csv", shell=True, capture_output=True, text=True).stdout
    cmd = (f"cd /work && /opt/{BL}/blender -b office-tower.blend --python render_full.py -- "
           f"--out /vol/probe_{engine} --engine {engine} --samples 32 --frames {frame}-{frame}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    vol.commit()
    return smi + "\n" + (r.stdout + r.stderr)[-4000:]


@app.function(volumes={"/vol": vol}, timeout=3600, cpu=8)
def encode():
    cmd = ("cd /vol && ffmpeg -y -framerate 60 -i frames/frame_%04d.png -i source.mp4 "
           "-map 0:v -map 1:a? -c:v libx264 -profile:v high -pix_fmt yuv420p -b:v 7400k -maxrate 9000k -bufsize 15000k "
           "-c:a copy -shortest -movflags +faststart office-tower-render.mp4")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    vol.commit()
    return r.stderr[-1500:]


def _upload():
    names = ["office-tower.blend", "tex.zip", "render_full.py", "source.mp4"]
    for n in names:
        assert os.path.exists(n), f"{n} not found in current folder"
    with vol.batch_upload(force=True) as up:
        for n in names:
            up.put_file(n, f"/{n}")
    print("uploaded:", names)


@app.local_entrypoint()
def probe(frame: int = 871, engine: str = "EEVEE"):
    _upload()
    print(probe_fn.remote(frame, engine))
    with open(f"probe_{frame:04d}.png", "wb") as f:
        for chunk in vol.read_file(f"probe_{engine}/frame_{frame:04d}.png"):
            f.write(chunk)
    print(f"saved probe_{frame:04d}.png - compare it with the same moment in source.mp4")


@app.function(volumes={"/vol": vol}, timeout=1800, cpu=8)
def encode_part(a: int, b: int):
    name = f"seg_{a:04d}_{b:04d}.mp4"
    cmd = (f"cd /vol && ffmpeg -y -framerate 60 -start_number {a} -i frames/frame_%04d.png -frames:v {b-a+1} "
           f"-c:v libx264 -profile:v high -pix_fmt yuv420p -b:v 7400k -maxrate 9000k -bufsize 15000k {name}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    vol.commit()
    return name, r.stderr[-800:]


@app.local_entrypoint()
def part(start: int = 1, end: int = 1000, chunk: int = 100, engine: str = "EEVEE"):
    """Render frames start..end in parallel chunks, then save seg_START_END.mp4 locally."""
    _upload()
    ranges = [(a, min(a + chunk - 1, end)) for a in range(start, end + 1, chunk)]
    bad = 0
    for a, b, n, log in render.starmap([(a, b, engine) for a, b in ranges]):
        print(f"chunk {a}-{b}: {n}")
        if n != "skip" and n < b - a + 1:
            bad += 1
            print(log)
    if bad:
        raise SystemExit(f"{bad} chunks incomplete")
    name, log = encode_part.remote(start, end)
    print(log)
    with open(name, "wb") as f:
        for c in vol.read_file(name):
            f.write(c)
    print("saved", name)


@app.local_entrypoint()
def full(chunk: int = 200, engine: str = "EEVEE", total: int = 3990):
    _upload()
    ranges = [(a, min(a + chunk - 1, total)) for a in range(1, total + 1, chunk)]
    done = 0
    for a, b, n, log in render.starmap([(a, b, engine) for a, b in ranges]):
        print(f"chunk {a}-{b}: {n}")
        if n != "skip" and n < b - a + 1:
            print(log)
    print(encode.remote())
    with open("office-tower-render.mp4", "wb") as f:
        for c in vol.read_file("office-tower-render.mp4"):
            f.write(c)
    print("done: office-tower-render.mp4")
