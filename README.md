# OpenDroneMap

```
git clone https://github.com/OpenDroneMap/WebODM --config core.autocrlf=input --depth 1
cd WebODM
./webodm.sh start --media-dir /mnt/hgfs/Downloads/Drone --port 8413
./webodm.sh stop
./webodm.sh down # important to fully shut down network etc
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

Create a geo.txt or gcp_list.txt file by reading the MP4 along with the CSV.
The geo.txt file is preferred. Supposedly a gcp_list is only used for fine adjustments.
Also needs to read one PNG file to determine its dimensions if writing the gcp_list.txt format.
The gcp file will contain one line for each useful image; the other images can be removed.
Useful images are those where the coverage is different compared to the previous image.
This is determined by position not by camera angle so if the drone rotates it won't notice.
It also assumes the drone camera is pointing at the nadir.
```
create_gcp.py DJI_nnnn.MP4 DJIFlightRecord_xxx.csv
```

For example

```
./extract_from_video.sh /mnt/hgfs/Downloads/Drone/SourceCopies/DJI_0185.MP4 /mnt/hgfs/Downloads/Drone/Frames
./extract_from_video.sh /mnt/hgfs/Downloads/Drone/SourceCopies/DJI_0186.MP4 /mnt/hgfs/Downloads/Drone/Frames

./create_gcp.py "/mnt/hgfs/Downloads/Drone/Frames/DJI_0185.MP4" \
        "/mnt/hgfs/Downloads/Drone/SourceCopies/DJIFlightRecord_2022-04-13_[15-20-46].csv"

./create_gcp.py "/mnt/hgfs/Downloads/Drone/Frames/DJI_0186.MP4" \
        "/mnt/hgfs/Downloads/Drone/SourceCopies/DJIFlightRecord_2022-04-13_[15-20-46].csv"
```
