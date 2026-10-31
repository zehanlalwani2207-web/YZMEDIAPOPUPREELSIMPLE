# Word-timed transcript of each SOURCE clip (Whisper, model loaded once, 8s chunks every 7s).
#   python tx.py <config.json>            -> work/words.json + work/transcript.txt (source-clip times)
#   python tx.py <config.json> --master   -> work/transcript_master.txt (words that survive the cuts, on master time)
import json, os, subprocess, sys
from common import load, to_master

C, P = load(sys.argv[1])
words_path = os.path.join(P, "work", "words.json")

if "--master" in sys.argv:
    words = json.load(open(words_path, encoding="utf-8"))
    lines = []
    for w in words:
        m = to_master(C, w["clip"], w["start"])
        if m is not None:
            lines.append(f"{m:6.2f} {w['word']}")
    open(os.path.join(P, "work", "transcript_master.txt"), "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines))
    sys.exit()

import torch, whisper
cuda = torch.cuda.is_available()
model_name = C.get("whisper_model") or ("large-v3" if cuda else "small")
model = whisper.load_model(model_name, device="cuda" if cuda else "cpu")
print(f"whisper {model_name} on {'GPU' if cuda else 'CPU'}", file=sys.stderr)
prompt = C.get("whisper_prompt", f"{C.get('shop', '')}, Hinglish, shop, collection, sizes, price.")

words, out = [], []
for ci, c in enumerate(C["clips"]):
    wav = os.path.join(P, "work", f"src{ci}.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c["path"], "-map", "0:a:0", "-ac", "1", "-ar", "16000", wav], check=True)
    audio = whisper.load_audio(wav)
    sr, step, win = 16000, 7.0, 8.0
    dur, t, last = len(audio) / sr, 0.0, -1.0
    out.append(f"== clip {ci}: {os.path.basename(c['path'])} ({dur:.1f}s)")
    while t < dur:
        r = model.transcribe(audio[int(t * sr):int((t + win) * sr)], language=C["language"], word_timestamps=True,
                             fp16=cuda, initial_prompt=prompt)
        for s in r["segments"]:
            for w in s.get("words", []):
                st = t + w["start"]
                if st <= last + 0.05:
                    continue
                last = st
                words.append({"clip": ci, "start": round(st, 2), "end": round(t + w["end"], 2), "word": w["word"].strip()})
                out.append(f"{st:6.2f} {t + w['end']:6.2f} {w['word'].strip()}")
        t += step
json.dump(words, open(words_path, "w", encoding="utf-8"), ensure_ascii=False)
open(os.path.join(P, "work", "transcript.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
