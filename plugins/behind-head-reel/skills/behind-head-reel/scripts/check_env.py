# Setup check: ffmpeg (zscale/tonemap/libvpx-vp9/deesser), Python packages, GPU for Whisper + rembg, Node + HyperFrames.
# Prints what's missing and the install command for it. usage: python check_env.py
import importlib, shutil, subprocess

ok = True


def bad(msg, fix):
    global ok
    ok = False
    print(f"  ✗ {msg}\n      fix: {fix}")


print("ffmpeg")
if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
    bad("ffmpeg/ffprobe not on PATH", "install a full build: Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`")
else:
    f = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    e = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    for name in ("zscale", "tonemap", "afftdn", "deesser", "sidechaincompress", "loudnorm", "alphaextract"):
        if f" {name} " not in f:
            bad(f"ffmpeg filter '{name}' missing", "use a 'full' ffmpeg build (gyan.dev full / brew ffmpeg)")
    for name in ("libx264", "libvpx-vp9"):
        if name not in e:
            bad(f"ffmpeg encoder {name} missing", "use a 'full' ffmpeg build")
    print("  ok" if ok else "")

print("python packages")
for mod, pip in (("numpy", "numpy"), ("PIL", "pillow"), ("whisper", "openai-whisper"), ("torch", "torch"), ("rembg", "rembg")):
    try:
        importlib.import_module(mod)
    except Exception:
        bad(f"{mod} not importable", f"pip install {pip}")

print("GPU")
try:
    import torch
    print(f"  whisper: {'CUDA ' + torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU (uses the small model; slower, less accurate)'}")
    if not torch.cuda.is_available() and shutil.which("nvidia-smi"):
        print("      tip: NVIDIA GPU found but torch is CPU-only: pip install torch --index-url https://download.pytorch.org/whl/cu128")
except Exception:
    pass
try:
    import onnxruntime as o
    if hasattr(o, "preload_dlls"):
        try:
            o.preload_dlls()
        except Exception:
            pass
    prov = o.get_available_providers()
    gpu = "CUDAExecutionProvider" in prov or "CoreMLExecutionProvider" in prov
    print(f"  cutout:  {'GPU' if gpu else 'CPU only (~25 min per minute of video)'}  {prov}")
    if not gpu and shutil.which("nvidia-smi"):
        print('      tip: pip uninstall -y onnxruntime onnxruntime-gpu && pip install "onnxruntime-gpu[cuda,cudnn]"')
except Exception:
    bad("onnxruntime not importable", 'pip install "onnxruntime-gpu[cuda,cudnn]" (NVIDIA) or pip install onnxruntime')

print("node + hyperframes")
if not shutil.which("node") or not shutil.which("npx"):
    bad("Node.js not found", "install Node 20+ from nodejs.org")
else:
    v = subprocess.run("npx -y hyperframes --version", shell=True, capture_output=True, text=True).stdout.strip()
    print(f"  hyperframes {v}" if v else "")
    if not v:
        bad("hyperframes CLI not runnable", "npm i -g hyperframes   (first render also downloads a headless Chrome)")

print("\nALL GOOD" if ok else "\nfix the ✗ items above, then run this again")
