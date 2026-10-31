---
name: behind-head-reel
description: Turn talking-head clips (shop owner, creator, salesperson speaking to camera) into a 1080x1920 Instagram reel in the "Behind-Head Pop-Up" style - keyword pop-ups with emoji/pictures that appear BEHIND the speaker's head, colourful premium-simple captions, address pill + CTA card, cleaned soft voice with ducked music. Use when the user says /behind-head-reel, asks for "behind the head pop-ups", "pop-up wali reel", or gives talking-head clips to turn into a reel. Asks the user to choose the text style, music and cuts.
---

# Behind-Head Pop-Up Reel

Everything is driven by one `config.json` per reel. The scripts live in `scripts/` next to this file; use the base directory shown when this skill loads as `<SKILL>`. Fonts are in `<SKILL>/assets/fonts/` (SIL OFL), and `<SKILL>/config.example.json` shows the config **format only**: it comes from one clothing-shop reel. Never reuse its pops, names or address; every reel's pop-ups come from that reel's own transcript and that business (a phone-cover shop gets covers, brands, prices, models; a gym gets its own words).

Talk to the user in their language. Many users write Hinglish, so mirror it, using Roman script unless they write Devanagari themselves.

## 0. Setup (first time on a machine)
Run `python <SKILL>/scripts/check_env.py`. It checks ffmpeg (full build with zscale), Python packages (openai-whisper, torch, rembg, onnxruntime), the GPU, Node and the HyperFrames CLI. It prints the fix command for anything missing.
- Ask before installing anything.
- No GPU is fine: everything works on CPU, but the cutout takes ~25 min per minute of video (vs ~2.5 min on an NVIDIA GPU) and Whisper drops to the `small` model.
- On Windows, set `PYTHONIOENCODING=utf-8` when running the scripts.

## 1. Collect inputs
Get:
- the clip paths in order
- the shop/brand name
- on-screen info: address, shop no., phone, offer

Then create the project folder (ask where, or default to `./<Brand> Reel/`) and write `config.json` with `name`, `shop`, `language` (`hi` for Hindi/Hinglish, `en`, ...) and `clips: [{"path", "in": 0, "out": null}]`.

## 2. Look and listen
1. Run `ffprobe` on each clip. HDR (iPhone HLG / PQ) is detected and tone-mapped automatically by prep.py.
2. Make a contact sheet (a frame every 3s, tiled) to see the framing and how much the speaker moves.
3. Run `python <SKILL>/scripts/tx.py config.json`. This writes word timestamps per source clip to `work/transcript.txt`. Re-check unclear windows by re-transcribing them in another language.
4. Show the user the transcript, cleaned up, with timestamps, and list the keywords that will become pop-ups.

## 3. ASK the user: 3 choices, one at a time, with clickable options
**A. Text/caption style:** design 3 fresh options. Each is a `theme` block: font pairing, 6-colour palette, `kicker_style` (pill / tag / outline / underline), `anim` (pop / slide / drop) and `shadow` (3d / glow).
- Render one sample still per option on a real frame of their footage and show the stills before asking. A quick way: build a one-pop test page, or draw the style with ffmpeg/Pillow over a frame.
- One option is the default theme (Playfair Display 900 giant with a coloured 3D shadow, Montserrat pills, pink/violet/teal/amber/coral/blue).
- For other fonts, download woff2 from `https://cdn.jsdelivr.net/npm/@fontsource/<font>@5.1.0/files/<font>-latin-<weight>-normal.woff2` into `<project>/hf/assets/fonts/` and list them in `theme.fonts`. Set `giant_width` to the font's average caps width in em: about 0.74 for Playfair, 0.45 for condensed fonts like League Gothic or Anton, about 0.68 for Montserrat.

**B. Music:** their own song file (ask for the path), or 3 suggestions that fit the vibe (royalty-free sources such as Pixabay Music if it's for a business). Never reuse a track from an earlier reel. Pick a strong start point by looking at energy and tell them, so they can move it. Set `music: {"path", "start"}`, or `null` for voice only.

**C. Cuts:** propose 2–3 plans and name the exact lines each one removes:
- (a) trim only the dead air at the start and end
- (b) also cut bloopers, repeats, camera/crew instructions ("cut kar do", "stop it here") and weak lines
- (c) tight: speed up walking/no-talk stretches 2–3x and keep only the strongest lines

The user may answer in their own words (e.g. "cut before the one-piece line" = end that clip right before that line). Find cut points on a silence: compute short-window RMS around the word boundary and cut in the quiet gap. Write these into `clips[].in/out`, or use `clips[].segments: [{"in","out","speed"}]` for several pieces or speed-ups of one clip.

## 4. Build
1. `python prep.py config.json` → `hf/assets/main.mp4` (graded master) + `work/voice.wav` (soft cleaned voice).
   - The default grade is bright, clean and **natural**. Users found saturation of about 1.28 "too poppy", so keep it near 1.08–1.15. Override with `"grade"` (an ffmpeg chain).
   - The default voice chain is deliberately gentle: heavy denoise sounds harsh and metallic. Override with `"voice_chain"`.
   - Show a before/after still of the grade.
2. `python tx.py config.json --master` → transcript on the master timeline. Use these times for pop-ups.
3. Fill `pops` in config.json. Each pop is `{"start","end","kicker","giant","emoji"}`, plus optional `"chips": ["M","L","XL"]`, `"swatches": ["#hex",...]` or `"color"`.
   - **One pop per keyword the speaker says**, starting on the word.
   - Pops run back to back with no long empty gaps.
   - Keep the giant word short (1–3 words, CAPS).
   - The kicker is the lead-in phrase in their language ("HAR TARAH KI", "YEH HAI APNA STORE").
   - Use 1–3 emoji that picture the word. Avoid flag emoji (they render as letters on Windows).
   - Set `address_pill: {"html", "start"}` (pill from a few seconds in until the CTA) and `cta: {"start","line","name","sub"}` (front card while they say the visit/address line, to the end).
4. `python cutout.py config.json`, then `python heads.py config.json`. Pop height follows the speaker's head (median head-top per pop window).
5. `python build_hf.py config.json`, then in `hf/` run `npx hyperframes check`.
   - Fix every ✗: contrast below 3:1 → a darker palette colour; never tween letterSpacing.
   - Then `npx hyperframes render --quiet --sdr -o renders/v1_gfx.mp4 .` (run it in the background; it takes several minutes).
6. **Check the render yourself before showing the user.** Make a contact sheet of ~12 frames and look for:
   - giant text overflowing 1080px
   - unreadable text
   - pops covering the face
   - emoji showing as letters or boxes
   - a cutout glitch

   Fix the problems and re-render.
7. `python mix.py config.json` → `export/<name>.mp4` (H.264 1080x1920, yuv420p, AAC, -14 LUFS) + `review/<name>_540p.mp4`.

## 5. Deliver
Send the **540p preview first** and wait for notes. Apply changes, usually in small rounds (cut X, move music, change a word), re-running only the steps that are affected:
- pops/theme → build_hf + render + mix
- cuts → prep, cutout, heads, then build onwards
- music/voice → mix only

When they approve, deliver the 1080p file from `export/`. If they say "just give the full export", send it without another preview round.

## The style: what stays FIXED
- Keyword pop-ups appear **behind the head**: the cutout of the speaker is layered over the graphics. Each pop has an emoji row (bounce-in, gentle float), a kicker chip, a giant word and optional chips/swatches, with a soft dark radial scrim behind it.
- Colourful: each pop takes the next palette colour.
- A punch-in zoom on every pop plus a slow drift.
- The giant word auto-fits the width.
- An address pill at the bottom, and a CTA card in front at the end.
- No word-by-word subtitles unless asked.

## What VARIES every reel (premium + simple, never an exact copy)
Font pairing, palette, kicker style, entry animation, shadow style, emoji choices and CTA wording. For anything more, put CSS in `theme.extra_css`. Keep it classy, readable and uncluttered.
