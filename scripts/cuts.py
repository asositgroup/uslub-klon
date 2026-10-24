"""cuts.py <video> [chegara=12] — kamera kesimlarini topadi (kadr farqi; ffmpeg scene filtri IG/VP9 fayllarda ishonchsiz).

Natija: kesim vaqtlari (s) + har kadr (shot) oralig'i. 30 fps, 54x96 kulrang kadrlar bo'yicha o'rtacha mutlaq farq;
median'dan `chegara` baravar katta sakrash = kesim. Bir-biriga 0.4 s dan yaqin cho'qqilardan kattasi olinadi.
"""
import json
import subprocess
import sys

import numpy as np

video = sys.argv[1]
k = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
W, H = 54, 96
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps=30,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                     capture_output=True).stdout
a = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
d = np.abs(np.diff(a, axis=0)).mean((1, 2))
med = float(np.median(d)) + 1e-6
cand = [(i + 1) / 30 for i in np.where(d > med * k)[0]]
cuts = []
for t in cand:
    if cuts and t - cuts[-1] < 0.4:
        continue
    cuts.append(round(float(t), 3))
dur = len(a) / 30
edges = [0.0] + cuts + [round(dur, 3)]
shots = [{"t0": edges[i], "t1": edges[i + 1]} for i in range(len(edges) - 1)]
print("kesimlar:", cuts)
print(json.dumps(shots, indent=1))
