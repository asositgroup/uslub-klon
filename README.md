# uslub-klon — Claude Code skill

Namuna video tashlasangiz — uning uslubini **hamma jihatdan o'rganadi** va o'z kutubxonasiga saqlaydi; keyin o'z videongizni
tashlasangiz — **xuddi shu uslubda** 9:16 reel qilib montaj qiladi. O'rgangan uslublarini yig'ib boradi, bitta muallifning hamma
videolarini bitta uslubga birlashtiradi. To'liq mustaqil (boshqa montaj skillariga bog'liq emas).

**O'rganish:** yt-dlp → tahlil (tuzilma, temp, montaj ritmi, kesim-nutq munosabati, har kadr rangi, kamera, ovoz, SFX) → grafik element
hodisalari (har biriga kadrma-kadr strip) → `library/<uslub>/` (STYLE.md, style.json tokenlari, style.py qurilishi, metrics.json).

**Montaj:** Auphonic shovqin tozalash → whisper + MMS forced alignment (aynan so'zlar, so'zma-so'z vaqt) → kesim va yuz zonalari →
referensga rang moslash → reja (tasdiq) → HyperFrames + GSAP (overshootsiz, silliq) → 60 fps render → −14 LUFS → referens bilan raqamli solishtirish.

## O'rnatish
```bash
git clone https://github.com/asositgroup/uslub-klon.git ~/.claude/skills/uslub-klon
```
Claude Code'ni qayta oching — `/uslub-klon` paydo bo'ladi. Yangilash: `cd ~/.claude/skills/uslub-klon && git pull`.
Talablar: ffmpeg ≥5.1, Node.js (`npx hyperframes`), yt-dlp, Python 3.9+ venv:
`pip install numpy scipy pillow opencv-python-headless faster-whisper torch "torchaudio<=2.8"`.
Kalitlar: `~/.auphonic.env` (`AUPHONIC_API_KEY=...`), Pexels kaliti repoda bor (`keys/pexels.env`; o'zingizniki bo'lsa `~/.pexels.env`). Ixtiyoriy: [video-use](https://github.com/browser-use/video-use) → `~/video-use`.

## Ishlatish (Claude Code'da)
- "Shu videoni o'rgan: <havola>" — yangi uslub kutubxonaga qo'shiladi
- "Shu uslubda montaj qil" + videongiz — o'rganilgan uslubda montaj (avval reja jadvali, "boshla" deganingizdan keyin quriladi)
- "<Muallif> uslubida qil" — o'sha muallifning hamma o'rganilgan videolari birga
- "Qanday uslublar o'rgangansan?" — `library/INDEX.md`

Batafsil: [`SKILL.md`](SKILL.md) · qoidalar: [`references/rules.md`](references/rules.md) · silliqlik: [`references/smooth-motion.md`](references/smooth-motion.md)
