"""Voice script.json through a local VoiceStudio server -> assets/audio/*.wav + assets/lines.json.
Run from the HyperFrames project folder. Env: VOICESTUDIO_URL, VOICESTUDIO_API_KEY.
A voice is either a saved profile ("profile_id") or designed once ("instruct" + "seed"), then cloned for every
line so it stays the same. Audio is cached by speaker and text, so edits re-voice only the lines that changed."""
import hashlib, json, os, sys, urllib.error, urllib.request, uuid, wave

API = os.environ.get("VOICESTUDIO_URL", "http://localhost:3000").rstrip("/")
KEY = os.environ.get("VOICESTUDIO_API_KEY", "")  # same value as OMNIVOICE_API_KEY on the server; never commit it
GAP = 0.35  # seconds of silence between turns
OUT = "assets/audio"


def post(fields, files=None):
    b = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, path in (files or {}).items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="ref.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
        body += open(path, "rb").read() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={b}"}
    if KEY:
        headers["Authorization"] = f"Bearer {KEY}"
    try:
        data = urllib.request.urlopen(urllib.request.Request(f"{API}/generate", body, headers), timeout=600).read()
    except urllib.error.HTTPError as e:
        sys.exit(f"VoiceStudio error {e.code}: {e.read()[:300]!r}")
    if data[:4] != b"RIFF":
        sys.exit(f"VoiceStudio error: {data[:300]!r}")
    return data


def dur(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


s = json.load(open("script.json"))
os.makedirs(OUT, exist_ok=True)
refs = {}
for who, v in s["voices"].items():
    if "profile_id" in v:  # saved VoiceStudio profile (a real cloned voice): no reference clip to design
        continue
    p, pt = f"{OUT}/ref_{who}.wav", f"{OUT}/ref_{who}.txt"
    if not os.path.exists(p):
        first = next(l["text"] for l in s["lines"] if l["who"] == who)
        open(p, "wb").write(post({"text": first, "instruct": v["instruct"], "language": "English", "seed": v["seed"]}))
        open(pt, "w").write(first)
    refs[who] = (p, open(pt).read())  # ref text must match the clip, even after the script changes

t, out = 0.6, []
for i, l in enumerate(s["lines"]):
    p = f"{OUT}/{hashlib.sha1((l['who'] + l['text']).encode()).hexdigest()[:12]}.wav"
    if not os.path.exists(p):
        v = s["voices"][l["who"]]
        if "profile_id" in v:
            audio = post({"text": l["text"], "profile_id": v["profile_id"], "language": "English"})
        else:
            ref, ref_text = refs[l["who"]]
            audio = post({"text": l["text"], "ref_text": ref_text, "language": "English", "seed": v["seed"]},
                         {"ref_audio": ref})
        open(p, "wb").write(audio)
    d = round(dur(p), 3)
    out.append({**l, "src": p, "start": round(t, 3), "duration": d})
    print(f"{i:02d} {l['who']:5} {t:6.2f}s +{d:.2f}s", flush=True)
    t += d + GAP

json.dump({"total": round(t + 0.6, 2), "lines": out}, open("assets/lines.json", "w"), indent=1)
print("total", round(t + 0.6, 2))
