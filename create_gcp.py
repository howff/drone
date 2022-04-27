#!/usr/bin/env python3
#
# Usage: DJI_nnnn.MP4 DJIFlightRecord_xxx.csv
#   where the MP4 is straight from the drone
#   and the CSV file has been converted from the txt file save by the app
#   using the phantomhelp.com/LogViewer website.
#   You should already have extracted frames from the video at 1 second
#   intervals into the same directory as the MP4 with _nnnn.png filenames.
# Output will write to gcp_list.txt or append if it already exists
# so you can process each video segment from a single flight in turn.
# NB. Assumes the camera is pointing at the nadir i.e. directly down.

# Requirements:
#  python-dateutil
#  ffprobe external command (as installed with ffmpeg)


import bisect
import csv
import datetime
import dateutil.parser
import json
import logging
from math import cos, tan, radians, sqrt
import os
import png
import pprint
import re
import subprocess
import sys

# Variables
mp4_filename = '/mnt/hgfs/Downloads/Drone/Frames/DJI_0185.MP4'
csv_filename = '/mnt/hgfs/Downloads/Drone/SourceCopies/DJIFlightRecord_2022-04-13_[15-20-46].csv'

# Constants
projection = 'EPSG:4326'
FOV_ACROSS = 70 # DJI Mini 2
FOV_ALONG  = 55 # DJI Mini 2
earth_rad_m = 6371000.0


def err(msg):
    logging.error(msg)
    exit(1)


def png_filename_from_mp4_filename(mp4file, seconds):
    """ Deduce a PNG filename given a MP4 filename
    """
    return '%s_%04d.png' % (mp4file, seconds)


def find_png_filename(mp4file):
    """ Find an existing PNG file given a MP4 filename
    """
    for seconds in range(300):
        png_filename = png_filename_from_mp4_filename(mp4file, seconds)
        if os.path.isfile(png_filename):
            return png_filename
    return None


def png_dimensions(png_filename):
    """ Extract the width and height from a PNG file
    """
    pngreader = png.Reader(filename=png_filename)
    (width, height, pngiter, pngmeta) = pngreader.read()
    return width, height


def mp4_creation_time(mp4_filename):
    """ Extract the creation_time from a MP4 video file
    """
    cmd = "ffprobe -v quiet -print_format json -show_format -show_streams -print_format json"

    res = subprocess.run(cmd.split(' ') + [mp4_filename], capture_output=True, text=True)
    res_dict = json.loads((res.stdout))
    # 'creation_time': '2022-04-13T14:20:52.000000Z',
    creation_time = res_dict['format']['tags']['creation_time']
    datetime = dateutil.parser.parse(creation_time)
    return datetime


def read_gpx(gpx_filename):
    """ Read a GPX file
    """
    with open(gpx_filename) as gpx_fd:
        gpx = gpxpy.parse(gpx_fd)

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    print('Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation))


def read_srt(srt_filename):
    """ Read the SRT subtitle file extracted by ffmpeg from a DJI drone video
    """
    with open(srt_filename) as srtreader:
        for srtline in srtreader:
            if '-->' in srtline:
                seconds = int(re.split(':|,', srtline)[1])*60 + int(re.split(':|,', srtline)[2])
            if 'GPS' in srtline:
                m = re.split(' |\)|\(|,|m/s|m|/', srtline)
                lon = float(m[m.index('GPS')+2])
                lat = float(m[m.index('GPS')+4])
                dist_from_home = float(m[m.index('D')+1])
                altitude = float(m[m.index('H')+1])


def field_of_view(altitude):
    """ Return the FOV field of view for a given altitude
    assuming a sensor having angle (degrees) FOV_ACROSS x FOV_ALONG
    """
    fov_w = altitude * tan(radians(FOV_ACROSS/2.0))*2.0
    fov_h = altitude * tan(radians(FOV_ALONG/2.0))*2.0
    return fov_w, fov_h


def index_of_nearest(mylist, findme):
    idx = bisect.bisect_left(mylist, findme)
    if idx == len(mylist): idx -= 1
    if mylist[idx] == findme:
        return idx
    if idx == 0: idx = 1
    before = mylist[idx-1]
    after = mylist[idx]
    return idx if (findme - before) > (after - findme) else idx-1


def read_csv(csv_filename):
    # sep=,
    # CUSTOM.date [local], CUSTOM.updateTime [local], OSD.flyTime, OSD.flyTime [s], OSD.latitude, OSD.longitude, OSD.height [ft], OSD.heightMax [ft], OSD.vpsHeight [ft], OSD.altitude [ft], OSD.hSpeed [MPH], OSD.hSpeedMax [MPH], OSD.xSpeed [MPH], OSD.xSpeedMax [MPH], OSD.ySpeed [MPH], OSD.ySpeedMax [MPH], OSD.zSpeed [MPH], OSD.zSpeedMax [MPH], OSD.pitch, OSD.roll, OSD.yaw, OSD.yaw [360], OSD.flycState, OSD.flycCommand, OSD.flightAction, OSD.gpsNum, OSD.gpsLevel, OSD.isGPSUsed, OSD.nonGPSCause, OSD.droneType, OSD.isSwaveWork, OSD.waveError, OSD.goHomeStatus, OSD.batteryType, OSD.ctrlDevice, OSD.isOnGround, OSD.isMotorOn, OSD.isMotorBlocked, OSD.motorStartFailedCause, OSD.motorFailReason, OSD.isImuPreheated, OSD.imuInitFailReason, OSD.isAcceletorOverRange, OSD.isBarometerDeadInAir, OSD.isCompassError, OSD.isGoHomeHeightModified, OSD.canIOCWork, OSD.isNotEnoughForce, OSD.isOutOfLimit, OSD.isPropellerCatapult, OSD.isVibrating, OSD.isVisionUsed, OSD.voltageWarning, GIMBAL.mode, GIMBAL.pitch, GIMBAL.roll, GIMBAL.yaw, GIMBAL.yaw [360], GIMBAL.isPitchAtLimit, GIMBAL.isRollAtLimit, GIMBAL.isYawAtLimit, GIMBAL.isStuck, CAMERA.isPhoto, CAMERA.isVideo, CAMERA.filename, CAMERA.sdCardIsInserted, CAMERA.sdCardState, RC.downlinkSignal, RC.uplinkSignal, RC.aileron, RC.elevator, RC.throttle, RC.rudder, RC.mode, RC.goHomeDepressed, RC.recordDepressed, RC.shutterDepressed, RC.playbackDepressed, RC.wheelDepressed, RC.wheelOffset, RC.custom1Depressed, RC.custom2Depressed, RC.custom3Depressed, RC.custom4Depressed, BATTERY.chargeLevel, BATTERY.currentPV [V], BATTERY.currentCapacity [mAh], BATTERY.fullCapacity [mAh], BATTERY.voltage [V], BATTERY.isCellVoltageEstimated, BATTERY.cellVoltage1 [V], BATTERY.cellVoltage2 [V], BATTERY.maxCellVoltageDeviation, BATTERY.isCellVoltageDeviationHigh, BATTERY.isVoltageLow, BATTERY.current [A], BATTERY.temperature [F], BATTERY.minTemperature [F], BATTERY.maxTemperature [F], BATTERY.usefulTime [s], BATTERY.goHomeTime [s], BATTERY.landTime [s], BATTERY.goHomeBattery, BATTERY.landBattery, BATTERY.safeFlyRadius, BATTERY.volumeConsume, BATTERY.status, BATTERY.goHomeStatus, BATTERY.goHomeCountdown, BATTERY.lowWarning, BATTERY.lowWarningGoHome, BATTERY.seriousLowWarning, BATTERY.seriousLowWarningLanding, BATTERY.timesCharged, MC.failSafeAction, HOME.latitude, HOME.longitude, HOME.distance [ft], HOME.height [ft], HOME.heightLimit [ft], HOME.isHomeRecord, HOME.goHomeMode, HOME.aircraftHeadDirection, HOME.isDynamicHomePointEnabled, HOME.isReachedLimitDistance, HOME.isReachedLimitHeight, HOME.isCompassCeleing, HOME.compassCeleStatus, HOME.isMultipleFlightModeEnabled, HOME.isBeginnerMode, HOME.isIOCEnabled, HOME.iocMode, HOME.goHomeHeight [ft], HOME.courseLockAngle, HOME.forceLandingHeight [ft], HOME.wind, HOME.dataRecorderFileIndex, RECOVER.appType, RECOVER.appVersion, RECOVER.aircraftName, RECOVER.aircraftSerial, RECOVER.cameraSerial, RECOVER.rcSerial, RECOVER.batterySerial, DETAILS.totalTime [s], DETAILS.totalDistance [ft], DETAILS.maxHeight [ft], DETAILS.maxHorizontalSpeed [MPH], DETAILS.maxVerticalSpeed [MPH], DETAILS.photoNum, DETAILS.videoTime [s], DETAILS.aircraftName, DETAILS.aircraftSerial, DETAILS.cameraSerial, DETAILS.rcSerial, DETAILS.batterySerial, DETAILS.appName, DETAILS.appType, DETAILS.appVersion, APPGPS.latitude, APPGPS.longitude, APPGPS.accuracy, APP.message, APP.tip, APP.warning
    # 4/13/2022,2:22:59.45 PM,2m 12.7s,132.7,39.35072727,-7.39508646,220.8,331.4,42.0,2516,2.6,8.5,2.2,7.6,-1.3,7.2,0.5,6.7,-17.2,3,-30.6,329.4,P-GPS,Auto Fly,,18,5,True,,Mini 2,False,False,,Smart,RC,False,True,False,,,True,,False,False,False,False,False,False,False,False,False,False,0,Follow Yaw,-89.9,0,-26.9,333.1,False,False,False,False,False,True,,True,Normal,100,100,1030,1684,1024,1024,0,False,False,False,False,False,0,False,False,False,False,92,8.094,1762,1931,8.083,False,4.036,4.029,0.033,False,False,3.871,84.6,75.4,84.6,1331,6,22,13,7,19052.5,4763.13,,Idle,0,20,False,10,True,,Go Home,39.35035968,-7.39522179,139.4,2290.8,393.7,True,1,1,False,False,False,False,0,True,False,False,Course Lock,164.0,,16.4,Moderate,7,, 1.5.4,DJI Mini 2 arb,3NZCHBG003A2NS,1SFLHAK0AB0AR8,396CHC10019VLT,3QFPHBSCA50Q3U,927.3,9.7,331.4,24.1,6.9,0,636186,DJI Mini 2 arb,3NZCHBG003A2NS,1SFLHAK0AB0AR8,396CHC10019VLT,3QFPHBSCA50Q3U,DJI Fly,, 1.5.4,,,,,,
    # 4/13/2022,2:22:59.55 PM,2m 12.8s,132.8,39.35072843,-7.39508729,220.8,331.4,42.0,2516,3.0,8.5,2.5,7.6,-1.6,7.2,0.5,6.7,-16.3,3,-30.3,329.7,P-GPS,Auto Fly,,18,5,True,,Mini 2,False,False,,Smart,RC,False,True,False,,,True,,False,False,False,False,False,False,False,False,False,False,0,Follow Yaw,-90,0,-26.9,333.1,False,False,False,False,False,True,,True,Normal,100,100,1030,1684,1024,1024,0,False,False,False,False,False,0,False,False,False,False,92,8.094,1762,1931,8.065,False,4.036,4.029,0.033,False,False,3.871,84.6,75.4,84.6,1331,6,22,13,7,19052.5,4763.13,,Idle,0,20,False,10,True,,Go Home,39.35035968,-7.39522179,139.8,2290.8,393.7,True,1,1,False,False,False,False,0,True,False,False,Course Lock,164.0,,16.4,Moderate,7,, 1.5.4,DJI Mini 2 arb,3NZCHBG003A2NS,1SFLHAK0AB0AR8,396CHC10019VLT,3QFPHBSCA50Q3U,927.3,9.7,331.4,24.1,6.9,0,636186,DJI Mini 2 arb,3NZCHBG003A2NS,1SFLHAK0AB0AR8,396CHC10019VLT,3QFPHBSCA50Q3U,DJI Fly,, 1.5.4,,,,,,
    # 4/13/2022,2:22:59.65 PM,2m 12.9s,132.9,39.35072959,-7.39508814,220.8,331.4,42.0,2516,3.2,8.5,2.7,7.6,-1.6,7.2,0.5,6.7,-16.5,2.6,-30.3,329.7,P-GPS,Auto Fly,,18,5,True,,Mini 2,False,False,,Smart,RC,False,True,False,,,True,,False,False,False,False,False,False,False,False,False,False,0,Follow Yaw,-90,0,-26.9,333.1,False,False,False,False,False,True,,True,Normal,100,100,1031,1684,1024,1024,0,False,False,False,False,False,0,False,False,False,False,92,8.094,1762,1931,8.065,False,4.036,4.029,0.033,False,False,3.871,84.6,75.4,84.6,1331,6,22,13,7,19052.5,4763.13,,Idle,0,20,False,10,True,,Go Home,39.35035968,-7.39522179,140.1,2290.8,393.7,True,1,1,False,False,False,False,0,True,False,False,Course Lock,164.0,,16.4,Moderate,7,, 1.5.4,DJI Mini 2 arb,3NZCHBG003A2NS,1SFLHAK0AB0AR8,396CHC10019VLT,3QFPHBSCA50Q3U,927.3,9.7,331.4,24.1,6.9,0,636186,DJI Mini 2 arb,3NZCHBG003A2NS,1SFLHAK0AB0AR8,396CHC10019VLT,3QFPHBSCA50Q3U,DJI Fly,, 1.5.4,,,,,,

    global csv_time, csv_lat, csv_lon, csv_height

    csv_time = []
    csv_lat = []
    csv_lon = []
    csv_height = []
    fd = open(csv_filename)
    fd.readline() # ignore sep=,
    rdr = csv.DictReader(fd) #, skipinitialspace=True)
    for row in rdr:
        datestr = row['CUSTOM.date [local]']          # NB no leading space in name
        timestr = row[' CUSTOM.updateTime [local]']   # NB leading space in name
        flightsecs = float(row[' OSD.flyTime [s]'])
        lat = float(row[' OSD.latitude'])
        lon = float(row[' OSD.longitude'])
        height = float(row[' OSD.height [ft]']) * 0.3048 # convert to m
        #print('time %s flytime %s flytimeS %s lat %s lon %s ft %s' % (timestr, row[' OSD.flyTime'], flightsecs, lat, lon, height))
        #print('  PRY = %s %s %s / %s %s %s' % (
        #    row[' OSD.pitch'],row[' OSD.roll'],row[' OSD.yaw'],row[' GIMBAL.pitch'],row[' GIMBAL.roll'],row[' GIMBAL.yaw']      ))
        # Extract the parts of the date and time
        H,M,S,AMPM = re.split(':| ', timestr)
        if AMPM=='PM':
            H=str(int(H)+12)
        MM,DD,YY = datestr.split('/')
        # Convert to a datetime, but this cannot handle fractional seconds
        dd = dateutil.parser.parse('%d/%02d/%02dT%02d:%02d:%02d+00:00' %
            (int(YY), int(MM), int(DD), int(H), int(M), float(S)))
        # Add on the fractions of a second
        dd += datetime.timedelta(microseconds = 1000000*(float(S)-int(float(S))))
        #print(dd.strftime("%Y-%m-%d %H:%M:%S.%f").rstrip('0'))
        csv_time.append(dd)
        csv_lat.append(lat)
        csv_lon.append(lon)
        csv_height.append(height)
    # Now test finding the nearest to a given time
    #time_to_find = '2022-04-13 02:34:45.831+00:00'
    #findtime = dateutil.parser.parse(time_to_find)
    #print('%d' % index_of_nearest(csv_time, findtime))


def gcp_header():
    """ Create a gcp file and write the header.
    This is just a fixed latlon projection line.
    If file already exists then return without doing anything.
    """
    if os.path.isfile(gcp_filename):
        return
    with open(gcp_filename, 'w') as fd:
        print(projection, file=fd)
    logging.info('Created %s' % gcp_filename)


def gcp_append(png_filename, lat, lon, height, x, y):
    """ Append the given coordinate to the gcp file.
    Create the file with a header if it doesn't exist.
    """
    gcp_header()
    with open(gcp_filename, 'a') as fd:
        print('%f %f %f %d %d %s' % (
            lon, lat, height, x, y, os.path.basename(png_filename)),
            file=fd)


if __name__ == '__main__':

    logging.basicConfig(level = logging.INFO)
    if len(sys.argv) > 1:
        mp4_filename = sys.argv[1]
    if len(sys.argv) > 2:
        csv_filename = sys.argv[2]
    gcp_filename = os.path.join(os.path.dirname(mp4_filename), 'gcp_list.txt')

    # 1. Find a PNG file and get its dimensions, used later to calculate FOV
    png_filename = find_png_filename(mp4_filename)
    if not png_filename:
        err('Cannot find a PNG file to go with %s' % mp4_filename)
    png_width, png_height = png_dimensions(png_filename)
    logging.info('PNG is %d x %d' % (png_width, png_height))

    # 2. Read all the records in the CSV file
    read_csv(csv_filename)

    # 3. Read the MP4 video to get the creation time
    start_time = mp4_creation_time(mp4_filename)
    logging.info('Movie starts at %s' % start_time)
    logging.info('CSV starts at   %s' % csv_time[0])

    # 4. For each image
    #      calculate the time of that image from the mp4 creation time + frame num
    #      find closest time in the CSV/GPX file
    #      calculate distance from previous point
    #      compare to the field of view at that altitude (and gimbal yaw etc)
    #      if we've moved by > 0.3 * FOV then keep image, write to gcp_list
    prev_lat = 0
    prev_lon = 0
    for sec in range(1, 9999):
        png_filename = png_filename_from_mp4_filename(mp4_filename, sec)
        if not os.path.isfile(png_filename):
            break
        image_time = start_time + datetime.timedelta(seconds = sec)
        csv_idx = index_of_nearest(csv_time, image_time)
        lat = csv_lat[csv_idx]
        lon = csv_lon[csv_idx]
        height = csv_height[csv_idx]
        fov_width, fov_height = field_of_view(height)
        x = (radians(lon) - radians(prev_lon)) * cos((radians(lat)+radians(prev_lat))/2)
        y = (radians(lat) - radians(prev_lat))
        simple_dist_diff = sqrt(x*x + y*y) * earth_rad_m;
        if simple_dist_diff > 0.3 * fov_width:
            logging.info('keep %s' % png_filename)
            gcp_append(png_filename, lat, lon, height, png_width/2, png_height/2)
            prev_lat = lat
            prev_lon = lon

