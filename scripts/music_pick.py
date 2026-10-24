"""Musiqa nomzodlarini o'lchab saralash (eshitmasdan): qaysi trek ekspert ovozini to'smaydi.

python scripts/music_pick.py analysis/music/*.mp3
  speech  — nutq polosasi 300-3400 Hz ulushi, full'ga nisbatan dB (<= -7 yaxshi: trek energiyasi basda/yuqorida)
  perc    — zarbdorlik: 100 ms RMS farqining o'rtachasi, dB (< 2 yaxshi: sokin pad/pianino)
  lufs    — trekning o'z balandligi (ma'lumot uchun)
Ekspert/ta'lim reeli uchun: speech past + perc past = 1-o'rin. Zarbli fashion/trap/EDM — ro'yxat oxirida.
"""
import re, subprocess, sys
import numpy as np

def pcm(path, af="", sr=16000):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr)] + (["-af", af] if af else []) + ["-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)

def rms_db(x):
    return 10 * np.log10(np.mean(x.astype(np.float64) ** 2) + 1e-12)

rows = []
for p in sys.argv[1:]:
    full = pcm(p)
    band = pcm(p, "highpass=f=300:p=2,lowpass=f=3400:p=2")
    speech = rms_db(band) - rms_db(full)
    w = 1600  # 100 ms
    n = len(full) // w
    env = 10 * np.log10(np.mean(full[: n * w].reshape(n, w).astype(np.float64) ** 2, axis=1) + 1e-9)
    env = env[env > env.max() - 40]          # jimlikni hisobga olma
    perc = float(np.mean(np.abs(np.diff(env)))) if len(env) > 2 else 0.0
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", m)[-1])
    rows.append((speech + 1.5 * perc, speech, perc, lufs, p))

print(f"{'#':>2}  {'speech':>7} {'perc':>5} {'lufs':>6}  fayl")
for i, (_, s, pc, l, p) in enumerate(sorted(rows), 1):
    ok = "OK " if s <= -7 and pc < 2 else "   "
    print(f"{i:>2}  {s:7.1f} {pc:5.2f} {l:6.1f}  {ok}{p}")
