"""qc.py <video> <prefix> t0:nom ... — har oynadan 12 kadr (15 fps) qatori, hammasi bitta rasmda."""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

video, prefix = sys.argv[1], sys.argv[2]
out = Path(video).resolve().parent.parent / "tahlil" / "qc"
out.mkdir(parents=True, exist_ok=True)
rows = []
for arg in sys.argv[3:]:
    t0, name = arg.split(":")
    p = out / f"{prefix}_{name}.jpg"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", t0, "-i", video, "-vf",
                    "fps=15,scale=180:-2,tile=12x1:padding=2", "-frames:v", "1", str(p)], check=True)
    im = Image.open(p)
    lab = Image.new("RGB", (im.width, im.height + 22), "white")
    lab.paste(im, (0, 22))
    ImageDraw.Draw(lab).text((6, 4), f"{name}  {t0}s  (+1/15 s qadam)", fill="black")
    rows.append(lab)
W = max(r.width for r in rows)
sheet = Image.new("RGB", (W, sum(r.height for r in rows)), "white")
y = 0
for r in rows:
    sheet.paste(r, (0, y))
    y += r.height
sheet.save(out / f"{prefix}_strips.jpg", quality=85)
print(out / f"{prefix}_strips.jpg")
