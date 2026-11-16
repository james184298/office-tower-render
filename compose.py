# compose.py FRAMEDIR STEP OUT.mp4 : overlay the source video's 2D UI onto our renders (frames fNNNN.jpg every STEP frames), add source audio
import sys, subprocess, numpy as np, glob, os
from PIL import Image
FD, STEP, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
SRC = '/workspace/work/render/moon/moon_src.mp4'; W, H = 1080, 1350
d = np.load(os.path.join(os.path.dirname(__file__), 'ui/det.npy'))
def smooth(b, k=7):
    b = b.astype(float); pad = np.pad(b, k//2, mode='edge')
    m = np.array([np.median(pad[i:i+k]) for i in range(len(b))]) > 0.5
    out = m.copy()
    for s in (-2, -1, 1, 2): out |= np.roll(m, s)
    return out
card = smooth((d[:, 0] > 0.3) & (d[:, 1] > 0.3)); nav = smooth((d[:, 2] > 0.3) & (d[:, 3] > 0.3))
def rr_mask(w, h, r, feather=1.5):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    dx = np.maximum(np.maximum(r - x, x - (w - 1 - r)), 0); dy = np.maximum(np.maximum(r - y, y - (h - 1 - r)), 0)
    dist = np.sqrt(dx*dx + dy*dy) - r
    return np.clip(0.5 - dist/feather, 0, 1)[..., None]
BOX = {'tl': (24, 22, 318, 78, 26), 'tr': (770, 22, 1058, 78, 26), 'nav': (24, 90, 82, 348, 22),
       'card': (24, 1223, 1057, 1329, 18), 'loc': (406, 1278, 682, 1327, 24)}
MASK = {k: rr_mask(v[2]-v[0], v[3]-v[1], v[4]) for k, v in BOX.items()}
src = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                        '-i', SRC, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', OUT], stdin=subprocess.PIPE)
cur = None; n = 0
while True:
    b = src.stdout.read(W*H*3)
    if len(b) < W*H*3: break
    s = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(float)
    fno = n + 1; key = ((fno - 1)//STEP)*STEP + 1
    fp = os.path.join(FD, 'f%04d.jpg' % key)
    if os.path.exists(fp) and (cur is None or cur[0] != key):
        im = Image.open(fp).convert('RGB')
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
        cur = (key, np.asarray(im).astype(float))
    o = cur[1].copy()
    i = min(n, len(card)-1)
    # title text (white + orange on black sky): lighten blend where the source shows it
    t = s[95:420, 20:330]; R, G, B = t[..., 0], t[..., 1], t[..., 2]
    orange = ((R > 200) & (G > 110) & (G < 200) & (B < 90)).sum()
    if orange > 150:
        o[95:420, 20:330] = np.maximum(o[95:420, 20:330], t)
    # location pill: green dot present
    gd = s[1296:1308, 418:432]
    on = {'tl': True, 'tr': True, 'nav': bool(nav[i]), 'card': bool(card[i]),
          'loc': bool(((gd[..., 1] > 150) & (gd[..., 0] < 120)).sum() > 20) and not card[i]}
    for k, (x0, y0, x1, y1, r) in BOX.items():
        if on[k]:
            m = MASK[k]; o[y0:y1, x0:x1] = o[y0:y1, x0:x1]*(1-m) + s[y0:y1, x0:x1]*m
    enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes()); n += 1
enc.stdin.close(); enc.wait(); print('frames', n, 'card', int(card.sum()), 'nav', int(nav.sum()))
