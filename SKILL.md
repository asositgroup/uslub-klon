---
name: uslub-klon
description: O'zining uslublar kutubxonasiga ega mustaqil reel montaj skilli — foydalanuvchi namuna video yoki havola tashlasa, uning uslubini HAMMA jihatdan o'rganadi (har element o'lchanadi — shrift, rang, % joylashuv, kirish/chiqish; montaj ritmi, rang/grade, kamera, ovoz, tuzilma) va library/ ga yangi uslub sifatida saqlaydi (o'rgangan uslublarini yig'ib boradi, bir muallifning hamma videolarini birlashtiradi); keyin foydalanuvchi o'z videosini tashlasa — shu o'rganilgan uslubda 9:16 premium, silliq reel qilib montaj qiladi (aynan so'zlar bilan so'zma-so'z subtitr, yuz zonalari, HyperFrames, −14 LUFS) va natijani referens bilan raqamda solishtiradi. "/uslub-klon", "uslub klon", "shu videoni o'rgan", "bu uslubni o'rganib ol", "kutubxonaga qo'sh", "shunaqa qilib ber", "shu uslubda montaj qil", "<muallif> uslubida qil", "o'rgangan uslublaringni ko'rsat" so'rovlarida ishlat.
---

# uslub-klon — video uslubini o'rganish va shu uslubda montaj

Ish tili: **o'zbekcha**. To'liq mustaqil: hamma skriptlar, shriftlar, SFX, qoidalar va o'rganilgan uslublar shu papkada
(`~/.claude/skills/uslub-klon`). Boshqa montaj skillariga murojaat qilinmaydi.

**Avval o'qi:** `references/rules.md` (qat'iy qoidalar — har montajda), `references/smooth-motion.md` (silliqlik qiymatlari),
`references/lessons.md` (tuzoqlar), `library/INDEX.md` (o'rganilgan uslublar).

```
SK=~/.claude/skills/uslub-klon/scripts ; PY=~/Desktop/AI-Videos/.venv/bin/python      # boshqa joyda: UK_PY / o'z venv
LIB=~/.claude/skills/uslub-klon/library                                              # yoki UK_LIBRARY
```

## Uch rejim
| Foydalanuvchi | Rejim |
|---|---|
| namuna video/havola tashlaydi: "o'rgan", "kutubxonaga qo'sh", "shu uslubni yodla" | **A. O'rganish** |
| o'z videosini tashlaydi: "shu uslubda qil", "<uslub/muallif> uslubida", "shunaqa qilib ber" | **B. Montaj** (uslub kutubxonada bo'lmasa — avval A) |
| namuna + o'z videosi birga: "shunday video qilib ber" | **A → B** |
| "qanday uslublar o'rgangansan" | `library/INDEX.md` jadvalini ko'rsat (tanlovni foydalanuvchiga qoldir) |

---

## A. O'RGANISH (har yangi uslub — kutubxonaga qo'shiladi, eskilari saqlanadi)

### A1. Yuklab olish + avtomatik tahlil
```bash
$PY $SK/learn.py "<havola1>" "<havola2>" ... --slug <uslub-nomi> --author "<Muallif ismi>"
```
- `--slug`: qisqa lotin nom (masalan `iman-monolog`, `asror-reel`). Shu muallifning boshqa videolari keyin kelsa — **o'sha slug** bilan qayta
  chaqir (referenslar qo'shiladi, mavjud STYLE.md buzilmaydi) yoki format boshqacha bo'lsa yangi slug, lekin bir xil `--author`.
- Har referens: `library/_src/<id>.mp4` → `ref_analyze.py` (texnik, transkript + frazalar, kesimlar va nutqqa munosabati, har kadr grade,
  kamera harakati, audio: nutq−pauza, SFX zarbalari, kontakt varaqlar, video-use `timeline_view` bor bo'lsa) → `events.py`
  (grafik element hodisalari + har biriga 18 kadrlik strip, quti belgilangan).
- Natija: `library/<slug>/` — `refs.json`, `metrics.json` (median + oraliq), `STYLE.md` (raqamlar to'ldirilgan qolip), `style.json`, `style.py`,
  `keyframes/`; `library/INDEX.md` va `library/_mualliflar/<muallif>.md` yangilanadi.

### A2. Ko'z bilan o'rganish (ENG MUHIM — qoida 10: HAR elementni o'lcha)
1. `keyframes/*contact*` (2 fps, har qator 4 s) — hamma referenslarni oxirigacha ko'r.
2. `_src/<id>_an/events/events.md` + `ev_*.jpg` — har hodisa strip'ini ko'r; haqiqiy element bo'lsa inventarga yoz.
   Kerak bo'lsa aniq vaqtda qo'shimcha strip (lessons.md). Shrift o'lchami: element balandligi px (1080 kenglikka keltirilgan).
3. `_src/<id>_an/report.md` (raqamlar), `edit/takes_packed.md` (beat'lar), `tv_*.png` (to'lqin: SFX qaysi hodisaga bog'langan).
4. Ranglar: kadrdan piksel (lessons.md). Shriftlar: 3–6 nomzodni haqiqiy kadrda mock qilib solishtir (assets/fonts yoki OFL yuklab, uslub `fonts/` ga).

### A3. Uslubni yozish
- **STYLE.md** — barcha TODO bo'limlari: umumiy, tuzilma, kompozitsiya, tipografiya, ranglar, **elementlar inventari** (har element:
  qachon ishlatiladi / joy % / o'lcham-shrift-rang / kirish-turish-chiqish), subtitr, o'tishlar+kamera, B-roll, CTA, audio,
  **silliqlik moslamasi** (referensdagi tez pop → bizning qiymat), **OLINMAYDI** (qoida 7, 9, 6 bo'yicha).
- **style.json** — tokenlar: `faces`, `captions` (mode: `words|phrase|karaoke|dimfill`, font, accent, box, dim), `keyword` (+`keyword_dim`),
  `number`, `tag`, `card`, `cta`, `end`, `vignette`, `broll_text_entry`. Font spec: `{family,size,weight,case,color|gradient,grad_angle,lh,ls,shadow,stroke}`.
- **style.py** — `kit.Style.from_dir(__file__)` + `S.captions()` + `kit.run_plan(S)` (project.json "plan") + uslubga XOS elementlar
  (`S.add(css=..., body=..., js=...)` — kit'da yo'q bo'lsa shu yerda yoz, GSAP `tl`, `enter()`, `exit()`, `draw()` yordamchilari bor).
- **Sinov:** shu uslubni bitta qisqa klipda (foydalanuvchining eski videosi yoki istalgan talking-head 10–15 s) qur → `check` + `snapshot` →
  referens kadrlari bilan yonma-yon solishtir; o'xshamasa tuzat. `library/INDEX.md` qatorini to'ldir (holat: tayyor, qachon ishlatish).
- Foydalanuvchiga qisqa hisobot: nima o'rganildi (5–8 asosiy element), raqamlar, OLINMAYDI ro'yxati, sinov kadrlari.

---

## B. MONTAJ (o'rganilgan uslubda)

### B0. Uslubni aniqlash
- Foydalanuvchi uslub/muallif aytgan bo'lsa — `INDEX.md` dan. **Muallif nomi → uning HAMMA uslublari/referenslari birga** (qoida 11):
  qolip foydalanuvchi videosiga qarab (bitta spiker / suhbat / B-roll ko'p), raqamli maqsad — hamma referenslar median/oraliq.
- Aytmagan va bir nechta mos bo'lsa — ro'yxatni ko'rsat va so'ra (o'zing tanlama).

### B1. Loyiha + tozalash + matn
```bash
PRJ=~/Desktop/AI-Videos/<Mijoz yoki Mavzu>/<NN_nom>
$PY $SK/new_project.py /yo'l/video.mp4 $PRJ <NN_nom>    # src/manba.mp4, assets/base.mp4 (1080x1920 60fps), audio/voice.wav + clean16k.wav (asl ovoz, qoida 2), project.json
for L in uz kk tr; do HF_DEV=cpu HF_CT=int8 $PY $SK/tr.py $PRJ/audio/clean16k.wav $PRJ/audio/tr_$L.json $L; done
# audio/segments_final.json [{t0,t1,text}] — mutaxassis AYNAN aytgani (3 whisper'ni solishtirib, adabiy imlo); shubhali joy:
$PY $SK/align.py score $PRJ/audio/clean16k.wav <t0> <t1> "variant 1" "variant 2"
$PY $SK/align.py words $PRJ/audio/clean16k.wav $PRJ/audio/segments_final.json $PRJ/audio/words_final.json
```

### B2. Kadrlar, yuz, rang
```bash
$PY $SK/cuts.py $PRJ/src/manba.mp4                                     # kesimlar -> project.json "shots"
$PY $SK/face_zones.py $PRJ/assets/base.mp4 $PRJ/project.json $PRJ/tahlil/zones.jpg   # origin %, sub_y, tepa bo'sh zona (KO'R)
$PY -I $SK/retouch_src.py $PRJ/src/manba.mp4 $PRJ/assets/base_retush.mp4 0.65   # ixtiyoriy yuz retushi (asl 4K'dan bir marta)
$PY $SK/grade_match.py <LIB>/_src/<ref1>.mp4[,<ref2>.mp4...] $PRJ/src/manba.mp4 $PRJ/tahlil   # grade_match.jpg ni KO'R (teri tabiiymi)
ffmpeg -i $PRJ/assets/base_retush.mp4 -vf "<GRADE filtr>[,vignette=...]" -c:v libx264 -crf 16 -r 60 -an $PRJ/assets/base_grade.mp4
# project.json media.base = assets/base_grade.mp4 (retushsiz bo'lsa base.mp4 dan)
```
Uslub montaj ritmini talab qilsa (masalan kesim har ~2 s, bitta kamera) — `shots` ni virtual kameralar bilan bo'l
(scale 1.0 / 1.3–1.35 / 1.7, origin = yuz markazi, kesimlar so'z chegarasida, kamera miqyosi kesimda sakramaydi). Pauzalarni kesish — faqat
foydalanuvchi rozi bo'lsa (sinxron!).

### B3. Reja → TASDIQ (qoida 1)
`project.json`: `phrases` (ma'no bo'yicha 1–4 so'z, words_final bilan aynan mos), `accents`, `styles: ["<slug>"]`, `plan` —
uslub inventaridagi elementlarni foydalanuvchi gaplariga moslab: `{"type": keyword|number|tag|card|broll|flash|blur_dip|dim_bg|cta_pill|end_card, "t":…, "t_end":…, …}`.
Foydalanuvchiga jadval ko'rsat:
| Vaqt | Gap (aynan) | Referensdagi mos element (STYLE.md #) | Bizdagi element | Izoh |
+ referensdan 3–4 kalit kadr, OLINMAYDI ro'yxati, ❓ ochiq savollar (handle/avatar, musiqa kerakmi — qoida 7, B-roll mavzulari,
pauza kesish). **"boshla" demaguncha qurma.**

### B4. Qurish va tekshirish
```bash
$PY $SK/broll_search.py $PRJ <slot> "so'rov 1" "so'rov 2"     # sheet.jpg ni KO'R (qoida 6) -> broll_prep.py $PRJ <slot> <idx> <ss> <dur> full <grade>
$PY $SK/build.py --project $PRJ <slug>                         # -> $PRJ/hf_<slug>/index.html
(cd $PRJ/hf_<slug> && npx --yes hyperframes@0.8.171 lint && npx --yes hyperframes@0.8.171 check)
$PY $SK/smooth_check.py $PRJ/hf_<slug>/index.html               # 0 bo'lishi shart
(cd $PRJ/hf_<slug> && npx --yes hyperframes@0.8.171 snapshot --at t1,t2,... --no-end --describe false)   # contact-sheet ni KO'R:
#   yuzga tushmaydimi, matn o'qiladimi, referensga o'xshaydimi (yonma-yon), xavfsiz zona
```

### B5. Render + uslub tekshiruvi + topshirish
```bash
(cd $PRJ/hf_<slug> && PRODUCER_ENABLE_CHUNKED_ENCODE=true FFMPEG_ENCODE_TIMEOUT_MS=5400000 \
  npx --yes hyperframes@0.8.171 render -o renders/<slug>_raw.mp4 -q delivery -w 1 -f 60 > renders/render.log 2>&1)
$SK/finish.sh <slug> $PRJ                                       # -> out/<nom>_<slug>_v1.mp4 (−14 LUFS) + out/telefon/..._tel.mp4
$PY $SK/smooth_check.py $PRJ/out/<fayl>.mp4                      # keskin yorug'lik sakrashi = 0
$PY $SK/qc.py $PRJ/out/<fayl>.mp4 <slug> 1.3:huk 6.0:otish ...   # tahlil/qc/*_strips.jpg — kirish oynalari kadrma-kadr (KO'R)
$PY $SK/ref_analyze.py $PRJ/out/<fayl>.mp4 $PRJ/tahlil/out_an
$PY $SK/style_compare.py <LIB>/_src/<ref1>_an/metrics.json [...] $PRJ/tahlil/out_an/metrics.json --md $PRJ/tahlil/style_compare.md
```
FARQ qatorlarini tuzat (ko'pi bilan 3 aylanish), QOIDA — tuzatilmaydi. Foydalanuvchiga: video (telefon nusxasi), davomiylik, LUFS,
style_compare jadvali, OLINMAGAN narsalar, ❓ qolganlar. Yangi saboq bo'lsa — `references/lessons.md` ga.

## Fayllar
```
SKILL.md · README.md
references/  rules.md · smooth-motion.md · lessons.md
scripts/     learn.py (o'rganish) · ref_analyze.py · events.py · kit.py (komponentlar) · common.py · build.py · finish.sh
             new_project.py · tr.py · align.py · cuts.py · face_zones.py · retouch_src.py
             grade_match.py · style_compare.py · smooth_check.py · qc.py · textw.py · sheets.sh · music_pick.py · broll_search.py · broll_prep.py
assets/      fonts/ (OFL) · gsap.min.js · sfx/ (yumshoq; sparkle/chime yo'q) · models/ (YuNet yuz)
library/     INDEX.md · <uslub>/{STYLE.md, style.json, style.py, metrics.json, refs.json, keyframes/, fonts/, img/} · _mualliflar/ · _src/ (videolar — git'ga kirmaydi)
```
Talablar: ffmpeg ≥5.1, node + `npx hyperframes@0.8.171`, `yt-dlp`, Python 3.9+ venv (numpy scipy pillow opencv faster-whisper torch torchaudio≤2.8),
Pexels kaliti — `keys/pexels.env` da bor (o'zingizniki bo'lsa `~/.pexels.env`, u ustun). Ixtiyoriy: `~/video-use` (timeline_view tasmalari).
