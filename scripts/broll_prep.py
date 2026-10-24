"""Tanlangan Pexels klipini yuklab, joyiga moslaydi → <loyiha>/assets/broll/<slot>.mp4 (60 fps, ovozsiz).

python broll_prep.py <loyiha> <slot> <nomzod_indeks> <boshlanish_s> <davomiylik_s> [full|split|top] [grade]
  full = 1080x1920, split = 1080x958 (pastki panel), top = 1080x1060 (tepa panel)
  grade: none | warm | bw | "<ffmpeg filtr satri>" (uslub grade'iga moslash uchun — style.json "broll_grade")
"""
import json, os, subprocess, sys, urllib.request

proj, slot, idx, ss, dur = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
mode = sys.argv[6] if len(sys.argv) > 6 else "full"
grade = sys.argv[7] if len(sys.argv) > 7 else "none"
G = {"none": "null", "warm": "eq=contrast=1.06:saturation=1.08,colorbalance=rs=-0.03:bs=0.04:rh=0.04:bh=-0.03",
     "bw": "hue=s=0,eq=contrast=1.22:brightness=-0.02,noise=alls=7:allf=t"}
W, H = {"full": (1080, 1920), "split": (1080, 958), "top": (1080, 1060)}[mode]
c = json.load(open(os.path.join(proj, "tahlil", "broll", slot, "cand.json")))[idx]
raw = os.path.join(proj, "tahlil", "broll", slot, f"{c['id']}.mp4")
if not os.path.exists(raw):
    urllib.request.urlretrieve(c["url"], raw)
os.makedirs(os.path.join(proj, "assets", "broll"), exist_ok=True)
out = os.path.join(proj, "assets", "broll", f"{slot}.mp4")
vf = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},{G.get(grade, grade)},fps=60,format=yuv420p"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur), "-i", raw, "-an", "-vf", vf,
                "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-movflags", "+faststart", out], check=True)
log = os.path.join(proj, "tahlil", "broll", "manbalar.txt")
open(log, "a").write(f"{slot}: {c['page']} (Pexels {c['id']}) {ss}-{ss + dur}s\n")
print(out)
