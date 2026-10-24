# Silliq harakat standarti (foydalanuvchi talabi — HAR montajda, MAJBURIY)

> "Videoning ichidagi barcha narsa, motion animatsiya va grafikalar smooth tarzda bo'lsin" (2026-10-05).
> Bu faqat so'zlarga emas — kartalar, ikonkalar, chiziqlar, raqamlar, kamera, o'tishlar, chaqnash, fon blur, tugma bosilishi,
> kursor — HAMMASIGA tegishli. Bitta keskin element butun videoni "arzon" ko'rsatadi.

## Qiymatlar

| Nima | Qiymat |
|---|---|
| So'z / qator kirishi | 0.55–0.7 s, `expo.out` (yoki `power3.out`), `y:+40→0`, `filter: blur(12px)→0`, opacity 0→1; so'z vaqtidan 0.08 s oldin |
| So'zlar ketma-ketligi | har biri o'z vaqtida, lekin oldingisi tugamasdan (0.06–0.08 s overlap) |
| Katta sarlavha so'zi | 0.7–0.8 s, `expo.out`, scale 1.06→1 qo'shimcha |
| Karta / panel / telefon kirishi | 0.8–0.9 s `expo.out`, y 140–520 → 0, blur 10–14 → 0 |
| Chiqish (hamma narsa) | **0.5 s** `power2.inOut`, y −16, blur 0→8, opacity →0 — hech qachon hard-cut, hech qachon <0.35 s |
| Subtitr | kirish 0.45 s `expo.out` (y 14→0, blur 6→0), chiqish 0.3 s `power2.inOut` |
| "Pop" (ikonka, belgi, yorliq, Like, muhr) | **overshootsiz**: scale 0.82–0.88→1 + blur 8→0, 0.6–0.75 s `expo.out` |
| Tugma bosilishi | ikki tween: scale 1→0.9 (0.22 s `power2.inOut`) → 1 (0.4 s `expo.out`) — `yoyo` 0.08–0.1 s EMAS |
| Matn/belgi almashishi (placeholder → "+") | ikki qatlam crossfade 0.3–0.4 s + kelayotganiga scale 1.25→1, blur 6→0 |
| Tez siljish (sweep, karta uchishi) | harakat davomida blur 6–10 px → 0 (motion blur) |
| SVG chizish (✓, strelka, grafik) | 0.4–1.1 s `power2.inOut`, opacity 0 dan |
| Raqam sanog'i | `power2.inOut`, ≥1.2 s (5 000→25 000: 2.0 s), qadam 50 ga yaxlitlash, `tabular-nums` |
| Kamera "nafas" push | butun kadr bo'yicha `sine.inOut`; kadrlar NAVBAT bilan 1.0→1.035 va 1.035→1.0 — kesimda miqyos sakramaydi |
| Huk zoom-out | 1.07→1.0, 3.5 s `sine.inOut` |
| Fon blur (bob kartasi) | kirish 0.7 s, chiqish 0.8 s `sine.inOut`, blur ≤7 px + brightness 0.72 |
| Ekspozitsiya chaqnashi (kesimda) | opacity ≤0.22, kirish 0.3 s + chiqish 0.7 s `sine.inOut` (0.12 s chaqnash — keskin) |
| Kursor miltillashi | `sine.inOut` 0.5 s, ko'pi bilan 2 marta |
| Qora ekranga yakun | 0.6 s `sine.inOut` |
| Render fps | manba fps × 2 (25→50, 30→60): `npx hyperframes render -f 50` |

## Referens ustunligi (2026-10-05)
Foydalanuvchi "referens bilan 1 xil" desa — referensdan O'LCHANGAN tezlik (kadrma-kadr) bu jadvaldan ustun: masalan uslub-27 so'z
kirishi 0.26 s, chiqish 0.24 s. Overshoot/elastic/sakrash taqiqi esa baribir amal qiladi.

## Taqiqlangan (keskin ko'rinadi)
- `back.out(...)`, `elastic`, `bounce` — overshoot "sakrash" (premium/jiddiy uslubda hech qachon).
- `yoyo` bilan ≤0.15 s "tepki"/silkinish, `repeat` bilan titratish (glitch faqat uslub talab qilsa va 1 marta).
- 0.1–0.2 s li opacity almashishlari, `duration` < 0.3 s li har qanday ko'rinadigan tween.
- `ease: "none"` / `power1.in` kirish yoki chiqishda (progress-bar to'lishi bundan mustasno).
- Layout xossalarini (height, margin, top, letterSpacing) tween qilish — piksel sakraydi; faqat transform/opacity/filter.

## Tuzoq: `filter` tween'i boshlang'ich qiymatsiz
`tl.to("#cam", {filter: "blur(7px) brightness(0.72)"})` — agar #cam da oldin filter bo'lmasa, GSAP `none` dan interpolyatsiya
qiladi va `brightness` 0 dan boshlanadi → bir kadrda QORA ekran, keyin sekin yorishadi (Storis v1/v2, 6.78 s: yorug'lik 88→18).
Har doim `fromTo` bilan to'liq juftlik: `{filter:"blur(0px) brightness(1)"}` → `{filter:"blur(7px) brightness(0.72)"}`,
yoki boshida `gsap.set(el, {filter:"blur(0px) brightness(1)"})`. Xuddi shu `drop-shadow`, `saturate`, `contrast` uchun.

## Tekshiruv (render qilingandan keyin, majburiy)
Avval avtomatik: `python ~/.claude/skills/uslub-klon/scripts/smooth_check.py hf/index.html` (kod) va `python ~/.claude/skills/uslub-klon/scripts/smooth_check.py final.mp4`
(kadrma-kadr yorug'lik sakrashi ≥20 — 0 bo'lishi kerak). Keyin vaqtlar bilan kadr varaqlari: `smooth_check.py final.mp4 t1 t2 ...`.
Snapshot yetarli emas. Render qilingan videodan har asosiy kirish/chiqish oynasini 10–12 kadr ketma-ket chiqarib ko'r:
```bash
ffmpeg -i final.mp4 -vf "select='between(n,N0,N0+11)',scale=270:-1,tile=6x2" -frames:v 1 -fps_mode passthrough entry.jpg
```
Har kadrda o'zgarish bir tekis bo'lsin (sakrash, birdan paydo bo'lish, overshoot yo'q). Lint/check'dan keyin
`grep -c "back.out\|elastic" index.html` = 0 bo'lishi kerak.
