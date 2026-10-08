# Hebrew (and any right-to-left language) — rules that were paid for

1. **Transcribe Hebrew with ElevenLabs Scribe** (`ugc.py transcribe -l he`). Measured on real Hebrew shorts it
   beat Whisper large/turbo and Gemini Flash (Whisper produced fake words). Still read every caption line once:
   an ASR mistake burned into a video is permanent.
2. **Never burn unverified Hebrew** for sacred, legal or memorial content: only text checked word by word.
3. **Captions are rendered by libass** (`ugc.py captions` + `render`). ffmpeg `drawtext` has no bidi and shows
   empty boxes for Hebrew — never use it for Hebrew.
4. The caption style uses `Encoding=-1` (base direction detected per line: `?` and leading digits land on the
   correct side) and wraps any line that mixes Latin words in RLE…PDF so it keeps a right-to-left base.
   Proven on a real short: "מנוע חיפוש של SEO", "ה-AI בעצם סורק את", "למנועי חיפוש כמו ChatGPT" all read correctly.
5. **Run `ugc.py selftest` before a batch** — it renders a witness line and MEASURES word widths; a
   left-to-right rendering fails loudly. Reading Hebrew order "by eye" in a thumbnail is not reliable; zoom
   the real frame (`ffmpeg -ss T -i final.mp4 -frames:v 1 -vf crop=1080:360:0:1160 cap.png`) and read it.
6. **Trailing punctuation is removed** from captions (native UGC look, and no period on the wrong side).
7. **Brand names in a spoken Hebrew script → write them in Hebrew letters** (יוטיוב, אינסטגרם, צ'אט ג'י-פי-טי),
   otherwise Hebrew TTS voices read them as gibberish. For captions you may keep Latin, or map them with
   `ugc.py captions --replace map.json` (e.g. `{"Instagram": "אינסטגרם"}`) when the person wants Hebrew only.
8. **HyperFrames / HTML compositions:** `<html dir="rtl">` renders a black video — put `direction: rtl` on the
   text elements instead. Do not animate `letter-spacing` on Hebrew.
9. **Do not "improve" the person's Hebrew.** Their phrasing is their voice. If a sentence must be cut, cut whole
   words and show them the result.
10. Hebrew text you write yourself (hooks, captions) is shown to the person for approval before rendering.
