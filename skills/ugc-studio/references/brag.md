# /brag — launch videos from a website or an app (MIT, github.com/latent-spaces/brag)

/brag reads a project (its code) or a live website and turns it into a short, polished, shareable launch video
built with HyperFrames: story, motion, music, poster frame and share caption. On Claude Opus 5.5 it hands the
run to **/brag-slim**, where the model builds the whole video itself with the tools on the machine.
DreamNova used it on 05/10/2026 for its studio promo videos (voice agent, sites & films, AI assessment).

## When to use it (vs the UGC rails)
- The thing to show is a **website, landing page, app or new feature** → /brag.
- The thing to show is a **person** (trust, authority, story) → UGC rails 1–3, or Rail 5 icons reel.
- Best combo for a business: **UGC hook (person, 3 s) → hard cut → /brag reel of the site (15 s) → person CTA (3 s)**,
  joined with `ugc.py concat` and captioned with `ugc.py captions/render`.

## Run it
```bash
/brag                                         # inside the project folder (reads the code)
/brag https://leeyamedia.com --format vertical --tone polished
/brag https://site.com --tone cinematic --duration 20 --title "LeeyaMedia"
/brag-slim https://site.com make it feel like a quiet luxury magazine ad   # freeform direction works
```
Options: `--format landscape|vertical|square` (1920×1080 / 1080×1920 / 1080×1080, 30 fps) · `--duration` (15–25 s
sweet spot) · `--tone` · `--title` · `--no-music` · `--no-sfx` · `--voice` (narration, full /brag only).
Say "use the full brag" to force the full workflow on Opus 5.5.

## Tones
| Tone | Feel | Use for |
|---|---|---|
| `polished` | serious, elegant, long holds, soft fades | premium services, Leeya, experts |
| `default` | punchy, playful, clean | most launches |
| `app-store` | clean feature cards, smooth slides | apps, SaaS features |
| `cinematic` | trailer scale, big type, dramatic wipes | big announcements |
| `yc-parody` | deadpan startup launch | playful founders |
| `deadpan` | calm, dry, lots of space | humour that stays classy |
| `chaotic` | fast, loud, all caps | youth / gaming / memes |

## Its creative laws (same spirit as ours)
Hook in the first 2 s · 15–25 s · show the REAL product (its own UI, copy, images — no abstract filler) ·
specific to this project (no "streamline your workflow") · readable (≈0.3 s per word on screen, fast in then hold) ·
every frozen frame postable · humour only from the project's own absurdity.
Shape: hook (2–3 s) → reveal (2–4 s) → 2–3 highlights → punchline/outro (2–4 s).

## Outputs (`brag-output/` or `brag-output-<timestamp>/`)
`brag.mp4` (poster baked in as frame 0 so every platform thumbnail is good) · `brag.jpg` (poster) ·
`share-copy.txt` (1–3 postable sentences) · `brag-plan.md` (angle + storyboard) · `work/` (intermediates).

## DreamNova rules on top
- Only the site's REAL text — no invented testimonials, numbers or client logos (if the site has none, the video has none).
- Feed the business profile as direction: colours, font, tone, words to avoid (e.g. Leeya: white, quiet luxury,
  Open Sans/Heebo, red as one accent, no "viral/hacks").
- Hebrew site: brag captures the real RTL page; still zoom-check every Hebrew line (`hebrew.md` §5).
- Look at 5 key frames + run `ugc.py qc brag-output/brag.mp4` before delivering. Never post it yourself.
- Needs Node + `npx hyperframes doctor` OK (`setup.md` §5–§6).
