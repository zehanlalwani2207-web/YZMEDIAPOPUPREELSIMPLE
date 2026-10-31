# Head-top y every 0.5s from the cutout alpha (first solid row in the centre 60% of the width) -> work/heads.json.
# usage: python heads.py <config.json>
import json, os, subprocess, sys
import numpy as np
from common import load

C, P = load(sys.argv[1])
W, H = 270, 480
raw = subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", os.path.join(P, "hf", "assets", "cutout.webm"),
                      "-vf", f"fps=2,scale={W}:{H},format=yuva420p,alphaextract", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                     capture_output=True).stdout
out = []
for k in range(len(raw) // (W * H)):
    a = np.frombuffer(raw, np.uint8, W * H, k * W * H).reshape(H, W)[:, int(W * .2):int(W * .8)]
    rows = np.where((a > 128).sum(1) > 6)[0]
    out.append([k * 0.5, int(rows[0] * 4) if len(rows) else None])
json.dump(out, open(os.path.join(P, "work", "heads.json"), "w"))
print(" ".join(f"{t:.0f}:{y}" for t, y in out[::2]))
