"""Command line tool to interact with Vicon Autographer wearable camera."""

import argparse
from datetime import datetime
import fnmatch
import glob
import os
import re
import shutil
import sys
from tqdm import tqdm


def main():
    """
    Application entry point responsible for parsing command line requests
    """

    parser = argparse.ArgumentParser(
        description="""Setup Vicon Autographer cameras for data collection \n
                Also download data from camera.""",
        add_help=False,
    )

    # required args
    parser.add_argument(
        "--cameraDir",
        type=str,
        help="path with root of camera dir",
        default="/Volumes/Autographer/",
    )
    parser.add_argument(
        "--destDir",
        type=str,
        help="destination path to copy camera data to",
        default="camera/test/",
    )
    parser.add_argument(
        "--setTime",
        metavar="True/False",
        default=False,
        type=str2bool,
        help="""Setup device with correct time \n
                Call this function immediately after camera is plugged in.""",
    )
    parser.add_argument(
        "--download",
        metavar="True/False",
        default=False,
        type=str2bool,
        help="Download data from device to destination directory",
    )
    parser.add_argument(
        "--delete",
        metavar="True/False",
        default=False,
        type=str2bool,
        help="Delete all of participant's data from camera",
    )
    # parse arguments
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(-1)
    args = parser.parse_args()

    if not args.destDir.endswith("/"):
        args.destDir = args.destDir + "/"

    if args.download is True:
        downloadData(args.cameraDir, args.destDir)

    if args.setTime is True:
        setCameraTime(args.cameraDir)

    if args.delete is True:
        deleteCameraData(args.cameraDir)


def downloadData(cameraDir, participantDir):
    """Download participant data from camera to disk

    Image files and sensor files copied from device to local drive

    :param str cameraDir: Input path to root dir of camera
    :param str cameraDir: Output path to store study data for participant

    :return: Camera data copied to <participantDir>
    :rtype: void
    """

    def append_paths(img_list, filenames, root):
        for filename in fnmatch.filter(filenames, "*.JPG"):
            img_list.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "*.RES"):
            img_list.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "*.txt"):
            img_list.append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, "*.CSV"):
            img_list.append(os.path.join(root, filename))

    for folder in glob.glob(cameraDir + "DATA/"):
        images = []
        small_images = []
        for root, dirnames, filenames in os.walk(folder):
            if root.endswith("256_192"):
                pass
            elif root.endswith("640_480"):
                append_paths(small_images, filenames, root)
            else:
                append_paths(images, filenames, root)

        if not os.path.exists(participantDir):
            os.makedirs(participantDir)
            os.makedirs(participantDir + "small/")

        # copy images to <participantDir> and display tqdm() progress bar
        def copy_images(images, dir):
            for image in tqdm(images):
                newImg = dir + image.replace("\\", "//").split("/")[-1]
                newImg = newImg.replace(".RES", ".JPG")
                shutil.copyfile(image, newImg)

        copy_images(images, participantDir)
        copy_images(small_images, participantDir + "small/")

        print(
            "copy of", len(images), "data items to", participantDir, "is now complete"
        )


def deleteCameraData(cameraDir):
    """Wipe particiapnt's data from camera

    Delete all of participant's data from camera

    :param str cameraDir: Input path to root dir of camera

    :return: Participant's data wiped from camera
    :rtype: void
    """

    # delete data from camera
    shutil.rmtree(cameraDir + "DATA/")
    shutil.rmtree(cameraDir + "LOGS/")

    print("Camera data has now been deleted.")


def setCameraTime(cameraDir):
    """Set time correction on camera

    Write clock_correction.txt on camera with the difference in seconds between
    the camera time and the computer time. The correction is applied when the
    camera is disconnected from the computer usb port. The file will subsequently
    be deleted. Calculating the camera time is possible but non trivial. We can
    read the camera time from autographer.inf but this is a static value that
    is written when the camera is connected to the usb. If we can determine the
    (computer) time when the camera was connected then we can calculate the
    current camera time. If this can't be found, go with the present time

    :param str cameraDir: Input path to root dir of camera

    :return: clock_correction.txt written to camera
    :rtype: void
    """

    # get computer time estimate for when camera was plugged in
    computerTime = datetime.now()
    # todo - read system logs to identify device plug-in time
    # e.g. for OSX ... $ grep "New disk" /var/log/system.log | tail -1

    # get camera time estimate for when camera was plugged in
    cameraTime = datetime.now()
    try:
        for line in open(cameraDir + "autographer.inf"):
            if "Time=" in line:
                timePart = line.split("=")[-1]
                cameraTime = datetime.strptime(timePart[0:19], "%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        print(str(e), "could not read camera timestamp file")

    # write difference (in seconds) between computer and camera time
    secondDiff = (computerTime - cameraTime).total_seconds()
    w = open(cameraDir + "clock_correction.txt", "w")
    w.write(str(int(secondDiff)))
    w.close()

    print("Camera clock now synced to PC time.")


def str2bool(v):
    """
    Used to parse true/false values from the command line. E.g. "True" -> True
    """
    return v.lower() in ("yes", "true", "t", "1")


if __name__ == "__main__":
    main()  # Standard boilerplate to call the main() function to begin the program.
