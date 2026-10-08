#!/usr/bin/env python3
"""wow_reel.py — Rail 5 v2: the "wow" reel, upgraded (2026-10-08).
Keeps what Leeya loved in the 06/10 reel (3D icons / social / AI logos popping on the spoken word) and adds:
hook-first opening (no logo intro), optional white editorial header, AI b-roll cutaways (Grok Imagine / Kling …)
over her voice, karaoke captions (spoken word highlighted), jump cuts between segments with alternating punch-in,
progress bar (fills right→left in RTL), short CTA outro in her own words. Output = HyperFrames project.

  python3 wow_reel.py spec.json   →  <out>/index.html + mix.mp3 + clips/ + b/ + img/
  npx hyperframes check <out> && npx hyperframes render <out> -o <out>.mp4

Spec keys: out, rtl, music, music_vol, colors{gold,red}, header{height}|null, hook{lines[],until},
lower[name,brand] + lower_at[start,end], outro{wordmark,lines[],url,dur}, replace{},
segments[{id,video,words,start,end,video_end?,crop_top?}], cutaways[{seg,at|t,lead?,dur,video,from?}],
cards[{seg,icons[[kind,key,word]],label,at,until|dur}] (kinds: fl=Fluent 3D, brand=simple-icons, ai=lobe-icons).
Words: `ugc.py transcribe`. Word lookups are per segment, in order; a missing word stops the build loudly.
"""
import html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ugc import ffbin, load_words, run  # noqa: E402
from icons_reel import icon_asset, icon_html, norm, SFX_DIRS  # noqa: E402

W, H = 1080, 1920
COVER = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30"


def build(spec, base):
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)  # noqa: E731
    out = P(spec.get("out", "reel"))
    for d in ("clips", "b", "img"):
        os.makedirs(f"{out}/{d}", exist_ok=True)
    ff = ffbin("ffmpeg")
    rtl = spec.get("rtl", False)
    dirc = "direction:rtl" if rtl else "direction:ltr"
    gold = spec.get("colors", {}).get("gold", "#c9a961")
    red = spec.get("colors", {}).get("red", "#e3122c")
    hdr = (spec.get("header") or {}).get("height", 0)
    sfx_dir = next((d for d in SFX_DIRS if os.path.isdir(d)), None)
    T = lambda x: round(x, 3)  # noqa: E731

    # ---------- segments: her real speech, jump-cut together ----------
    segs, t = [], 0.0
    for s in spec["segments"]:
        a, b = float(s["start"]), float(s["end"])
        vend = float(s.get("video_end", b))
        mp4, wav = f"{out}/clips/{s['id']}.mp4", f"{out}/clips/{s['id']}.wav"
        if not os.path.exists(mp4):
            ct = int(s.get("crop_top", 0))
            vf = (f"crop=iw:ih-{ct}:0:{ct}," if ct else "") + COVER
            run([ff, "-y", "-loglevel", "error", "-ss", str(a), "-to", str(vend), "-i", P(s["video"]), "-an", "-vf", vf,
                 "-c:v", "libx264", "-g", "30", "-keyint_min", "30", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", mp4])
            run([ff, "-y", "-loglevel", "error", "-ss", str(a), "-to", str(b), "-i", P(s["video"]), "-vn",
                 "-af", f"afade=t=in:d=0.02,afade=t=out:st={b - a - 0.03:.3f}:d=0.03", "-ac", "2", "-ar", "44100", wav])
        ws = [(w, t + st - a, t + en - a) for w, st, en in load_words(P(s["words"])) if a - 0.05 <= st <= b - 0.05]
        segs.append(dict(id=s["id"], g=t, vdur=vend - a, adur=b - a, words=ws))
        t += vend - a
    vid_end = t
    od = float(spec.get("outro", {}).get("dur", 3.4))
    total = round(vid_end + od, 3)
    seg_by = {s["id"]: s for s in segs}

    def find(seg, tok, after=-1.0):
        ws = [x for x in seg_by[seg]["words"] if x[1] >= after - 0.01]
        for exact in (True, False):  # exact word first: 'יוטיוב' must not match 'ביוטיוב'
            for w, st, en in ws:
                if norm(tok) and (norm(tok) == norm(w) if exact else norm(tok) in norm(w)):
                    return st, en
        sys.exit(f"wow_reel: word '{tok}' not found in segment {seg}")

    # ---------- audio bookkeeping ----------
    inp, flt, vo, sf = [], [], [], []

    def add(path, at, vol=1.0, loop=False):
        i = len([x for x in inp if x == "-i"])
        inp.extend((["-stream_loop", "-1"] if loop else []) + ["-i", path])
        ms = max(0, int(at * 1000))
        flt.append(f"[{i}:a]adelay={ms}|{ms},volume={vol}[x{i}]")
        return i

    def sfx(name, at, vol):
        if sfx_dir and os.path.exists(f"{sfx_dir}/{name}"):
            sf.append(add(f"{sfx_dir}/{name}", at, vol))

    for s in segs:
        vo.append(add(f"{out}/clips/{s['id']}.wav", s["g"]))

    vids, layers, tl = [], [], []
    # her segments: alternate framing on every jump cut, slow push-in inside each
    for k, s in enumerate(segs):
        z0 = 1.0 if k % 2 == 0 else 1.1
        vids.append(f'<video id="v{k}" class="clip vfull seg" src="clips/{s["id"]}.mp4" data-start="{T(s["g"])}" '
                    f'data-duration="{T(s["vdur"])}" data-track-index="2" muted playsinline></video>')
        tl.append(f'tl.fromTo("#v{k}",{{scale:{z0}}},{{scale:{z0 + 0.035},duration:{T(s["vdur"])},ease:"none"}},{T(s["g"])});')

    # cutaways: AI b-roll over her voice
    for i, c in enumerate(spec.get("cutaways", [])):
        st = float(c["t"]) if "t" in c else find(c["seg"], c["at"])[0] - float(c.get("lead", 0.15))
        du = float(c["dur"])
        dst = f"{out}/b/c{i}.mp4"
        if not os.path.exists(dst):
            run([ff, "-y", "-loglevel", "error", "-ss", str(c.get("from", 0)), "-t", str(du), "-i", P(c["video"]), "-an",
                 "-vf", COVER, "-c:v", "libx264", "-g", "30", "-keyint_min", "30", "-crf", "16", "-pix_fmt", "yuv420p", dst])
        vids.append(f'<video id="b{i}" class="clip vfull cut" src="b/c{i}.mp4" data-start="{T(st)}" data-duration="{T(du)}" '
                    f'data-track-index="3" muted playsinline></video>')
        tl.append(f'tl.fromTo("#b{i}",{{scale:1.12}},{{scale:1.0,duration:{T(du)},ease:"power2.out"}},{T(st)});')
        sfx("whoosh-short.mp3", st - 0.05, 0.35)

    # header (white editorial band) + hook title + small wordmark
    hook = spec.get("hook")
    if hdr:
        layers.append(f'<div class="header" style="height:{hdr}px"><div class="mark" id="mark">{html.escape(spec.get("outro", {}).get("wordmark", ""))}</div></div>')
        tl.append(f'tl.fromTo("#mark",{{opacity:0}},{{opacity:1,duration:.5}},{T((hook or {}).get("until", 0) + 0.2)});')
    if hook:
        lines = "".join('<div class="hl">' + " ".join(f'<span class="hw">{html.escape(w)}</span>' for w in ln.split()) + "</div>"
                        for ln in hook["lines"])  # spaces outside inline-blocks, or the words glue together
        top = max((hdr - 2 * 92) // 2, 40) if hdr else 230
        boxed = "" if hdr else " boxed"  # no header: white card behind the title so it reads on any footage
        layers.append(f'<div class="hook{boxed}" id="hook" style="top:{hook.get("top", top)}px;--hs:{hook.get("size", 76)}px;{dirc}">{lines}<div class="hbar" id="hbar"></div></div>')
        tl.append('tl.set("#hook",{autoAlpha:1},0);')
        tl.append('tl.fromTo("#hook .hw",{opacity:0,y:28,scale:.92},{opacity:1,y:0,scale:1,duration:.35,ease:"back.out(2)",stagger:.06},0.02);')
        tl.append('tl.fromTo("#hbar",{scaleX:0},{scaleX:1,duration:.5,ease:"power3.out"},0.45);')
        tl.append(f'tl.to("#hook",{{autoAlpha:0,y:-20,duration:.3}},{T(float(hook["until"]))});')

    # icon cards (06/10 style she loved)
    card_top = (hdr - 300) // 2 + 20 if hdr else 64
    for ci, cd in enumerate(spec.get("cards", [])):
        icons = cd.get("icons", [])
        for kd, ky, _ in icons:
            icon_asset(kd, ky, f"{out}/img")
        a0 = find(cd["seg"], cd["at"])[0] - 0.05
        first = min([find(cd["seg"], tk, a0 - 0.3)[0] for _, _, tk in icons] + [a0 + 0.05]) - 0.05
        T0 = min(a0, first)
        end = find(cd["seg"], cd["until"], T0)[1] + 0.3 if cd.get("until") else T0 + float(cd.get("dur", 2.2))
        cid = f"k{ci}"
        ih = "".join(icon_html(kd, ky, f"{out}/img") for kd, ky, _ in icons)
        lh = f'<div class="lab" style="{dirc}">{html.escape(cd["label"])}</div>' if cd.get("label") else ""
        layers.append(f'<div class="card{" multi" if len(icons) >= 3 else ""}" id="{cid}" style="top:{cd.get("top", card_top)}px;{dirc}"><div class="irow">{ih}</div>{lh}</div>')
        tl.append(f'tl.fromTo("#{cid}",{{autoAlpha:0}},{{autoAlpha:1,duration:.2}},{T(T0)});')
        for ii, (kd, ky, tk) in enumerate(icons):
            ta = max(find(cd["seg"], tk, a0 - 0.3)[0] - 0.02, T0)
            sel = f"#{cid} .ic:nth-child({ii + 1})"
            tl.append(f'tl.fromTo("{sel}",{{scale:0,rotateY:-100,opacity:0}},{{scale:1,rotateY:0,opacity:1,duration:.75,ease:"back.out(2.2)"}},{T(ta)});')
            tl.append(f'tl.fromTo("{sel} .shine",{{x:"-130%"}},{{x:"230%",duration:.9,ease:"power2.inOut"}},{T(ta + .3)});')
            tl.append(f'tl.fromTo("{sel}",{{y:0}},{{y:-9,duration:1.1,yoyo:true,repeat:1,ease:"sine.inOut"}},{T(ta + .8)});')
            sfx("sparkle.mp3" if kd == "ai" else "pop.mp3", ta, 0.4)
        if cd.get("label"):
            tl.append(f'tl.fromTo("#{cid} .lab",{{opacity:0,x:-40,scale:.9}},{{opacity:1,x:0,scale:1,duration:.55,ease:"back.out(1.6)"}},{T(T0 + 0.25)});')
        tl.append(f'tl.to("#{cid}",{{autoAlpha:0,y:-24,duration:.3}},{T(end)});')

    # karaoke captions: one line at a time, the spoken word lights up in brand red
    rep = spec.get("replace", {})
    caps = ""
    for s in segs:
        chunks, cur = [], []
        for w in s["words"]:
            if cur and sum(len(x[0]) + 1 for x in cur) + len(w[0]) > 20:
                chunks.append(cur)
                cur = []
            cur.append(w)
            if re.search(r"[.?!]$", w[0]) or (len(cur) >= 2 and re.search(r"[,;:]$", w[0])) or len(cur) >= 4:
                chunks.append(cur)
                cur = []
        if cur:
            if len(cur) == 1 and chunks and len(chunks[-1]) < 4:
                chunks[-1] += cur
            else:
                chunks.append(cur)
        for j, c in enumerate(chunks):
            lid = f"c_{s['id']}_{j}"
            spans = ""
            for wi, (w, st, en) in enumerate(c):
                txt = w
                for k2, v2 in rep.items():
                    txt = txt.replace(k2, v2)
                txt = re.sub(r"[.,?!;:…]+$", "", txt)
                spans += f'<span class="w" id="{lid}_{wi}">{html.escape(txt)}</span> '
                nxt = c[wi + 1][1] if wi + 1 < len(c) else en + 0.08
                tl.append(f'tl.to("#{lid}_{wi}",{{backgroundColor:"{red}",color:"#ffffff",scale:1.06,duration:.06}},{T(st)});')
                tl.append(f'tl.to("#{lid}_{wi}",{{backgroundColor:"rgba(250,44,44,0)",scale:1,duration:.08}},{T(max(nxt, st + 0.12))});')
            caps += f'<div class="cap" id="{lid}" style="{dirc}"><span class="box">{spans.strip()}</span></div>'
            a = c[0][1] - 0.03
            b = c[-1][2] + 0.12
            if j + 1 < len(chunks):
                b = min(b, chunks[j + 1][0][1] - 0.04)
            tl.append(f'tl.set("#{lid}",{{autoAlpha:1}},{T(a)});tl.set("#{lid}",{{autoAlpha:0}},{T(max(b, a + 0.3))});')
    layers.append(caps)

    # lower third, once
    if spec.get("lower"):
        la, lb = spec.get("lower_at", [3.0, 7.0])
        nm, br = spec["lower"]
        side = "right" if rtl else "left"
        layers.append(f'<div class="lower" id="lower" style="{side}:60px;{dirc}"><div class="rule gold" id="lg"></div>'
                      f'<div class="who">{html.escape(nm)}</div><div class="who2">{html.escape(br)}</div></div>')
        tl.append(f'tl.fromTo("#lower",{{autoAlpha:0,x:{40 if rtl else -40}}},{{autoAlpha:1,x:0,duration:.45,ease:"power3.out"}},{T(la)});')
        tl.append(f'tl.to("#lower",{{autoAlpha:0,duration:.35}},{T(lb)});')

    # progress bar (retention cue) — fills in reading direction
    layers.append(f'<div class="prog" id="prog" style="top:{hdr}px;transform-origin:{"right" if rtl else "left"} center"></div>')
    tl.append(f'tl.fromTo("#prog",{{scaleX:0}},{{scaleX:1,duration:{T(vid_end)},ease:"none"}},0);')
    tl.append(f'tl.to("#prog",{{opacity:0,duration:.2}},{T(vid_end)});')

    # outro: CTA in her words
    o = spec.get("outro", {})
    letters = "".join(f'<span class="lt">{html.escape(ch)}</span>' for ch in o.get("wordmark", ""))
    ctas = "".join(f'<div class="cta" style="{dirc}">{html.escape(x)}</div>' for x in o.get("lines", []))
    url = f'<div class="url">{html.escape(o["url"])}</div>' if o.get("url") else ""
    sec = (f'<section id="outro" class="clip scene opaque cen" data-start="{T(vid_end)}" data-duration="{T(od)}">'
           f'<div class="ring"><svg viewBox="0 0 400 400"><circle id="r9" cx="200" cy="200" r="190"/></svg></div>'
           f'<div class="wm">{letters}</div><div class="rule red" id="rr9"></div>{ctas}{url}</section>')
    s0 = vid_end
    tl += [f'tl.fromTo("#r9",{{strokeDashoffset:1200}},{{strokeDashoffset:0,duration:1.3,ease:"power2.inOut"}},{T(s0 + .05)});',
           f'tl.fromTo("#outro .lt",{{yPercent:110,opacity:0}},{{yPercent:0,opacity:1,duration:.55,ease:"back.out(1.6)",stagger:.045}},{T(s0 + .1)});',
           f'tl.fromTo("#rr9",{{scaleX:0}},{{scaleX:1,duration:.5,ease:"power3.out"}},{T(s0 + .6)});',
           f'tl.fromTo("#outro .cta",{{opacity:0,y:26,scale:.95}},{{opacity:1,y:0,scale:1,duration:.5,ease:"back.out(1.8)",stagger:.15}},{T(s0 + .75)});',
           f'tl.fromTo("#outro .url",{{opacity:0}},{{opacity:1,duration:.5}},{T(s0 + 1.2)});']
    sfx("whoosh-short.mp3", s0 - 0.05, 0.4)
    sfx("impact-bass-1.mp3", s0 + 0.05, 0.55)
    sfx("sparkle.mp3", s0 + 0.8, 0.35)

    # ---------- mix: voice 100 %, music ducked (sidechain), SFX, -16 LUFS ----------
    mix = [f'{"".join(f"[x{i}]" for i in vo)}amix=inputs={len(vo)}:normalize=0,apad=whole_dur={total}[vo]']
    final = "[vo]"
    if spec.get("music"):
        m = len([x for x in inp if x == "-i"])
        inp.extend(["-stream_loop", "-1", "-i", P(spec["music"])])
        mv = spec.get("music_vol", 0.45)
        mix[0] += ";[vo]asplit=2[vo1][vo2]"
        mix.append(f"[{m}:a]atrim=0:{total},afade=t=in:d=0.6,afade=t=out:st={total - 1.6}:d=1.6,volume={mv}[bg];"
                   "[bg][vo2]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[bgd]")
        final = "[vo1][bgd]"
    if sf:
        mix.append(f'{"".join(f"[x{i}]" for i in sf)}amix=inputs={len(sf)}:normalize=0,apad=whole_dur={total}[sfx]')
        final += "[sfx]"
    n_in = final.count("[")
    mix.append((f"{final}amix=inputs={n_in}:normalize=0," if n_in > 1 else final) + f"loudnorm=I=-16:TP=-1.5:LRA=9,atrim=0:{total}[out]")
    run([ff, "-y", "-loglevel", "error"] + inp + ["-filter_complex", ";".join(flt + mix), "-map", "[out]",
         "-ar", "44100", "-b:a", "192k", f"{out}/mix.mp3"])

    css = f'''body{{margin:0;background:#fff;color:#0a0a0a;font-family:"Heebo","Open Sans",system-ui,-apple-system,Arial,sans-serif}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#000}}
.vfull{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform-origin:50% 38%}}
.seg{{z-index:1}}.cut{{z-index:8}}
.header{{position:absolute;left:0;right:0;top:0;background:#fff;z-index:5;border-bottom:2px solid {gold}}}
.mark{{position:absolute;bottom:26px;left:0;right:0;text-align:center;font-family:"Open Sans",Arial,sans-serif;font-weight:600;font-size:30px;letter-spacing:.5em;padding-inline-start:.5em;color:#0a0a0a;opacity:0}}
.hook{{position:absolute;left:60px;right:60px;z-index:12;text-align:center;visibility:hidden}}
.hl{{font-weight:800;font-size:var(--hs,76px);line-height:1.15;color:#0a0a0a}}
.hw{{display:inline-block}}
.hook.boxed{{left:70px;right:70px;background:#fff;border-radius:30px;padding:22px 28px 24px;box-shadow:0 18px 44px rgba(0,0,0,.35)}}
.hbar{{height:10px;width:280px;margin:18px auto 0;background:{red};transform-origin:center;border-radius:5px}}
.card{{position:absolute;left:40px;right:40px;z-index:20;display:flex;align-items:center;justify-content:center;gap:26px;visibility:hidden;perspective:900px}}
.irow{{display:flex;gap:22px;align-items:center}}.card.multi{{flex-direction:column;gap:16px}}.card.multi .tile{{width:128px;height:128px;border-radius:30px}}.card.multi .lab{{font-size:42px;padding:12px 30px}}
.ic{{opacity:0;transform-style:preserve-3d}}
.tile{{position:relative;width:170px;height:170px;border-radius:40px;overflow:hidden;box-shadow:0 18px 30px rgba(0,0,0,.4),inset 0 3px 0 rgba(255,255,255,.55);display:flex;align-items:center;justify-content:center}}
.tile svg{{width:62%;height:62%}}.tile.white{{background:#fff}}.tile .ai{{width:66%;height:66%;object-fit:contain}}
.shine{{position:absolute;top:-20%;left:0;width:45%;height:140%;background:rgba(255,255,255,.55);transform:skewX(-20deg) translateX(-130%)}}
.fl{{width:176px;height:176px;object-fit:contain;filter:drop-shadow(0 16px 18px rgba(0,0,0,.4))}}
.lab{{background:#fff;color:#0a0a0a;font-weight:800;font-size:50px;padding:16px 36px;border-radius:999px;border:3px solid {gold};box-shadow:0 14px 26px rgba(0,0,0,.28);opacity:0;white-space:nowrap}}
.cap{{position:absolute;left:40px;right:40px;bottom:470px;z-index:30;text-align:center;visibility:hidden;font-weight:800;font-size:66px;line-height:1.3;color:#fff}}
.cap .box{{display:inline-block;background:rgba(10,10,10,.8);padding:12px 18px;border-radius:22px;box-shadow:0 10px 30px rgba(0,0,0,.25)}}
.cap .w{{display:inline-block;padding:2px 12px;border-radius:14px;background:rgba(0,0,0,0)}}
.lower{{visibility:hidden;position:absolute;bottom:250px;z-index:25;display:flex;flex-direction:column;gap:8px;align-items:{"flex-end" if rtl else "flex-start"};color:#fff;background:rgba(10,10,10,.72);padding:20px 32px;border-radius:6px}}
.rule{{height:2px;width:120px;transform-origin:center}}.gold{{background:{gold}}}.red{{background:{red};width:140px}}
.who{{font-size:42px;font-weight:800}}.who2{{font-size:26px;letter-spacing:.42em;color:{gold};font-family:"Open Sans",Arial,sans-serif}}
.prog{{position:absolute;left:0;right:0;height:9px;background:{red};z-index:40}}
.scene{{position:absolute;inset:0;overflow:hidden;z-index:50}}.opaque{{background:#fff}}
.cen{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px}}
.ring{{position:absolute;width:820px;height:820px;top:50%;left:50%;margin:-410px 0 0 -410px}}
.ring svg{{width:100%;height:100%;transform:rotate(-90deg)}}.ring circle{{fill:none;stroke:{gold};stroke-width:2;stroke-dasharray:1200;stroke-dashoffset:1200}}
.wm{{font-family:"Open Sans",Arial,sans-serif;font-size:64px;font-weight:600;letter-spacing:.4em;padding-inline-start:.4em;position:relative;white-space:nowrap;overflow:hidden}}.lt{{display:inline-block}}
.cta{{font-size:66px;font-weight:800;color:#0a0a0a;position:relative}}
.url{{font-family:"Open Sans",Arial,sans-serif;font-size:34px;letter-spacing:.18em;color:#6b6b6b;position:relative}}'''
    # never <html dir="rtl"> (renders black in HyperFrames) — direction is set per element
    page = (f'<!doctype html><html lang="{"he" if rtl else "en"}"><head><meta charset="UTF-8"><meta name="viewport" content="width={W}, height={H}">'
            f'<title>{html.escape(spec.get("outro", {}).get("wordmark", "reel"))}</title>'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;800&family=Open+Sans:wght@600;700&display=block" rel="stylesheet">'
            f'<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script><style>{css}</style></head><body>\n'
            f'<div id="root" data-composition-id="main" data-start="0" data-width="{W}" data-height="{H}" data-duration="{total}">\n'
            + "\n".join(vids) + "\n" + "\n".join(layers) + "\n" + sec +
            f'\n<audio id="mix" src="mix.mp3" data-start="0" data-duration="{total}" data-track-index="9"></audio>\n'
            '</div><script>const tl=gsap.timeline({paused:true});\n' + "\n".join(tl) +
            '\nwindow.__timelines["main"]=tl;</script></body></html>')
    open(f"{out}/index.html", "w", encoding="utf-8").write(page)
    print(f"{out}  total {total}s (speech {vid_end:.2f}s + outro {od}s)  segments {len(segs)}  cutaways {len(spec.get('cutaways', []))}  "
          f"cards {len(spec.get('cards', []))}  sfx={'yes' if sfx_dir else 'none'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(json.load(open(sys.argv[1], encoding="utf-8")), os.path.dirname(os.path.abspath(sys.argv[1])))
