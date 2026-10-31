# Writes <project>/hf/index.html (HyperFrames + GSAP) from config.json: keyword pop-ups behind the speaker's head
# (cutout layered on top), address pill, front CTA card. Pop tops follow the head via work/heads.json.
# usage: python build_hf.py <config.json>
import html, json, os, shutil, sys
from common import SKILL, load, probe

C, P = load(sys.argv[1])
D = round(probe(os.path.join(P, "hf", "assets", "main.mp4"))["duration"] - 0.03, 2)
heads = json.load(open(os.path.join(P, "work", "heads.json")))

# ---- theme (defaults = the original look: Playfair + Montserrat, 6-colour palette; vary per reel via config "theme") ----
T = {
    "palette": ["#FF2E86", "#7C4DFF", "#0B9884", "#F5A300", "#EE4E16", "#1E88F0"],
    "fonts": [
        {"family": "Playfair", "file": "playfair-display-latin-900-normal.woff2", "weight": 900},
        {"family": "Playfair", "file": "playfair-display-latin-700-italic.woff2", "weight": 700, "style": "italic"},
        {"family": "Montserrat", "file": "montserrat-latin-800-normal.woff2", "weight": 800},
        {"family": "Montserrat", "file": "montserrat-latin-600-normal.woff2", "weight": 600},
    ],
    "giant_family": "Playfair", "giant_weight": 900, "giant_width": 0.74,  # avg cap width in em, for auto-fit
    "accent_family": "Playfair",                                           # italic line on the CTA card
    "kicker_family": "Montserrat", "kicker_weight": 800, "kicker_radius": 60,
    "kicker_style": "pill",        # pill | tag | outline | underline
    "anim": "pop",                 # pop | slide | drop
    "shadow": "3d",                # 3d (coloured drop) | glow
    "extra_css": "",
}
T.update(C.get("theme", {}))
PAL = T["palette"]

for f in T["fonts"]:  # fonts come from the skill's assets/fonts or the project's hf/assets/fonts
    dst = os.path.join(P, "hf", "assets", "fonts", f["file"])
    src = os.path.join(SKILL, "assets", "fonts", f["file"])
    if not os.path.exists(dst):
        if not os.path.exists(src):
            sys.exit(f"font file missing: {f['file']} (put it in {os.path.dirname(dst)})")
        shutil.copy(src, dst)


def head_top(t0, t1):
    ys = [y for t, y in heads if t0 <= t <= t1 and y is not None]
    return sorted(ys)[len(ys) // 2] if ys else 600  # median: raised arms read as a high 'head'


def split_emoji(s):
    items, cur = [], ""
    for ch in s:
        if cur and (ch in "️‍" or cur[-1] == "‍" or 0x1F3FB <= ord(ch) <= 0x1F3FF):
            cur += ch
        else:
            if cur:
                items.append(cur)
            cur = ch
    return items + ([cur] if cur else [])


esc = html.escape
pops, js = [], []
for i, p in enumerate(C.get("pops", [])):
    a, b = p["start"], p["end"]
    c = p.get("color") or PAL[i % len(PAL)]
    k, g = p.get("kicker", ""), p["giant"]
    chips, sw = p.get("chips") or [], p.get("swatches") or []
    emo = split_emoji(p.get("emoji", ""))
    ht = head_top(a, b)
    h = 330 if (chips or sw) else 290
    top = int(min(ht + 70 - h, 760))                       # block bottom tucks ~70px below the head top
    size = min(150, int(960 / (max(len(g), 1) * T["giant_width"])))
    parts = []
    if emo:
        parts.append('<div class="emos">' + "".join(f'<span class="emo" id="e{i}_{j}">{e}</span>' for j, e in enumerate(emo)) + "</div>")
    if k:
        parts.append(f'<div class="kick" id="k{i}" style="--c:{c}">{esc(k)}</div>')
    parts.append(f'<div class="giant" id="g{i}" style="font-size:{size}px;--c:{c}">{esc(g)}</div>')
    if chips:
        parts.append('<div class="row">' + "".join(
            f'<span class="sz" id="x{i}_{j}" style="background:{PAL[(i + j) % len(PAL)]}">{esc(s)}</span>' for j, s in enumerate(chips)) + "</div>")
    elif sw:
        parts.append('<div class="row">' + "".join(
            f'<span class="sw" id="x{i}_{j}" style="background:{col}"></span>' for j, col in enumerate(sw)) + "</div>")
    pops.append(f'<div id="p{i}" style="top:{max(130, top - (150 if emo else 0))}px" class="clip pop" data-start="{a:.2f}" '
                f'data-duration="{b - a:.2f}" data-track-index="{2 + i % 2}"><div class="in" id="i{i}">{"".join(parts)}</div></div>')
    js.append(f"punch({a:.2f},{b:.2f});")
    if k:
        js.append(f'kick("#k{i}",{a + 0.03:.2f});')
    js.append(f'giant("#g{i}",{a + 0.10:.2f});')
    js += [f'emo("#e{i}_{j}",{a + 0.18 + j * 0.12:.2f},{b:.2f});' for j in range(len(emo))]
    js += [f'chip("#x{i}_{j}",{a + 0.35 + j * 0.14:.2f});' for j in range(len(chips) or len(sw))]
    js.append(f'out("#i{i}",{b - 0.17:.2f});')

cta = C.get("cta")
cta_start = cta["start"] if cta else D
pill = C.get("address_pill")
pill_html, js_tail = "", []
if pill:
    ps, pe = pill.get("start", 5.0), pill.get("end") or cta_start
    pill_html = (f'<div id="addr" class="clip" data-start="{ps:.2f}" data-duration="{pe - ps:.2f}" data-track-index="5">'
                 f'<div id="addr_in">{pill["html"]}</div></div>')
    js_tail += [f'tl.fromTo("#addr_in", {{y:80, opacity:0}}, {{y:0, opacity:1, duration:0.5, ease:"back.out(1.8)"}}, {ps + 0.05:.2f});',
                f'tl.to("#addr_in", {{opacity:0, duration:0.2}}, {pe - 0.22:.2f});']
cta_html = ""
if cta:
    cs = cta["start"]
    cta_html = (f'<div id="cta" class="clip" data-start="{cs:.2f}" data-duration="{D - cs:.2f}" data-track-index="6">'
                f'<div class="v" id="c_v">{esc(cta.get("line", ""))}</div><div class="n" id="c_n">{esc(cta["name"])}</div>'
                f'<div class="s" id="c_s">{esc(cta.get("sub", ""))}</div></div>')
    js_tail += [f'tl.fromTo("#cta", {{y:220, opacity:0, scale:0.9}}, {{y:0, opacity:1, scale:1, duration:0.55, ease:"back.out(1.6)"}}, {cs:.2f});',
                f'tl.fromTo("#c_v", {{y:30, opacity:0}}, {{y:0, opacity:1, duration:0.4, ease:"power3.out"}}, {cs + 0.25:.2f});',
                f'tl.fromTo("#c_n", {{scale:1.4, opacity:0}}, {{scale:1, opacity:1, duration:0.45, ease:"power4.out"}}, {cs + 0.4:.2f});',
                f'tl.fromTo("#c_s", {{y:40, opacity:0}}, {{y:0, opacity:1, duration:0.35, ease:"back.out(2)"}}, {cs + 0.7:.2f});',
                f'tl.to("#c_s", {{scale:1.06, duration:0.5, yoyo:true, repeat:3, ease:"sine.inOut"}}, {cs + 1.2:.2f});']

faces = "\n".join(f'@font-face {{ font-family:"{f["family"]}"; src:url("assets/fonts/{f["file"]}") format("woff2"); '
                  f'font-weight:{f.get("weight", 400)}; font-style:{f.get("style", "normal")}; }}' for f in T["fonts"])
emoji_faces = "\n".join(f'@font-face {{ font-family:"{n}"; src:local("{n}"); }}' for n in ("Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji"))
GF, KF, AF = T["giant_family"], T["kicker_family"], T["accent_family"]
shadow = ("0 6px 0 var(--c), 0 10px 0 rgba(0,0,0,.18), 0 0 16px rgba(0,0,0,.45), 0 0 44px rgba(0,0,0,.35)" if T["shadow"] == "3d"
          else "0 0 18px var(--c), 0 0 16px rgba(0,0,0,.5), 0 0 44px rgba(0,0,0,.4)")
kick_css = {
    "pill": f"background:var(--c); color:#fff; border-radius:{T['kicker_radius']}px;",
    "tag": "background:var(--c); color:#fff; border-radius:8px; transform:rotate(-2deg);",
    "outline": "background:rgba(0,0,0,.35); color:#fff; border:4px solid var(--c); border-radius:14px;",
    "underline": "background:none; color:#fff; border-bottom:6px solid var(--c); border-radius:0; box-shadow:none !important; text-shadow:0 2px 12px rgba(0,0,0,.7);",
}[T["kicker_style"]]
giant_from = {"pop": "{scale:1.5, y:20, opacity:0}", "slide": "{x:-120, opacity:0}", "drop": "{y:-120, scale:1.1, opacity:0}"}[T["anim"]]
giant_to = {"pop": "{scale:1, y:0, opacity:1, duration:0.45, ease:\"power4.out\"}",
            "slide": "{x:0, opacity:1, duration:0.5, ease:\"power3.out\"}",
            "drop": "{y:0, scale:1, opacity:1, duration:0.5, ease:\"bounce.out\"}"}[T["anim"]]
P0, P1, P5 = PAL[0], PAL[1 % len(PAL)], PAL[5 % len(PAL)]

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
{faces}
{emoji_faces}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"{KF}", sans-serif; }}
#vwrap {{ position:absolute; inset:0; transform-origin:50% 35%; }}
#vwrap video {{ position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; }}
#cut {{ z-index:3; }}
.vig {{ position:absolute; inset:0; z-index:1; pointer-events:none; background:linear-gradient(180deg, rgba(0,0,0,.28) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 75%, rgba(0,0,0,.35) 100%); }}
.pop {{ position:absolute; left:0; width:1080px; text-align:center; z-index:2; }}
.in {{ display:flex; flex-direction:column; align-items:center; gap:14px; padding:30px 60px 40px;
  background:radial-gradient(ellipse 60% 55% at 50% 58%, rgba(0,0,0,.42) 0%, rgba(0,0,0,.2) 50%, rgba(0,0,0,0) 75%); }}
.giant {{ font:{T["giant_weight"]} 150px/0.95 "{GF}", Georgia, serif; color:#fff; white-space:nowrap; letter-spacing:.01em; text-shadow:{shadow}; }}
.kick {{ font:{T["kicker_weight"]} 40px "{KF}", sans-serif; padding:10px 28px; letter-spacing:.12em; white-space:nowrap;
  box-shadow:0 8px 22px rgba(0,0,0,.28), inset 0 -4px 0 rgba(0,0,0,.15); {kick_css} }}
.emos {{ display:flex; gap:24px; }}
.emo {{ font-family:"Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji", sans-serif; font-size:130px; line-height:1; display:inline-block; filter:drop-shadow(0 10px 18px rgba(0,0,0,.35)); }}
.row {{ display:flex; gap:18px; margin-top:6px; }}
.sz {{ font:{T["kicker_weight"]} 46px "{KF}", sans-serif; color:#fff; min-width:110px; height:110px; padding:0 18px; border-radius:60px; display:inline-flex; align-items:center; justify-content:center; border:5px solid #fff; box-shadow:0 8px 20px rgba(0,0,0,.3); }}
.sw {{ width:96px; height:96px; border-radius:50%; border:6px solid #fff; box-shadow:0 8px 20px rgba(0,0,0,.3); display:inline-block; }}
#addr {{ position:absolute; left:0; width:1080px; top:1690px; z-index:6; display:flex; justify-content:center; }}
#addr div {{ font:600 34px "{KF}", sans-serif; color:#222; background:rgba(255,255,255,.94); padding:14px 34px; border-radius:60px; letter-spacing:.04em;
  box-shadow:0 8px 24px rgba(0,0,0,.25); border-left:10px solid {P0}; border-right:10px solid {P1}; }}
#addr b {{ font-weight:800; color:{P0}; }}
#cta {{ position:absolute; left:60px; right:60px; top:1270px; z-index:7; padding:40px 30px 46px; border-radius:46px; text-align:center;
  background:linear-gradient(135deg, {P0} 0%, {P1} 55%, {P5} 100%); box-shadow:0 20px 50px rgba(0,0,0,.4); border:5px solid rgba(255,255,255,.9); }}
#cta .v {{ font:italic 700 64px "{AF}", serif; color:#FFE9A8; }}
#cta .n {{ font:{T["giant_weight"]} 130px/1 "{GF}", serif; color:#fff; margin:8px 0 18px; text-shadow:0 6px 0 rgba(0,0,0,.18); white-space:nowrap; }}
#cta .s {{ display:inline-block; font:800 40px "{KF}", sans-serif; color:#2a1a4a; background:#fff; padding:14px 32px; border-radius:60px; }}
{T["extra_css"]}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{D}" data-width="1080" data-height="1920">
  <div id="vwrap">
    <video id="v" class="clip" src="assets/main.mp4" data-start="0" data-duration="{D}" data-track-index="0" data-has-audio="true"></video>
    <div class="vig"></div>
{chr(10).join("    " + p for p in pops)}
    <video id="cut" class="clip" src="assets/cutout.webm" muted data-start="0" data-duration="{D}" data-track-index="4" data-layout-allow-occlusion></video>
  </div>
  {pill_html}
  {cta_html}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
const punch = (a, b) => {{
  tl.fromTo("#vwrap", {{scale:1.08}}, {{scale:1.0, duration:0.35, ease:"power3.out", immediateRender:false}}, a);
  tl.fromTo("#vwrap", {{scale:1.0}}, {{scale:1.035, duration:Math.max(0.1, b - a - 0.36), ease:"none", immediateRender:false}}, a + 0.35);
}};
const kick = (s, t) => tl.fromTo(s, {{y:30, scale:0.4, opacity:0}}, {{y:0, scale:1, opacity:1, duration:0.32, ease:"back.out(2.6)"}}, t);
const giant = (s, t) => tl.fromTo(s, {giant_from}, {giant_to}, t);
const chip = (s, t) => tl.fromTo(s, {{y:50, scale:0, opacity:0}}, {{y:0, scale:1, opacity:1, duration:0.32, ease:"back.out(2.4)"}}, t);
const emo = (s, t, end) => {{
  tl.fromTo(s, {{y:90, scale:0, rotation:-25, opacity:0}}, {{y:0, scale:1, rotation:0, opacity:1, duration:0.42, ease:"back.out(2.2)"}}, t);
  const n = Math.max(1, Math.floor((end - t - 0.6) / 0.9));
  tl.to(s, {{y:-14, rotation:6, duration:0.45, yoyo:true, repeat:n * 2 - 1, ease:"sine.inOut"}}, t + 0.45);
}};
const out = (s, t) => tl.to(s, {{opacity:0, scale:0.85, duration:0.16, ease:"power2.in"}}, t);
{chr(10).join(js)}
{chr(10).join(js_tail)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
open(os.path.join(P, "hf", "index.html"), "w", encoding="utf-8").write(page)
if not os.path.exists(os.path.join(P, "hf", "meta.json")):
    json.dump({"id": "hf", "name": C["name"]}, open(os.path.join(P, "hf", "meta.json"), "w"))
print(f"pops: {len(pops)}  duration: {D}s")
