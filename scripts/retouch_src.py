"""Yuz retushi: har kadrda yuz (Haar, vaqt bo'yicha silliqlangan quti) -> teri niqobi (YCrCb) -> chastota ajratish:
past chastota bilateral bilan silliqlanadi, mayda tuzilish 35% qaytariladi (plastik emas). Kadr soni/fps o'zgarmaydi (sinxron).
python tools/retouch_src.py <asl_4k.mp4> <out_1080.mp4> [kuch=0.65]  — asl manbadan bir marta kodlash (sifat yo'qolmaydi)
"""
import subprocess, sys, cv2, numpy as np
src, dst = sys.argv[1], sys.argv[2]; K = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
W, H = 1080, 1920
fps = subprocess.run(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=r_frame_rate","-of","csv=p=0",src],capture_output=True,text=True).stdout.strip()
import os
DW, DH = W // 3, H // 3
_M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "models", "face_detection_yunet_2023mar.onnx")
if not os.path.exists(_M):
    _M = os.path.expanduser("~/.cache/yunet/face_detection_yunet_2023mar.onnx")
yn = cv2.FaceDetectorYN.create(_M, "", (DW, DH), 0.6, 0.3, 5)
rd = subprocess.Popen(["ffmpeg","-v","error","-i",src,"-an","-vf",f"scale={W}:{H}:in_color_matrix=bt709:in_range=tv:flags=lanczos+accurate_rnd+full_chroma_int+bitexact","-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE)
wr = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",fps,"-i","-","-vf","scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int+bitexact,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
                       "-color_range","tv","-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
                       "-c:v","libx264","-crf","13","-preset","slow","-g","30","-movflags","+faststart",dst],stdin=subprocess.PIPE)
box = None; n = 0; miss = 0
while True:
    b = rd.stdout.read(W*H*3)
    if len(b) < W*H*3: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
    _, det = yn.detect(cv2.resize(f, (DW, DH)))
    if det is not None and len(det):
        x, y, w, h = max(det, key=lambda d: d[2]*d[3])[:4]; nb = np.array([x, y, w, h], float) * 3
        box = nb if box is None else box * 0.6 + nb * 0.4; miss = 0
    else:
        miss += 1
    if box is not None and miss < 20:
        x, y, w, h = box; x0 = int(max(0, x - .25*w)); y0 = int(max(0, y - .25*h)); x1 = int(min(W, x + 1.25*w)); y1 = int(min(H, y + 1.25*h))
        roi = f[y0:y1, x0:x1].astype(np.float32)
        ycc = cv2.cvtColor(roi.astype(np.uint8), cv2.COLOR_BGR2YCrCb)
        sk = cv2.inRange(ycc, (40, 135, 85), (255, 180, 135)).astype(np.float32) / 255
        ell = np.zeros(sk.shape, np.float32)
        cv2.ellipse(ell, (int((x + w/2) - x0), int((y + h*0.52) - y0)), (int(w*0.58), int(h*0.66)), 0, 0, 360, 1, -1)
        m = cv2.GaussianBlur(sk * ell, (0, 0), 6 * max(0.5, w / 300.0))[..., None] * K
        sc = max(0.45, min(1.2, w / 300.0))  # yuz kichik bo'lsa (keng kadr) silliqlash radiusi ham kichik
        low = cv2.bilateralFilter(roi, 0, 22, 9 * sc)
        low = cv2.bilateralFilter(low, 0, 16, 5 * sc)
        hi = roi - cv2.GaussianBlur(roi, (0, 0), 1.2 * sc)
        sm = low + 0.35 * hi
        f[y0:y1, x0:x1] = np.clip(roi * (1 - m) + sm * m, 0, 255).astype(np.uint8)
    wr.stdin.write(f.tobytes()); n += 1
    if n % 250 == 0: print("kadr", n, flush=True)
wr.stdin.close(); wr.wait(); print("ok", n)
