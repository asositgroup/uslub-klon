"""Tayyor montajni referens(lar) bilan raqamda solishtirish (ref_analyze.py metrics.json lari).

python ~/.claude/skills/uslub-klon/scripts/style_compare.py <ref1/metrics.json> [ref2 ...] <out/metrics.json> [--md out.md]
  - oxirgi fayl = bizning video, oldingilari = referenslar (bitta muallifning bir nechta videosi — oila uslubi)
  - bir nechta referensda: maqsad = median, ruxsat etilgan oraliq = referenslar [min, max] (+ tolerans)
Holat: OK (oraliq ichida yoki medianga yaqin) / YAQIN / FARQ / QOIDA (foydalanuvchi qoidasi bo'yicha ataylab farq — tuzatma).
"""
import json, statistics, sys

args = [a for a in sys.argv[1:] if a != "--md"]
md = None
if "--md" in sys.argv:
    md = sys.argv[sys.argv.index("--md") + 1]
    args.remove(md)
refs = [json.load(open(p)) for p in args[:-1]]
out = json.load(open(args[-1]))
for m in refs + [out]:   # videolar uzunligi har xil — soni emas, daqiqadagi zichlik solishtiriladi
    if m.get("dur"):
        m["sfx_per_min"] = round(m.get("sfx_onsets", 0) / m["dur"] * 60, 1)

# (kalit, nomi, tolerans-turi, qiymat, qoida izohi)
CHECK = [
    ("cut_every_s", "kesim har N s", "rel", 0.25, None),
    ("shot_median_s", "kadr median, s", "rel", 0.3, None),
    ("wpm", "so'z/daqiqa", "rel", 0.15, None),
    ("long_pauses", "uzun pauzalar (>=0.4 s)", "abs", 2, None),
    ("cuts_in_speech_share", "gap o'rtasidagi kesim ulushi", "abs", 0.25, None),
    ("luma_p50", "o'rta yorug'lik", "abs", 0.06, None),
    ("contrast", "kontrast", "abs", 0.04, None),
    ("sat", "to'yinganlik", "abs", 0.05, None),
    ("warm", "iliqlik (R-B)", "abs", 0.03, None),
    ("motion", "kamera/kadr harakati", "rel", 0.5, None),
    ("speech_minus_pause_db", "nutq - pauza, dB", "abs", 3, "qoida 9: musiqa referensdan sokinroq (>=19 dB nutq polosasida)"),
    ("sfx_per_min", "SFX zarbalari / daqiqa", "rel", 0.5, None),
    ("lufs", "umumiy LUFS", "abs", 1.0, None),
]
rows, bad = [], 0
for k, name, kind, tol, rule in CHECK:
    vals = [r[k] for r in refs if r.get(k) is not None]
    b = out.get(k)
    if not vals or b is None:
        continue
    a = statistics.median(vals)
    lo, hi = min(vals), max(vals)
    d = b - a
    err = abs(d) / max(abs(a), 1e-6) if kind == "rel" else abs(d)
    in_range = lo <= b <= hi
    st = "OK" if (in_range or err <= tol) else ("YAQIN" if err <= tol * 2 else "FARQ")
    if st != "OK" and rule and d > 0:
        st = "QOIDA"
    bad += st == "FARQ"
    rng = f"{lo}–{hi}" if len(vals) > 1 else ""
    rows.append(f"| {name} | {round(a, 3)} | {rng} | {b} | {d:+.3f} | {st}{' — ' + rule if st == 'QOIDA' else ''} |")
txt = (f"Referenslar: {len(refs)} ta\n\n| Ko'rsatkich | Referens (median) | Oraliq | Bizniki | Farq | Holat |\n|---|---|---|---|---|---|\n"
       + "\n".join(rows) + f"\n\nFARQ: {bad} ta" + (" — tuzatish kerak (yoki nega ataylab farqligini hisobotda yoz)" if bad else " — uslub raqamda mos"))
print(txt)
if md:
    open(md, "w", encoding="utf-8").write(txt + "\n")
sys.exit(1 if bad else 0)
