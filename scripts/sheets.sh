#!/bin/zsh
# sheets.sh SRC_DIR OUT_DIR : 1 fps timed contact sheet per mp4 (8 cols)
src="$1"; out="$2"; mkdir -p "$out"
for f in "$src"/*.mp4; do
  id=$(basename "$f" .mp4); [ -f "$out/$id.jpg" ] && continue
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f"); d=${d%.*}; d=$((d+1))
  rows=$(( (d+7)/8 )); [ $rows -lt 1 ] && rows=1
  ffmpeg -nostdin -v error -i "$f" -vf "fps=1,scale=200:-2,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=14:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x${rows}:padding=2" -frames:v 1 -q:v 3 "$out/$id.jpg"
  echo "$id ${d}s"
done
