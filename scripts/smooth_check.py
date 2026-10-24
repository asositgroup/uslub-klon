"""Silliqlik tekshiruvi (references/smooth-motion.md). Ikki bosqich:

1) Kod: python scripts/smooth_check.py hf/index.html
   overshoot ease, qisqa yoyo, <0.3 s ko'rinadigan tween, ease:none kirish, layout-xossa tween'larini topadi.
2) Kadrlar: python scripts/smooth_check.py renders/x_final.mp4 3.2 7.0 12.66 ...
   har vaqt uchun 12 ketma-ket kadr varag'i -> analysis/smooth/entry_<t>.jpg (KO'Z bilan ko'r: sakrash/overshoot yo'qmi).
3) Yorug'lik sakrashi: python scripts/smooth_check.py renders/x_final.mp4   (vaqtlarsiz)
   butun video bo'yicha kadrma-kadr o'rtacha yorug'lik; bir kadrda >=20 birlik o'zgarish = keskin qorayish/chaqnash
   (Storis v2: 6.8 s da 88->18 bir kadrda — fon xiralashuvi o'rniga qora "teshik"). Har topilganini kadr varag'ida ko'r.
"""
import os, re, subprocess, sys

src = sys.argv[1]
if src.endswith(".html"):
    h = open(src, encoding="utf-8").read()
    js = "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", h, re.S))
    bad = []
    for i, line in enumerate(js.splitlines(), 1):
        L = line.strip()
        if re.search(r"back\.(out|in)|elastic|bounce", L):
            bad.append((i, "overshoot ease", L))
        if "yoyo" in L and re.search(r"duration\s*:\s*0?\.(0\d|1[0-5])\b", L):
            bad.append((i, "qisqa yoyo tepki", L))
        for d in re.findall(r"duration\s*:\s*(0?\.\d+)", L):
            if float(d) < 0.3 and "opacity" in L and "set(" not in L:
                bad.append((i, f"juda qisqa tween {d}s", L))
        if re.search(r"ease\s*:\s*[\"'](none|linear|power1\.in)[\"']", L) and not re.search(r"progress|follow|proxy|onUpdate|count|scaleX|#pb", L):
            bad.append((i, "keskin ease (none/power1.in)", L))
        if re.search(r"\b(letterSpacing|height|width|margin\w*|top|left)\s*:", L) and re.search(r"\.(to|from|fromTo)\(", L):
            bad.append((i, "layout xossasi tween", L))
    for i, why, L in bad:
        print(f"[{why}] script:{i}: {L[:140]}")
    print(f"\n{len(bad)} ta shubhali joy" + (" — tuzat yoki asoslab qoldir" if bad else " — kod toza; endi render kadrlarini tekshir"))
    sys.exit(1 if bad else 0)

fps = eval(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip())
out = os.path.join("analysis", "smooth"); os.makedirs(out, exist_ok=True)
if len(sys.argv) == 2:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-an", "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                        "-f", "null", "-"], capture_output=True, text=True).stdout
    y = [float(v) for v in re.findall(r"YAVG=([\d.]+)", r)]
    hits = [(i, y[i - 1], y[i]) for i in range(1, len(y)) if abs(y[i] - y[i - 1]) >= 20]
    last = -99
    for i, a, b in hits:
        if i - last > fps * 0.5:
            print(f"{i / fps:7.2f} s  kadr {i}: yorug'lik {a:.0f} -> {b:.0f}")
        last = i
    print(f"\n{len(hits)} ta keskin yorug'lik sakrashi" + (" — har birini kadr varag'ida tekshir (rejalashtirilgan hard-cut bo'lsa izohla)" if hits else ""))
    sys.exit(1 if hits else 0)
for t in map(float, sys.argv[2:]):
    n0 = max(0, round((t - 0.1) * fps))
    step = max(1, round(fps / 30))          # 60 fps renderda har 2-kadr -> ~0.4 s oyna
    sel = "+".join(f"eq(n,{n0 + k * step})" for k in range(12))
    f = os.path.join(out, f"entry_{t:.2f}.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"select='{sel}',scale=270:-1,tile=6x2",
                    "-frames:v", "1", "-fps_mode", "passthrough", f], check=True)
    print(f)
