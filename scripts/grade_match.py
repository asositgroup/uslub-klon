"""Manba videoning rangini referensga yaqinlashtiruvchi ffmpeg filtri (edit.json "grade" uchun).

python ~/.claude/skills/uslub-klon/scripts/grade_match.py <referens.mp4[,ref2.mp4,...]> <manba.mp4> [out_dir] [--ref-times a,b,c] [--src-times a,b,c]
  - bir nechta referens (vergul bilan) — bitta muallif uslubi uchun hammasidan teng kadr olinadi
  - ikkala videodan 8 tadan kadr (yoki berilgan vaqtlar — referensda SPIKER kadrlarini tanla, B-roll/oq ekran emas)
  - o'lchov: luma p2/p50/p98, to'yinganlik, iliqlik (R-B)
  - filtr: curves (3 nuqta: soya/o'rta/yorug') + eq=saturation + colorbalance (o'rta tonlar), 2 iteratsiya bilan aniqlashtiriladi
  - qora/oq nuqta va to'yinganlik to'liq, o'rta yorug'lik va iliqlik --strength (0.4) ulushda (sahna mazmuni farqi uchun)
  - natija: <out_dir>/grade_match.jpg (yuqorida referens | manba xom | manba moslangan), filtr satri stdout'da va grade_match.json da
Teri ranglarini ko'z bilan tekshir: kuchli siljish (|iliqlik| > 0.08, to'yinganlik > 1.5x) bo'lsa yarmini ol.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = {sys.argv[i][2:]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith("--")}
args = [a for a in args if a not in opt.values()]
REF, SRC = args[0], args[1]
OUT = args[2] if len(args) > 2 else "analysis"
os.makedirs(OUT, exist_ok=True)

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)

def frames(p, times, vf=""):
    out = []
    for t in times:
        # format=rgb24 — 10-bit (yuv420p10le) manbada curves/colorbalance YUV ustida ishlab rangni buzadi (2026-10-09)
        f = "scale=270:-2,format=rgb24" + ("," + vf if vf else "")
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", p, "-frames:v", "1", "-vf", f,
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        h = len(r) // (270 * 3)
        if h:
            out.append(np.frombuffer(r[: h * 270 * 3], np.uint8).reshape(h, 270, 3))
    return out

def stats(fr):
    a = np.concatenate([f.reshape(-1, 3) for f in fr]).astype(np.float64) / 255
    Y = a @ [0.2126, 0.7152, 0.0722]
    mx, mn = a.max(1), a.min(1)
    return {"p2": float(np.percentile(Y, 2)), "p50": float(np.median(Y)), "p98": float(np.percentile(Y, 98)),
            "sat": float(np.mean(np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0))), "warm": float((a[:, 0] - a[:, 2]).mean())}

def times(p, key):
    if key in opt:
        return [float(x) for x in opt[key].split(",")]
    d = dur(p)
    return list(np.linspace(d * 0.08, d * 0.85, 8))   # boshi/oxiridagi oq yakun ekranlaridan qochish

def build(cur, ref, prev=None):
    # curves nuqtalari: manba qiymati -> referens qiymati (monoton bo'lishi shart)
    xs = [cur["p2"], cur["p50"], cur["p98"]]
    ys = [ref["p2"], ref["p50"], ref["p98"]]
    pts = ["0/0"] + [f"{min(max(x, 0.01), 0.99):.3f}/{min(max(y, 0.0), 1.0):.3f}" for x, y in zip(xs, ys)] + ["1/1"]
    sat = float(np.clip(ref["sat"] / max(cur["sat"], 1e-3), 0.0, 1.8))
    dw = float(np.clip((ref["warm"] - cur["warm"]) * 1.6, -0.35, 0.35))
    return f"curves=all='{' '.join(pts)}',eq=saturation={sat:.3f},colorbalance=rm={dw:.3f}:bm={-dw:.3f}:rs={dw / 2:.3f}:bs={-dw / 2:.3f}"

# REF vergul bilan bir nechta bo'lishi mumkin (bitta muallifning bir nechta videosi = oila uslubi):
# har referensdan teng miqdorda kadr olinadi, statistika hammasidan birga.
REFS = REF.split(",")
stt = times(SRC, "src-times")
if len(REFS) == 1:
    rf = frames(REFS[0], times(REFS[0], "ref-times"))
else:
    rf = []
    for p in REFS:
        d = dur(p)
        rf += frames(p, list(np.linspace(d * 0.08, d * 0.85, max(3, 12 // len(REFS)))))
    rf = [rf[i] for i in np.argsort([i % (len(rf) // len(REFS)) for i in range(len(rf))], kind="stable")]  # varaqda har xil referenslar
sf = frames(SRC, stt)
R0, S = stats(rf), stats(sf)
# Sahna mazmuni boshqa (oq devor vs qorong'i ofis) — o'rta yorug'lik va iliqlikni TO'LIQ ko'chirish teri/ekspozitsiyani buzadi.
# Tonal xarakter (qora/oq nuqtalar, to'yinganlik) to'liq, ekspozitsiya va iliqlik qisman (--strength, standart 0.4) ko'chiriladi.
K = float(opt.get("strength", 0.4))
R = dict(R0)
R["p50"] = S["p50"] + float(np.clip((R0["p50"] - S["p50"]) * K, -0.08, 0.08))
R["warm"] = S["warm"] + float(np.clip((R0["warm"] - S["warm"]) * K, -0.04, 0.04))
filt = build(S, R)
# 2-iteratsiya: filtrdan keyingi qoldiq xatoni kompensatsiya qilib qayta qurish
G = stats(frames(SRC, stt, filt))
tgt = {k: R[k] + (R[k] - G[k]) * 0.7 for k in R}
filt = build(S, tgt)
G = stats(frames(SRC, stt, filt))

def row(fr):
    return np.concatenate(fr[:4], 1) if fr else None

top = [row(rf), row(sf), row(frames(SRC, stt[:4], filt))]
H = min(x.shape[0] for x in top)
img = np.concatenate([x[:H] for x in top], 0)
Image.fromarray(img).save(os.path.join(OUT, "grade_match.jpg"), quality=88)
res = {"ref": R0, "target": R, "strength": K, "src": S, "graded": G, "filter": filt, "bw_reference": R0["sat"] < 0.06}
json.dump(res, open(os.path.join(OUT, "grade_match.json"), "w"), indent=1)
f = lambda d: f"p2 {d['p2']:.3f} p50 {d['p50']:.3f} p98 {d['p98']:.3f} sat {d['sat']:.3f} warm {d['warm']:+.3f}"
print("referens :", f(R0)); print("maqsad   :", f(R), f"(strength {K})"); print("manba    :", f(S)); print("moslangan:", f(G))
if res["bw_reference"]:
    print("DIQQAT: referens asosan oq-qora — grade o'rniga faqat tanlangan kadrlarga hue=s=0 qo'llash kerak bo'lishi mumkin")
print("\nGRADE = format=rgb24," + filt, "  (format=rgb24 — 10-bit manba uchun shart)")
print("varaq:", os.path.join(OUT, "grade_match.jpg"), "(1-qator referens, 2 manba xom, 3 moslangan)")
