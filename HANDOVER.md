# HANDOVER — DreamNova UGC Studio (for Codex / next agent)

Started 2026-10-08 ~20:30 Jerusalem, Claude Opus 5.5 session. Goal (David): one complete,
automatic UGC/promo video method that Leeya's Opus 5.5 can run (ElevenLabs and/or Gemini),
including /brag, adapted to her business and usable for any business (David's too).

## Where everything is
- Project root: `~/Projects/Active/dreamnova-ugc-studio/`
- The skill (what her Opus loads): `skills/ugc-studio/SKILL.md` + `references/` + `profiles/` + `scripts/ugc.py`
- Install for Claude Code: `install.sh` · for claude.ai: zip of `skills/ugc-studio/`

## Status (update this block as you go)
- [x] scripts/ugc.py (voices, tts, transcribe, captions, render, concat, qc, selftest) — stdlib + ffmpeg + curl, Python 3.9 OK
- [x] selftest PASS on this Mac: logic + Hebrew RTL render gate (word widths [95,64,164,109])
- [x] E2E on Leeya's real short_06_he (no API cost): captions tiktok + box → render → qc 8/8 PASS; mixed HE/Latin
      lines (SEO, ה-AI, ChatGPT, GEO) zoom-checked at native resolution = correct RTL order
- [x] scripts/icons_reel.py ("wow" reel she liked, generalised from build_he.py, JSON spec, icons fetched from
      Fluent/simple-icons/lobe CDNs) → hyperframes check PASS → render → qc 8/8 PASS → contact sheet looked at
- [x] SKILL.md (5 rails), references (method-ugc, engines, setup, hebrew, qc, brag, business-brief), profiles (leeyamedia, dreamnova-studio), README, install.sh, MIT
- [x] GitHub PUBLIC https://github.com/CodeNoLimits/dreamnova-ugc-studio + release v1.0.0 (ugc-studio.zip, pack zip). Secret/confidential grep = clean
- [x] WhatsApp 5/5 (Leeya 91564458151954@lid: zip + demo · David: zip + pack + demo) — David's explicit GO 08/10 20:45

## Not done / for Codex to test & polish
- install.sh not executed on a clean Mac (only `bash -n`); run it on Leeya's Mac or a fresh user.
- `ugc.py tts`, `transcribe`, `voices` not called live (to avoid spending; key `dn-secret ELEVENLABS_KEY` exists). Test with 1 short line.
- ElevenLabs connector rails (Aurora/OmniHuman/Kling/Omni) documented from live model guides, not run (credits).
- icons_reel: GSAP "target not found" warnings at render (harmless, inherited from build_he.py) — find the empty selector.
- Leeya's cloned voice_id: fill `profiles/leeyamedia.md` after she clones her voice.

## Sources used (do not rebuild, reuse)
- /brag (MIT, latent-spaces/brag) — on Opus 5.5 it hands off to brag-slim. Install: `npx skills add https://github.com/latent-spaces/brag --skill brag -g -y`
- Leeya Hebrew pipeline proven 06/10: `~/Projects/Active/leeya-media-promo-videos/build_he.py` (Scribe > Whisper for Hebrew)
- RTL rules: skill `hebrew-video-rtl-libass` (Encoding=-1, Hebrew-first lines, never burn unverified Whisper Hebrew)
- UGC performance rules: skill `woodeex-ugc-expressif` (generic parts only — no Woodeex data in Leeya's pack)
- UGC formats + vertical safe zones: `~/.claude/skills/ad-creative/references/short-form-video-specs.md`
- ElevenLabs connector (ElevenCreative) model guides read live 2026-10-08: creatify-aurora, omnihuman, kling-3-pro, gemini-omni-1.1-flash, eleven_v3
- Leeya taste: skills `lia-criteria`, `lia-interview`, memory `reference_leeya_brand_bible_v2`

## Hard rules kept
- No secrets in the pack. Keys live in macOS Keychain (`ELEVENLABS_API_KEY`), typed by the human in Terminal.
- Nothing confidential about Leeya (no Orian, no ViraLeeya/NovaReels, no family info) — the repo may be public.
- Never message Leeya directly; David forwards the link.
- Leeya is David's wife: never billed, never in a sales funnel.
