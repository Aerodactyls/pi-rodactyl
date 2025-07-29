from enums import StatusTextMessage, QRCodeType
from status_text import sendStatusText
from log import log
import videos
from pyzbar import pyzbar
from typing import Optional, Any
import globals


def strToQRCodeType(originalStr: str) -> Optional[QRCodeType]:
    string = originalStr.replace("https://", "")
    string = string.replace("amablog.modelaircraft.org/uas4stem/", "")
    match string:
        case "BALLPEEN-HAMMER":
            return QRCodeType.BALL_HAMMMER_PICKUP
        case "CLAW-HAMMER":
            return QRCodeType.CLAW_HAMMER_PICKUP
        case "i.sstatic.net/dHrQl.jpg":
            return QRCodeType.DROPOFF
        case "TOWER":
            return QRCodeType.TOWER
        case "BENT-METAL-BALLPEEN":
            return QRCodeType.TOWER_HAMMER_BALL
        case "BENT-NAIL-CLAW":
            return QRCodeType.TOWER_HAMMER_CLAW
        case "MOVING-TARGET":
            return QRCodeType.HAT_DROPOFF
        case _:
            log(f"Unknown QR Code, sent out HAT_DROPOFF, qr was {string}")
            sendStatusText(f"Unknown QR Code: {string}", StatusTextMessage.DEBUG)
            return QRCodeType.HAT_DROPOFF


def checkQrCodes() -> None:
    videos.checkVideo()
    globals.scheduler.add_job(_reportQrCodes, "interval", seconds=0.25)


def _reportQrCodes() -> None:
    if globals.exposureFrameRunning or globals.precisionLandingRunning:
        return

    qrCodeList = _processFrame()
    if qrCodeList is None:
        return
    if len(qrCodeList) == 0:
        sendStatusText("Detected QR Code", StatusTextMessage.QR_CODE_DETECTED)

    for qrCode in qrCodeList:
        sendStatusText(
            f"QR Code: {qrCode}",
            StatusTextMessage.QR_CODE_VALUE,
            strToQRCodeType(str(qrCode)),
        )


def _detectQrCodes(frame: Any) -> Optional[list[str]]:
    qrCodes = pyzbar.decode(frame)
    if len(qrCodes) == 0:
        return None
    qrCodeList: list[str] = []
    for qrCode in qrCodes:
        qrCodeList.append(qrCode.data.decode("utf-8"))
    return qrCodeList


def _processFrame() -> Optional[list[str]]:
    if globals.device is None:
        raise RuntimeError("Cannot process frame, create device first.")

    # sendStatusText("QR Code", StatusTextMessage.DEBUG)

    qRgb: Any = globals.device.getOutputQueue("rgb", maxSize=1, blocking=False)  # type: ignore
    frame = None
    in_rgb = qRgb.tryGet()
    if in_rgb is not None:
        frame = in_rgb.getCvFrame()

    qrCodes: Optional[list[str]] = None
    if frame is not None:
        qrCodes = _detectQrCodes(frame)
        if videos.video is not None:
            videos.video.write(frame)
    return qrCodes
