#!/bin/bash

# Usage: extract_from_video.sh DJI_nnnn.mp4 OutputDir
#   creates PNG files for each second of video
#   extracts the subtitle track which holds the lat,lon etc

mp4="$1"
outputdir="$2"
mp4name=$(basename "$mp4")
logfile="$outputdir/$mp4name".extract.log
frames_per_sec=1

if [ "$2" == "" ]; then echo "Usage: file.mp4 outputdir" >&2; exit 1; fi

msg()
{
	echo "$1"
}

err()
{
	msg "$1"
	exit 1
}

msg "Extracting metadata from $mp4name ..."
ffmpeg -i "$mp4" "$outputdir/$mp4name".srt > "$logfile" 2>&1
if [ $? -ne 0 ]; then err "Error extracting SRT from $mp4"; fi

echo "Extracting frames from $mp4name ..."
ffmpeg -i "$mp4" -r $frames_per_sec "$outputdir/$mp4name"_%04d.png > "$logfile" 2>&1
if [ $? -ne 0 ]; then err "Error extracting frames from $mp4"; fi
