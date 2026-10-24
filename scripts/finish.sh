#!/bin/zsh
# finish.sh <uslub> <loyiha_papka> — raw render -> yakuniy (−14 LUFS, 2-pass lineal loudnorm) + telefon nusxasi (<30 MB)
set -e
L=$1
P=${2:-$UK_PROJECT}
[ -z "$P" ] && { echo "loyiha papkasini bering: finish.sh <uslub> <papka>"; exit 1; }
P=${P:A}
read NAME PREF VER <<< $(python3 -c "import json,sys;c=json.load(open('$P/project.json'));print(c.get('output_names',{}).get('$L','$L'), c.get('name','video'), c.get('version','v1'))")
RAW=$P/hf_$L/renders/${L}_raw.mp4
OUT=$P/out/${PREF}_${NAME}_${VER}.mp4
TEL=$P/out/telefon/${PREF}_${NAME}_${VER}_tel.mp4
mkdir -p $P/out/telefon
# 2-pass loudnorm (lineal)
J=$(ffmpeg -nostdin -hide_banner -i $RAW -af "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
mi=$(echo $J | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['input_i'])")
mtp=$(echo $J | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['input_tp'])")
mlra=$(echo $J | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['input_lra'])")
mth=$(echo $J | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['input_thresh'])")
mof=$(echo $J | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['target_offset'])")
ffmpeg -nostdin -v error -y -i $RAW -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=${mi}:measured_TP=${mtp}:measured_LRA=${mlra}:measured_thresh=${mth}:offset=${mof}:linear=true,aresample=48000" \
  -c:a aac -b:a 256k -movflags +faststart $OUT
ffmpeg -nostdin -v error -y -i $OUT -c:v libx264 -preset slow -crf 25 -maxrate 3.6M -bufsize 7M -pix_fmt yuv420p -c:a copy -movflags +faststart $TEL
echo "$L -> $OUT"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact=p=0 $OUT | tr '\n' ' '; echo
echo "LUFS: $(ffmpeg -nostdin -hide_banner -i $OUT -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' ')"
ls -la $OUT $TEL | awk '{print $5, $9}'
