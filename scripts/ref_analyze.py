"""Referens reelni HAMMA jihatdan tahlil qilish (uslub o'rganish uchun) — video-use vositalari + bizning whisper.

python ~/.claude/skills/uslub-klon/scripts/ref_analyze.py <video.mp4> [out_dir]   (odatda learn.py chaqiradi)
  out_dir standart: <video papkasi>/<stem>_an/

Natija (out_dir):
  report.md                  — barcha o'lchovlar + STYLE.md uchun to'ldiriladigan ro'yxat
  edit/transcripts/<stem>.json, edit/takes_packed.md   — so'z-darajali transkript (whisper) + video-use frazali ko'rinishi
  contact_NN.jpg             — 2 fps varaqlar (16 s bo'lak, har qator 4 s)
  tv_*.png                   — video-use timeline_view: filmstrip + to'lqin + so'zlar (huk, yakun, kesimlar)
  shots.json                 — har kadr: vaqt, grade, harakat, kesim-nutq munosabati

Transkripsiya: video-use Scribe (ElevenLabs) ISHLATILMAYDI — foydalanuvchi taqiqi. tr.py (faster-whisper) chiqishi
video-use formatiga mos ({"words":[{"text","start","end"}]}), shuning uchun pack_transcripts/timeline_view uni o'qiydi.
video-use: ~/video-use (yo'q bo'lsa: git clone --depth 1 https://github.com/browser-use/video-use ~/video-use).
"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VU = os.environ.get("VIDEO_USE_DIR", os.path.expanduser("~/video-use"))
PY = sys.executable
src = os.path.abspath(sys.argv[1])
stem = os.path.splitext(os.path.basename(src))[0]
OUT = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(os.path.dirname(src), f"{stem}_an")
ED = os.path.join(OUT, "edit"); TRD = os.path.join(ED, "transcripts")
os.makedirs(TRD, exist_ok=True)

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def pcm(af="", sr=16000):
    c = ["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", str(sr)] + (["-af", af] if af else []) + ["-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(c, capture_output=True).stdout, np.float32).astype(np.float64)

def db(x):
    return 10 * np.log10(np.mean(x ** 2) + 1e-12) if len(x) else -120.0

# ---------- 1. Texnik ----------
pr = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", src]).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video")
fps = eval(v["r_frame_rate"]); DUR = float(pr["format"]["duration"]); W, H = int(v["width"]), int(v["height"])
eb = run(["ffmpeg", "-hide_banner", "-i", src, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr.split("Summary:")[-1]
g = lambda k: (re.search(k + r":\s+(-?[\d.]+)", eb) or [None, "nan"])[1]
LUFS, LRA, TP = float(g("I")), float(g("LRA")), float(g("Peak"))
info = {}
ij = os.path.join(os.path.dirname(src), stem + ".info.json")
if os.path.exists(ij):
    d = json.load(open(ij)); info = {k: d.get(k) for k in ("uploader", "channel", "like_count", "description", "webpage_url")}

# ---------- 2. Transkript (whisper -> video-use formati) ----------
TJ = os.path.join(TRD, stem + ".json")                 # video-use formati: {"words": [...]}
WJ = os.path.join(OUT, "whisper", stem + ".json")      # tr.py chiqishi: so'zlar ro'yxati (+ -segments.json)
if os.path.exists(TJ) and isinstance(json.load(open(TJ)), list):   # eski versiya tr.py chiqishini shu yerga yozgan
    os.makedirs(os.path.dirname(WJ), exist_ok=True); os.replace(TJ, WJ)
    sg = TJ.replace(".json", "-segments.json")
    if os.path.exists(sg): os.replace(sg, WJ.replace(".json", "-segments.json"))
if not os.path.exists(TJ):
    os.makedirs(os.path.dirname(WJ), exist_ok=True)
    if not os.path.exists(WJ):
        wav = os.path.join(OUT, "audio16k.wav")
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav])
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        r = run([PY, os.path.join(SK, "scripts", "tr.py"), wav, WJ, os.environ.get("REF_LANG", "uz")], env=env)
        if not os.path.exists(WJ):
            print(r.stdout[-800:], r.stderr[-800:]); sys.exit("transkript chiqmadi")
    wl = json.load(open(WJ))
    wl = wl.get("words", []) if isinstance(wl, dict) else wl
    # whisper so'z chegaralari pauzalarni "yeydi" (so'zlar ketma-ket yopishadi) -> nutq polosasi energiyasi bo'yicha
    # har so'zni ovozli qismiga qisqartir; shunda pauzalar video-use pack/timeline_view'da ko'rinadi.
    _b = pcm("highpass=f=300,lowpass=f=3400"); _n = len(_b) // 160
    E10 = 10 * np.log10(np.mean(_b[: _n * 160].reshape(_n, 160) ** 2, 1) + 1e-12)       # 10 ms
    _thr = np.median([E10[int(w["start"] * 100):int(w["end"] * 100) + 1].max() for w in wl if int(w["end"] * 100) > int(w["start"] * 100)] or [-30]) - 22
    out = []
    for w in wl:
        a, b = int(w["start"] * 100), max(int(w["start"] * 100) + 1, int(w["end"] * 100))
        vo = np.nonzero(E10[a:b] > _thr)[0]
        s0, e0 = ((a + vo[0]) / 100, (a + vo[-1] + 1) / 100) if len(vo) else (w["start"], w["end"])   # ovozsiz so'z: asl vaqt
        out.append(dict(w, start=round(s0, 2), end=round(max(e0, s0 + 0.05), 2), type="word"))
    json.dump({"words": out, "note": "whisper + energiya bo'yicha chegaralar"}, open(TJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
words = [w for w in json.load(open(TJ))["words"] if w.get("start") is not None]
if os.path.isdir(VU):
    run([PY, os.path.join(VU, "helpers", "pack_transcripts.py"), "--edit-dir", ED, "--silence-threshold", "0.35"])

# ---------- 3. Kesimlar va kadrlar ----------
sc = run(["ffmpeg", "-i", src, "-vf", "select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"]).stderr
cuts = []
for t in map(float, re.findall(r"pts_time:([\d.]+)", sc)):
    if t > 0.15 and (not cuts or t - cuts[-1] > 0.2):
        cuts.append(round(t, 3))
bounds = [0.0] + cuts + [DUR]
shots = [{"i": k, "start": bounds[k], "end": bounds[k + 1], "len": round(bounds[k + 1] - bounds[k], 2)} for k in range(len(bounds) - 1)]

def word_at(t):
    for w in words:
        if w["start"] < t < w["end"]:
            return w
    return None

def gap_at(t):
    prev = max([w["end"] for w in words if w["end"] <= t] or [-1])
    nxt = min([w["start"] for w in words if w["start"] >= t] or [1e9])
    return prev, nxt

cut_rows = []
for c in cuts:
    w = word_at(c); p, n = gap_at(c)
    kind = f"SO'Z ICHIDA ('{w['text'].strip()}') — nutq kesimdan o'tadi (J/L-cut yoki B-roll ostida ovoz)" if w else \
           (f"pauzada (oldingi so'zdan {c - p:.2f} s, keyingisigacha {n - c:.2f} s)" if p > 0 and n < 1e9 else "nutqsiz joyda")
    cut_rows.append((c, kind))

# ---------- 4. Grade va harakat (har kadr) ----------
def frame(t, w=270):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-vf", f"scale={w}:-2",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    h = len(r) // (w * 3)
    return np.frombuffer(r[: h * w * 3], np.uint8).reshape(h, w, 3).astype(np.float64) / 255 if h else None

for s in shots:
    f = frame((s["start"] + s["end"]) / 2)
    if f is None:
        continue
    Y = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    mx, mn = f.max(-1), f.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    s.update(luma_p2=round(float(np.percentile(Y, 2)), 3), luma_p50=round(float(np.median(Y)), 3), luma_p98=round(float(np.percentile(Y, 98)), 3),
             contrast=round(float(Y.std()), 3), sat=round(float(sat.mean()), 3),
             warm=round(float((f[..., 0] - f[..., 2]).mean()), 3), bw=bool(sat.mean() < 0.06))
    # harakat: kadr ichida 6 fps kulrang farq
    n = max(2, min(12, int(s["len"] * 6)))
    ts = np.linspace(s["start"] + 0.05, s["end"] - 0.05, n)
    gs = [frame(t, 90) for t in ts]
    gs = [x.mean(-1) for x in gs if x is not None]
    if len(gs) > 1:
        s["motion"] = round(float(np.mean([np.abs(a - b).mean() for a, b in zip(gs, gs[1:])]) * 100), 2)
    s["words"] = " ".join(w["text"].strip() for w in words if s["start"] <= w["start"] < s["end"])[:120]

# ---------- 5. Audio bo'limlar ----------
x = pcm(); sr = 16000; win = 1600
nW = len(x) // win
env = 10 * np.log10(np.mean(x[: nW * win].reshape(nW, win) ** 2, 1) + 1e-12)
tw = np.arange(nW) / 10
speech = np.zeros(nW, bool)
for w in words:
    speech[(tw >= w["start"] - 0.05) & (tw <= w["end"] + 0.05)] = True
sp_db = float(np.median(env[speech])) if speech.any() else float("nan")
pa = env[~speech & (tw > 0.3) & (tw < DUR - 0.3)]
pa_db = float(np.median(pa)) if len(pa) else float("nan")
hf = pcm("highpass=f=4000"); eh = 10 * np.log10(np.mean(hf[: nW * win].reshape(nW, win) ** 2, 1) + 1e-12)
onsets = [round(i / 10, 1) for i in range(1, nW) if eh[i] - eh[i - 1] > 9 and eh[i] > np.percentile(eh, 60)]
on_cut = [o for o in onsets if any(abs(o - c) <= 0.15 for c in cuts)]
lo = pcm("lowpass=f=150"); band = pcm("highpass=f=300,lowpass=f=3400")
bass_share = db(lo) - db(x); band_share = db(band) - db(x)
music_bed = "BOR" if pa_db > -45 else "yo'q yoki juda past"

# ---------- 6. Temp ----------
sp_time = sum(w["end"] - w["start"] for w in words)
wpm_total = len(words) / DUR * 60 if DUR else 0
gaps = [b["start"] - a["end"] for a, b in zip(words, words[1:])]
long_p = [round(gp, 2) for gp in gaps if gp >= 0.4]
lens = [s["len"] for s in shots]

# ---------- 7. Vizual: kontakt varaqlar + video-use timeline_view ----------
k = 0
while k * 16 < DUR:
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(k * 16), "-t", "16", "-i", src, "-vf", "fps=2,scale=200:-1,tile=8x4",
         "-frames:v", "1", os.path.join(OUT, f"contact_{k * 16:02d}.jpg")])
    k += 1
tv = []
if os.path.isdir(VU):
    wins = [("huk", 0, min(4, DUR)), ("yakun", max(0, DUR - 6), DUR - 0.15)]
    pick = cuts if len(cuts) <= 8 else [cuts[int(i)] for i in np.linspace(0, len(cuts) - 1, 8)]
    wins += [(f"kesim_{c:.2f}", max(0, c - 1.5), min(DUR, c + 1.5)) for c in pick]
    for name, a, b in wins:
        o = os.path.join(OUT, f"tv_{name}.png")
        run([PY, os.path.join(VU, "helpers", "timeline_view.py"), src, f"{a:.2f}", f"{b:.2f}", "-o", o, "--transcript", TJ, "--n-frames", "8"])
        if os.path.exists(o):
            tv.append(os.path.basename(o))

json.dump(shots, open(os.path.join(OUT, "shots.json"), "w"), ensure_ascii=False, indent=1)
def _med(k):
    v = [s[k] for s in shots if k in s]
    return round(float(np.median(v)), 3) if v else None
metrics = {"dur": round(DUR, 2), "fps": round(fps, 3), "lufs": LUFS, "lra": LRA,
           "wpm": round(wpm_total, 1), "speech_share": round(sp_time / DUR, 3) if DUR else None, "long_pauses": len(long_p),
           "cuts": len(cuts), "cut_every_s": round(DUR / max(1, len(shots)), 2), "shot_median_s": round(float(np.median(lens)), 2) if lens else None,
           "cuts_in_speech_share": round(sum(1 for _, kd in cut_rows if kd.startswith("SO'Z")) / max(1, len(cut_rows)), 2),
           "luma_p2": _med("luma_p2"), "luma_p50": _med("luma_p50"), "luma_p98": _med("luma_p98"), "contrast": _med("contrast"),
           "sat": _med("sat"), "warm": _med("warm"), "motion": _med("motion"), "bw_shots": sum(1 for s in shots if s.get("bw")),
           "speech_db": round(sp_db, 1), "pause_db": round(pa_db, 1), "speech_minus_pause_db": round(sp_db - pa_db, 1),
           "bass_share_db": round(bass_share, 1), "sfx_onsets": len(onsets), "sfx_on_cuts": len(on_cut)}
json.dump(metrics, open(os.path.join(OUT, "metrics.json"), "w"), indent=1)

# ---------- 8. Hisobot ----------
L = []
A = L.append
A(f"# Referens tahlili — {stem}\n")
if info:
    A(f"Manba: {info.get('webpage_url') or ''} | {info.get('uploader')} (@{info.get('channel')}) | like: {info.get('like_count')}")
    A(f"Izoh: {(info.get('description') or '').strip()[:200]!r}\n")
A("## 1. Texnik")
A(f"- {W}x{H}, {fps:.3f} fps, {DUR:.2f} s | {LUFS} LUFS, LRA {LRA} LU, peak {TP} dBFS\n")
A("## 2. Tuzilma (transkript — `edit/takes_packed.md`)")
A(f"- {len(words)} so'z, nutq {sp_time:.1f} s ({sp_time / DUR * 100:.0f}% vaqt), {wpm_total:.0f} so'z/daq")
A(f"- Uzun pauzalar (>=0.4 s): {len(long_p)} ta {long_p[:12]}")
A("- TODO (Claude): takes_packed.md ni o'qib beat'larga ajrat — HUK / MUAMMO / DALIL / XULOSA / CTA (video-use arxetiplari) va har beat vaqti.\n")
A("## 3. Montaj (kesimlar)")
if lens:
    A(f"- {len(cuts)} kesim, kadr uzunligi: median {np.median(lens):.2f} s, min {min(lens):.2f}, max {max(lens):.2f} (kesim har {DUR / max(1, len(shots)):.2f} s)")
inside = sum(1 for _, kd in cut_rows if kd.startswith("SO'Z"))
A(f"- Kesim-nutq: {inside}/{len(cut_rows)} so'z ichida (ovoz kesimdan o'tadi), qolgani pauzada/nutqsiz")
for c, kd in cut_rows:
    A(f"  - {c:7.2f} s — {kd}")
A("")
A("## 4. Grade va harakat (har kadr, o'rtadagi kadr)")
A("| # | vaqt | uzun | luma p2/p50/p98 | kontrast | to'yinganlik | iliq(R-B) | harakat | so'zlar |")
A("|---|---|---|---|---|---|---|---|---|")
for s in shots:
    if "luma_p50" in s:
        A(f"| {s['i']} | {s['start']:.2f} | {s['len']} | {s['luma_p2']}/{s['luma_p50']}/{s['luma_p98']} | {s['contrast']} | {s['sat']}{' (oq-qora)' if s['bw'] else ''} | {s['warm']} | {s.get('motion', '-')} | {s['words'][:60]} |")
A("- harakat: 6 fps kadr farqi (0.3 dan past = statik/shtativ, 1+ = qo'l kamera/zoom/tez B-roll).\n")
A("## 5. Audio")
A(f"- Nutq paytida median {sp_db:.1f} dBFS, pauzalarda {pa_db:.1f} dBFS → farq {sp_db - pa_db:.1f} dB; fon musiqasi: {music_bed}")
A(f"- Spektr: bas (<150 Hz) ulushi {bass_share:.1f} dB, nutq polosasi {band_share:.1f} dB (full'ga nisbatan)")
A(f"- Yuqori chastotali zarbalar (SFX nomzodlari): {len(onsets)} ta, shundan kesimda (±0.15 s): {len(on_cut)} → {onsets[:20]}")
A("- TODO (Claude): SFX turlari (whoosh/pop/glitch/riser) va qaysi vizual hodisaga bog'langani — tv_*.png to'lqinlarida ko'r.\n")
A("## 6. Vizual material (KO'R)")
A("- Kontakt: " + ", ".join(sorted(f for f in os.listdir(OUT) if f.startswith("contact_"))))
A("- video-use timeline_view (filmstrip + to'lqin + so'zlar): " + ", ".join(tv))
A("- Har element kirishi uchun 18 kadrlik strip: `ffmpeg -ss T -t 0.62 -i v.mp4 -vf scale=216:-1,tile=9x2:padding=2 -frames:v 1 s.jpg`\n")
A("## 7. STYLE.md uchun to'liq ro'yxat (hamma jihat — har birini to'ldir)")
for item in ["Umumiy taassurot va janr (video-use: avval qara, keyin taxmin qil)", "Tuzilma/beat'lar + vaqtlar (2-bo'lim)",
             "Montaj ritmi va kesim hunari: J/L-cut, pauzada kesim, spiker almashinuvi oralig'i (3-bo'lim)",
             "Kompozitsiya va xavfsiz zonalar (yuz qayerda, matn qayerda)", "Tipografiya: shrift nomzodlari, o'lcham, ierarxiya, holat (CAPS/kichik)",
             "Ranglar (hex) va grade (4-bo'lim raqamlari)", "Matn/subtitr: bo'laklash (1/2/3 so'z/gap), joylashuv, urg'u usullari",
             "Grafik elementlar: har biri kirish/turish/chiqish vaqti (kadr strip bilan o'lcha)", "O'tishlar", "Kamera: push/zoom/tebranish (harakat ustuni)",
             "B-roll: turi, ulushi, manbasi, qoidalarimizga mosligi (odamlar, mualliflik huquqi)", "CTA va yakun", "Audio: musiqa turi/darajasi, SFX lug'ati, nutq-musiqa farqi (5-bo'lim)",
             "Silliqlik moslamasi (smooth-motion.md qiymatlari)", "HyperFrames retsepti"]:
    A(f"- [ ] {item}")
open(os.path.join(OUT, "report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("tayyor:", os.path.join(OUT, "report.md"))
