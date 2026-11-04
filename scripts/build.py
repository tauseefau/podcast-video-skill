"""Generate index.html + compositions/<scene>.html from script.json and assets/lines.json (run make_voice.py first).
Run from the HyperFrames project folder. Output is plain HyperFrames HTML: edit it in Studio, or edit script.json and re-run."""
import array, html, json, os, subprocess

L = json.load(open("assets/lines.json"))
S = json.load(open("script.json"))
CREDITS = json.load(open("assets/img/credits.json")) if os.path.exists("assets/img/credits.json") else {}
TOTAL = L["total"]
SCENES = S["scenes"]  # scene id -> {kicker, title, icon, sub, source}; the last scene carries subscribe + credits
ICON_AT = 0.45  # seconds into a scene, once the wipe has cleared
WIPES = [("xPercent", -100), ("yPercent", -100), ("xPercent", 100)]  # rotated so transitions don't all look alike

missing = [f"assets/img/{sc}.jpg" for sc in SCENES if not os.path.exists(f"assets/img/{sc}.jpg")]
missing += [f"assets/icons/{c['icon']}.svg" for c in SCENES.values() if not os.path.exists(f"assets/icons/{c['icon']}.svg")]
missing += [f for f in ("assets/sfx/whoosh.mp3", "assets/sfx/pop.mp3") if not os.path.exists(f)]
assert not missing, f"missing assets, see SKILL.md: {missing}"
assert {l["who"] for l in L["lines"]} <= set(S["voices"]), "a line uses a voice missing from script.json"



def pcm(path):
    return array.array("h", subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", "8000", "-"],
                                           capture_output=True, check=True).stdout)


def hit(path):
    """(seconds until the loudest 10 ms, duration), so a sound can land on its picture."""
    a = pcm(path)
    env = [sum(abs(x) for x in a[i:i + 80]) for i in range(0, len(a), 80)]
    return round(env.index(max(env)) * 0.01, 3), round(len(a) / 8000, 3)


# three pitches of one whoosh, so repeats don't sound identical
TAKES = ["assets/sfx/whoosh.mp3"]
for n, rate in ((2, 0.84), (3, 1.16)):
    TAKES.append(f"assets/sfx/whoosh{n}.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", TAKES[0], "-af", f"asetrate=44100*{rate},aresample=44100", TAKES[-1]], check=True)
HITS = {t: hit(t) for t in TAKES + ["assets/sfx/pop.mp3"]}

order = list(dict.fromkeys(l["scene"] for l in L["lines"]))
assert order == list(SCENES), f"scene order mismatch: {order}"
firsts = {sc: min(l["start"] for l in L["lines"] if l["scene"] == sc) for sc in order}
bounds = {}
for i, sc in enumerate(order):
    start = 0 if i == 0 else round(firsts[sc] - 0.15, 3)
    end = TOTAL if i == len(order) - 1 else round(firsts[order[i + 1]] - 0.15, 3)
    bounds[sc] = (start, round(end - start, 3))

esc = html.escape
svg = lambda sc: open(f"assets/icons/{SCENES[sc]['icon']}.svg").read()
os.makedirs("compositions", exist_ok=True)

for sc, scene in SCENES.items():
    kicker, title, sub = scene["kicker"], scene["title"], scene.get("sub", "")
    s0, dur = bounds[sc]
    p = sc[:3]  # id prefix, unique per scene
    spk, js = [], []
    for j, l in enumerate(l for l in L["lines"] if l["scene"] == sc):
        v = S["voices"][l["who"]]
        st, d = round(l["start"] - s0, 3), round(l["duration"] + 0.3, 3)
        sid = f"{p}-spk{j}"
        bars = "".join(f'<i class="bar b{k}"></i>' for k in range(5))
        spk.append(f'''    <div id="{sid}" class="clip spk" data-start="{st}" data-duration="{d}" style="--c:{v["color"]}">
      <div class="spk-in">
        <div class="avatar">{v["name"][0]}</div>
        <div class="who"><b>{esc(v["name"])}</b><span>{esc(v["role"])}</span></div>
        <div class="bars">{bars}</div>
      </div>
    </div>''')
        js.append(f'    tl.fromTo("#{sid} .spk-in", {{opacity: 0, x: -30}}, {{opacity: 1, x: 0, duration: 0.35, ease: "power3.out"}}, {st});')
        reps = max(1, int(l["duration"] / 0.26))
        for k in range(5):  # deterministic "talking" bars: fixed heights per bar, finite repeats
            js.append(f'    tl.fromTo("#{sid} .b{k}", {{scaleY: 0.25}}, {{scaleY: {0.55 + 0.45 * ((k * 37) % 5) / 4:.2f}, duration: {0.2 + k * 0.03:.2f}, ease: "sine.inOut", yoyo: true, repeat: {reps}}}, {st + k * 0.05:.2f});')
    credit = ""
    if sc == order[-1]:
        last = round(L["lines"][-1]["start"] - s0, 2)  # closing line
        b, t = round(min(last + 1.6, dur - 3), 2), round(min(last + 6.0, dur - 2), 2)
        team = "".join(f'<span class="chip">{t}</span>' for t in map(esc, S["chips"]))
        credit += f'''    <div id="{p}-sub-btn" class="clip subbtn" data-start="{b}" data-duration="{dur - b:.3f}"><div class="subbtn-in">&#9654;&nbsp; SUBSCRIBE</div></div>
    <div id="{p}-team" class="clip team" data-start="{t}" data-duration="{dur - t:.3f}"><div class="team-in">{team}</div></div>
'''
        js += [f'    tl.fromTo("#{p}-sub-btn .subbtn-in", {{opacity: 0, scale: 0.6}}, {{opacity: 1, scale: 1, duration: 0.5, ease: "back.out(2)"}}, {b});',
               f'    tl.to("#{p}-sub-btn .subbtn-in", {{scale: 1.06, duration: 0.6, ease: "sine.inOut", yoyo: true, repeat: {max(0, int((dur - b - 1) / 0.6))}}}, {b + 0.5});',
               f'    tl.fromTo("#{p}-team .chip", {{opacity: 0, y: 20}}, {{opacity: 1, y: 0, duration: 0.4, ease: "power3.out", stagger: 0.15}}, {t});']
        names = " · ".join(sorted({c["artist"] for c in CREDITS.values()}))
        photos = (f" · Photos: {esc(names)}" if names else "") + " · Icons: Lucide (ISC)"
        credit += f'    <p id="{p}-credit" class="clip credit" data-start="0.2" data-duration="{dur - 0.2:.3f}">Voices generated locally with VoiceStudio{photos}</p>'
    src = f'      <p class="src">{esc(scene["source"])}</p>' if scene.get("source") else ""
    subp = f'      <p class="sub" id="{p}-sub">{esc(sub)}</p>' if sub else ""
    open(f"compositions/{sc}.html", "w").write(f'''<template>
  <style>
    #{sc} {{ position: absolute; inset: 0; overflow: hidden; background: #14100d; font-family: Inter, sans-serif; color: #f6efe6; }}
    #{sc} .bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
    #{sc} .shade {{ position: absolute; inset: 0; background: linear-gradient(90deg, rgba(14,10,8,.92) 0%, rgba(14,10,8,.72) 45%, rgba(14,10,8,.25) 100%), linear-gradient(0deg, rgba(14,10,8,.85) 0%, rgba(14,10,8,0) 40%); }}
    #{sc} .bug {{ position: absolute; left: 140px; top: 96px; font: 700 22px Inter; letter-spacing: .28em; text-transform: uppercase; color: #f6efe6; opacity: .85; }}
    #{sc} .bug i {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #ff4d4d; margin-right: 14px; vertical-align: 2px; }}
    #{sc} .card {{ position: absolute; left: 140px; top: 300px; width: 1050px; }}
    #{sc} .icon {{ position: absolute; left: 140px; top: 176px; width: 96px; height: 96px; border-radius: 50%; background: #ffb27a; color: #14100d; display: flex; align-items: center; justify-content: center; }}
    #{sc} .icon svg {{ width: 56px; height: 56px; }}
    #{sc} .kicker {{ font: 700 26px Inter; letter-spacing: .22em; text-transform: uppercase; color: #ffb27a; margin-bottom: 26px; }}
    #{sc} h1 {{ font: 700 92px/1.04 "Playfair Display", serif; letter-spacing: -.01em; }}
    #{sc} .sub {{ font: 400 36px/1.4 Inter; margin-top: 30px; color: #e9dfd2; max-width: 980px; }}
    #{sc} .src {{ font: 400 22px Inter; margin-top: 22px; color: #b9ad9f; }}
    #{sc} .spk {{ position: absolute; left: 140px; bottom: 120px; }}
    #{sc} .spk-in {{ display: flex; align-items: center; gap: 24px; padding: 20px 34px 20px 20px; border-radius: 999px; background: rgba(20,16,13,.78); border: 2px solid var(--c); }}
    #{sc} .avatar {{ width: 76px; height: 76px; border-radius: 50%; background: var(--c); color: #14100d; font: 900 38px/76px Inter; text-align: center; }}
    #{sc} .who b {{ display: block; font: 700 34px Inter; }}
    #{sc} .who span {{ font: 400 24px Inter; color: #d8ccbd; }}
    #{sc} .bars {{ display: flex; gap: 7px; align-items: center; height: 56px; margin-left: 14px; }}
    #{sc} .bar {{ width: 8px; height: 56px; border-radius: 4px; background: var(--c); transform-origin: 50% 50%; }}
    #{sc} .subbtn {{ position: absolute; right: 140px; top: 300px; }}
    #{sc} .subbtn-in {{ background: #ff0033; color: #fff; font: 900 40px Inter; letter-spacing: .06em; padding: 26px 48px; border-radius: 14px; }}
    #{sc} .team {{ position: absolute; left: 140px; top: 640px; }}
    #{sc} .team-in {{ display: flex; gap: 16px; }}
    #{sc} .chip {{ font: 700 24px Inter; padding: 12px 22px; border-radius: 999px; border: 2px solid #ffb27a; color: #ffe2cc; background: rgba(20,16,13,.6); }}
    #{sc} .credit {{ position: absolute; left: 140px; right: 140px; bottom: 60px; font: 400 18px/1.5 Inter; color: #b9ad9f; }}
  </style>
  <div id="{sc}" data-composition-id="{sc}" data-width="1920" data-height="1080">
    <img id="{p}-bg" class="bg" src="assets/img/{sc}.jpg" alt="" />
    <div class="shade"></div>
    <div class="bug"><i></i>{esc(S["show"])}</div>
    <div id="{p}-icon" class="icon">{svg(sc)}</div>
    <div id="{p}-card" class="card">
      <p class="kicker" id="{p}-kicker">{esc(kicker)}</p>
      <h1 id="{p}-title">{esc(title)}</h1>
{subp}
{src}
    </div>
{chr(10).join(spk)}
{credit}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.fromTo("#{p}-bg", {{scale: 1.0}}, {{scale: 1.08, duration: {dur}, ease: "none"}}, 0);
    tl.fromTo("#{p}-card", {{opacity: 0}}, {{opacity: 1, duration: 0.4, ease: "power2.out"}}, 0.1);
    tl.fromTo("#{p}-kicker", {{opacity: 0, y: 24}}, {{opacity: 1, y: 0, duration: 0.5, ease: "power3.out"}}, 0.2);
    tl.fromTo("#{p}-title", {{opacity: 0, y: 40}}, {{opacity: 1, y: 0, duration: 0.7, ease: "power3.out"}}, 0.35);
{f'    tl.fromTo("#{p}-sub", {{opacity: 0, y: 24}}, {{opacity: 1, y: 0, duration: 0.6, ease: "power3.out"}}, 0.75);' if sub else ""}
    tl.fromTo("#{p}-icon", {{opacity: 0, scale: 0.4}}, {{opacity: 1, scale: 1, duration: 0.45, ease: "back.out(2.5)"}}, {ICON_AT});
{chr(10).join(js)}
    window.__timelines["{sc}"] = tl;
  </script>
</template>
''')

# one full-frame wipe per topic change: covers the frame on the cut, in the colour of whoever speaks next
seams = [bounds[sc][0] for sc in order[1:]]
panels, wjs, sfx = [], [], []
for i, (sc, at) in enumerate(zip(order[1:], seams)):
    axis, frm = WIPES[i % len(WIPES)]
    who = next(l["who"] for l in L["lines"] if l["scene"] == sc)
    panels.append(f'    <div id="wipe{i}" class="panel" style="background:{S["voices"][who]["color"]}">{svg(sc)}</div>')
    wjs += [f'    tl.set("#wipe{i}", {{{axis}: {frm}}}, 0);',
            f'    tl.to("#wipe{i}", {{{axis}: 0, duration: 0.28, ease: "power3.in"}}, {round(at - 0.28, 3)});',
            f'    tl.to("#wipe{i}", {{{axis}: {-frm}, duration: 0.32, ease: "power3.out"}}, {round(at + 0.06, 3)});']
    take = TAKES[i % 3]
    sfx.append(f'''      <audio id="wh{i}" class="clip" src="{take}" data-start="{max(0, round(at + 0.033 - HITS[take][0], 3))}" data-duration="{HITS[take][1]}" data-volume="0.6" data-track-index="90"></audio>''')
for i, sc in enumerate(order):  # pop peaks as the icon's scale-up overshoots
    pk, d = HITS["assets/sfx/pop.mp3"]
    sfx.append(f'''      <audio id="pop{i}" class="clip" src="assets/sfx/pop.mp3" data-start="{max(0, round(bounds[sc][0] + ICON_AT + 0.15 - pk, 3))}" data-duration="{d}" data-volume="0.5" data-track-index="91"></audio>''')
open("compositions/wipes.html", "w").write(f'''<template>
  <style>
    #wipes {{ position: absolute; inset: 0; overflow: hidden; }}
    #wipes .panel {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #14100d; }}
    #wipes .panel svg {{ width: 220px; height: 220px; }}
  </style>
  <div id="wipes" data-composition-id="wipes" data-width="1920" data-height="1080" data-layout-allow-overflow>
{chr(10).join(panels)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(wjs)}
    tl.set({{}}, {{}}, {TOTAL});
    window.__timelines["wipes"] = tl;
  </script>
</template>
''')

hosts = "\n".join(f'''      <div id="{sc}" data-composition-id="{sc}" data-composition-src="compositions/{sc}.html" data-start="{bounds[sc][0]}" data-duration="{bounds[sc][1]}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>''' for sc in order)
hosts += f'''\n      <div id="wipes" data-composition-id="wipes" data-composition-src="compositions/wipes.html" data-start="0" data-duration="{TOTAL}" data-track-index="80" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 10"></div>'''
audios = "\n".join(f'''      <audio id="vo{i:02d}" class="clip" src="{l["src"]}" data-start="{l["start"]}" data-duration="{l["duration"]}" data-track-index="{list(S["voices"]).index(l["who"]) + 2}"></audio>''' for i, l in enumerate(L["lines"]))
open("index.html", "w").write(f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #14100d; }}
      #root {{ position: relative; width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{hosts}
{audios}
{chr(10).join(sfx)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
''')
print("scenes:", {k: v for k, v in bounds.items()}, "total", TOTAL)
