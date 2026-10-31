# Master video + soft voice from config.json: per-segment trims/speeds, HDR auto-tonemap, grade,
# 1080x1920 crop-fill, concat -> hf/assets/main.mp4 (with the soft voice as its audio) + work/voice.wav.
# usage: python prep.py <project>/config.json
import os, sys
from common import load, probe, segments, run

C, P = load(sys.argv[1])
fps = C["fps"]
# bright, clean, natural grade; override with config "grade" (ffmpeg filter chain) per reel
G = C.get("grade", "eq=brightness=0.02:contrast=1.04:saturation=1.10:gamma=1.05,vibrance=intensity=0.10,unsharp=5:5:0.4")
# soft voice chain: light denoise, presence dip, de-esser, roll-off (heavy denoise sounds harsh)
VC = C.get("voice_chain", "highpass=f=85,afftdn=nr=12:nf=-35:tn=1,equalizer=f=3300:t=o:w=1.2:g=-4.5,"
           "equalizer=f=6500:t=o:w=1:g=-2.5,deesser=i=0.45:m=0.5:f=0.5,treble=g=-2:f=9000,"
           "equalizer=f=220:t=o:w=1:g=1.5,acompressor=threshold=0.12:ratio=2.5:attack=15:release=200:makeup=1.5")


def tonemap(pq):
    npl = 100 if pq else 203
    return (f"zscale=t=linear:npl={npl},format=gbrpf32le,zscale=p=bt709,tonemap=mobius:param=0.4:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def atempo(sp):
    chain, s = [], sp
    while s > 2.0:
        chain.append("atempo=2.0"); s /= 2.0
    while s < 0.5:
        chain.append("atempo=0.5"); s /= 0.5
    chain.append(f"atempo={s:.4f}")
    return ",".join(chain)


segs, total = segments(C)
info = [probe(c["path"]) for c in C["clips"]]
inputs, fc, cat = [], [], ""
for i, c in enumerate(C["clips"]):
    inputs += ["-i", c["path"]]
for k, (i, a, b, sp, _) in enumerate(segs):
    tm = tonemap(info[i]["pq"]) + "," if info[i]["hdr"] else ""
    fc.append(f"[{i}:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},{tm}{G},"
              f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps={fps},format=yuv420p[v{k}]")
    if info[i]["has_audio"]:
        fc.append(f"[{i}:a:0]atrim={a}:{b},asetpts=PTS-STARTPTS,{atempo(sp)},aresample=48000[a{k}]")
    else:
        fc.append(f"anullsrc=r=48000:cl=mono,atrim=0:{(b - a) / sp}[a{k}]")
    cat += f"[v{k}][a{k}]"
fc.append(f"{cat}concat=n={len(segs)}:v=1:a=1[v][ar]")
fc.append(f"[ar]{VC},loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,asplit[a][aw]")

main = os.path.join(P, "hf", "assets", "main.mp4")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", main,
     "-map", "[aw]", "-c:a", "pcm_s16le", os.path.join(P, "work", "voice.wav")])
print(f"master {probe(main)['duration']:.2f}s ({len(segs)} segments, HDR clips: {sum(x['hdr'] for x in info)})")
