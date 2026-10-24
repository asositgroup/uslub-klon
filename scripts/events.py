"""events.py <video> <out_dir> [--max 40] — referensdagi GRAFIK ELEMENT hodisalarini topadi (matn/karta/yorliq paydo bo'lishi).

Kesim emas, lekin kadrning bir qismida keskin o'zgarish = element kirishi/chiqishi. 15 fps, 108x192 kulrang:
  - kesimlar (butun kadr o'zgarishi) va ±0.15 s atrofi chiqarib tashlanadi
  - har kadrda |farq| > 38 VA grafikaga o'xshash (oq / yorqin-to'yingan) piksellar qutisi; maydon 0.08–25 % → nomzod
  - ketma-ket nomzodlar bitta hodisaga yig'iladi (boshlanish, davomiylik, quti 1080x1920 px va %)
Natija: <out_dir>/events.json, events.md (jadval), ev_NN_<t>.jpg (har hodisa: 18 kadr 30 fps strip, quti belgilangan).
Bu NOMZODLAR ro'yxati — strip'larni ko'z bilan ko'rib, haqiqiy elementlarni STYLE.md "Elementlar inventari"ga yoz
(shrift, o'lcham, rang, % joylashuv, kirish/chiqish vaqti va turi). Odam harakati (qo'l, bosh) ham tushishi mumkin.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

video, out = sys.argv[1], sys.argv[2]
MAXN = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 40
os.makedirs(out, exist_ok=True)
W, H, FPS = 108, 192, 15
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     capture_output=True).stdout
rgb = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.int16)
a = rgb.mean(-1)
mx, mn = rgb.max(-1), rgb.min(-1)
# "grafikaga o'xshash" piksel: deyarli oq yoki yorqin-to'yingan rang (matn, plashka, karta) — teri/soch harakati emas
graphic = ((mn > 200) | ((mx - mn) > 0.55 * np.maximum(mx, 1)) & (mx > 150))
n = len(a)
d = np.abs(np.diff(a, axis=0))
full = d.mean((1, 2))
med = float(np.median(full)) + 1e-6
cut = full > max(med * 10, 18)
near_cut = np.convolve(cut.astype(int), np.ones(5, int), mode="same") > 0
cands = []
for i in range(n - 1):
    if near_cut[i]:
        continue
    m = (d[i] > 38) & (graphic[i + 1] | graphic[i])
    area = m.mean()
    if not (0.0008 < area < 0.25):
        continue
    ys, xs = np.nonzero(m)
    # tarqoq shovqinni kesish: 10–90 persentil qutisi
    x0, x1 = np.percentile(xs, 10), np.percentile(xs, 90)
    y0, y1 = np.percentile(ys, 10), np.percentile(ys, 90)
    cands.append((i + 1, float(area), x0, y0, x1, y1))
events = []
for f, area, x0, y0, x1, y1 in cands:
    if events and f - events[-1]["f1"] <= 3 and abs(y0 - events[-1]["y0"]) < 30:
        e = events[-1]
        e["f1"] = f
        e["strength"] += area
        e["x0"], e["y0"] = min(e["x0"], x0), min(e["y0"], y0)
        e["x1"], e["y1"] = max(e["x1"], x1), max(e["y1"], y1)
    else:
        events.append(dict(f0=f, f1=f, strength=area, x0=x0, y0=y0, x1=x1, y1=y1))
events = sorted(events, key=lambda e: -e["strength"])[:MAXN]
events.sort(key=lambda e: e["f0"])
rows, res = [], []
for k, e in enumerate(events):
    t0, t1 = e["f0"] / FPS, (e["f1"] + 1) / FPS
    box = [int(e["x0"] * 10), int(e["y0"] * 10), int(e["x1"] * 10), int(e["y1"] * 10)]
    pct = [round(box[0] / 10.8), round(box[1] / 19.2), round(box[2] / 10.8), round(box[3] / 19.2)]
    p = os.path.join(out, f"ev_{k:02d}_{t0:.2f}.jpg")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{max(0, t0 - 0.1):.3f}", "-t", "0.62", "-i", video,
                    "-vf", "fps=30,scale=216:-2,tile=9x2:padding=2", "-frames:v", "1", p])
    if os.path.exists(p):
        im = Image.open(p).convert("RGB")
        dr = ImageDraw.Draw(im)
        tw, th = 216, im.height // 2
        for r in range(2):
            for c in range(9):
                ox, oy = c * 218, r * (th + 1)
                dr.rectangle([ox + box[0] / 5, oy + box[1] / 5 * (th / 384), ox + box[2] / 5, oy + box[3] / 5 * (th / 384)], outline=(255, 0, 0))
        im.save(p, quality=85)
    res.append(dict(t0=round(t0, 2), dur=round(t1 - t0, 2), box_px=box, box_pct=pct, strength=round(e["strength"], 3), strip=os.path.basename(p)))
    rows.append(f"| {k} | {t0:.2f} | {t1 - t0:.2f} | x {pct[0]}–{pct[2]} % , y {pct[1]}–{pct[3]} % | {e['strength']:.3f} | {os.path.basename(p)} |")
json.dump(res, open(os.path.join(out, "events.json"), "w"), indent=1)
open(os.path.join(out, "events.md"), "w").write(
    "| # | boshlanish s | davom s | joy (kadr %) | kuch | strip |\n|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
print(f"{len(res)} hodisa -> {out}/events.md (+ ev_*.jpg strip'lar)")
