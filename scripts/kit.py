"""kit.py — o'rganilgan uslublar quriladigan komponentlar (HyperFrames + GSAP). Hammasi sukut bo'yicha SILLIQ
(references/smooth-motion.md): kirish expo.out + blur, chiqish 0.5 s power2.inOut, overshoot yo'q, filter tween'lari fromTo.

library/<uslub>/style.py ichida:
    import kit
    S = kit.Style.from_dir(__file__)          # style.json tokenlarini o'qiydi
    S.vignette(0.45)
    S.captions()                              # style.json "captions" bo'yicha
    S.keyword(12.4, 14.0, "MUHIMI ESA")
    S.number(20.1, 26.0, "2")
    S.tag(31.2, 36.0, "YAXSHI KO'RGANI YONIDA", x=60, y=820)
    S.card(40.0, 44.0, "Oylik to'lov", "kechiksa jarima")
    S.broll(15.0, 18.2, "assets/broll/b1.mp4", text="PUL", sub="erkinlikka")
    S.flash(24.0)
    S.cta_pill(47.0, 50.0, "@handle")
    S.end_card("RAHMAT", "@handle")
    def build(): return S.result()

Yangi, kit'da yo'q element kerak bo'lsa — style.py ichida S.add(css=..., body=..., js=...) bilan qo'sh (shu uslubga xos kod).
Koordinatalar 1080x1920 px. Vaqtlar = sekund (words_final.json dagi so'z boshlanishiga bog'la).
"""
import html
import json
from pathlib import Path

import common as C

SAFE_Y_MAX = 1450          # IG pastki UI — hech narsa bundan pastda emas
SFX_SOFT = {"whoosh": ("air_woosh.wav", 0.22), "sweep": ("sweep_small.wav", 0.25), "click": ("select_click.wav", 0.30),
            "pop": ("long_pop.wav", 0.22), "impact": ("whoosh_deep_impact.wav", 0.18), "shutter": ("camera_shutter.wav", 0.20)}


def esc(t):
    return html.escape(str(t))


class Style:
    def __init__(self, tokens, sdir=None):
        self.t = tokens
        self.dir = Path(sdir) if sdir else None
        self.css, self.body, self.js = [], [], []
        self.faces = set(tokens.get("faces", ["Inter"]))
        self.sfx = []
        self.media = []
        self._n = 0
        self._track = 2           # media klip track'lari (1 = base, 20/21 = audio)
        self.css.append(BASE_CSS)

    @classmethod
    def from_dir(cls, style_py):
        d = Path(style_py).resolve().parent
        return cls(json.load(open(d / "style.json", encoding="utf-8")), d)

    # ---------- yordamchilar ----------
    def uid(self, p="e"):
        self._n += 1
        return f"{p}{self._n}"

    def tok(self, key, default=None):
        cur = self.t
        for k in key.split("."):
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def cue(self, t, kind="whoosh", gain=None):
        """yumshoq SFX (rules: sparkle/chime YO'Q). kind: whoosh|sweep|click|pop|impact|shutter yoki assets/sfx fayl nomi."""
        f, g = SFX_SOFT.get(kind, (kind, 0.25))
        self.sfx.append((round(max(0, t), 3), f, gain if gain is not None else g))

    def add(self, css="", body="", js=""):
        css and self.css.append(css)
        body and self.body.append(body)
        js and self.js.append(js)

    def font_css(self, spec):
        """spec: {"family":"Anton","size":104,"weight":400,"case":"upper","ls":0.0,"lh":1.0,"color":"#fff","gradient":[...]}"""
        f = spec.get("family", "Inter")
        self.faces.add(f)
        out = [f"font-family:'{f}'", f'font-size:{spec.get("size", 48)}px', f'font-weight:{spec.get("weight", 600)}',
               f'line-height:{spec.get("lh", 1.12)}', f'letter-spacing:{spec.get("ls", 0)}em']
        if spec.get("case") == "upper":
            out.append("text-transform:uppercase")
        if spec.get("italic"):
            out.append("font-style:italic")
        if spec.get("gradient"):
            g = spec["gradient"]
            out += [f'background:linear-gradient({spec.get("grad_angle", 90)}deg,{",".join(g)})',
                    "-webkit-background-clip:text", "background-clip:text", "-webkit-text-fill-color:transparent",
                    f'color:{g[0]}']
        else:
            out.append(f'color:{spec.get("color", "#fff")}')
        if spec.get("shadow", True):
            # yorug' fonda ham o'qilsin: yaqin qattiq + keng yumshoq soya (check contrast_aa)
            sh = spec.get("shadow") if isinstance(spec.get("shadow"), str) else "0 2px 4px rgba(0,0,0,.55), 0 4px 22px rgba(0,0,0,.45)"
            out.append(f"filter:drop-shadow({sh.split('),')[0]}{')' if '),' in sh else ''})" if spec.get("gradient") else f"text-shadow:{sh}")
        if spec.get("stroke"):
            out.append(f'-webkit-text-stroke:{spec["stroke"]}')
        return ";".join(out)

    # ---------- doimiy qatlamlar ----------
    def vignette(self, strength=0.45, shape="75% 62% at 50% 46%"):
        self.add(body=f'<div class="layer" style="background:radial-gradient(ellipse {shape},rgba(0,0,0,0) 55%,rgba(0,0,0,{strength}) 100%);z-index:5"></div>')

    def grain(self, opacity=0.06):
        self.add(body=f'<div class="layer uk-grain" style="opacity:{opacity};z-index:6"></div>')

    # ---------- subtitr ----------
    def captions(self, **over):
        """style.json "captions": {mode: words|phrase|karaoke|dimfill, font:{...}, accent:{...} (aksent so'zlar), box:{bg,radius,pad},
        align: center|left, x: 60, width: 960, y_offset: 0, dim: "rgba(...)" (karaoke/dimfill xira rangi)}"""
        cfg = dict(self.tok("captions", {}) or {})
        cfg.update(over)
        mode = cfg.get("mode", "words")
        fcss = self.font_css(cfg.get("font", {"family": "Inter", "size": 46, "weight": 600}))
        acc = cfg.get("accent")
        acss = self.font_css(acc) if acc else ""
        box = cfg.get("box")
        bcss = (f'background:{box.get("bg", "rgba(0,0,0,.55)")};border-radius:{box.get("radius", 14)}px;padding:{box.get("pad", "8px 18px")};'
                f'display:inline-block;{box.get("extra", "")}') if box else ""
        align, x, w = cfg.get("align", "center"), cfg.get("x", 60), cfg.get("width", 960)
        dim = cfg.get("dim", "rgba(255,255,255,.35)")
        self.add(css=f".uk-sub{{position:absolute;left:{x}px;width:{w}px;text-align:{align};z-index:70}}"
                     f".uk-sub .si{{position:absolute;left:0;right:0;transform:translateY(-50%);{fcss}}}"
                     f".uk-sub .bx{{{bcss}}} .uk-sub .w{{display:inline-block;margin:0 .12em;position:relative}}"
                     f".uk-sub .acc{{{acss}}} .uk-sub .dim{{opacity:.999}}")
        js = []
        for c in C.chunks():
            y = min(SAFE_Y_MAX, c["y"] + cfg.get("y_offset", 0))
            accw = set((c["acc"] or "").lower().split())
            spans = []
            for k, (w, t0, t1) in enumerate(c["ws"]):
                isacc = w.lower().strip(",.?!") in {a.strip(",.?!") for a in accw}
                spans.append(f'<span class="w{" acc" if isacc and acc else ""}" id="sb{c["i"]}w{k}">{esc(w)}</span>')
            inner = " ".join(spans)
            inner = f'<span class="bx">{inner}</span>' if box else inner
            self.body.append(f'<div class="uk-sub ov" id="sb{c["i"]}" style="top:{y}px"><div class="si">{inner}</div></div>')
            i = c["i"]
            if mode == "phrase":
                js.append(f'enter("#sb{i}", {c["t0"]:.2f}, {{ y: 12, b: 6, d: 0.45 }});')
            else:
                js.append(f'tl.set("#sb{i}", {{ opacity: 1 }}, {c["t0"]:.3f});')
                for k, (w, t0, t1) in enumerate(c["ws"]):
                    sel = f"#sb{i}w{k}"
                    if mode == "words":
                        js.append(f'enter("{sel}", {max(c["t0"], t0 - 0.08):.3f}, {{ y: 14, b: 6, d: 0.45 }});')
                    elif mode == "karaoke":
                        col = (acc or {}).get("color", "#F9E23F")
                        js.append(f'tl.set("{sel}", {{ color: "{dim}" }}, {c["t0"]:.3f});')
                        js.append(f'tl.to("{sel}", {{ color: "{col}", duration: 0.3, ease: IO }}, {t0 - 0.05:.3f});')
                    elif mode == "dimfill":
                        js.append(f'enter("{sel}", {max(c["t0"], t0 - 0.08):.3f}, {{ y: 14, b: 8, d: 0.5, op: 0.4 }});')
                        js.append(f'tl.to("{sel}", {{ opacity: 1, duration: 0.4, ease: IO }}, {t0 + 0.12:.3f});')
            js.append(f'exit("#sb{i}", {c["t1"] - 0.06:.2f}, 0.3);')
        self.js += js

    # ---------- urg'u elementlari ----------
    def keyword(self, t, t_end, text, y=1080, spec=None, entry="scale", x=60, width=960, align="center", sfx="impact"):
        """katta urg'u so'z/ibora. entry: scale (1.25→1 + blur, tepkisiz) | rise | fill (xira → chapdan o'ngga to'lish)."""
        spec = spec or self.tok("keyword", {"family": "Anton", "size": 110, "case": "upper", "color": "#fff"})
        e = self.uid("kw")
        st = self.font_css(spec)
        if entry == "fill":
            dimc = self.tok("keyword_dim", "rgba(122,96,34,.9)")
            words = " ".join(f'<span class="kwf"><span class="d" data-layout-allow-overlap style="color:{dimc};-webkit-text-fill-color:{dimc}">{esc(w)}</span>'
                             f'<span class="g" data-layout-allow-overlap style="{st}">{esc(w)}</span></span>' for w in text.split())
            self.add(body=f'<div class="abs ov uk-kw" id="{e}" style="left:{x}px;top:{y}px;width:{width}px;text-align:{align};{st};'
                          f'-webkit-text-fill-color:initial;background:none;filter:none">{words}</div>',
                     js=f'tl.set("#{e}", {{ opacity: 1 }}, {t - 0.1:.3f});'
                        f'document.querySelectorAll("#{e} .kwf").forEach(function (w, i) {{'
                        f' enter(w, {t:.3f} + i * 0.22, {{ y: 22, b: 8, d: 0.55 }});'
                        f' tl.fromTo(w.querySelector(".g"), {{ clipPath: "inset(0% 100% 0% 0%)" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: 0.45, ease: IO }}, {t + 0.18:.3f} + i * 0.22); }});'
                        f'exit("#{e}", {t_end - 0.5:.3f});')
        else:
            o = "{ s: 1.25, y: 0, b: 18, d: 0.7 }" if entry == "scale" else "{ y: 40, b: 12, d: 0.7 }"
            self.add(body=f'<div class="abs ov uk-kw" id="{e}" style="left:{x}px;top:{y}px;width:{width}px;text-align:{align};{st}">{esc(text)}</div>',
                     js=f'enter("#{e}", {t:.3f}, {o}); exit("#{e}", {t_end - 0.5:.3f});')
        sfx and self.cue(t, sfx)

    def number(self, t, t_end, n, x=52, y=250, spec=None, sfx="sweep"):
        """ro'yxat raqami (1/2/3). Pastdan bo'yiga o'sadi (scaleY 0.25→1), overshoot yo'q."""
        spec = spec or self.tok("number", {"family": "Anton", "size": 330, "gradient": ["#f9c23f", "#fa7b01"], "grad_angle": 180, "lh": 0.82})
        e = self.uid("nm")
        self.add(body=f'<div class="abs ov" id="{e}" style="left:{x}px;top:{y}px;transform-origin:50% 100%;{self.font_css(spec)}">{esc(n)}</div>',
                 js=f'tl.fromTo("#{e}", {{ opacity: 0, scaleY: 0.25, y: 30, filter: "blur(10px)" }}, {{ opacity: 1, scaleY: 1, y: 0, filter: "blur(0px)", duration: 0.7, ease: IN }}, {t:.3f});'
                    f'exit("#{e}", {t_end - 0.5:.3f});')
        sfx and self.cue(t, sfx)

    def tag(self, t, t_end, text, x=60, y=820, spec=None, sfx="pop"):
        """yorliq/plashka (ro'yxat bandi, izoh). style.json "tag": {bg, border, radius, pad, font:{...}}"""
        cfg = spec or self.tok("tag", {"bg": "#AB0103", "border": "3px solid #D8B04A", "font": {"family": "Anton", "size": 36, "color": "#F7EF49", "shadow": False}})
        e = self.uid("tg")
        st = (f'background:{cfg.get("bg")};border:{cfg.get("border", "none")};border-radius:{cfg.get("radius", 0)}px;'
              f'padding:{cfg.get("pad", "4px 16px 6px")};box-shadow:{cfg.get("box_shadow", "0 6px 16px rgba(0,0,0,.35)")};{self.font_css(cfg.get("font", {}))}')
        self.add(body=f'<div class="abs ov" id="{e}" style="left:{x}px;top:{y}px;{st}">{esc(text)}</div>',
                 js=f'enter("#{e}", {t:.3f}, {{ s: 0.85, y: 0, b: 8, d: 0.6 }}); exit("#{e}", {t_end - 0.5:.3f});')
        sfx and self.cue(t, sfx)

    def card(self, t, t_end, title, sub="", x=60, y=1000, width=960, spec=None, sfx="pop"):
        """fakt kartasi. style.json "card": {bg, radius, pad, shadow, title:{font}, sub:{font}, border}"""
        cfg = spec or self.tok("card", {"bg": "#fff", "radius": 26, "title": {"family": "Inter", "size": 64, "weight": 800, "color": "#151515", "shadow": False},
                                        "sub": {"family": "Inter", "size": 34, "weight": 500, "color": "#444", "shadow": False}})
        e = self.uid("cd")
        sub_html = f'<div style="margin-top:6px;{self.font_css(cfg.get("sub", {}))}">{esc(sub)}</div>' if sub else ""
        self.add(body=f'<div class="abs ov" id="{e}" style="left:{x}px;top:{y}px;width:{width}px;background:{cfg.get("bg")};'
                      f'border-radius:{cfg.get("radius", 26)}px;padding:{cfg.get("pad", "26px 34px 30px")};border:{cfg.get("border", "none")};'
                      f'box-shadow:{cfg.get("shadow", "0 18px 40px rgba(0,0,0,.28)")}"><div style="{self.font_css(cfg.get("title", {}))}">{esc(title)}</div>{sub_html}</div>',
                 js=f'enter("#{e}", {t:.3f}, {{ s: 0.88, y: 60, b: 12, d: 0.8 }}); exit("#{e}", {t_end - 0.5:.3f});')
        sfx and self.cue(t, sfx)

    def broll(self, t, t_end, src, text=None, sub=None, mode="full", tx=60, ty=330, sfx="whoosh"):
        """to'liq ekran B-roll (loyihadagi fayl, masalan assets/broll/b1.mp4) + ixtiyoriy chap-tepa matn (keyword tokeni)."""
        e = self.uid("br")
        name = Path(src).name
        self.media.append(src)
        h = {"full": 1920, "top": 1060}.get(mode, 1920)
        self.body.append(f'<video id="{e}" class="clip" src="assets/{name}" muted playsinline data-start="{t:.3f}" data-duration="{t_end - t:.3f}" '
                         f'data-track-index="{self._track}" style="position:absolute;left:0;top:0;width:1080px;height:{h}px;object-fit:cover;z-index:20"></video>')
        self._track += 1
        if text:
            self.keyword(t + 0.15, t_end, text, y=ty, x=tx, width=900, align="left", entry=self.tok("broll_text_entry", "fill"), sfx=None)
        if sub:
            s2 = self.uid("bs")
            self.add(body=f'<div class="abs ov" id="{s2}" style="left:{tx}px;top:{ty + 120}px;width:900px;z-index:30;{self.font_css(self.tok("captions.font", {"family": "Inter", "size": 40}))}">{esc(sub)}</div>',
                     js=f'enter("#{s2}", {t + 0.5:.3f}, {{ y: 14, b: 6, d: 0.45 }}); exit("#{s2}", {t_end - 0.5:.3f});')
        sfx and self.cue(t, sfx)

    # ---------- o'tishlar va kamera ----------
    def flash(self, t, color="#fff", peak=0.28, sfx="shutter"):
        """yumshoq ekspozitsiya chaqnashi (0.3 s kirish + 0.7 s chiqish). Keskin 0.1 s chaqnash YO'Q."""
        e = self.uid("fl")
        self.add(body=f'<div class="layer" id="{e}" style="background:{color};opacity:0;z-index:60"></div>',
                 js=f'tl.fromTo("#{e}", {{ opacity: 0 }}, {{ opacity: {peak}, duration: 0.3, ease: "sine.inOut" }}, {t - 0.3:.3f});'
                    f'tl.to("#{e}", {{ opacity: 0, duration: 0.7, ease: "sine.inOut" }}, {t:.3f});')
        sfx and self.cue(t - 0.1, sfx)

    def blur_dip(self, t, amount=8, sfx="whoosh"):
        """kadr bir zum xiralashib qaytadi (o'tish). filter fromTo — boshlang'ich qiymat ANIQ (qora kadr tuzog'i)."""
        self.add(js=f'tl.fromTo("#cam", {{ filter: "blur(0px) brightness(1)" }}, {{ filter: "blur({amount}px) brightness(1.06)", duration: 0.3, ease: IO, immediateRender: false }}, {t - 0.3:.3f});'
                    f'tl.to("#cam", {{ filter: "blur(0px) brightness(1)", duration: 0.5, ease: IO }}, {t:.3f});')
        sfx and self.cue(t - 0.2, sfx)

    def dim_bg(self, t, t_end, blur=7, bright=0.72):
        """fon xiralashuvi (bob kartasi uchun) — fromTo bilan."""
        self.add(js=f'tl.fromTo("#cam", {{ filter: "blur(0px) brightness(1)" }}, {{ filter: "blur({blur}px) brightness({bright})", duration: 0.7, ease: "sine.inOut", immediateRender: false }}, {t:.3f});'
                    f'tl.to("#cam", {{ filter: "blur(0px) brightness(1)", duration: 0.8, ease: "sine.inOut" }}, {t_end - 0.8:.3f});')

    # ---------- CTA va yakun ----------
    def cta_pill(self, t, t_end, handle, after="Obuna bo'ling", y=1240, spec=None, sfx="click"):
        """oq pill: avatar + @handle → bir zumdan so'ng 'Obuna bo'ling' + ✓ (crossfade, tepkisiz)."""
        cfg = spec or self.tok("cta", {"bg": "#fff", "color": "#111", "accent": "#FB6C2A"})
        e = self.uid("ct")
        av = '<img src="assets/avatar.jpg" style="width:72px;height:72px;border-radius:50%;object-fit:cover;flex:none">'
        self.faces.add("Inter")
        self.add(css=f"#{e} .l2{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:14px;opacity:0}}",
                 body=f'<div class="abs ov" id="{e}" style="left:50%;top:{y}px;transform:translateX(-50%);z-index:65">'
                      f'<div style="position:relative;display:flex;align-items:center;gap:16px;padding:12px 30px 12px 12px;border-radius:60px;background:{cfg["bg"]};'
                      f'box-shadow:0 12px 30px rgba(0,0,0,.3);font:600 36px Inter;color:{cfg["color"]}">'
                      f'<span class="l1" style="display:flex;align-items:center;gap:16px">{av}{esc(handle)}</span>'
                      f'<span class="l2">{esc(after)}<span style="width:44px;height:44px;border-radius:50%;background:{cfg["accent"]};color:#fff;'
                      f'display:inline-flex;align-items:center;justify-content:center;font-size:28px">✓</span></span></div></div>',
                 js=f'enter("#{e}", {t:.3f}, {{ y: 40, b: 10, d: 0.7 }});'
                    f'tl.to("#{e} .l1", {{ opacity: 0, filter: "blur(6px)", duration: 0.35, ease: IO }}, {t + 1.3:.3f});'
                    f'tl.fromTo("#{e} .l2", {{ opacity: 0, scale: 1.15, filter: "blur(6px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.45, ease: IN }}, {t + 1.4:.3f});'
                    f'exit("#{e}", {t_end - 0.5:.3f});')
        sfx and self.cue(t + 1.4, sfx)

    def end_card(self, title, handle="", sub="", bg=None, spec=None):
        """yakuniy karta (DUR_VIDEO dan DUR gacha): fon qoplaydi, sarlavha + handle."""
        bg = bg or self.tok("end.bg", "#0d0d0d")
        spec = spec or self.tok("end.title", self.tok("keyword", {"family": "Anton", "size": 96, "case": "upper", "color": "#fff"}))
        e = self.uid("en")
        t0 = C.DUR_VIDEO - 0.68          # karta video tugashidan OLDIN to'liq paydo bo'ladi (aks holda bir kadr qora)
        h2 = f'<div class="h2" style="margin-top:22px;font:600 40px Inter;color:{self.tok("end.handle_color", "#fff")};opacity:.9">{esc(handle)}</div>' if handle else ""
        s2 = f'<div style="margin-top:10px;font:500 32px Inter;color:#ddd">{esc(sub)}</div>' if sub else ""
        self.add(body=f'<div class="layer" id="{e}" style="background:{bg};opacity:0;z-index:80;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center">'
                      f'<div class="t1" style="{self.font_css(spec)}">{esc(title)}</div>{h2}{s2}</div>',
                 js=f'tl.fromTo("#{e}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "sine.inOut" }}, {t0:.3f});'
                    f'enter("#{e} .t1", {t0 + 0.3:.3f}, {{ s: 1.15, y: 0, b: 14, d: 0.7 }});'
                    + (f'enter("#{e} .h2", {t0 + 0.6:.3f}, {{ y: 16, b: 6, d: 0.5 }});' if handle else ""))
        self.cue(t0, "whoosh")

    # ---------- natija ----------
    def result(self, **extra):
        d = dict(faces=sorted(self.faces), css="\n".join(self.css), body="\n".join(self.body), js="\n".join(self.js),
                 sfx_extra=self.sfx, media=self.media, bg=self.tok("bg", "#000"))
        d.update(extra)
        return d


PLAN_TYPES = ("keyword", "number", "tag", "card", "broll", "flash", "blur_dip", "dim_bg", "cta_pill", "end_card")


def run_plan(S, plan=None):
    """project.json "plan": [{"type":"keyword","t":12.4,"t_end":14.0,"text":"MUHIMI ESA", ...ixtiyoriy parametrlar}, ...]
    type -> Style metodi (PLAN_TYPES). Qolgan kalitlar metodga to'g'ridan-to'g'ri uzatiladi."""
    for it in (plan if plan is not None else C.CFG.get("plan", [])):
        it = dict(it)
        typ = it.pop("type")
        if typ not in PLAN_TYPES:
            raise SystemExit(f"plan: noma'lum element turi {typ!r} (bor: {PLAN_TYPES}) — uslubga xos bo'lsa style.py da qo'sh")
        getattr(S, typ)(**it)


BASE_CSS = """
.uk-grain{background-image:repeating-radial-gradient(circle at 17% 32%,rgba(255,255,255,.5) 0 1px,transparent 1px 3px);mix-blend-mode:overlay}
.uk-kw .kwf{position:relative;display:inline-block;margin:0 .07em}
.uk-kw .kwf .g{position:absolute;left:0;top:0;white-space:nowrap;clip-path:inset(0 100% 0 0)}
.uk-kw{z-index:40}
"""
