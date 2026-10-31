# Shared helpers: load a reel's config.json, project paths, ffprobe, and source -> master time mapping.
import json, os, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(cfg_path):
    cfg_path = os.path.abspath(cfg_path)
    with open(cfg_path, encoding="utf-8") as f:
        C = json.load(f)
    P = os.path.dirname(cfg_path)
    for d in ("work", "review", "export", "hf/assets/fonts", "hf/renders"):
        os.makedirs(os.path.join(P, d), exist_ok=True)
    C.setdefault("name", os.path.basename(P))
    C.setdefault("fps", 30)
    C.setdefault("language", "hi")
    return C, P


def save(C, P):
    with open(os.path.join(P, "config.json"), "w", encoding="utf-8") as f:
        json.dump(C, f, ensure_ascii=False, indent=2)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,color_transfer",
                          "-of", "json", path], capture_output=True, text=True).stdout
    j = json.loads(out)
    v = next((s for s in j["streams"] if s.get("codec_type") == "video"), {})
    return {"duration": float(j["format"]["duration"]),
            "hdr": v.get("color_transfer") in ("arib-std-b67", "smpte2084"),
            "pq": v.get("color_transfer") == "smpte2084",
            "has_audio": any(s.get("codec_type") == "audio" for s in j["streams"])}


def segments(C):
    """Clip segments on the master timeline: [(clip_index, in, out, speed, master_start)]."""
    segs, t = [], 0.0
    for i, c in enumerate(C["clips"]):
        for s in c.get("segments") or [{"in": c.get("in", 0), "out": c.get("out"), "speed": c.get("speed", 1)}]:
            out = s["out"] if s.get("out") is not None else probe(c["path"])["duration"]
            sp = s.get("speed", 1)
            segs.append((i, s["in"], out, sp, t))
            t += (out - s["in"]) / sp
    return segs, t


def to_master(C, clip_index, t):
    """Source-clip time -> master time, or None if that moment was cut."""
    for i, a, b, sp, m in segments(C)[0]:
        if i == clip_index and a <= t <= b:
            return m + (t - a) / sp
    return None


def run(cmd):
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit(f"command failed: {' '.join(cmd[:6])} ...")
