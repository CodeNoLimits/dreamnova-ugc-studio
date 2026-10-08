# HANDOVER — DreamNova UGC Studio (for Codex / next agent)

Started 2026-10-08 ~20:30 Jerusalem, Claude Opus 5.5 session. Goal (David): one complete,
automatic UGC/promo video method that Leeya's Opus 5.5 can run (ElevenLabs and/or Gemini),
including /brag, adapted to her business and usable for any business (David's too).

## Where everything is
- Project root: `~/Projects/Active/dreamnova-ugc-studio/`
- The skill (what her Opus loads): `skills/ugc-studio/SKILL.md` + `references/` + `profiles/` + `scripts/ugc.py`
- Install for Claude Code: `install.sh` · for claude.ai: zip of `skills/ugc-studio/`

## Status (update this block as you go)
- [x] scripts/ugc.py written (voices, tts, transcribe, captions, render, concat, qc, selftest) — stdlib + ffmpeg + curl
- [ ] ugc.py selftest run on this Mac (RTL gate)
- [ ] end-to-end proof on Leeya's real short (`~/Projects/02-clients/leeya-katz-v3/public/videos/short_02_he.mp4`,
      Scribe words already in `~/Projects/Active/leeya-media-promo-videos/he_src/short_02_he_scribe.json` — no API cost)
- [ ] SKILL.md, references, profiles, README, install.sh
- [ ] publish (GitHub CodeNoLimits/dreamnova-ugc-studio, no secrets) + zip + report to David

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
