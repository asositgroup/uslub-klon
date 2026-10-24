# Qat'iy qoidalar (foydalanuvchi o'rnatgan — har montajda)

1. **Reja → tasdiq → montaj.** Transkript + uslub pasporti + beat-ma-beat reja jadvalini ko'rsatmaguncha va foydalanuvchi
   "boshla" demaguncha qurma. Ishni o'z tashabbusing bilan kengaytirma. Uslubni foydalanuvchi o'zi tanlayman desa — ro'yxatni ko'rsat va KUT.
2. **Ovoz — asl yozuvdan, Auphonic ISHLATILMAYDI** (foydalanuvchi talabi, 2026-10-24) va boshqa tashqi/pullik tozalash servislari ham.
   `new_project.py` ovozni o'zi ajratadi (faqat 70 Hz highpass), balandlik `finish.sh` da (−14 LUFS). Kuchli lokal shovqin filtrlari
   (afftdn/RNNoise) sukut bo'yicha yo'q — nutqni yeydi; ovoz juda shovqinli bo'lsa foydalanuvchiga ayt va so'ra.
3. **Subtitr = mutaxassisning AYNAN so'zlari** (adabiy imlo, uning so'z shakllari, qisqartirilmaydi). Har so'z vaqti MMS forced alignment
   (`scripts/align.py`). Bo'lak birinchi so'zida chiqadi, oxirgi so'zi tugaguncha turadi. Subtitr hamma narsa ustida (z-index 70).
4. **Hamma narsa silliq** (`smooth-motion.md`): kirish ≥0.45–0.9 s `expo.out` + blur, chiqish ≥0.5 s `power2.inOut`, overshoot/elastic/bounce
   va qisqa `yoyo` tepkilar YO'Q, kamera kesimda sakramaydi, `filter` tween'lari doim `fromTo` (aniq boshlang'ich qiymat).
   Referensda tez "pop" bo'lsa ham — bizda silliq ekvivalenti. `smooth_check.py` kod va video = 0.
5. **Yuz va bosh ochiq.** Hech bir yozuv/grafika yuzga tushmaydi (`face_zones.py` bilan o'lcha). IG xavfsiz zona: hech narsa y>1450 da emas,
   1000–1700 polosada x>930 da emas.
6. **B-roll odamlari:** qora tanlilar faqat gapda aytilsa; diniy mavzuda boshi ochiq ayollar yo'q (fondagisi ham); yuzsiz kadrlar
   (qo'l, predmet, orqadan) afzal; muqaddas shaxslar hech qanday shaklda tasvirlanmaydi. Manba: Pexels (yoki foydalanuvchining o'z footage'i).
7. **Musiqa so'ramasdan qo'shilmaydi.** Qo'shilsa — sokin, zarbsiz, ovozni HECH QACHON to'smaydi (nutq polosasida nutq musiqadan median
   ≥19 dB), Content ID'siz. SFX faqat yumshoq whoosh/click/pop — **«trling» sparkle/chime HECH QACHON**.
8. **Premium, bachkana emas** — emoji, komiks effektlari faqat foydalanuvchi so'rasa.
9. **Referensdan faqat TEXNIKA olinadi** — uning sahnalari, metaforalari, B-roll kadrlari, matnlari ko'chirilmaydi (foydalanuvchi buni
   "o'g'irlik" degan). Uslub = shrift, rang, joylashuv, harakat, ritm, element turlari.
10. **Referensni to'liq inventarlash** — har referensdagi HAR element o'lchanadi (shrift, o'lcham, rang, kadr % joylashuv, kirish/chiqish
    vaqti va turi), umumiy taassurot emas. `events.py` + strip'lar + STYLE.md "Elementlar inventari".
11. **Muallif nomi aytilsa — uning HAMMA o'rganilgan videolari birga** (bitta video emas): `library/_mualliflar/<muallif>.md`.
12. **Eski versiya o'chirilmaydi** — yangisi `_v2`, eski `out/` da qoladi. Natijalar loyiha papkasida, Downloads'da emas.
13. Ruxsatsiz ishlatilmaydi: ElevenLabs, kie.ai va boshqa pullik generativ servislar.
14. **"Tayyor" deyishdan oldin tekshir:** lint/check 0 xato, snapshot'larni ko'z bilan, render'dan keyin kirish oynalarini kadrma-kadr
    (`qc.py`), `smooth_check.py` video, LUFS (−14), fon jarayonlari haqiqatda tugaganini.
