#!/usr/bin/env python3
"""icons_reel.py — the "wow" reel: real talking clips + glossy 3D icons, social logos and AI logos that pop in
on the exact spoken word, word-timed captions, wordmark intro/outro, red wipes, SFX and ducked music.
Generalised from the LeeyaMedia Hebrew reel of 2026-10-06 (the version she liked). Output = a HyperFrames
project; render it with `npx hyperframes render <out> -o <out>.mp4`.

  python3 icons_reel.py spec.json            # writes <out>/index.html, mix.mp3, clips/, img/
  python3 icons_reel.py --example > spec.json

Free icon sources (fetched on demand, cached in <out>/img): Fluent Emoji 3D (MIT, kind "fl"),
simple-icons (CC0, kind "brand"), lobe-icons (MIT, kind "ai"). Words come from `ugc.py transcribe`.
"""
import html, json, os, re, subprocess, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ugc import ffbin, load_words, run  # noqa: E402

TILE = {"instagram": "grad", "facebook": "#0866FF", "tiktok": "#000000", "youtube": "#FF0000", "linkedin": "#0A66C2",
        "x": "#000000", "whatsapp": "#25D366", "google": "#ffffff", "spotify": "#1DB954", "telegram": "#26A5E4"}
SFX_DIRS = [os.path.expanduser(p) for p in ("~/.claude/skills/media-use/audio/assets/sfx", "~/.agents/skills/media-use/audio/assets/sfx")]
EXAMPLE = {
    "out": "reel", "rtl": True, "music": "bgm.mp3",
    "wordmark": "LEEYAMEDIA", "kicker": "ליאה כץ · בונים סמכות ביוטיוב",
    "outro": ["ליאה כץ · בונים סמכות ביוטיוב", "יוטיוב · סמכות · לידים איכותיים"], "outro_kicker": "LEEYA KATZ",
    "lower": ["ליאה כץ", "LEEYAMEDIA"], "colors": {"gold": "#c9a961", "red": "#c8102e"},
    "replace": {"Instagram": "אינסטגרם", "Facebook": "פייסבוק", "TikTok": "טיקטוק", "YouTube": "יוטיוב"},
    "clips": [{"id": "C1", "video": "short_01_he.mp4", "words": "short_01_he_scribe.json", "start": 0.0, "end": 17.35}],
    "cards": {"C1": [
        {"icons": [["brand", "instagram", "Instagram"], ["brand", "facebook", "Facebook"], ["brand", "tiktok", "TikTok"]],
         "label": "שטח שכור", "at": "שכור", "until": "אורחים"},
        {"icons": [["fl", "locked", "נחסם"]], "label": "החשבון נחסם", "at": "נחסם", "dur": 2.0}]}}


def norm(w):
    return re.sub(r"[^\w֐-׿-]", "", w).strip()


def fetch(url, dst):
    if not os.path.exists(dst):
        req = urllib.request.Request(url, headers={"User-Agent": "ugc-studio"})
        try:
            data = urllib.request.urlopen(req, timeout=30).read()
        except Exception:  # macOS python without certs → curl
            data = subprocess.run(["curl", "-fsSL", url], capture_output=True, check=True).stdout
        open(dst, "wb").write(data)
    return dst


def icon_asset(kind, key, img):
    if kind == "fl":  # Fluent Emoji 3D: folder "Magnifying glass tilted left" / file magnifying_glass_tilted_left_3d.png
        folder = urllib.parse.quote(key.replace("_", " ").capitalize())
        return fetch(f"https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/{folder}/3D/{key}_3d.png",
                     f"{img}/fl_{key}.png")
    if kind == "ai":
        return fetch(f"https://cdn.jsdelivr.net/npm/@lobehub/icons-static-png@latest/light/{key}.png", f"{img}/ai_{key}.png")
    return fetch(f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{key}.svg", f"{img}/br_{key}.svg")


def icon_html(kind, key, img):
    if kind == "fl":
        return f'<div class="ic"><img class="fl" src="img/fl_{key}.png"></div>'
    if kind == "ai":
        return f'<div class="ic"><div class="tile white"><img class="ai" src="img/ai_{key}.png"><div class="shine"></div></div></div>'
    d = re.search(r' d="([^"]+)"', open(f"{img}/br_{key}.svg").read()).group(1)
    bg = TILE.get(key, "#111111")
    fill = ("background:linear-gradient(45deg,#feda75,#fa7e1e 28%,#d62976 55%,#962fbf 78%,#4f5bd5)"
            if bg == "grad" else f"background:{bg}")
    glyph = f'<path d="{d}" fill="#fff"/>'
    if key == "tiktok":
        glyph = (f'<path d="{d}" fill="#25F4EE" transform="translate(-.45,-.35)"/>'
                 f'<path d="{d}" fill="#FE2C55" transform="translate(.45,.35)"/><path d="{d}" fill="#fff"/>')
    if key == "google":
        glyph = f'<path d="{d}" fill="#4285F4"/>'
    return f'<div class="ic"><div class="tile" style="{fill}"><svg viewBox="0 0 24 24">{glyph}</svg><div class="shine"></div></div></div>'


def build(spec, base):
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)  # noqa: E731
    out = P(spec.get("out", "reel"))
    img = f"{out}/img"
    os.makedirs(f"{out}/clips", exist_ok=True)
    os.makedirs(img, exist_ok=True)
    rtl = spec.get("rtl", False)
    dirc = "direction:rtl" if rtl else "direction:ltr"
    gold, red = spec.get("colors", {}).get("gold", "#c9a961"), spec.get("colors", {}).get("red", "#c8102e")
    ff = ffbin("ffmpeg")
    sfx_dir = next((d for d in SFX_DIRS if os.path.isdir(d)), None)
    info = {}
    for c in spec["clips"]:  # cut each clip (+0.6 s frozen tail so it never ends before its scene) and its words
        n, a, b = c["id"], float(c["start"]), float(c["end"])
        mp4, wav = f"{out}/clips/{n}.mp4", f"{out}/clips/{n}.wav"
        if not os.path.exists(mp4):
            run([ff, "-y", "-loglevel", "error", "-ss", str(a), "-to", str(b), "-i", P(c["video"]),
                 "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,tpad=stop_mode=clone:stop_duration=0.6",
                 "-af", "apad=pad_dur=0.6,loudnorm=I=-17:TP=-2:LRA=7", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                 "-r", "30", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", mp4])
            run([ff, "-y", "-loglevel", "error", "-i", mp4, "-vn", "-ac", "2", "-ar", "44100", wav])
        ws = [(t, s - a, e - a) for t, s, e in load_words(P(c["words"])) if a - 0.1 <= s <= b - 0.05]
        info[n] = dict(words=ws, dur=round(b - a, 2))

    def find(n, tok, after=0.0):
        for w, s, e in info[n]["words"]:
            if norm(tok) in norm(w) and s >= after - 0.01:
                return s, e
        sys.exit(f"icons_reel: word '{tok}' not found in clip {n} — check the transcript spelling")

    INTRO, OUTRO = 3.4, 5.2
    sc, t = [dict(k="intro", s=0, d=INTRO)], INTRO
    for c in spec["clips"]:
        d = round(info[c["id"]]["dur"] + 1.05, 2)
        sc.append(dict(k="vid", n=c["id"], s=round(t, 2), d=d))
        t += d
    sc.append(dict(k="outro", s=round(t, 2), d=OUTRO))
    total = round(t + OUTRO, 2)

    inp, flt, vo, sf = [], [], [], []

    def add(path, at, vol=1.0):
        i = len(inp) // 2
        inp.extend(["-i", path])
        ms = max(0, int(at * 1000))
        flt.append(f"[{i}:a]adelay={ms}|{ms},volume={vol}[x{i}]")
        return i

    def sfx(name, at, vol):
        if sfx_dir and os.path.exists(f"{sfx_dir}/{name}"):
            sf.append(add(f"{sfx_dir}/{name}", at, vol))

    for s in sc:
        if s["k"] == "vid":
            vo.append(add(f"{out}/clips/{s['n']}.wav", s["s"]))
    sfx("riser.mp3", 0.2, 0.5)
    for s in sc[1:]:
        sfx("whoosh-short.mp3", s["s"] - 0.02, 0.5)

    T = lambda x: round(x, 2)  # noqa: E731
    vids, secs, tl = [], [], []
    for k, s in enumerate(sc):
        st, du = s["s"], s["d"]
        wipe = f'<div class="wipe" id="w{k}"></div>'
        if s["k"] == "intro":
            letters = "".join(f'<span class="lt">{html.escape(ch)}</span>' for ch in spec.get("wordmark", ""))
            secs.append(f'<section id="s{k}" class="clip scene opaque cen" data-start="0" data-duration="{du}"><div class="ring">'
                        f'<svg viewBox="0 0 400 400"><circle id="r0" cx="200" cy="200" r="190"/></svg></div><div class="rule gold" id="g0"></div>'
                        f'<div class="wm">{letters}</div><div class="rule red" id="rr0"></div>'
                        f'<div class="kicker" style="{dirc}">{html.escape(spec.get("kicker", ""))}</div>{wipe}</section>')
            tl += ['tl.fromTo("#r0",{strokeDashoffset:1200},{strokeDashoffset:0,duration:1.6,ease:"power2.inOut"},0.3);',
                   'tl.fromTo("#g0",{scaleX:0},{scaleX:1,duration:.9,ease:"power3.out"},0.5);',
                   'tl.fromTo("#s0 .lt",{yPercent:110,opacity:0,rotateX:-80},{yPercent:0,opacity:1,rotateX:0,duration:.8,ease:"back.out(1.6)",stagger:.07},0.7);',
                   'tl.fromTo("#rr0",{scaleX:0},{scaleX:1,duration:.7,ease:"power3.out"},1.7);',
                   'tl.fromTo("#s0 .kicker",{opacity:0,y:20},{opacity:1,y:0,duration:.7,ease:"power2.out"},1.9);']
        elif s["k"] == "vid":
            n, W = s["n"], info[s["n"]]["words"]
            vids.append(f'<video id="v{k}" class="clip vfull" src="clips/{n}.mp4" data-start="{st}" data-duration="{du}" data-track-index="2" muted playsinline></video>')
            tl.append(f'tl.fromTo("#v{k}",{{scale:1.0}},{{scale:1.06,duration:{T(du)},ease:"none"}},{st});')
            chunks, cur = [], []
            for w in W:  # captions: ≤5 words / ≤30 chars, break on punctuation after 3+ words
                cur.append(w)
                ln = sum(len(x[0]) for x in cur) + len(cur)
                if (len(cur) >= 3 and re.search(r"[.?!,]$", w[0])) or len(cur) >= 5 or ln >= 30:
                    chunks.append(cur)
                    cur = []
            if cur:
                if len(cur) < 2 and chunks and len(chunks[-1]) <= 4:
                    chunks[-1] += cur
                else:
                    chunks.append(cur)
            caps = ""
            for j, c in enumerate(chunks):
                txt = " ".join(w[0] for w in c)
                for e, h in spec.get("replace", {}).items():
                    txt = txt.replace(e, h)
                txt = re.sub(r"[.,?!]+$", "", txt)
                caps += f'<div class="cap" id="c{k}_{j}" style="{dirc}">{html.escape(txt)}</div>'
                a = st + c[0][1]
                b = st + c[-1][2] + 0.12
                if j + 1 < len(chunks):
                    b = min(b, st + chunks[j + 1][0][1] - 0.04)
                b = max(b, a + 0.25)
                tl.append(f'tl.to("#c{k}_{j}",{{opacity:1,duration:.06}},{T(a)});tl.to("#c{k}_{j}",{{opacity:0,duration:.06}},{T(b)});')
            cards = ""
            for ci, cd in enumerate(spec.get("cards", {}).get(n, [])):
                icons = cd.get("icons", [])
                for kd, ky, _ in icons:
                    icon_asset(kd, ky, img)
                first = min(find(n, tk)[0] for _, _, tk in icons) if icons else find(n, cd["at"])[0]
                a_card = min(first, find(n, cd["at"])[0]) - 0.05 if cd.get("at") else first - 0.05
                end = find(n, cd["until"], a_card)[1] + 0.3 if cd.get("until") else a_card + float(cd.get("dur", 2.2))
                cid = f"k{k}_{ci}"
                ih = "".join(icon_html(kd, ky, img) for kd, ky, _ in icons)
                lh = f'<div class="lab" style="{dirc}">{html.escape(cd["label"])}</div>' if cd.get("label") else ""
                cards += f'<div class="card{" multi" if len(icons) >= 3 else ""}" id="{cid}" style="{dirc}"><div class="irow">{ih}</div>{lh}</div>'
                T0 = st + a_card
                tl.append(f'tl.fromTo("#{cid}",{{opacity:0}},{{opacity:1,duration:.2}},{T(T0)});')
                for ii, (kd, ky, tk) in enumerate(icons):
                    ta = max(st + find(n, tk)[0] - 0.02, T0)
                    sel = f"#{cid} .ic:nth-child({ii + 1})"
                    tl.append(f'tl.fromTo("{sel}",{{scale:0,rotateY:-100,opacity:0}},{{scale:1,rotateY:0,opacity:1,duration:.75,ease:"back.out(2.2)"}},{T(ta)});')
                    tl.append(f'tl.fromTo("{sel} .shine",{{x:"-130%"}},{{x:"230%",duration:.9,ease:"power2.inOut"}},{T(ta + .3)});')
                    tl.append(f'tl.fromTo("{sel}",{{y:0}},{{y:-9,duration:1.1,yoyo:true,repeat:1,ease:"sine.inOut"}},{T(ta + .8)});')
                    tl.append(f'tl.fromTo("#fl{k}",{{opacity:0}},{{opacity:.16,duration:.06,yoyo:true,repeat:1}},{T(ta)});')
                    sfx("sparkle.mp3" if kd == "ai" else "pop.mp3", ta, 0.45)
                if cd.get("label"):
                    tl.append(f'tl.fromTo("#{cid} .lab",{{opacity:0,x:-40,scale:.9}},{{opacity:1,x:0,scale:1,duration:.55,ease:"back.out(1.6)"}},{T(T0 + 0.25)});')
                tl.append(f'tl.to("#{cid}",{{opacity:0,y:-24,duration:.3}},{T(st + end)});')
            lower = spec.get("lower", ["", ""])
            secs.append(f'<section id="s{k}" class="clip scene ovl" data-start="{st}" data-duration="{du}"><div class="flash" id="fl{k}"></div>{cards}'
                        f'<div class="lower" style="{dirc}"><div class="rule gold" id="lg{k}"></div><div class="who">{html.escape(lower[0])}</div>'
                        f'<div class="who2">{html.escape(lower[1])}</div></div>{caps}{wipe}</section>')
            tl.append(f'tl.to("#s{k} .lower",{{opacity:1,duration:.4}},{T(st + .85)});tl.fromTo("#lg{k}",{{scaleX:0}},{{scaleX:1,duration:.7,ease:"power3.out"}},{T(st + .9)});')
        else:
            lines = "".join(f'<div class="tg" style="{dirc}">{html.escape(x)}</div>' for x in spec.get("outro", []))
            secs.append(f'<section id="s{k}" class="clip scene opaque cen" data-start="{st}" data-duration="{du}"><div class="ring big">'
                        f'<svg viewBox="0 0 400 400"><circle id="r9" cx="200" cy="200" r="190"/></svg></div><div class="rule gold" id="g9"></div>'
                        f'<div class="wm big">{html.escape(spec.get("wordmark", ""))}</div><div class="rule red" id="rr9"></div>{lines}'
                        f'<div class="kicker">{html.escape(spec.get("outro_kicker", ""))}</div>{wipe}</section>')
            a = st + .45
            tl += [f'tl.fromTo("#r9",{{strokeDashoffset:1200}},{{strokeDashoffset:0,duration:1.8,ease:"power2.inOut"}},{T(a)});',
                   f'tl.fromTo("#g9",{{scaleX:0}},{{scaleX:1,duration:.9,ease:"power3.out"}},{T(a + .2)});',
                   f'tl.fromTo("#s{k} .wm",{{opacity:0,scale:1.25}},{{opacity:1,scale:1,duration:1.1,ease:"power3.out"}},{T(a + .35)});',
                   f'tl.fromTo("#rr9",{{scaleX:0}},{{scaleX:1,duration:.7,ease:"power3.out"}},{T(a + 1.2)});',
                   f'tl.fromTo("#s{k} .tg",{{opacity:0,y:24}},{{opacity:1,y:0,duration:.7,ease:"power3.out",stagger:.25}},{T(a + 1.4)});',
                   f'tl.fromTo("#s{k} .kicker",{{opacity:0}},{{opacity:1,duration:.8}},{T(a + 2.4)});']
            sfx("impact-bass-1.mp3", st + 0.1, 0.7)
            sfx("sparkle.mp3", st + 0.9, 0.4)
        if k > 0:
            tl.append(f'tl.fromTo("#w{k}",{{x:"0%"}},{{x:"101%",duration:.45,ease:"power3.out",immediateRender:false}},{st});')
        if k + 1 < len(sc):
            tl.append(f'tl.fromTo("#w{k}",{{x:"-101%"}},{{x:"0%",duration:.35,ease:"power3.in",immediateRender:false}},{T(st + du - 0.37)});')

    # audio: voices 100 %, music ducked under them (sidechain), SFX on top, -16 LUFS
    mix = [f'{"".join(f"[x{i}]" for i in vo)}amix=inputs={len(vo)}:normalize=0,apad=whole_dur={total}[vo]']
    final = "[vo]"
    if spec.get("music"):
        m = len(inp) // 2
        inp.extend(["-stream_loop", "-1", "-i", P(spec["music"])])
        mix[0] += ";[vo]asplit=2[vo1][vo2]"
        mix.append(f"[{m}:a]atrim=0:{total},afade=t=in:d=1.2,afade=t=out:st={total - 2.5}:d=2.5,volume=0.5[bg];"
                   "[bg][vo2]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[bgd]")
        final = "[vo1][bgd]"
    if sf:
        mix.append(f'{"".join(f"[x{i}]" for i in sf)}amix=inputs={len(sf)}:normalize=0,apad=whole_dur={total}[sfx]')
        final += "[sfx]"
    nin = final.count("[")
    mix.append(f"{final}amix=inputs={nin}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9,atrim=0:{total}[out]" if nin > 1
               else f"{final}loudnorm=I=-16:TP=-1.5:LRA=9,atrim=0:{total}[out]")
    run([ff, "-y", "-loglevel", "error"] + inp + ["-filter_complex", ";".join(flt + mix), "-map", "[out]",
         "-ar", "44100", "-b:a", "192k", f"{out}/mix.mp3"])

    css = f'''body{{margin:0;background:#fff;color:#0a0a0a;font-family:system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif}}
#root{{position:relative;width:100%;height:100%;overflow:hidden;background:#fff}}
.vfull{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
.scene{{position:absolute;inset:0;overflow:hidden}}.opaque{{background:#fff}}.ovl{{background:transparent}}
.cen{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:44px}}
.rule{{height:2px;width:240px;transform-origin:center;position:relative}}.gold{{background:{gold}}}.red{{background:{red};width:140px}}
.wm{{font-size:66px;font-weight:600;letter-spacing:.42em;padding-inline-start:.42em;position:relative;white-space:nowrap}}.wm.big{{font-size:58px}}.lt{{display:inline-block}}
.kicker{{font-size:34px;letter-spacing:.12em;color:#6b6b6b;position:relative}}.tg{{font-size:38px;color:#2b2b2b;position:relative}}
.ring{{position:absolute;width:760px;height:760px;top:50%;left:50%;margin:-380px 0 0 -380px}}.ring.big{{width:980px;height:980px;margin:-490px 0 0 -490px}}
.ring svg{{width:100%;height:100%;transform:rotate(-90deg)}}.ring circle{{fill:none;stroke:{gold};stroke-width:2;stroke-dasharray:1200;stroke-dashoffset:1200}}
.wipe{{position:absolute;inset:0;background:{red};transform:translateX(-101%);z-index:50}}
.flash{{position:absolute;inset:0;background:#fff;opacity:0}}
.card{{position:absolute;top:64px;left:40px;right:40px;display:flex;align-items:center;justify-content:center;gap:26px;opacity:0;perspective:900px}}
.irow{{display:flex;gap:22px;align-items:center}}.card.multi{{flex-direction:column;gap:16px}}.card.multi .tile{{width:132px;height:132px;border-radius:30px}}.card.multi .lab{{font-size:42px;padding:14px 30px}}
.ic{{opacity:0;transform-style:preserve-3d}}
.tile{{position:relative;width:176px;height:176px;border-radius:40px;overflow:hidden;box-shadow:0 18px 30px rgba(0,0,0,.45),inset 0 3px 0 rgba(255,255,255,.55);display:flex;align-items:center;justify-content:center}}
.tile svg{{width:62%;height:62%}}.tile.white{{background:#fff}}.tile .ai{{width:66%;height:66%;object-fit:contain}}
.shine{{position:absolute;top:-20%;left:0;width:45%;height:140%;background:rgba(255,255,255,.55);transform:skewX(-20deg) translateX(-130%)}}
.fl{{width:180px;height:180px;object-fit:contain;filter:drop-shadow(0 16px 18px rgba(0,0,0,.45))}}
.lab{{background:#fbf6ee;color:#2a1d17;font-weight:700;font-size:50px;padding:20px 38px;border-radius:34px;border:3px solid {gold};box-shadow:0 14px 26px rgba(0,0,0,.4),inset 0 3px 0 rgba(255,255,255,.9);opacity:0;white-space:nowrap}}
.cap{{position:absolute;left:60px;right:60px;bottom:400px;text-align:center;color:#fff;background:rgba(10,10,10,.8);padding:22px 26px;font-size:64px;font-weight:700;line-height:1.2;opacity:0}}
.lower{{opacity:0;position:absolute;{"right" if rtl else "left"}:70px;bottom:150px;display:flex;flex-direction:column;gap:10px;align-items:{"flex-end" if rtl else "flex-start"};color:#fff;background:rgba(10,10,10,.74);padding:22px 34px}}
.lower .rule{{width:120px}}.who{{font-size:44px;font-weight:700}}.who2{{font-size:28px;letter-spacing:.42em;color:{gold}}}'''
    # never <html dir="rtl"> — HyperFrames renders it black; direction is set per element above
    page = (f'<!doctype html><html lang="{"he" if rtl else "en"}"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">'
            f'<title>{html.escape(spec.get("wordmark", "reel"))}</title>'
            f'<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script><style>{css}</style></head><body>\n'
            f'<div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{total}">\n'
            + "\n".join(vids) + "\n" + "\n".join(secs) +
            f'\n<audio id="mix" src="mix.mp3" data-start="0" data-duration="{total}" data-track-index="9"></audio>\n'
            '</div><script>const tl=gsap.timeline({paused:true});\n' + "\n".join(tl) +
            '\nwindow.__timelines["main"]=tl;</script></body></html>')
    open(f"{out}/index.html", "w", encoding="utf-8").write(page)
    print(f"{out}  {total}s  {len(sc)} scenes  sfx={'yes' if sfx_dir else 'none found'}\n"
          f"next: npx hyperframes check {out} && npx hyperframes render {out} -o {out}.mp4 && python3 ugc.py qc {out}.mp4 --format vertical")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        print(json.dumps(EXAMPLE, ensure_ascii=False, indent=1))
    elif len(sys.argv) == 2:
        build(json.load(open(sys.argv[1], encoding="utf-8")), os.path.dirname(os.path.abspath(sys.argv[1])))
    else:
        sys.exit(__doc__)
