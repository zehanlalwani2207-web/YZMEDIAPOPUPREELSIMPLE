# Person cutout for the behind-the-head look: rembg u2net_human_seg per frame -> VP9 alpha webm.
# Uses the GPU when onnxruntime-gpu works (~30 ms/frame), else CPU (~1 s/frame; a 60s reel ~25 min).
# usage: python cutout.py <config.json>
import os, subprocess, sys
import numpy as np
from PIL import Image
from common import load

C, P = load(sys.argv[1])
try:
    import onnxruntime
    if hasattr(onnxruntime, "preload_dlls"):
        onnxruntime.preload_dlls()  # loads CUDA/cuDNN DLLs from the nvidia pip wheels when present
except Exception:
    pass
from rembg import new_session, remove

src = os.path.join(P, "hf", "assets", "main.mp4")
dst = os.path.join(P, "hf", "assets", "cutout.webm")
W, H, FPS = 1080, 1920, C["fps"]
sess = new_session("u2net_human_seg", providers=["CUDAExecutionProvider", "CoreMLExecutionProvider", "CPUExecutionProvider"])
print("providers:", sess.inner_session.get_providers()[0], flush=True)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "6M", "-deadline", "realtime", "-cpu-used", "8",
                        "-auto-alt-ref", "0", dst], stdin=subprocess.PIPE)
n, prev = 0, None
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    small = Image.fromarray(rgb).resize((W // 2, H // 2))
    m = np.asarray(remove(small, session=sess, only_mask=True).resize((W, H), Image.BILINEAR), np.float32)
    if prev is not None:  # light temporal smoothing to stop edge flicker
        m = 0.65 * m + 0.35 * prev
    prev = m
    enc.stdin.write(np.dstack([rgb, m.clip(0, 255).astype(np.uint8)]).tobytes())
    n += 1
    if n % 200 == 0:
        print(n, flush=True)
enc.stdin.close(); enc.wait()
print("done", n)
