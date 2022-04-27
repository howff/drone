# OpenDroneMap

```
git clone https://github.com/OpenDroneMap/WebODM --config core.autocrlf=input --depth 1
cd WebODM
./webodm.sh start --media-dir /mnt/hgfs/Downloads/Drone --port 8413
```

## OpenDroneMap GCPs

See https://docs.opendronemap.org/gcp/

# Extract/Convert DJI log file to OpenDroneMap GCPs

The aim is to extract suitable images from the video,
and create a GCP file which allows OpenDroneMap to register the images
and create a ground map or DSM.

The video already includes some information as a subtitle track.
This can be extracted using ffmpeg. However it is lacking
full resolution latitude and longitude (the four decimal places
means the drone appears stationary if moving less than 10 meters).
It also lacks pointing angles. But it does have altitude above take-off
point and both horizontal and vertical speed.

More information can be obtained by downloading a GPX file from airdata.
More frequent and higher resolution coordinates.

Best information can be obtained by downloading a CSV file from
phantomhelp.com/LogViewer. It contains almost everything we need
although units are feet.

Extract images, rate of one per second:
```
extract_from_video.sh /mnt/hgfs/Downloads/Drone/Frames/DJI_0185.mp4
```

```
srt_to_gcp.py /mnt/hgfs/Downloads/Drone/Frames/DJI_0185.srt /mnt/hgfs/Downloads/Drone/Frames/DJI_0185_0001.png
./srt_to_gcp.py /mnt/hgfs/Downloads/Drone/Frames/DJI_0185.srt /mnt/hgfs/Downloads/Drone/Frames/DJI_0185_0001.png /mnt/hgfs/Downloads/Drone/Frames/DJI_0185 > /mnt/hgfs/Downloads/Drone/Frames/gcp_list.txt
./srt_to_gcp.py /mnt/hgfs/Downloads/Drone/Frames/DJI_0185 /mnt/hgfs/Downloads/Drone/Frames/DJI_0185.srt
```

```
gpx_to_gcp.py
```

Create a gcp_list.txt file by reading the MP4 along with the CSV.
Also needs to read one PNG file to determine its dimensions.
The gcp file will contain one line for each useful image; the other images can be removed.
```
create_gcp.py DJI_nnnn.MP4 DJIFlightRecord_xxx.csv
```

