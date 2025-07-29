from enums import StatusTextMessage
from status_text import sendStatusText
from data import (
    setExposureTuningIsoData,
    setExposureTuningTimeData,
    getExposureTuningIsoData,
    getExposureTuningTimeData,
)
from typing import Any
from log import log
import depthai
import globals

_exposureTunerLock: bool = True


def runExposureTuner() -> None:
    global _exposureTunerLock

    if globals.device is None:
        sendStatusText(
            "Camera failure, cannot run exposure tuner. exit",
            StatusTextMessage.DEBUG,
        )
        raise RuntimeError("No DepthAI device available. Cannot run exposure tuner.")

    _exposureTunerLock = not _exposureTunerLock

    sendStatusText(f"Exposure lock: {_exposureTunerLock}", StatusTextMessage.DEBUG)

    ctrl = depthai.CameraControl()
    ctrl.setAutoExposureLock(_exposureTunerLock)

    if not _exposureTunerLock:
        ctrl.setAutoExposureEnable()

    if globals.controlQueue is None:
        raise RuntimeError("No control queue available. Cannot run exposure tuner.")

    globals.controlQueue.send(ctrl)

    if _exposureTunerLock:
        _storeExposureTuningData()


def _storeExposureTuningData() -> None:
    globals.scheduler.add_job(_saveExposureTuningData)


def _saveExposureTuningData() -> None:
    globals.exposureFrameRunning = True
    sendStatusText(
        "Fetching RGB frame for exposure tuning data", StatusTextMessage.DEBUG
    )

    qRgb: Any = globals.device.getOutputQueue("rgb", maxSize=1, blocking=True)  # type: ignore
    in_rgb = qRgb.get()

    if in_rgb is not None:
        setExposureTuningIsoData(in_rgb.getSensitivity())
        setExposureTuningTimeData(in_rgb.getExposureTime().total_seconds() * 1e6)
    else:
        log(
            "Failed to get RGB frame for saving exposure tuning data",
        )
    globals.exposureFrameRunning = False


def setupExposureTuningFromFile() -> None:
    if getExposureTuningTimeData() >= 0 or getExposureTuningIsoData() >= 0:
        ctrl = depthai.CameraControl()
        ctrl.setManualExposure(
            int(getExposureTuningTimeData()), int(getExposureTuningIsoData())
        )
        if globals.controlQueue is None:
            raise RuntimeError("No control queue available. Cannot set exposure.")

        globals.controlQueue.send(ctrl)
        sendStatusText("Exposure set to file", StatusTextMessage.DEBUG)
        sendStatusText(f"Iso: {getExposureTuningIsoData()}", StatusTextMessage.DEBUG)
        sendStatusText(
            f"Timing: {getExposureTuningTimeData()}", StatusTextMessage.DEBUG
        )
    else:
        sendStatusText(
            "ET data not found, should auto exposure",
            StatusTextMessage.DEBUG,
        )
