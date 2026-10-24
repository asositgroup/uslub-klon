"""new_project.py <video.mp4> <loyiha_papka> [nom] — yangi video uchun loyiha papkasini ochadi.

Yaratadi: src/manba.mp4 (APFS'da klon/hardlink), audio/, assets/, tahlil/, out/, project.json shabloni,
assets/base.mp4 (1080x1920 60fps CRF16, retushsiz zaxira). Keyingi qadamlar SKILL.md "Ish tartibi" da.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

src, proj = Path(sys.argv[1]).expanduser().resolve(), Path(sys.argv[2]).expanduser().resolve()
name = sys.argv[3] if len(sys.argv) > 3 else proj.name
for d in ("src", "audio", "assets", "tahlil/qc", "out/telefon"):
    (proj / d).mkdir(parents=True, exist_ok=True)
dst = proj / "src" / "manba.mp4"
if not dst.exists():
    try:
        subprocess.run(["cp", "-c", str(src), str(dst)], check=True)  # macOS APFS klon (disk sarflamaydi)
    except Exception:
        shutil.copy2(src, dst)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dst)],
                           capture_output=True, text=True).stdout.strip())
base = proj / "assets" / "base.mp4"
if not base.exists():
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(dst), "-an", "-vf",
                    "scale=1080:1920:flags=lanczos,format=yuv420p", "-r", "60", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "16", "-g", "30", "-movflags", "+faststart", str(base)], check=True)
cfg = proj / "project.json"
if not cfg.exists():
    json.dump({
        "name": name,
        "title": "",
        "media": {"base": "assets/base_retush.mp4", "voice": "audio/manba_auphonic.wav", "avatar": "assets/avatar.jpg",
                  "source": "src/manba.mp4"},
        "dur_video": round(dur, 3),
        "dur": round(dur + 1.4, 2),
        "shots": [{"t0": 0.0, "t1": round(dur, 3), "origin": "50% 40%", "scale0": 1.0, "scale1": 1.04, "sub_y": 1250}],
        "phrases": [],
        "accents": [],
        "words": "audio/words_final.json",
        "output_names": {},          # {"<uslub>": "Chiqish_nomi"} — bo'lmasa uslub nomi ishlatiladi
        "styles": [],                # tanlangan uslublar (library/INDEX.md)
        "version": "v1"
    }, open(cfg, "w"), ensure_ascii=False, indent=1)
print(f"loyiha: {proj}\n  davomiylik {dur:.3f} s\n  keyingi qadam: ~/.claude/skills/uslub-klon/scripts/auphonic_clean.sh {dst} {proj}/audio")
