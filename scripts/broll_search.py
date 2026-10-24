"""B-roll nomzodlari (Pexels video) → <loyiha>/tahlil/broll/<slot>/cand.json + sheet.jpg (KO'R, keyin broll_prep.py).

python broll_search.py <loyiha> <slot> "so'rov 1" ["so'rov 2" ...]
Kalit (birinchisi topilgani): $PEXELS_API_KEY | ~/.pexels.env | skill ichidagi keys/pexels.env (repoda bor)
Pexels License — tijoriy bepul, atributsiya shart emas. Odamlar qoidasi (rules.md 4) — varaqda ko'z bilan tekshir.
"""
import io, json, os, re, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw


def key():
    if os.environ.get("PEXELS_API_KEY"):
        return os.environ["PEXELS_API_KEY"]
    for p in ("~/.pexels.env", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "keys", "pexels.env")):
        p = os.path.expanduser(p)
        if os.path.exists(p):
            m = re.search(r"PEXELS_API_KEY=\"?([^\"\r\n]+)", open(p).read())
            if m:
                return m.group(1)
    raise SystemExit("Pexels kaliti topilmadi: export PEXELS_API_KEY=... yoki ~/.pexels.env")


BAN = re.compile(r"christmas|xmas|santa|halloween|wine|beer|alcohol|church|cross|bikini|party", re.I)
proj, slot, queries = sys.argv[1], sys.argv[2], sys.argv[3:]
out = os.path.join(proj, "tahlil", "broll", slot)
os.makedirs(out, exist_ok=True)
K, cands = key(), []
for q in queries:
    u = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": q, "orientation": "portrait", "per_page": 8, "size": "medium"})
    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"Authorization": K, "User-Agent": "uslub-klon"})))
    for v in d.get("videos", []):
        if BAN.search(v.get("url", "")):
            continue
        files = sorted([f for f in v["video_files"] if f.get("height") and f["height"] >= 1280], key=lambda f: f["height"])
        if not files:
            continue
        cands.append({"id": v["id"], "q": q, "dur": v["duration"], "url": files[0]["link"], "page": v["url"], "img": v["image"]})
json.dump(cands, open(os.path.join(out, "cand.json"), "w"), indent=1)
tiles = []
for i, c in enumerate(cands[:24]):
    try:
        im = Image.open(io.BytesIO(urllib.request.urlopen(c["img"]).read())).convert("RGB").resize((180, 320))
    except Exception:
        im = Image.new("RGB", (180, 320), "gray")
    ImageDraw.Draw(im).text((4, 4), f"{i} {c['dur']}s", fill=(255, 255, 0))
    tiles.append(im)
if tiles:
    sheet = Image.new("RGB", (min(8, len(tiles)) * 180, ((len(tiles) + 7) // 8) * 320))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % 8) * 180, (i // 8) * 320))
    sheet.save(os.path.join(out, "sheet.jpg"), quality=85)
print(f"{len(cands)} nomzod -> {out}/sheet.jpg")
