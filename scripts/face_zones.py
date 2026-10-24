"""face_zones.py <base_1080x1920.mp4> <shots.json yoki project.json> [out.jpg]

Har kadr (shot) ichida har 0.5 s da YuNet bilan yuzni topadi va 1080x1920 koordinatada yuz qutisi
min/max ni chiqaradi + har shot o'rtasidan % to'rli kadr varag'ini (out.jpg) yasaydi.
Bundan: transform-origin (yuz markazi %), subtitr y (iyakdan ≥100 px pastda, 1450 dan yuqori) va
tepadagi bo'sh zona balandligi (scrim/panel/band shu chiziqdan oshmasin) olinadi.
"""
import json
import os
import sys

import cv2
from PIL import Image, ImageDraw

video, shots_p = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(video)[0] + "_zones.jpg"
cfg = json.load(open(shots_p))
shots = cfg["shots"] if isinstance(cfg, dict) else cfg
M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "models", "face_detection_yunet_2023mar.onnx")
yn = cv2.FaceDetectorYN.create(M, "", (360, 640), 0.6, 0.3, 5)
cap = cv2.VideoCapture(video)
tiles = []
for s in shots:
    boxes, t = [], s["t0"] + 0.1
    while t < s["t1"] - 0.05:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if not ok:
            break
        _, det = yn.detect(cv2.resize(f, (360, 640)))
        if det is not None and len(det):
            x, y, w, h = [v * 3 for v in max(det, key=lambda d: d[2] * d[3])[:4]]
            boxes.append((x, y, x + w, y + h))
        t += 0.5
    if boxes:
        x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
        cx, cy = (x0 + x1) / 2 / 1080 * 100, (y0 + y1) / 2 / 1920 * 100
        print(f"{s['t0']:7.2f}-{s['t1']:7.2f}: yuz x {x0:.0f}-{x1:.0f}, y {y0:.0f}-{y1:.0f} | origin ~{cx:.0f}% {cy:.0f}% | "
              f"iyak ~{y1:.0f} -> subtitr y >= {min(1450, y1 + 120):.0f} | tepa bo'sh zona ~{max(0, y0 - 120):.0f} px")
    else:
        print(f"{s['t0']:7.2f}-{s['t1']:7.2f}: yuz topilmadi")
    cap.set(cv2.CAP_PROP_POS_MSEC, (s["t0"] + s["t1"]) / 2 * 1000)
    ok, f = cap.read()
    if ok:
        im = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).resize((360, 640))
        d = ImageDraw.Draw(im)
        for k in range(1, 10):
            d.line([(0, k * 64), (360, k * 64)], fill=(255, 255, 0)); d.text((2, k * 64 - 11), str(k * 192), fill=(255, 255, 0))
        for k in range(1, 6):
            d.line([(k * 60, 0), (k * 60, 640)], fill=(0, 255, 255)); d.text((k * 60 + 2, 2), str(k * 180), fill=(0, 255, 255))
        if boxes:
            d.rectangle([x0 / 3, y0 / 3, x1 / 3, y1 / 3], outline=(255, 0, 0), width=2)
        d.text((6, 620), f"{s['t0']:.1f}-{s['t1']:.1f}", fill=(255, 0, 0))
        tiles.append(im)
if tiles:
    cols = min(6, len(tiles)); rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 360, rows * 640))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 360, (i // cols) * 640))
    sheet.save(out, quality=85)
    print("varaq:", out)
