"""Umumiy ma'lumot: kadrlar, subtitr bo'laklari, bo'g'inlar, piktogrammalar, HTML skelet."""
import html

import json as _json
import os as _os
from pathlib import Path as _Path

# ---------- loyiha konfiguratsiyasi ----------
# Videoga xos hamma narsa loyiha papkasidagi project.json da (kadrlar, subtitr bo'laklari, aksentlar, davomiylik).
# Loyiha papkasi: UK_PROJECT muhit o'zgaruvchisi (build.py --project buni o'zi o'rnatadi).
SKILL_DIR = _Path(__file__).resolve().parent.parent
LIBRARY = _Path(_os.environ.get("UK_LIBRARY", SKILL_DIR / "library")).expanduser().resolve()
if "UK_PROJECT" not in _os.environ:
    raise SystemExit("UK_PROJECT o'rnatilmagan — build.py --project <loyiha> orqali chaqiring")
PROJECT = _Path(_os.environ["UK_PROJECT"]).expanduser().resolve()
CFG = _json.load(open(PROJECT / "project.json", encoding="utf-8"))

DUR_VIDEO = CFG["dur_video"]
DUR = CFG["dur"]  # yakuniy karta bilan
# (start, end, transform-origin, scale0, scale1, subtitle_y)
SHOTS = [(s["t0"], s["t1"], s["origin"], s["scale0"], s["scale1"], s["sub_y"]) for s in CFG["shots"]]
# subtitr: so'z vaqtlari MMS forced alignment'dan (words json), matn mutaxassis aytganidek
_WORDS = _json.load(open(PROJECT / CFG.get("words", "audio/words_final.json"), encoding="utf-8"))
ACC = CFG["accents"]
PHRASES = CFG["phrases"]
# oxirgi subtitr yakuniy karta paydo bo'lishidan oldin tugaydi
SUBS_END = CFG.get("subs_end", round(DUR_VIDEO - 0.366, 2))


def shot_at(t):
    for s in SHOTS:
        if s[0] <= t < s[1]:
            return s
    return SHOTS[-1]




def chunks():
    norm = lambda w: w.lower().strip(",.?!")
    groups, k = [], 0
    for ph in PHRASES:
        n = len(ph.split())
        g = _WORDS[k:k + n]
        assert [norm(x["text"]) for x in g] == [norm(x) for x in ph.split()], (ph, [x["text"] for x in g])
        groups.append((ph, g))
        k += n
    assert k == len(_WORDS), (k, len(_WORDS))
    out = []
    for i, (ph, g) in enumerate(groups):
        text = ph.rstrip(".")
        t0 = max(0.02, g[0]["start"] - 0.05)
        nxt = groups[i + 1][1][0]["start"] - 0.05 if i + 1 < len(groups) else 99
        t1 = min(nxt - 0.03, g[-1]["end"] + 0.35, SUBS_END)
        acc, acc_t = None, t0
        low = text.lower()
        for a in ACC:
            if a.lower() in low:
                j = low.index(a.lower())
                acc = text[j:j + len(a)]
                first = a.split()[0].lower()
                acc_t = next((x["start"] for x in g if x["text"].lower().startswith(first)), t0)
                break
        ws = [(w, round(x["start"], 3), round(x["end"], 3)) for w, x in zip(ph.split(), g)]   # (ko'rsatiladigan so'z, bosh, oxir)
        out.append(dict(i=i, t0=round(t0, 3), t1=round(t1, 3), text=text, acc=acc, acc_t=round(acc_t, 3), y=shot_at(t0 + 0.05)[5], ws=ws))
    return out


def split_acc(text, acc):
    """matnni (oldin, aksent, keyin) ga ajratadi, HTML-escape bilan."""
    if not acc or acc not in text:
        return html.escape(text), None, ""
    a = text.index(acc)
    return html.escape(text[:a]), html.escape(acc), html.escape(text[a + len(acc):])


# ---------- piktogrammalar (viewBox 0 0 120 120, faqat chiziq) ----------
ICONS = {
    "nail": '<path d="M36 118V54Q36 22 60 22Q84 22 84 54V118"/><path d="M45 74V50Q45 36 60 36Q75 36 75 50V74Z"/>',
    "nail_bitten": '<path d="M36 118V54Q36 22 60 22Q84 22 84 54V118"/><path d="M45 76V47L50 42L54 47L58 40L63 46L67 40L71 46L75 42V76Z"/>',
    "nail_crack": '<path d="M36 118V54Q36 22 60 22Q84 22 84 54V118"/><path d="M45 74V50Q45 36 60 36Q75 36 75 50V74Z"/><path d="M58 37L54 49L62 55L56 70"/>',
    "check": '<path d="M30 62L52 84L92 38"/>',
    "shield": '<path d="M60 16L96 29V58Q96 88 60 104Q24 88 24 58V29Z"/><path d="M44 60L56 72L78 48"/>',
    "bowl": '<path d="M16 60H104Q100 100 60 102Q20 100 16 60Z"/><path d="M28 74Q36 68 44 74T60 74T76 74T92 74"/><path d="M48 46L52 42L56 46L52 50Z"/><path d="M64 38L68 34L72 38L68 42Z"/><path d="M58 52L61 49L64 52L61 55Z"/>',
    "clock": '<circle cx="60" cy="62" r="40"/><path d="M60 62V38"/><path d="M60 62L76 72"/><path d="M50 14H70"/><path d="M60 14V22"/>',
    "cone": '<path d="M60 108L38 34Q60 20 82 34Z"/><path d="M44 52Q60 46 76 52"/><path d="M48 66Q60 62 72 66"/><path d="M56 108L60 116L64 108"/>',
    "eye_off": '<path d="M12 60Q60 18 108 60Q60 102 12 60Z"/><circle cx="60" cy="60" r="15"/><path d="M22 98L98 22"/>',
    "arrow_up": '<path d="M60 104V22"/><path d="M34 48L60 22L86 48"/>',
    "plane": '<path d="M12 58L108 18L76 106L58 70Z"/><path d="M58 70L108 18"/>',
    "user": '<circle cx="60" cy="42" r="20"/><path d="M22 106Q22 72 60 72Q98 72 98 106"/>',
    "loop": '<path d="M88 34A38 38 0 1 0 98 66"/><path d="M98 38V66H70"/>',
}


def icon(name, cls="ic", extra=""):
    return f'<svg class="{cls}" viewBox="0 0 120 120" {extra}>{ICONS[name]}</svg>'


FONTS = {
    "Pinyon": ("PinyonScript.ttf", "normal", "400"),
    "CormorantI": ("CormorantGaramond-Italic.ttf", "italic", "300 700"),
    "Cormorant": ("CormorantGaramond-var.ttf", "normal", "300 700"),
    "Manrope": ("Manrope.ttf", "normal", "200 800"),
    "Bodoni": ("BodoniModa-var.ttf", "normal", "400 900"),
    "BodoniI": ("BodoniModa-Italic.ttf", "italic", "400 900"),
    "Jost": ("Jost-var.ttf", "normal", "100 900"),
    "PlayfairSC": ("PlayfairSC-700.ttf", "normal", "700"),
    "PlayfairI": ("PlayfairDisplay-Italic-var.ttf", "italic", "400 900"),
    "JBMono": ("JetBrainsMono-var.ttf", "normal", "100 800"),
    "Archivo": ("Archivo-var.ttf", "normal", "100 900"),
    "Caveat": ("Caveat-var.ttf", "normal", "400 700"),
    "DMSerif": ("DMSerifDisplay-Regular.ttf", "normal", "400"),
    "Karla": ("Karla-var.ttf", "normal", "200 800"),
    "Anton": ("Anton.ttf", "normal", "400"),
    "Inter": ("Inter-var.ttf", "normal", "100 900"),
    "Poppins6": ("Poppins-600.ttf", "normal", "600"),
    "Poppins7": ("Poppins-700.ttf", "normal", "700"),
    "Poppins8": ("Poppins-800.ttf", "normal", "800"),
    "Playfair": ("PlayfairDisplay-var.ttf", "normal", "400 900"),
    "Outfit": ("Outfit-var.ttf", "normal", "100 900"),
}
# Yangi shrift kerak bo'lsa: assets/fonts/ ga OFL .ttf qo'y va shu ro'yxatga qo'sh (yoki uslub papkasidagi fonts/ — kit.style_fonts()).


def font_faces(names):
    css = []
    for n in names:
        f, style, w = FONTS[n]
        css.append(f'@font-face{{font-family:"{n}";src:url("assets/fonts/{f}") format("truetype");'
                   f'font-style:{style};font-weight:{w};}}')
    return "\n".join(css)


JS_HELPERS = r"""
const IN = "expo.out", IO = "power2.inOut";
const tl = gsap.timeline({ paused: true });
function enter(sel, t, o) { o = o || {};
  const el = typeof sel === "string" ? document.querySelectorAll(sel) : sel;
  tl.fromTo(el, { opacity: 0, y: (o.y == null ? 30 : o.y), x: (o.x || 0), scale: (o.s || 1), rotation: (o.r0 || 0),
      filter: "blur(" + (o.b == null ? 12 : o.b) + "px)" },
    { opacity: (o.op == null ? 1 : o.op), y: 0, x: 0, scale: 1, rotation: (o.r1 == null ? (o.r0 || 0) : o.r1), filter: "blur(0px)",
      duration: (o.d || 0.7), ease: (o.e || IN), stagger: (o.st || 0) }, t); }
function exit(sel, t, d) {
  const el = typeof sel === "string" ? document.querySelectorAll(sel) : sel;
  tl.to(el, { opacity: 0, y: "-=16", filter: "blur(8px)", duration: d || 0.5, ease: IO }, t); }
function draw(sel, t, d, st) {
  document.querySelectorAll(sel).forEach(function (p, i) {
    const L = Math.ceil(p.getTotalLength()) + 2;
    p.style.strokeDasharray = L + " " + L;
    tl.fromTo(p, { strokeDashoffset: L, opacity: 0 }, { strokeDashoffset: 0, opacity: 1, duration: d || 0.9, ease: IO }, t + i * (st || 0));
  }); }
function undraw(sel, t, d) {
  document.querySelectorAll(sel).forEach(function (p) {
    const L = Math.ceil(p.getTotalLength()) + 2;
    tl.to(p, { strokeDashoffset: -L, duration: d || 0.6, ease: IO }, t);
  }); }
"""


def camera_js():
    lines = []
    for k, (a, b, org, s0, s1, _) in enumerate(SHOTS):
        lines.append(f'tl.set("#cam", {{ transformOrigin: "{org}" }}, {a:.3f});')
        ir = "" if k == 0 else ", immediateRender: false"
        lines.append(f'tl.fromTo("#cam", {{ scale: {s0} }}, {{ scale: {s1}, duration: {b - a - 0.004:.3f}, '
                     f'ease: "sine.inOut"{ir} }}, {a:.3f});')
    return "\n".join(lines)


def subs_html(render_chunk):
    return "\n".join(render_chunk(c) for c in chunks())


def subs_js(enter_o="{ y: 12, b: 6, d: 0.38 }", exit_d=0.26, extra=None):
    out = []
    for c in chunks():
        out.append(f'enter("#sb{c["i"]}", {c["t0"]:.2f}, {enter_o});')
        out.append(f'exit("#sb{c["i"]}", {c["t1"] - 0.06:.2f}, {exit_d});')
        if extra and c["acc"]:
            out.append(extra(c))
    return "\n".join(out)


def page(title, faces, css, body, js, root_bg="#000"):
    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080, height=1920">
<title>{title}</title>
<script src="assets/gsap.min.js"></script>
<style>
{font_faces(faces)}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {root_bg}; }}
#root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: {root_bg}; }}
#cam {{ position: absolute; inset: 0; width: 1080px; height: 1920px; overflow: hidden; will-change: transform; }}
#cam video {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; }}
.layer {{ position: absolute; inset: 0; width: 1080px; height: 1920px; pointer-events: none; }}
.abs {{ position: absolute; }}
.ov {{ opacity: 0; }}
svg {{ overflow: visible; }}
.sub {{ position: absolute; left: 60px; width: 960px; text-align: center; transform-origin: 50% 50%; z-index: 70; }}
{css}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
  <div id="cam"><video id="base" class="clip" src="assets/base.mp4" muted playsinline data-start="0" data-duration="{DUR_VIDEO}" data-track-index="1"></video></div>
{body}
  <audio id="voice" src="assets/voice.wav" data-start="0" data-duration="{DUR_VIDEO}" data-track-index="20" data-volume="1"></audio>
  <audio id="sfx" src="assets/sfx.wav" data-start="0" data-duration="{DUR}" data-track-index="21" data-volume="1"></audio>
</div>
<script>
{JS_HELPERS}
{camera_js()}
{js}
tl.to({{}}, {{ duration: 0.001 }}, {DUR - 0.002});
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
</script>
</body>
</html>
"""
