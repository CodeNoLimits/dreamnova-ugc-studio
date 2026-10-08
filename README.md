# DreamNova UGC Studio

A Claude skill that turns Claude (Opus) into a complete short-video studio: UGC reels, talking-head videos,
faceless ads, website launch videos (/brag) and the "wow" reel with 3D icons and logos popping on the spoken
word — for any business, in Hebrew, English or French, with measured quality checks before delivery.

Engines: **ElevenLabs** (voice, voice clone, AI avatars, AI video, Hebrew transcription) and optionally
**Gemini** (Veo / Nano Banana / Flow). Local finishing with ffmpeg + HyperFrames.

## Install (one time)

**Claude Code / Claude desktop (Code tab), on a Mac** — tell Claude:
> Install the DreamNova UGC Studio: `git clone https://github.com/CodeNoLimits/dreamnova-ugc-studio ~/dreamnova-ugc-studio && bash ~/dreamnova-ugc-studio/install.sh` — then guide me through references/setup.md.

**claude.ai / Claude app (no terminal)** — Settings → Capabilities → Skills → *Upload skill* → `ugc-studio.zip`
(from this repo's Releases or the root folder). Then Settings → Connectors → connect **ElevenLabs**.

## Use

Just ask, in any language: "make me a reel about …", "תעשי לי סרטון על …", "make the wow version with icons",
"brag about my website". Claude asks one short question at a time, shows you hooks to pick, makes the video,
checks it (numbers + its own eyes), and gives you the file and a caption. Nothing is posted without your OK.

## What's inside

```
skills/ugc-studio/
  SKILL.md                    the method (start here)
  references/                 UGC technique · engines & prompts · setup · Hebrew/RTL · QC · /brag · any-business brief
  profiles/                   LeeyaMedia · DreamNova Studio (copy one to add a business)
  scripts/ugc.py              voices · tts · transcribe · captions · render · concat · qc · selftest
  scripts/icons_reel.py       the "wow" icons reel (HyperFrames)
install.sh                    installs the skill, ffmpeg-full, node, /brag, HyperFrames, runs the self-test
```

Keys are never stored in this repo: the ElevenLabs key lives in the macOS Keychain (`ELEVENLABS_API_KEY`).

Credits: /brag by latent-spaces (MIT) · HyperFrames by HeyGen · icons: Fluent Emoji (MIT), simple-icons (CC0),
lobe-icons (MIT). Method by DreamNova Studio.
