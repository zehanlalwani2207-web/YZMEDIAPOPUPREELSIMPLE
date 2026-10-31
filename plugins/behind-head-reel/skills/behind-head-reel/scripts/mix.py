# Final audio + delivery: soft voice (work/voice.wav) + optional music bed, ducked and EQ'd so the song's vocals
# don't clash, final -14 LUFS. Writes export/<name>.mp4 (H.264 1080x1920) and review/<name>_540p.mp4.
# usage: python mix.py <config.json> [render.mp4]
import glob, os, subprocess, sys
from common import load, probe, run

C, P = load(sys.argv[1])
renders = sorted(glob.glob(os.path.join(P, "hf", "renders", "*.mp4")), key=os.path.getmtime)
IN = sys.argv[2] if len(sys.argv) > 2 else renders[-1]
D = probe(IN)["duration"]
VOICE = os.path.join(P, "work", "voice.wav")
name = C.get("output_name", C["name"].replace(" ", "_"))
OUT = os.path.join(P, "export", f"{name}.mp4")
M = C.get("music")

if M and M.get("path"):
    fo = max(0.0, D - 1.2)
    fc = (f"[1:a]aresample=48000,equalizer=f=3000:t=o:w=1.5:g=-5,treble=g=-2:f=8000,"
          f"loudnorm=I={M.get('lufs', -27)}:TP=-3:LRA=11,afade=t=in:d=0.4,afade=t=out:st={fo:.2f}:d=1.2[m];"
          "[2:a]aresample=48000,asplit[v][key];"
          "[m][key]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400[md];"
          "[v][md]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.89:level=false,aresample=48000[a]")
    ins = ["-i", IN, "-ss", str(M.get("start", 0)), "-t", f"{D:.3f}", "-i", M["path"], "-i", VOICE]
else:
    fc = "[1:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.89:level=false[a]"
    ins = ["-i", IN, "-i", VOICE]

run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
     "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "256k", "-t", f"{D:.3f}", "-movflags", "+faststart", OUT])
PRE = os.path.join(P, "review", f"{name}_540p.mp4")
run(["ffmpeg", "-v", "error", "-y", "-i", OUT, "-vf", "scale=540:960", "-c:v", "libx264", "-crf", "23", "-preset", "fast",
     "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", PRE])
lufs = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", OUT, "-af", "ebur128", "-f", "null", "-"],
                      capture_output=True, text=True).stderr.split("Integrated loudness:")[-1].split("LUFS")[0].split("I:")[-1].strip()
v = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,pix_fmt,width,height",
                    "-of", "csv=p=0", OUT], capture_output=True, text=True).stdout.strip()
print(f"final:   {OUT}  [{v}]  {D:.2f}s  {lufs} LUFS\npreview: {PRE}")
