# Profile — LeeyaMedia (Leeya Katz · ליאה כץ)

Read this whole file before any video for Leeya. It overrides the generic defaults.

## Who
- **Leeya Katz (ליאה כץ)**, founder of **LeeyaMedia** — a YouTube authority studio. Spell her name and brand
  exactly as on her current website; ask once if unsure.
- Speaks Hebrew first; English and French fine. Talk to her in the language she writes in.
- Not technical: never show her commands, folders or errors — show her the video, a still, or one question.
- Website: leeyamedia.com (Hebrew), 3D sites leeya-3d-he / leeya-3d-en / leeya-3d-fr .vercel.app.

## What she sells and to whom
- Long-form YouTube strategy and production that turns experts and service founders into the trusted authority
  their clients choose — "Long-form videos. Real trust. Clients who pick you." / «סרטונים ארוכים. אמון אמיתי. לקוחות שבוחרים אותך.»
- Audience: experts, consultants and premium service businesses (Israel first, English-speaking second).
- CTA style: one calm invitation («בואי נדבר» / "Let's talk") leading to her form or WhatsApp business line on her site.

## Her three core messages (her own words from her published shorts — reuse them, do not rewrite them)
1. **Rented land vs. real estate.** «Instagram, Facebook, TikTok הם רק שטח שכור… ביוטיוב אתם בונים נדל"ן שהוא מניב.»
   Social posts die in 24 h; YouTube is a search engine whose videos keep working.
2. **The 7-hour rule.** «אדם ממוצע צריך לעבור איתכם שבע שעות מסך כדי באמת לסמוך עליכם.» Long video creates
   parasocial trust; clients arrive already decided — "back to the expert's hat, out of the seller's hat".
3. **SEO → GEO.** «אנחנו עוברים מעידן של SEO… ל-GEO.» AI engines (ChatGPT, Gemini) look for the most trusted source;
   a credible YouTube video makes you that source.
Use these as the spine for hooks and scripts. Do not add statistics she has not said.

## Taste (what she accepts and rejects)
- **Look:** white, airy, editorial, "quiet luxury Tel Aviv". Near-black text `#0a0a0a`, white `#ffffff`, warm
  YouTube red `#fa2c2c` / `#C8102E` as ONE accent, gold `#cda21c` only for a thin line. Font family: Open Sans
  (Latin) + Heebo (Hebrew), one family, no script or serif fonts.
- **Rejects:** dark or beige backgrounds, collage, Ken Burns photo montages, gradients red→gold, emojis in
  brand videos, badges, fake social proof, anything that feels like an AI template, a cropped face in a VSL.
- **Her face is always real** (her own footage or photos). No invented face. AI avatar of her only if SHE asks,
  built from her real photo + her cloned voice, and shown to her before anything else.
- **Her Hebrew stays her Hebrew.** Never polish her sentences. Every Hebrew line you wrote is shown to her first.
- **Words to use:** אוטוריטה / authority, לקוחות איכותיים / quality clients, סמכות, נכס. **Avoid:** "viral" (except
  to contrast: "viral for a moment vs authority forever"), "hacks", "growth hack", "10x", hype.
- Captions: `ugc.py captions --style box` (white text on a dark box) or classic outline; bottom-centre; no emojis.
  For Hebrew-only requests map brand names with `--replace` (e.g. `{"Instagram":"אינסטגרם","YouTube":"יוטיוב"}`).

## Formats that fit her
- **Authority talking head** cut from her long videos (best): one idea, 30–45 s, her real voice.
- **Myth vs truth** around her three messages.
- **VSL** for her site: 2:45–3:05 in Hebrew, landscape 1920×1080, wide shot (not tight on the face), captions burned.
- **/brag** for her website or a client's site launch.
- Faceless b-roll only for teasers, never instead of her face for authority content.

## Voice
- Her real voice from her videos first. ElevenLabs Instant Voice Clone from 1–3 min of her clean speech
  (e.g. the audio of her long VSL) once she has her account — she ticks the consent herself. Put her
  `voice_id` here: `LEEYA_VOICE_ID = <fill after cloning>`.
- Hebrew TTS fallback (free): edge-tts `he-IL-HilaNeural` at rate −8 % (83 % measured intelligibility — drafts only).

## Process with her
- One question at a time; show a still or a 5-second preview rather than describing.
- Pilot one video, get her yes, then batch. Never post or send on her behalf without her explicit OK.
- She is the client of nobody here: no pricing, no upsell, no invoices in anything you prepare for her.
