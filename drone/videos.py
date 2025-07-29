from log import log, getFullFormattedCurrentTime
from typing import Optional
import cv2
import globals
from status_text import sendStatusText, StatusTextMessage

video: Optional[cv2.VideoWriter] = None


def checkVideo():
    # globals.scheduler.add_job(_createVideo, "interval", seconds=0.1)
    _createVideo()


def _createVideo() -> None:
    global video
    if globals.master is None:
        log("No MAVLink connection, cannot create video")
        return

    motorsArmed = globals.isArmed
    videoRunning = video is not None

    if videoRunning:
        if not motorsArmed:
            video.release()  # type: ignore
            video = None
            sendStatusText("Video stopped", StatusTextMessage.DEBUG)
        return

    if not motorsArmed:
        return

    fourcc = cv2.VideoWriter_fourcc(*"XVID")  # type: ignore

    video = cv2.VideoWriter(
        f"{globals.WORKING_DIRECTORY}/videos/{getFullFormattedCurrentTime()}.avi",
        fourcc,  # type: ignore
        4.0,
        (globals.VIDEO_RESOLUTION, globals.VIDEO_RESOLUTION),
    )

    sendStatusText("Video started", StatusTextMessage.DEBUG)
