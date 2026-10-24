#!/bin/zsh
# auphonic_clean.sh — videoning orqa fon shovqinini Auphonic API orqali olib tashlaydi.
# Video Auphonic'ka yuborilmaydi: faqat audio (FLAC) yuklanadi, tozalangan WAV qaytib keladi
# va asl videoga qayta ulanadi (-c:v copy, tasvir o'zgarmaydi).
#
# Ishlatish:
#   auphonic_clean.sh <video.mp4> [chiqish_papka] [--method speech_isolation|dynamic|static|classic]
#                     [--amount 0|3|6|9|12|15|18|24|30|36|100] [--deverb 0|-1|3|6..] [--lufs -16] [--no-level]
# Natija: <papka>/<nom>_auphonic.mp4 (asl tasvir + toza ovoz) va <nom>_auphonic.wav
# Kalit: ~/.auphonic.env ichida  AUPHONIC_API_KEY=...   (auphonic.com → Account Settings → API Key)
#
# Usullar (Auphonic): speech_isolation = faqat nutq qoladi (musiqa ham ketadi) — standart;
# dynamic = nutq va musiqa qoladi; static = faqat doimiy shovqin (konditsioner, guvillash); classic = eski algoritm.
# --amount 0 = to'liq (100 dB), 12 = o'rtacha, 24 = kuchli.

set -e
setopt NO_NOMATCH
in="$1"; [ -z "$in" ] && { sed -n 2,14p "$0"; exit 1; }
[ -f "$in" ] || { echo "Fayl topilmadi: $in"; exit 1; }
shift
out_dir=""; method="speech_isolation"; amount=0; deverb=0; lufs=-16; level=true
while [ $# -gt 0 ]; do
  case "$1" in
    --method) method="$2"; shift 2;;
    --amount) amount="$2"; shift 2;;
    --deverb) deverb="$2"; shift 2;;
    --lufs) lufs="$2"; shift 2;;
    --no-level) level=false; shift;;
    *) out_dir="$1"; shift;;
  esac
done
[ -z "$out_dir" ] && out_dir="$(dirname "$in")"
mkdir -p "$out_dir"

[ -f ~/.auphonic.env ] && source ~/.auphonic.env
[ -z "$AUPHONIC_API_KEY" ] && { echo "AUPHONIC_API_KEY yo'q: ~/.auphonic.env fayliga AUPHONIC_API_KEY=... yozing"; exit 2; }
AUTH="Authorization: bearer $AUPHONIC_API_KEY"
API=https://auphonic.com/api
CURL=(curl -sS --retry 5 --retry-delay 3 --retry-all-errors --max-time 600)   # GET
POST=(curl -sS --retry 2 --retry-delay 3 --max-time 900)                     # POST: duplicate yaratmaslik uchun

name="$(basename "${in%.*}")"
work="$(mktemp -d "${TMPDIR:-/tmp}/auphonic.XXXXXX")"
trap 'rm -rf "$work"' EXIT

has_audio=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$in" | head -1)
[ -z "$has_audio" ] && { echo "Videoda audio yo'q"; exit 3; }

echo "1/5 Audio ajratilmoqda (FLAC)…"
ffmpeg -nostdin -v error -y -i "$in" -map 0:a:0 -vn -c:a flac "$work/in.flac"

echo "2/5 Auphonic production yaratilmoqda ($method, amount=$amount, deverb=$deverb, $lufs LUFS)…"
json=$(python3 -I - "$name" "$method" "$amount" "$deverb" "$lufs" "$level" <<'PY'
import json, sys
name, method, amount, deverb, lufs, level = sys.argv[1:7]
alg = {"denoise": True, "denoisemethod": method, "denoiseamount": int(amount),
       "filtering": True, "leveler": level == "true", "normloudness": True,
       "loudnesstarget": int(lufs), "maxpeak": -1}
if method in ("static", "dynamic", "speech_isolation"):
    alg["deverbamount"] = int(deverb)
print(json.dumps({"metadata": {"title": name}, "output_basename": name + "_auphonic",
                  "output_files": [{"format": "wav-24bit"}], "algorithms": alg}))
PY
)
resp=$("${POST[@]}" -X POST "$API/productions.json" -H "$AUTH" -H "Content-Type: application/json" -d "$json")
uuid=$(print -r -- "$resp" | python3 -I -c "import sys,json; d=json.load(sys.stdin); print((d.get('data') or {}).get('uuid','')) if d.get('status_code')==200 else print('')")
[ -z "$uuid" ] && { echo "Production yaratilmadi:"; print -r -- "$resp" | head -c 600; echo; exit 4; }
echo "   uuid: $uuid"

echo "3/5 Audio yuklanmoqda…"
up=$("${POST[@]}" -X POST "$API/production/$uuid/upload.json" -H "$AUTH" -F "input_file=@$work/in.flac")
print -r -- "$up" | python3 -I -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status_code')==200 else 1)" || { echo "Yuklash xatosi:"; print -r -- "$up" | head -c 600; echo; exit 5; }
"${POST[@]}" -X POST "$API/production/$uuid/start.json" -H "$AUTH" >/dev/null

echo "4/5 Auphonic ishlov bermoqda…"
last=""
while true; do
  st=$("${CURL[@]}" "$API/production/$uuid/status.json" -H "$AUTH" | python3 -I -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('status'), d.get('status_string'))" 2>/dev/null || echo "? ?")
  [ "$st" != "$last" ] && echo "   $st" && last="$st"
  case "${st%% *}" in
    3) break;;
    2|9|11|98) echo "Auphonic xatosi: $st  (https://auphonic.com/engine/status/$uuid)"; exit 6;;
  esac
  sleep 8
done

echo "5/5 Natija yuklab olinmoqda va videoga ulanmoqda…"
url=$("${CURL[@]}" "$API/production/$uuid.json" -H "$AUTH" | python3 -I -c "import sys,json; d=json.load(sys.stdin)['data']; print([f['download_url'] for f in d['output_files'] if f.get('download_url')][0])")
"${CURL[@]}" -L "$url" -H "$AUTH" -o "$work/raw.wav"
# Bepul tarif: Auphonic natijaga ~6.4 s reklama jinglini qo'shadi — ba'zan BOSHIGA, ba'zan OXIRIGA
# (59 s faylda boshida, 20 s faylda oxirida edi). auphonic_align.py asl ovozni natija ichidan topadi,
# aynan asl uzunlikda kesadi va boshi/o'rtasi/oxiri sinxronligini tekshiradi.
${UK_PY:-$( [ -x ~/Desktop/AI-Videos/.venv/bin/python ] && echo ~/Desktop/AI-Videos/.venv/bin/python || echo python3 )} -I "$(dirname "$0")/auphonic_align.py" "$in" "$work/raw.wav" "$out_dir/${name}_auphonic.wav" \
  || { cp "$work/raw.wav" "$out_dir/${name}_auphonic_RAW.wav"; echo "DIQQAT: sinxronlik buzilgan — RAW saqlandi, tekshiring"; exit 7; }
ffmpeg -nostdin -v error -y -i "$in" -i "$out_dir/${name}_auphonic.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 320k -ar 48000 -movflags +faststart "$out_dir/${name}_auphonic.mp4"

floor(){ ffmpeg -nostdin -hide_banner -i "$1" -map 0:a:0 -af astats -f null - 2>&1 | awk -F': ' '/RMS (trough|through) dB/{v=$2} END{printf "%.1f", v}'; }
loud(){ ffmpeg -nostdin -hide_banner -i "$1" -map 0:a:0 -af ebur128 -f null - 2>&1 | awk '/I:/{v=$2} END{print v}'; }
echo "Tayyor: $out_dir/${name}_auphonic.mp4"
echo "Shovqin qavati (RMS trough): oldin $(floor "$in") dB → keyin $(floor "$out_dir/${name}_auphonic.wav") dB"
echo "Balandlik: oldin $(loud "$in") LUFS → keyin $(loud "$out_dir/${name}_auphonic.wav") LUFS"
echo "Auphonic sahifasi: https://auphonic.com/engine/status/$uuid"
