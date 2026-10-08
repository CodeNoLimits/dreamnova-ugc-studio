# QC — nothing is "done" without these

Run `python3 scripts/ugc.py qc final.mp4 --format vertical [--max-dur 60] [--script spoken.txt --transcribe -l he]`.
It exits 1 if any gate fails and writes `final_qc.json`, `final_sheet.png`, `final_frame0.png`.

## Measured gates (automatic)

| Gate | Pass | Fix |
|---|---|---|
| resolution | 1080×1920 vertical (1920×1080 landscape, 1080×1080 square) | `render --format …` |
| fps | 24–60 | `render` outputs 30 |
| audio_track | present | `render` adds silence if none |
| loudness | −16 LUFS ±2.5 | `render` normalises to −16 |
| true_peak | ≤ −1 dBFS | idem |
| dead_air | no silence ≥ 1.2 s | trim the gap, re-render |
| black_frames / frozen_video | none | cut or replace the clip |
| duration | ≤ `--max-dur` | tighten the script |
| speech_coverage | ≥ 75 % of the script heard back (round-trip transcription) | regenerate the voice; check the missing words list — a missing brand or name fails even at 90 % |

## Look gates (you, with your own eyes — mandatory)

1. Open `final_sheet.png` (one frame every ~2 s) and `final_frame0.png` (the thumbnail most apps show).
2. For every frame check: face natural (eyes, teeth, hands, fingers), no watermark or foreign logo, no AI-made
   text, nothing important under the platform UI (top 220 px, bottom 500 px, 180 px sides), captions readable
   and inside the frame, no flash of a different image at a cut.
3. Zoom the real frame at full size for any caption line that mixes languages, digits or punctuation
   (see `hebrew.md` §5). Thumbnails lie.
4. For AI clips: check the FIRST frame of every clip (flashes from the reference image hide there) and compare
   the person's face side by side with a real photo.
5. Listen check by transcript: captions must match what is said; names and the brand must be correct.

## Report to the person (one line + files)

"`final.mp4` — 9/9 gates PASS, 24 frames checked by eye, speech coverage 96 %, 34 s, 1080×1920." If something
could not be verified (no key for transcription, etc.), say so plainly instead of claiming it.
