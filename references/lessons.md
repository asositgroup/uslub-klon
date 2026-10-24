# Saboqlar va tuzoqlar

## Referens o'rganish
- Instagram: `yt-dlp` havoladagi `?utm_source/stkn` siz ishlaydi; login so'rasa — brauzer orqali yuklab, faylni `learn.py` ga bering.
- Whisper so'z chegaralari pauzalarni "yeydi" — `ref_analyze.py` ularni nutq polosasi energiyasi bilan qisqartiradi (pauzalar va kesim-nutq
  munosabati shundan to'g'ri chiqadi). O'zbek-rus aralash nutqda whisper matni buziladi — beat'larni ekrandagi matn bilan birga aniqla.
- `events.py` NOMZOD beradi (odam harakati ham tushadi) — strip'larni ko'z bilan ko'rib, haqiqiy elementlarni inventarga yoz.
  Kadrma-kadr strip: `ffmpeg -ss T -t 0.62 -i v.mp4 -vf fps=30,scale=216:-2,tile=9x2:padding=2 -frames:v 1 s.jpg`.
- Kontakt varaq vaqti: 2 fps, har qator 8 kadr = 4 s → indeks/2 = sekund (strip vaqtini shundan hisobla, taxmin qilma).
- Rang: kadrdan eng to'yingan pikselni ol; kichik matnda chetga tushadi — taxminiy deb belgila.
- Tez montajli reellarda kesimlarning 2/3 qismi gap o'rtasida (ko'p kamera / B-roll ustiga ovoz) — bu normal, nutq kesilmaydi.
- Referenslar musiqasi ko'pincha baland (nutq−pauza 5–13 dB) — qoida 7 bo'yicha olinmaydi; `style_compare` QOIDA deb belgilaydi.

## HyperFrames / kit
- `style="..."` atributi ichida qo'sh tirnoq ishlatma — shrift nomi `'Anton'` (bir tirnoq). Aks holda atribut erta yopilib o'lcham/rang yo'qoladi.
- `color: transparent` (gradient matn) — lint `text_not_painted` → `rgba(...,.01)` + `-webkit-text-fill-color:transparent`.
- Ustma-ust qatlamli matn effekti (xira + to'lish) — `data-layout-allow-overlap` ELEMENTLARNING O'ZIGA (konteynerga emas).
- `<video>` vaqtli o'rovchi ichida bo'lmasin (`video_nested_in_timed_element`) — o'rovchi vaqtsiz, ko'rinish `tl.set(opacity)`.
  Bir xil src+start ikki video — `duplicate_media_discovery_risk` → ikkinchisi uchun fayl nusxasi.
- `filter` tween'i boshlang'ich qiymatsiz (`tl.to`) → GSAP brightness'ni 0 dan boshlaydi = bir kadr QORA. Doim `fromTo`.
- `letterSpacing`, `height`, `margin`, `top` tween qilma — piksel sakraydi; faqat transform/opacity/filter/clip-path.
- `snapshot --at a,b,c` — BITTA chaqiruvda hamma vaqtlar. Render: `-w 1` + `PRODUCER_ENABLE_CHUNKED_ENCODE=true` (16 GB RAM).
- Split-ekran bitta kameradan: tepa panel zoom ~1.35× (2× faqat ko'zlarni ko'rsatadi), yuz panel tepasidan ~380 px da.
- Yorug' fondagi oq subtitr — kit sukut bo'yicha ikki qatlamli soya beradi; baribir o'qilmasa `captions.box` yoki yumshoq scrim.

- Yakuniy karta fade'i asosiy video tugashidan OLDIN tugashi kerak (kit.end_card: DUR_VIDEO−0.68 dan 0.6 s), aks holda video
  tugagan kadrda qora fon chiqadi (smooth_check: yorug'lik 96→19).

## Rang moslash
- `grade_match.py` — o'rta yorug'lik va iliqlikni to'liq ko'chirish terini buzadi (sahna mazmuni boshqa) → `--strength 0.4` (qisman),
  qora/oq nuqta va to'yinganlik to'liq. Natija varag'ini ko'z bilan ko'r. Bir nechta referens — vergul bilan.

## Audio
- Auphonic: `auphonic_clean.sh` jingl joyini o'zi topadi va sinxronni tekshiradi; bepul tarif 2 soat/oy.
- Yakun: `finish.sh` 2-pass lineal loudnorm −14 LUFS, TP −1.5 + telefon nusxasi (<30 MB).
