# Setup — do each part once, guide the person step by step

You (Claude) guide; the PERSON clicks, signs up, pays and pastes keys. Never ask them to paste a key or a
password into the chat. One step per message, in their language, with what they should see on screen.

## §1 ElevenLabs account (the main engine)

1. They open **elevenlabs.io** → Sign up (Google sign-in is fine).
2. Plan: open **elevenlabs.io/pricing** together and read the current plans live (prices change). Pick the
   cheapest plan that includes **Instant Voice Cloning + commercial license**. If they want AI avatars and AI
   b-roll every week, those burn far more credits than voice → a mid plan; start small and upgrade only when
   the credit counter actually runs low.
3. Turn on 2-factor authentication in their profile.

## §2 API key (only needed for `scripts/ugc.py` on a Mac)

1. ElevenLabs → profile menu → **API Keys** (Developers) → *Create key*. Name: `claude-ugc`.
   Permissions: Text to Speech, Speech to Text, Voices (read). Copy it.
2. In **Terminal** they type this, press Enter, paste the key when asked, Enter again:
   ```bash
   security add-generic-password -U -a "$USER" -s ELEVENLABS_API_KEY -w
   ```
   The key now lives in the macOS Keychain. `python3 scripts/ugc.py voices` must list voices.
3. If a key ever leaks: delete it on the API Keys page and create a new one (step 1–2 again).

## §3 Connect ElevenLabs to Claude (voices, avatars, AI video, Scribe — no code)

claude.ai (or the Claude app) → **Settings → Connectors** → find **ElevenLabs** → *Connect* → sign in to
ElevenLabs → allow. New chats then have the `creative_*` tools. Claude Code on the same Claude account sees
the same connector. Test: ask for `creative_list_voices` with `languages=["he"]`.

## §3b Their own voice (the most valuable asset)

- **Instant Voice Clone** (all paid plans): ElevenLabs → *Voices* → *Add a new voice* → *Instant Voice Clone*.
  Upload 1–3 minutes of clean speech of THEIR OWN voice, one speaker, no music. Tick the consent box themselves.
  Name it with their name. Prepare the file from an existing video if they have one:
  ```bash
  ffmpeg -i their_video.mp4 -vn -ac 1 -ar 44100 -af "highpass=f=80,loudnorm=I=-16" voice_sample.wav
  ```
- **Professional Voice Clone** (higher plans, best quality): 30+ minutes of clean audio and a short live
  verification read by the voice owner. Worth it once they publish weekly.
- Then `python3 scripts/ugc.py voices` shows the new `voice_id` (category `cloned`). Save it in their profile file.
- Only ever clone the person's own voice, or a voice whose owner agreed in writing.

## §4 Gemini (optional second engine, uses their Google account)

- **gemini.google.com** — images (Nano Banana) and short Veo videos, inside their Google AI plan quota.
- **labs.google/flow** — Veo with reference images (*Ingredients*), first/last frame, extend: best when the same
  person or product must look identical across shots. Monthly credits.
- **aistudio.google.com** → *Get API key* (free tier) — only for light tests (Gemini TTS free ≈ 10 requests/day).
- Gemini models (Nano Banana, Omni, Veo) are ALSO available inside ElevenLabs → one bill is often simpler.

## §5 Local render tools (Claude Code / Claude desktop Code tab on a Mac)

Run once, in order (Homebrew asks for the Mac password — the person types it):
```bash
command -v brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ffmpeg-full node          # ffmpeg-full = has libass, needed for Hebrew captions
python3 ~/.claude/skills/ugc-studio/scripts/ugc.py selftest   # must print two PASS lines
```
The standard `ffmpeg` formula has no libass (captions would fail); `ugc.py` prefers `ffmpeg-full` automatically.

## §6 /brag (launch videos of a website or app)

```bash
npx skills add https://github.com/latent-spaces/brag --skill brag -g -y
npx skills add heygen-com/hyperframes -g -y
npx hyperframes doctor
```
(Or inside Claude Code: `/plugin marketplace add latent-spaces/brag` then `/plugin install brag@brag`.)
Restart Claude Code, then `/brag https://site.com --format vertical`. On Opus 5.5 it runs /brag-slim.

## §7 Install / update this skill

- Claude Code: `git clone https://github.com/CodeNoLimits/dreamnova-ugc-studio ~/dreamnova-ugc-studio && bash ~/dreamnova-ugc-studio/install.sh`
  (update later: `git -C ~/dreamnova-ugc-studio pull && bash ~/dreamnova-ugc-studio/install.sh`)
- claude.ai / Claude app: Settings → Capabilities → Skills → *Upload skill* → `ugc-studio.zip` from the repo.
