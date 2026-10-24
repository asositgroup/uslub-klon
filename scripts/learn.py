"""learn.py — referens video(lar)dan yangi uslub o'rganib, kutubxonaga (library/) qo'shadi.

python learn.py <havola|fayl> [<havola|fayl> ...] --slug <uslub-nomi> [--author "Muallif ismi"] [--lang uz]

Har referens uchun:
  1. library/_src/<id>.mp4 (+ .info.json) — yt-dlp bilan yuklash (havoladagi ?utm/stkn kesiladi) yoki faylni nusxalash
  2. ref_analyze.py → library/_src/<id>_an/ (report.md, metrics.json, transkript, kesimlar, grade, audio, kontakt varaqlar, tv_*.png)
  3. events.py → library/_src/<id>_an/events/ (grafik element hodisalari + har biriga 18 kadrlik strip)
Keyin library/<slug>/ yaratadi (bor bo'lsa — yangi referenslarni QO'SHADI, mavjud fayllarni buzmaydi):
  refs.json        — referenslar ro'yxati (id, havola, muallif, metrics yo'li)
  metrics.json     — hamma referenslar median + oraliq (style_compare uchun)
  STYLE.md         — o'lchangan raqamlar bilan to'ldirilgan qolip + "Elementlar inventari" (Claude ko'rib to'ldiradi)
  style.json       — dizayn tokenlari qolipi (shrift/rang/subtitr/kalit so'z/raqam/yorliq/karta/CTA/yakun) — to'ldiriladi
  style.py         — kit.py asosidagi qurilish qolipi — to'ldiriladi
  keyframes/       — kontakt varaqlar + eng kuchli hodisalar strip'lari
library/INDEX.md va library/_mualliflar/<muallif>.md (muallifning hamma uslublari va referenslari) yangilanadi.
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ap = argparse.ArgumentParser()
ap.add_argument("refs", nargs="+")
ap.add_argument("--slug", required=True)
ap.add_argument("--author", default="")
ap.add_argument("--lang", default="uz")
ap.add_argument("--library", default=os.environ.get("UK_LIBRARY", str(SKILL / "library")))
args = ap.parse_args()
LIB = Path(args.library).expanduser().resolve()
SRC = LIB / "_src"
SRC.mkdir(parents=True, exist_ok=True)
slug = re.sub(r"[^a-z0-9-]+", "-", args.slug.lower()).strip("-")
SD = LIB / slug
(SD / "keyframes").mkdir(parents=True, exist_ok=True)
PY = sys.executable


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def fetch(ref):
    if os.path.exists(ref):
        rid = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(ref).stem)
        dst = SRC / f"{rid}.mp4"
        if not dst.exists():
            shutil.copy2(ref, dst)
        return rid, str(Path(ref).resolve()), {}
    url = ref.split("?")[0].rstrip("/")
    m = re.search(r"/(reel|reels|p|shorts|video)/([A-Za-z0-9_-]+)", url)
    rid = m.group(2) if m else re.sub(r"[^A-Za-z0-9_-]+", "_", url)[-40:]
    if not (SRC / f"{rid}.mp4").exists():
        r = sh(["yt-dlp", "-q", "--no-warnings", "-f", "mp4/bestvideo*+bestaudio/best", "--merge-output-format", "mp4",
                "-o", str(SRC / f"{rid}.%(ext)s"), "--write-info-json", url])
        if not (SRC / f"{rid}.mp4").exists():
            sys.exit(f"yuklab bo'lmadi: {url}\n{r.stderr[-600:]}\n(Instagram login so'rasa: brauzer orqali yuklab, faylni bering)")
    info = {}
    ij = SRC / f"{rid}.info.json"
    if ij.exists():
        d = json.load(open(ij))
        info = {k: d.get(k) for k in ("uploader", "channel", "like_count", "description", "duration")}
    return rid, url, info


refs = json.load(open(SD / "refs.json")) if (SD / "refs.json").exists() else []
known = {r["id"] for r in refs}
for ref in args.refs:
    rid, url, info = fetch(ref)
    an = SRC / f"{rid}_an"
    print(f"== {rid}: tahlil", flush=True)
    if not (an / "metrics.json").exists():
        r = sh([PY, str(HERE / "ref_analyze.py"), str(SRC / f"{rid}.mp4"), str(an)], env=dict(os.environ, REF_LANG=args.lang))
        if not (an / "metrics.json").exists():
            sys.exit(f"ref_analyze xato: {r.stdout[-400:]} {r.stderr[-800:]}")
    if not (an / "events" / "events.json").exists():
        sh([PY, str(HERE / "events.py"), str(SRC / f"{rid}.mp4"), str(an / "events")])
    for f in sorted(an.glob("contact_*.jpg")):
        shutil.copy2(f, SD / "keyframes" / f"{rid}_{f.name}")
    ev = json.load(open(an / "events" / "events.json")) if (an / "events" / "events.json").exists() else []
    for e in sorted(ev, key=lambda e: -e["strength"])[:8]:
        p = an / "events" / e["strip"]
        if p.exists():
            shutil.copy2(p, SD / "keyframes" / f"{rid}_{e['strip']}")
    if rid not in known:
        refs.append({"id": rid, "url": url, "author": args.author or (info.get("uploader") or ""), "info": info,
                     "analysis": f"_src/{rid}_an", "metrics": f"_src/{rid}_an/metrics.json"})
        known.add(rid)
json.dump(refs, open(SD / "refs.json", "w"), ensure_ascii=False, indent=1)

# ---------- metrics: median + oraliq ----------
ms = [json.load(open(LIB / r["metrics"])) for r in refs if (LIB / r["metrics"]).exists()]
agg = {}
for k in ms[0]:
    vals = [m[k] for m in ms if isinstance(m.get(k), (int, float))]
    if vals:
        agg[k] = {"median": round(statistics.median(vals), 3), "min": min(vals), "max": max(vals)}
json.dump(agg, open(SD / "metrics.json", "w"), indent=1)

# ---------- STYLE.md / style.json / style.py qoliplari (faqat yo'q bo'lsa) ----------
author = args.author or (refs[0].get("author") if refs else "")


def row(k, name):
    a = agg.get(k)
    return f"| {name} | {a['median']} | {a['min']}–{a['max']} |" if a else f"| {name} | – | – |"


metr = "\n".join([row("dur", "Davomiylik, s"), row("wpm", "So'z/daqiqa"), row("speech_share", "Nutq ulushi"), row("long_pauses", "≥0.4 s pauzalar"),
                  row("cut_every_s", "Kesim har N s"), row("shot_median_s", "Kadr median, s"), row("cuts_in_speech_share", "Gap o'rtasidagi kesim"),
                  row("luma_p50", "O'rta yorug'lik"), row("contrast", "Kontrast"), row("sat", "To'yinganlik"), row("warm", "Iliqlik R−B"),
                  row("motion", "Kamera harakati"), row("speech_minus_pause_db", "Nutq − pauza, dB"), row("sfx_onsets", "SFX zarbalari"), row("lufs", "LUFS")])
reflist = "\n".join(f"| {i + 1} | {r['id']} | {r['url']} | {r.get('author', '')} | `{r['analysis']}/` |" for i, r in enumerate(refs))
style_md = SD / "STYLE.md"
if not style_md.exists():
    style_md.write_text(f"""# {slug} — {author or 'muallif'} uslubi

## 0. Referenslar
| # | id | havola | muallif | tahlil |
|---|---|---|---|---|
{reflist}

## 1. O'lchangan raqamlar (median / oraliq — `metrics.json`; har referens: `_src/<id>_an/report.md`)
| Ko'rsatkich | Median | Oraliq |
|---|---|---|
{metr}

## 2. Umumiy taassurot va janr
TODO — avval kontakt varaqlarni (`keyframes/*contact*`) ko'r, keyin yoz: format (monolog/podkast/intervyu/B-roll), kayfiyat, auditoriya.

## 3. Tuzilma (beat'lar)
TODO — `_src/<id>_an/edit/takes_packed.md` + ekrandagi matn: HUK → … → CTA → yakun, vaqtlari.

## 4. Kompozitsiya va xavfsiz zonalar
TODO — yuz qayerda (kadr %), matn qayerda (kadr %), panel/split bormi.

## 5. Tipografiya
TODO — har matn turi: shrift nomzodlari (mock bilan tekshir), o'lcham px (1080 kenglikda), og'irlik, holat (CAPS/kichik), rang hex, soya.

## 6. Ranglar va grade
TODO — palitra hex; grade raqamlari 1-bo'limda; vinyetka/don.

## 7. ELEMENTLAR INVENTARI (har element — o'lchab yoz; hodisalar: `_src/<id>_an/events/events.md` + strip'lar)
| # | Element | Qachon ishlatiladi (gap turi) | Joy (x,y % / px) | O'lcham, shrift, rang | Kirish (davom, harakat, ease) | Turish | Chiqish | Manba strip |
|---|---|---|---|---|---|---|---|---|
| 1 | TODO | | | | | | | |

## 8. Subtitr
TODO — bo'laklash (1/2/3 so'z / gap), rejim (so'zma-so'z / ibora / karaoke / xira→to'lish), joylashuv, urg'u usuli.

## 9. O'tishlar va kamera
TODO — o'tish turlari (hard cut / chaqnash / blur), kamera (statik / push / zoom), musiqa zarbasiga bog'liqmi.

## 10. B-roll
TODO — turi, ulushi, matn bilanmi; bizda: Pexels + qoidalar (rules.md 4).

## 11. CTA va yakun
TODO

## 12. Audio
TODO — musiqa turi/darajasi (nutq−pauza), SFX nimaga bog'langan. Bizda: musiqa so'ralmasdan qo'shilmaydi, sparkle/chime yo'q.

## 13. Silliqlik moslamasi (rules.md 3 — MAJBURIY)
TODO — referensdagi tez pop/overshoot/hard-cut grafika → bizning qiymatlar (kirish ≥0.5 s expo.out + blur, chiqish ≥0.5 s power2.inOut).

## 14. OLINMAYDI (sababi bilan)
- Referensning sahnalari, metaforalari, B-roll kadrlari — faqat TEXNIKA olinadi (rules.md 9).
- TODO

## 15. Qurilish (style.json + style.py)
Tokenlar `style.json` da, komponentlar `style.py` da (kit.py). Yangi element — `style.py` ichida `S.add(css, body, js)`.
""", encoding="utf-8")
sj = SD / "style.json"
if not sj.exists():
    json.dump({
        "_izoh": "TODO: referensdan o'lchangan qiymatlar bilan to'ldir (STYLE.md 5–8). Shriftlar: scripts/common.py FONTS yoki uslub/fonts/.",
        "faces": ["Inter", "Anton"],
        "bg": "#000",
        "captions": {"mode": "words", "align": "center", "x": 60, "width": 960, "y_offset": 0,
                     "font": {"family": "Inter", "size": 46, "weight": 600, "color": "#fff"},
                     "accent": {"family": "Inter", "size": 46, "weight": 800, "color": "#F9E23F"}, "box": None,
                     "dim": "rgba(255,255,255,.35)"},
        "keyword": {"family": "Anton", "size": 104, "case": "upper", "gradient": ["#FA7B01", "#F9E23F"]},
        "keyword_dim": "rgba(122,96,34,.9)",
        "number": {"family": "Anton", "size": 330, "gradient": ["#f9c23f", "#fa7b01"], "grad_angle": 180, "lh": 0.82},
        "tag": {"bg": "#AB0103", "border": "3px solid #D8B04A", "pad": "4px 16px 6px", "font": {"family": "Anton", "size": 36, "color": "#F7EF49", "shadow": False}},
        "card": {"bg": "#fff", "radius": 26, "title": {"family": "Inter", "size": 64, "weight": 800, "color": "#151515", "shadow": False},
                 "sub": {"family": "Inter", "size": 34, "weight": 500, "color": "#444", "shadow": False}},
        "cta": {"bg": "#fff", "color": "#111", "accent": "#FB6C2A"},
        "end": {"bg": "#0d0d0d", "handle_color": "#fff"},
        "broll_text_entry": "fill",
        "grade": "TODO: grade_match.py natijasi (loyihaga xos) yoki umumiy filtr",
        "vignette": 0.0
    }, open(sj, "w"), ensure_ascii=False, indent=1)
sp = SD / "style.py"
if not sp.exists():
    sp.write_text(f'''"""{slug} — {author or 'muallif'} uslubi (STYLE.md). Har yangi video uchun shu fayldagi BO'G'INLARni loyiha matniga moslab yoz:
vaqtlar words_final.json dagi so'z boshlanishiga bog'lanadi; matn — mutaxassisning aynan so'zlari (rules.md 2).
Loyiha ma'lumoti: kit.C.CFG (project.json), kit.C.chunks(), kit.C.SHOTS, kit.C.DUR_VIDEO.
Bo'g'inlarni loyihaga xos qilish uchun project.json ga "plan": [{{"type":"keyword","t":12.4,"t_end":14,"text":"..."}}, ...] yoz —
pastdagi umumiy ijrochi uni o'qiydi; uslubga xos qo'shimcha elementlarni shu yerda qo'sh.
"""
import kit

S = kit.Style.from_dir(__file__)


def build():
    v = S.tok("vignette", 0)
    if v:
        S.vignette(v)
    S.captions()
    kit.run_plan(S)          # project.json "plan" (keyword/number/tag/card/broll/flash/blur_dip/dim_bg/cta_pill/end_card)
    return S.result()
''', encoding="utf-8")

# ---------- INDEX.md va muallif pasporti ----------
idx = LIB / "INDEX.md"
if not idx.exists():
    idx.write_text("# uslub-klon kutubxonasi\n\nHar qator — o'rganilgan uslub. To'liq tavsif: `<uslub>/STYLE.md`; muallif bo'yicha: `_mualliflar/`.\n\n"
                   "| Uslub | Muallif | Referenslar | Holat | Qachon ishlatish |\n|---|---|---|---|---|\n", encoding="utf-8")
lines = idx.read_text(encoding="utf-8").splitlines()
row_txt = f"| `{slug}` | {author} | {len(refs)} | o'rganilmoqda (STYLE.md TODO) | TODO |"
lines = [l for l in lines if not l.startswith(f"| `{slug}` |")] + [row_txt]
idx.write_text("\n".join(lines) + "\n", encoding="utf-8")
if author:
    aslug = re.sub(r"[^a-z0-9]+", "-", author.lower()).strip("-") or "muallif"
    (LIB / "_mualliflar").mkdir(exist_ok=True)
    apath = LIB / "_mualliflar" / f"{aslug}.md"
    styles = sorted({p.parent.name for p in LIB.glob("*/refs.json")
                     if any((r.get("author") or "") == author for r in json.load(open(p)))})
    allrefs = [r for s_ in styles for r in json.load(open(LIB / s_ / "refs.json"))]
    apath.write_text(f"# {author}\n\nUslublar: " + ", ".join(f"`{s_}`" for s_ in styles) +
                     f"\n\nReferenslar ({len(allrefs)}): " + ", ".join(r["id"] for r in allrefs) +
                     "\n\n\"" + author + " uslubida\" deyilsa — shu uslublarning HAMMASI birga (bitta video emas): qolip foydalanuvchi videosiga qarab\n"
                     "tanlanadi, raqamli maqsad = hamma referenslar median/oraliq, grade_match va style_compare ga hamma referenslar beriladi.\n",
                     encoding="utf-8")
print(f"\nuslub: {SD}\n  referenslar: {len(refs)} | STYLE.md, style.json, style.py — TODO bo'limlarini to'ldir (SKILL.md 'O'rganish' qadami)")
