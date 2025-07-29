from typing import Optional
from enums import StatusTextMessage, QRCodeType
from log import log
import globals
from pymavlink import mavutil


def sendStatusText(
    comment: str, statusType: StatusTextMessage, qrCodeType: Optional[QRCodeType] = None
) -> None:
    message = _createStatusText(comment, statusType, qrCodeType)
    if globals.master is None:
        log(f"Need mavlink connection to send Status Text: {message}")
        return

    log(f"Sent status text message: {message}")
    globals.master.mav.statustext_send(
        mavutil.mavlink.MAV_SEVERITY_INFO,
        message.encode("utf-8"),
    )


def _createStatusText(
    comment: str, statusType: StatusTextMessage, qrCodeType: Optional[QRCodeType]
) -> str:
    message = f"~~{statusType.value}"

    if statusType is StatusTextMessage.QR_CODE_VALUE:
        if qrCodeType is None:
            raise RuntimeError("Need to pass QR Code type with QR_CODE_VALUE")
        message += f" {qrCodeType.value}"
        comment = comment.replace("https://amablog.modelaircraft.org/uas4stem/", "")
    message += f" {comment}"
    if len(message) > 50:
        log("Status text message cut off, greater than 50 characters")
    return message[:50]
