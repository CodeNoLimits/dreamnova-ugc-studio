#!/usr/bin/env python3
"""ugc.py — DreamNova UGC Studio toolbox. Python 3.9+ stdlib only, plus ffmpeg (with libass) and curl.

  ugc.py voices                                   list ElevenLabs voices (find your cloned voice_id)
  ugc.py tts "text" -v VOICE_ID -o vo.mp3         ElevenLabs text-to-speech (default eleven_v3)
  ugc.py transcribe in.mp4 -l he -o words.json    ElevenLabs Scribe, word timestamps
  ugc.py captions words.json -o caps.ass          word-timed captions (RTL-safe), vertical safe zone
  ugc.py render in.mp4 -o out.mp4 [--ass caps.ass] [--voice vo.mp3] [--music bgm.mp3]
  ugc.py concat a.mp4 b.mp4 ... -o joined.mp4     normalise + join clips (adds silence where audio is missing)
  ugc.py qc out.mp4 [--script script.txt --transcribe -l he]   technical gates + contact sheet + ASR coverage
  ugc.py selftest                                 logic asserts + Hebrew RTL render gate

Key lookup order: $ELEVENLABS_API_KEY, macOS Keychain service ELEVENLABS_API_KEY, `dn-secret ELEVENLABS_KEY`.
Store it once (the key never goes through a chat):
  security add-generic-password -U -a "$USER" -s ELEVENLABS_API_KEY -w
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, unicodedata
from collections import Counter

API = "https://api.elevenlabs.io/v1"
SIZES = {"vertical": (1080, 1920), "landscape": (1920, 1080), "square": (1080, 1080)}
# caption bottom margin keeps text above the TikTok/Reels/Shorts UI stack (bottom ~500px of 1920)
LAYOUT = {"vertical": dict(size=74, mv=540, ml=150), "landscape": dict(size=56, mv=90, ml=160),
          "square": dict(size=60, mv=150, ml=110)}
HEB = re.compile(r"[\u0590-\u05FF]")
LATIN = re.compile(r"[A-Za-z]")


def die(msg):
    sys.exit(f"ugc: {msg}")


# ---------- tools ----------
def ffbin(name):
    full = f"/opt/homebrew/opt/ffmpeg-full/bin/{name}"
    return full if os.path.exists(full) else (shutil.which(name) or die(f"{name} not found — brew install ffmpeg-full"))


def has_libass():
    out = subprocess.run([ffbin("ffmpeg"), "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return " subtitles " in out


def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode:
        die(f"command failed: {' '.join(map(str, cmd[:6]))} …\n{p.stderr[-1500:]}")
    return p


def probe(path):
    p = run([ffbin("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    d = json.loads(p.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    fps = 0.0
    if v and "/" in v.get("r_frame_rate", ""):
        n, m = v["r_frame_rate"].split("/")
        fps = float(n) / float(m) if float(m) else 0.0
    return dict(duration=float(d["format"].get("duration", 0)), width=v and v["width"], height=v and v["height"],
                fps=round(fps, 2), audio=a is not None)


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        p = subprocess.run(["security", "find-generic-password", "-s", "ELEVENLABS_API_KEY", "-w"], capture_output=True, text=True)
        k = p.stdout.strip() if p.returncode == 0 else ""
    if not k and shutil.which("dn-secret"):
        k = subprocess.run(["dn-secret", "ELEVENLABS_KEY"], capture_output=True, text=True).stdout.strip()
    return k or die('no ElevenLabs key. Run once: security add-generic-password -U -a "$USER" -s ELEVENLABS_API_KEY -w')


def curl(args, out=None):
    """curl with the API key sent on stdin as a header (never on the command line)."""
    cmd = ["curl", "-sS", "--fail-with-body", "-H", "@-"] + args + (["-o", out] if out else [])
    p = subprocess.run(cmd, input=f"xi-api-key: {api_key()}\n", capture_output=True, text=True)
    if p.returncode:
        die(f"ElevenLabs API error: {p.stdout[-800:]} {p.stderr[-400:]}")
    return p.stdout


# ---------- ElevenLabs ----------
def cmd_voices(a):
    for v in json.loads(curl([f"{API}/voices"]))["voices"]:
        print(f'{v["voice_id"]}  {v.get("category", ""):<12} {v["name"]}')


def cmd_tts(a):
    text = open(a.text[1:], encoding="utf-8").read() if a.text.startswith("@") else a.text
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"text": text, "model_id": a.model}, f, ensure_ascii=False)
    try:
        curl(["-X", "POST", f"{API}/text-to-speech/{a.voice}?output_format=mp3_44100_128",
              "-H", "Content-Type: application/json", "--data-binary", f"@{f.name}"], out=a.out)
    finally:
        os.unlink(f.name)
    if a.script:  # keep the exact source text next to the audio: QC needs it
        open(a.script, "w", encoding="utf-8").write(text)
    print(a.out)


def cmd_transcribe(a):
    with tempfile.TemporaryDirectory() as td:
        mp3 = os.path.join(td, "a.mp3")
        run([ffbin("ffmpeg"), "-y", "-loglevel", "error", "-i", a.input, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", mp3])
        fields = ["-F", f"file=@{mp3}", "-F", f"model_id={a.model}", "-F", "timestamps_granularity=word",
                  "-F", "tag_audio_events=false"] + (["-F", f"language_code={a.lang}"] if a.lang else [])
        data = curl(["-X", "POST", f"{API}/speech-to-text"] + fields)
    json.dump(json.loads(data), open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(a.out)


# ---------- captions ----------
def load_words(path):
    d = json.load(open(path, encoding="utf-8"))
    if isinstance(d, dict) and "words" in d:  # ElevenLabs Scribe
        items = [w for w in d["words"] if w.get("type", "word") == "word"]
    elif isinstance(d, dict) and "segments" in d:  # Whisper JSON
        items = [w for s in d["segments"] for w in s.get("words", [])]
    else:
        items = d
    return [((w.get("text") or w.get("word") or "").strip(), float(w["start"]), float(w["end"]))
            for w in items if (w.get("text") or w.get("word") or "").strip()]


def chunk(words, max_words=4, max_chars=22):
    """Group words into caption lines: break at sentence end, at a comma after 2+ words, or at size limits."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        n = sum(len(x[0]) for x in cur) + len(cur) - 1
        if re.search(r"[.?!]$", w[0]) or (len(cur) >= 2 and re.search(r"[,;:]$", w[0])) \
                or len(cur) >= max_words or n >= max_chars:
            out.append(cur)
            cur = []
    if cur:
        if len(cur) == 1 and out and len(out[-1]) < max_words:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def timed(chunks, hold=0.12, gap=0.04, min_dur=0.35):
    """(text, start, end) with no overlap: a line leaves before the next arrives."""
    res = []
    for i, c in enumerate(chunks):
        a, b = c[0][1], c[-1][2] + hold
        if i + 1 < len(chunks):
            b = min(b, chunks[i + 1][0][1] - gap)
        res.append((" ".join(w[0] for w in c), a, max(b, a + min_dur)))
    return res


def clean(text, lang, replace=None):
    for k, v in (replace or {}).items():
        text = text.replace(k, v)
    text = re.sub(r"[.,!?;:…]+$", "", text.strip())  # trailing punctuation: native look + no bidi trap
    text = text.replace("\\", "").replace("{", "(").replace("}", ")")
    if lang == "he" and LATIN.search(text):
        text = "\u202b" + text + "\u202c"  # RLE…PDF: keep a right-to-left base when a line mixes in Latin words
    return text


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def ass_doc(lines, fmt="vertical", style="tiktok", lang="he", font=None, size=None):
    W, H = SIZES[fmt]
    L = LAYOUT[fmt]
    font = font or ("Arial Hebrew" if lang == "he" else "Arial")
    size = size or L["size"]
    if style == "box":  # opaque dark box (LeeyaMedia look)
        st = f"Cap,{font},{int(size * .88)},&H00FFFFFF,&H00FFFFFF,&H33101010,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,2,{L['ml']},{L['ml']},{L['mv']},-1"
    else:  # classic UGC: white fill, black outline, no pill
        st = f"Cap,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,{L['ml']},{L['ml']},{L['mv']},-1"
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding\nStyle: %s\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n") % (W, H, st)
    # Encoding -1 (last Style field) = libass picks the paragraph direction: '?' and digits land on the RTL side.
    return head + "".join(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{t}\n" for t, a, b in lines)


def cmd_captions(a):
    replace = json.load(open(a.replace, encoding="utf-8")) if a.replace else None
    words = [(w[0], w[1] + a.offset, w[2] + a.offset) for w in load_words(a.words)]
    lines = [(clean(t, a.lang, replace), s, e) for t, s, e in timed(chunk(words, a.max_words, a.max_chars))]
    open(a.out, "w", encoding="utf-8").write(ass_doc(lines, a.format, a.style, a.lang, a.font, a.size))
    print(f"{a.out}  ({len(lines)} lines)")


# ---------- render ----------
def vchain(fmt, fit):
    W, H = SIZES[fmt]
    if fit == "blur":  # whole frame kept (no face crop), blurred copy fills the bars
        return (f"split[va][vb];[va]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2[bg];"
                f"[vb]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30")
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30"


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
       "-c:a", "aac", "-b:a", "160k", "-ar", "48000"]


def cmd_render(a):
    src = probe(a.input)
    dur = src["duration"]
    td = tempfile.mkdtemp()
    inputs = ["-i", os.path.abspath(a.input)]
    v = f"[0:v]{vchain(a.format, a.fit)}"
    if a.ass:
        if not has_libass():
            die("this ffmpeg has no libass — brew install ffmpeg-full")
        shutil.copy(a.ass, os.path.join(td, "caps.ass"))
        v += ",subtitles=caps.ass"
    graph = [v + "[v]"]
    voice = None
    if a.voice:
        inputs += ["-i", os.path.abspath(a.voice)]
        voice = "[1:a]"
    elif src["audio"]:
        voice = "[0:a]"
    if a.music:
        mi = len(inputs) // 2
        inputs += ["-stream_loop", "-1", "-i", os.path.abspath(a.music)]
        fade = f"afade=t=out:st={max(dur - 0.8, 0):.2f}:d=0.8"
        if voice:  # music ducks under the voice (sidechain), voice stays 100%
            graph.append(f"{voice}asplit=2[vo1][vo2];[{mi}:a]volume={a.music_vol},atrim=0:{dur:.2f},{fade}[m];"
                         f"[m][vo2]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[md];"
                         f"[vo1][md]amix=inputs=2:normalize=0,loudnorm=I={a.lufs}:TP=-1.5:LRA=11[a]")
        else:
            graph.append(f"[{mi}:a]volume={a.music_vol},atrim=0:{dur:.2f},{fade},loudnorm=I={a.lufs}:TP=-1.5:LRA=11[a]")
    elif voice:
        graph.append(f"{voice}loudnorm=I={a.lufs}:TP=-1.5:LRA=11[a]")
    else:
        graph.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur:.2f}[a]")
    run([ffbin("ffmpeg"), "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(graph),
        "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}"] + ENC + [os.path.abspath(a.out)], cwd=td)
    shutil.rmtree(td, ignore_errors=True)
    print(a.out)


def cmd_concat(a):
    inputs, graph, labels = [], [], ""
    for i, f in enumerate(a.inputs):
        p = probe(f)
        inputs += ["-i", f]
        graph.append(f"[{i}:v]{vchain(a.format, a.fit)}[v{i}]")
        if p["audio"]:
            graph.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
        else:  # silent clips (e.g. Runway, b-roll) get room-silence so the join never shifts sync
            graph.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{p['duration']:.3f}[a{i}]")
        labels += f"[v{i}][a{i}]"
    graph.append(f"{labels}concat=n={len(a.inputs)}:v=1:a=1[v][a]")
    run([ffbin("ffmpeg"), "-y", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(graph),
        "-map", "[v]", "-map", "[a]"] + ENC + [a.out])
    print(a.out)


# ---------- QC ----------
def norm_words(text):
    text = re.sub(r"[\u0591-\u05C7]", "", text)  # niqqud / te'amim
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()
    return re.findall(r"[\w\u0590-\u05FF']+", text)


def coverage(script, heard):
    s, h = Counter(norm_words(script)), Counter(norm_words(heard))
    total = sum(s.values())
    hit = sum(min(n, h[w]) for w, n in s.items())
    missing = [w for w, n in s.items() if h[w] < n]
    return (hit / total if total else 0.0), missing


def ff_log(path, filt):
    return subprocess.run([ffbin("ffmpeg"), "-hide_banner", "-nostats", "-i", path] + filt + ["-f", "null", "-"],
                          capture_output=True, text=True).stderr


def contact_sheet(path, dur, out, cols=6, n=24):
    every = max(dur / n, 0.5)
    run([ffbin("ffmpeg"), "-y", "-loglevel", "error", "-i", path, "-vf",
         f"fps=1/{every:.3f},scale=270:-2,tile={cols}x{-(-int(dur / every + 1) // cols)}:padding=6:color=white",
         "-frames:v", "1", out])
    return every


def cmd_qc(a):
    p, res = probe(a.input), []
    stem = os.path.splitext(a.input)[0]

    def gate(name, ok, info):
        res.append(dict(gate=name, ok=bool(ok), info=info))

    if a.format:
        gate("resolution", (p["width"], p["height"]) == SIZES[a.format], f'{p["width"]}x{p["height"]} expected {SIZES[a.format]}')
    gate("fps", 23.9 <= p["fps"] <= 60.1, p["fps"])
    gate("audio_track", p["audio"], p["audio"])
    if a.max_dur:
        gate("duration", p["duration"] <= a.max_dur, f'{p["duration"]:.2f}s ≤ {a.max_dur}s')
    if p["audio"]:
        log = ff_log(a.input, ["-af", "ebur128=peak=true"])
        i = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
        pk = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", log)
        lufs = float(i[-1]) if i else -99.0
        peak = float(pk[-1]) if pk and pk[-1] != "-inf" else -99.0
        gate("loudness", -18.5 <= lufs <= -13.5, f"{lufs} LUFS (target -16)")
        gate("true_peak", peak <= -0.9, f"{peak} dBFS (≤ -1)")
        sil = re.findall(r"silence_duration: ([\d.]+)", ff_log(a.input, ["-af", "silencedetect=n=-45dB:d=1.2"]))
        gate("dead_air", not sil, f"{len(sil)} silences ≥1.2s {sil[:5]}")
    blk = re.findall(r"black_start:([\d.]+)", ff_log(a.input, ["-vf", "blackdetect=d=0.25:pix_th=0.08"]))
    gate("black_frames", not blk, f"black at {blk[:6]}")
    frz = [f for f in re.findall(r"freeze_start: ([\d.]+)", ff_log(a.input, ["-vf", "freezedetect=n=-60dB:d=1.5"]))
           if float(f) < p["duration"] - 3.5]  # a held end card in the last 3.5 s is intentional
    gate("frozen_video", not frz, f"freeze at {frz[:6]}")
    sheet = stem + "_sheet.png"
    every = contact_sheet(a.input, p["duration"], sheet)
    run([ffbin("ffmpeg"), "-y", "-loglevel", "error", "-i", a.input, "-frames:v", "1", stem + "_frame0.png"])
    heard = None
    if a.words:
        heard = " ".join(w[0] for w in load_words(a.words))
    elif a.transcribe:
        wj = stem + "_heard.json"
        cmd_transcribe(argparse.Namespace(input=a.input, lang=a.lang, model="scribe_v1", out=wj))
        heard = " ".join(w[0] for w in load_words(wj))
    if a.script and heard is not None:
        cov, miss = coverage(open(a.script, encoding="utf-8").read(), heard)
        gate("speech_coverage", cov >= a.min_cov, f"{cov:.1%} of script heard; missing: {miss[:15]}")
    for r in res:
        print(("PASS " if r["ok"] else "FAIL ") + f'{r["gate"]:<16} {r["info"]}')
    print(f"LOOK  contact sheet {sheet} (1 frame / {every:.1f}s) + {stem}_frame0.png — open them and check every frame.")
    json.dump(dict(file=a.input, probe=p, gates=res, sheet=sheet), open(stem + "_qc.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    sys.exit(0 if all(r["ok"] for r in res) else 1)


# ---------- self-test ----------
def rtl_gate():
    """Render a Hebrew witness line through the real ASS pipeline and measure word widths left→right.
    'האיש שהדליק את האש' (4,6,2,3 letters). Correct RTL ⇒ visual order [האש, את, שהדליק, האיש]."""
    td = tempfile.mkdtemp()
    doc = ass_doc([("האיש שהדליק את האש", 0, 2)], "landscape", "tiktok", "he").replace(",2,160,160,90,-1", ",5,160,160,90,-1")
    open(os.path.join(td, "w.ass"), "w", encoding="utf-8").write(doc)
    run([ffbin("ffmpeg"), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=1",
         "-vf", "subtitles=w.ass", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "w.raw"], cwd=td)
    px = open(os.path.join(td, "w.raw"), "rb").read()
    shutil.rmtree(td, ignore_errors=True)
    W, H = 1920, 1080
    cols = [any(px[y * W + x] > 128 for y in range(380, 700)) for x in range(W)]
    runs, x = [], 0
    while x < W:
        if cols[x]:
            s = x
            while x < W and cols[x]:
                x += 1
            runs.append((s, x))
        x += 1
    gaps = sorted(range(len(runs) - 1), key=lambda i: runs[i + 1][0] - runs[i][1])[-3:]
    cuts = sorted(gaps)
    words, start = [], runs[0][0]
    for i in cuts:
        words.append(runs[i][1] - start)
        start = runs[i + 1][0]
    words.append(runs[-1][1] - start)
    ok = len(words) == 4 and words[2] == max(words) and words[1] == min(words) and words[0] < words[3]
    return ok, words


def cmd_selftest(a):
    ws = [("שלום", 0.0, 0.4), ("לכולם,", 0.45, 0.9), ("היום", 1.0, 1.3), ("נדבר", 1.35, 1.7), ("על", 1.75, 1.9),
          ("יוטיוב.", 1.95, 2.5), ("כן", 2.6, 2.8)]
    ch = chunk(ws, 4, 28)
    assert [len(c) for c in ch] == [2, 4, 1], ch  # break on comma, then at 4 words; full line keeps the tail apart
    assert [len(c) for c in chunk(ws[:3], 4, 28)] == [3]  # lone tail merges into a non-full line
    tl = timed(ch)
    assert all(tl[i][2] <= tl[i + 1][1] for i in range(len(tl) - 1)), tl  # never two lines on screen
    assert clean("שטח שכור.", "he") == "שטח שכור"
    assert clean("Instagram הוא שטח", "he").startswith("\u202b")
    assert clean("a {b} c", "en") == "a (b) c"
    cov, miss = coverage("YouTube הוא מנוע חיפוש", "יוטיוב הוא מנוע חיפוש")
    assert abs(cov - 0.75) < 1e-9 and miss == ["youtube"], (cov, miss)
    assert coverage("שָׁלוֹם עולם", "שלום עולם")[0] == 1.0  # niqqud ignored
    print("PASS logic (chunking, timing, cleaning, coverage)")
    if not has_libass():
        sys.exit("FAIL ffmpeg has no libass → brew install ffmpeg-full (Hebrew captions impossible without it)")
    ok, w = rtl_gate()
    print(("PASS" if ok else "FAIL") + f" Hebrew RTL render gate, word widths left→right {w}")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("voices")
    p = sp.add_parser("tts")
    p.add_argument("text", help='text, or @file.txt')
    p.add_argument("-v", "--voice", required=True)
    p.add_argument("-m", "--model", default="eleven_v3")
    p.add_argument("-o", "--out", default="vo.mp3")
    p.add_argument("--script", help="also save the exact spoken text here (for QC)")
    p = sp.add_parser("transcribe")
    p.add_argument("input")
    p.add_argument("-l", "--lang", default=None, help="he / en / fr … (omit = auto)")
    p.add_argument("-m", "--model", default="scribe_v1")
    p.add_argument("-o", "--out", default="words.json")
    p = sp.add_parser("captions")
    p.add_argument("words")
    p.add_argument("-o", "--out", default="caps.ass")
    p.add_argument("-l", "--lang", default="he")
    p.add_argument("--format", choices=SIZES, default="vertical")
    p.add_argument("--style", choices=["tiktok", "box"], default="tiktok")
    p.add_argument("--max-words", type=int, default=4)
    p.add_argument("--max-chars", type=int, default=22)
    p.add_argument("--offset", type=float, default=0.0, help="shift all words (s) when the clip was trimmed")
    p.add_argument("--replace", help='JSON {"Instagram": "אינסטגרם"} applied to caption text')
    p.add_argument("--font")
    p.add_argument("--size", type=int)
    p = sp.add_parser("render")
    p.add_argument("input")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--ass")
    p.add_argument("--voice", help="replace the clip audio with this voiceover")
    p.add_argument("--music")
    p.add_argument("--music-vol", type=float, default=0.22)
    p.add_argument("--format", choices=SIZES, default="vertical")
    p.add_argument("--fit", choices=["cover", "blur"], default="cover")
    p.add_argument("--lufs", type=float, default=-16)
    p = sp.add_parser("concat")
    p.add_argument("inputs", nargs="+")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--format", choices=SIZES, default="vertical")
    p.add_argument("--fit", choices=["cover", "blur"], default="cover")
    p = sp.add_parser("qc")
    p.add_argument("input")
    p.add_argument("--format", choices=SIZES)
    p.add_argument("--max-dur", type=float)
    p.add_argument("--script", help="text that was meant to be spoken")
    p.add_argument("--words", help="existing transcript JSON of the final file")
    p.add_argument("--transcribe", action="store_true", help="transcribe the final file with Scribe")
    p.add_argument("-l", "--lang", default=None)
    p.add_argument("--min-cov", type=float, default=0.75)
    sp.add_parser("selftest")
    a = ap.parse_args()
    globals()["cmd_" + a.cmd](a)


if __name__ == "__main__":
    main()
