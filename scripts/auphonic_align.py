"""auphonic_align.py <asl_media> <auphonic_raw.wav> <out.wav>

Auphonic bepul tarifi natijaga ~6.4 s reklama jinglini qo'shadi: ba'zan BOSHIGA, ba'zan OXIRIGA.
Bu skript asl ovoz natijaning qayerida turganini nutq polosasi (300-3400 Hz) konvertining
o'zaro korrelyatsiyasi bilan topadi, 1 ms aniqlikda sozlaydi, aynan asl uzunlikda kesadi va
boshi/o'rtasi/oxiri bo'yicha sinxronlikni tekshiradi. Sinxron buzilgan bo'lsa exit 1.
"""
import subprocess
import sys

import numpy as np
from scipy.signal import butter, sosfiltfilt

src, raw, out = sys.argv[1:4]


def load(f, sr):
    a = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-map', '0:a:0', '-ac', '1', '-ar', str(sr),
                        '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(a, np.float32).astype(np.float64)


def band(a, sr):
    return sosfiltfilt(butter(4, [300, 3400], btype='band', fs=sr, output='sos'), a)


def env(a, hop):
    n = len(a) // hop
    e = np.log(np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-7)
    return (e - e.mean()) / e.std()


def zcorr(x, y):
    x = (x - x.mean()) / (x.std() + 1e-12)
    y = (y - y.mean()) / (y.std() + 1e-12)
    return float((x * y).mean())


# 1) dag'al: 10 ms konvert, 0..15 s siljish
SR = 8000
o8, r8 = band(load(src, SR), SR), band(load(raw, SR), SR)
eo, er = env(o8, 80), env(r8, 80)
best = (-9.0, 0)
for lag in range(0, 1501):
    seg = er[lag:lag + len(eo)]
    if len(seg) < len(eo) * 0.85:
        break
    m = len(seg)
    best = max(best, (zcorr(eo[:m], seg), lag))
r_env, coarse = best
if r_env < 0.4:
    print(f'XATO: asl ovoz natijada topilmadi (r={r_env:.2f})')
    sys.exit(1)

# 2) aniq: 1 ms konvert, +-30 ms
eo1, er1 = env(o8, 8), env(r8, 8)
c1 = coarse * 10
fine = max((zcorr(eo1[:len(eo1) - 40], er1[c1 + d:c1 + d + len(eo1) - 40]), d) for d in range(-30, 31)
           if c1 + d >= 0 and len(er1[c1 + d:c1 + d + len(eo1) - 40]) == len(eo1) - 40)[1]
offset = (c1 + fine) / 1000.0
dur = len(load(src, 48000)) / 48000.0

subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{offset:.4f}', '-i', raw, '-t', f'{dur:.6f}',
                '-c:a', 'pcm_s24le', out], check=True)
raw_dur = len(r8) / SR
print(f'   Auphonic jingli: {"boshida" if offset > 0.3 else "oxirida"} '
      f'({raw_dur - dur:.1f} s), asl ovoz {offset:.3f} s dan boshlanadi -> kesildi')

# 3) tekshiruv: boshi / o'rtasi / oxiri, 6 s oynalar, 10 ms qadam
oc = band(load(out, SR), SR)
ea, eb = env(o8, 80), env(oc, 80)
res = []
for s0 in (0, len(ea) // 2 - 300, len(ea) - 600):
    x = ea[s0:s0 + 600]
    cand = [(zcorr(x, eb[s0 + d:s0 + d + 600]), d) for d in range(-30, 31)
            if s0 + d >= 0 and len(eb[s0 + d:s0 + d + 600]) == 600]
    res.append(max(cand))
names = ('boshi', "o'rtasi", 'oxiri')
print('   Sinxronlik: ' + ', '.join(f'{n} {d * 10:+d} ms (r {r:.2f})' for n, (r, d) in zip(names, res)))
sys.exit(0 if all(abs(d) <= 2 for _, d in res) else 1)
