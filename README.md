# Behind-Head Pop-Up Reel: a Claude Code skill

Turns talking-head clips (a shop owner or creator speaking to camera) into a 1080x1920 Instagram reel:
- keyword **pop-ups appear behind the speaker's head**, with emoji/pictures and colourful, premium-simple captions
- bright, natural colour grade (iPhone HDR handled automatically)
- cleaned, soft voice, with music ducked under it
- address pill + CTA card at the end

Claude asks you to choose the **text style** (3 sample stills on your footage), the **music** and the **cuts**, then sends a 540p preview before the final H.264 export.

## Install (Claude Code)

```
/plugin marketplace add zehanlalwani2207-web/YZMEDIAPOPUPREELSIMPLE
/plugin install behind-head-reel@yz-media-reels
```

Restart Claude Code if the skill doesn't show up. Then type:

```
/behind-head-reel  Shop: <name>, <address> — clips: C:\path\clip1.MOV, C:\path\clip2.MOV
```

On first use Claude runs `scripts/check_env.py` and tells you what to install.

## Requirements
- **ffmpeg** full build (with zscale): Windows `winget install Gyan.FFmpeg`, Mac `brew install ffmpeg`
- **Python 3.10+**: `pip install openai-whisper torch rembg numpy pillow` plus
  - NVIDIA GPU: `pip install "onnxruntime-gpu[cuda,cudnn]"` (don't also install plain `onnxruntime`), and a CUDA build of torch
  - no GPU: `pip install onnxruntime`. It works, but the cutout is slow (~25 min per minute of video).
- **Node.js 20+** for the HyperFrames renderer (`npx hyperframes`, downloaded on first use)

## How it works
`plugins/behind-head-reel/skills/behind-head-reel/` contains `SKILL.md` (the workflow Claude follows), `scripts/` and `assets/fonts/`. Every reel gets its own folder with a `config.json` (see `config.example.json`):

| script | does |
|---|---|
| `tx.py` | Whisper word timestamps per clip (`--master` maps them onto the edited timeline) |
| `prep.py` | trims/speeds, HDR tonemap, grade, 1080x1920, soft voice chain → `hf/assets/main.mp4` |
| `cutout.py` | person cutout (rembg) → alpha video layered over the pop-ups |
| `heads.py` | head position over time, so pop-ups sit just behind the head |
| `build_hf.py` | writes the HyperFrames/GSAP page from `pops`, `theme`, `address_pill`, `cta` |
| `mix.py` | music ducking + EQ, -14 LUFS, final H.264 + 540p preview |

Fonts: SIL Open Font License (see `assets/fonts/FONTS-LICENSE.txt`).
