import os, sys, json, glob, site, ctypes
os.environ.setdefault("CUDA_MODULE_LOADING","LAZY")

# --- CUDA runtime dlls from pip wheels: add to search path AND preload -------
cands = []
for sp in list(site.getsitepackages()) + [site.getusersitepackages()]:
    cands += glob.glob(os.path.join(sp, "nvidia", "*", "bin"))
for d in cands:
    try: os.add_dll_directory(d)
    except Exception: pass
    os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]

PRELOAD = os.environ.get("HF_PRELOAD","cublasLt64_12.dll,cublas64_12.dll").split(",")
OLD_PRELOAD = ["x",
           "cudnn_graph64_9.dll", "cudnn_ops64_9.dll", "cudnn_engines_precompiled64_9.dll",
           "cudnn_heuristic64_9.dll", "cudnn_cnn64_9.dll", "cudnn_adv64_9.dll", "cudnn64_9.dll"]
loaded = []
for name in PRELOAD:
    for d in cands:
        p = os.path.join(d, name)
        if os.path.exists(p):
            try:
                if os.name == "nt": ctypes.WinDLL(p); loaded.append(name)
            except OSError as e:
                print("preload fail", name, e)
            break
print("preloaded:", loaded, flush=True)

from faster_whisper import WhisperModel

AUDIO, OUT = sys.argv[1], sys.argv[2]
LANG  = sys.argv[3] if len(sys.argv) > 3 else "uz"
MODEL = os.environ.get("HF_MODEL", "large-v3")
def _has_cuda():
    try:
        import ctranslate2
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False
DEV   = os.environ.get("HF_DEV") or ("cuda" if _has_cuda() else "cpu")   # Mac/CPU: avtomatik
CT    = os.environ.get("HF_CT") or ("float16" if DEV == "cuda" else "int8")

import time
model = None
for attempt in range(6):
    try:
        model = WhisperModel(MODEL, device=DEV, compute_type=CT, cpu_threads=int(os.environ.get("HF_THREADS", 2 if DEV == "cuda" else max(2, (os.cpu_count() or 4) - 2))))
        break
    except RuntimeError as e:
        print(f"attempt {attempt+1} failed: {str(e)[:60]}", flush=True)
        time.sleep(4)
if model is None:
    raise SystemExit("MODEL_LOAD_FAILED")
print(f"model={MODEL} device={DEV} ct={CT}", flush=True)

segments, info = model.transcribe(
    AUDIO, language=LANG, word_timestamps=True, vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=400),
    condition_on_previous_text=False, beam_size=5,
)
print("lang:", info.language, "dur:", info.duration, flush=True)

words, segs = [], []
for s in segments:
    segs.append({"start": round(s.start,3), "end": round(s.end,3), "text": s.text.strip()})
    print(f"[{s.start:7.2f} -> {s.end:7.2f}] {s.text.strip()}", flush=True)
    for w in (s.words or []):
        t = w.word.strip()
        if t: words.append({"text": t, "start": round(w.start,3), "end": round(w.end,3)})

json.dump(words, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(segs,  open(OUT.replace(".json","-segments.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("words:", len(words), "->", OUT, flush=True)
