# Engines — which model for what (verified in the ElevenLabs connector on 2026-10-08)

Model lists change. Before a paid run, confirm with `creative_get_flow_node_types` and read
`creative_get_model_guide(model_id)` for anything you have not used this session.

## Inside the ElevenLabs connector (one account = voice + image + video + transcription)

| Job | Model | Notes |
|---|---|---|
| Voiceover, expressive | `eleven_v3` (or `eleven_v4`) | audio tags `[warmly]` `[excited]` `[pause]`; numbers as written |
| Voiceover, plain/fast | `eleven_multilingual_v2` / `eleven_flash_v2_5` | no tags; `<break time="0.8s" />` for pauses |
| Transcription with word timings | `eleven_scribe_v1` | best measured Hebrew ASR (beat Whisper large and Gemini Flash) |
| New voice from a description | `creative_design_voice` (`eleven_ttv_v3`) | needs a 100–1000 char line + language from the user |
| Talking head from photo + audio | `creatify-aurora` | prompt = framing/mood only. Base: "medium close-up, faces lens, steady eye contact, soft key light"; UGC: "selfie framing, slight handheld shake, casual delivery". `prompt_guidance` start 1 |
| Talking head, realistic gestures | `bytedance-omnihuman-v1.5` | front-facing, well-lit photo; clean audio drives everything |
| Avatar presenter | `heygen-avatar4` | alternative avatar engine |
| Re-dub an existing video | `sync-lipsync-v3` | new language or fixed line on real footage |
| B-roll default | `gemini-omni-1.1-flash` | 3–10 s, 360p drafts are fast, 1080p/4K finals; short intent prompts |
| B-roll realism / 4K / multi-shot | `kling-3-pro` | ≤ 8 s per clip for identity; negative prompts work |
| Spoken dialogue in-scene | `veo-3.1-generate-001` (`-fast` / `-lite` cheaper) | audio generated with the clip |
| Motion + consistency, multi-input | `bytedance-seedance-v2` / `v2.5` | text + image + video + audio together |
| Silent cinematic | `runway-gen4-turbo` | no audio — add voice/music after |
| Images (thumbnails, stills) | `gpt-image-2` default; `gemini-3-pro-image` / `gemini-nano-banana-2.1` to keep a character consistent or edit; `bytedance-seedream-5-pro` photoreal products | |
| Remove background | `birefnet-v2-bg-removal` | for greenscreen commentary |
| Brand kit from a website | `creative_create_brand_kit_from_website` | colours, fonts, tone in one call |

Spend discipline: put related generations on ONE flow (`creative_create_flow` first, pass `flow_id` everywhere),
`estimate_only=true` first, `generations_count=1` unless the person wants options, never re-call to retry.

## Prompt formulas

**Video (Kling / general):** scene and place → one action with an end point ("…then settles back") → camera
("slow push-in, medium close-up, shallow depth of field") → sound ("quiet café ambience") → mood/lighting.
Add realism: "film grain, skin texture, fabric creases"; anchor hands to objects. Always end with
"no text, no captions, no logos, no watermark". Under 120 words.

**Gemini Omni:** intent over shot lists, 1–2 sentences. "Natural smartphone footage, one continuous shot. A woman
at a sunlit desk turns her laptop toward camera and smiles. Quiet room tone." To change one thing in a clip,
wire it as a video reference and say "Edit this keeping everything the same. Change …".

**Image-to-video of a real product or person:** describe only motion and what must stay identical
("camera-only motion, the product stays exactly identical, no morphing").

**Talking head (Aurora):** never write the dialogue in the prompt — the audio carries the words.

## Gemini directly (the person's Google account)

- **Gemini app** (gemini.google.com): image generation and editing (Nano Banana) and Veo video, quota depends
  on the Google AI plan. Good for quick stills, thumbnails, and short b-roll.
- **Google Flow** (labs.google/flow): Veo with *Ingredients* (reference images), first/last frame, extend —
  best when one character or product must stay identical across shots. Credits are monthly, not unlimited.
- **Google AI Studio** key (free tier) can power Gemini TTS, but free TTS is ~10 requests/day per model per
  project — fine for tests, not for volume. For volume, use ElevenLabs.
- Gemini and Veo also break Hebrew text on screen → captions always by `ugc.py`.

## Free fallbacks (no account)

- `edge-tts` voices (`pip install edge-tts`): `he-IL-HilaNeural`, `he-IL-AvriNeural`, `en-US-AvaMultilingualNeural`,
  `fr-FR-VivienneMultilingualNeural` — measured round-trip: EN Ava 96 %, FR Vivienne 93 %, HE Hila 83 % at rate −8 %.
- macOS `say -v Carmit` for a draft Hebrew read.
