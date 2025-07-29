from enum import Enum
from dataclasses import dataclass
from typing import TypeAlias

class QRCodeType(Enum):
    """
    Enum representing different types of QR codes.
    """

    BALL_HAMMMER_PICKUP = 1
    CLAW_HAMMER_PICKUP = 2
    DROPOFF = 3
    TOWER = 4
    TOWER_HAMMER_BALL = 5
    TOWER_HAMMER_CLAW = 6
    HAT_DROPOFF = 7

    def __str__(self) -> str:
        match self:
            case QRCodeType.BALL_HAMMMER_PICKUP:
                return "Ball Hammer Pickup"
            case QRCodeType.CLAW_HAMMER_PICKUP:
                return "Claw Hammer Pickup"
            case QRCodeType.DROPOFF:
                return "Dropoff"
            case QRCodeType.TOWER:
                return "Tower"
            case QRCodeType.TOWER_HAMMER_BALL:
                return "Tower Hammer Ball"
            case QRCodeType.TOWER_HAMMER_CLAW:
                return "Tower Hammer Claw"
            case QRCodeType.HAT_DROPOFF:
                return "Hat Dropoff"
            case _:
                return "Unknown QR Code Type"

@dataclass
class StatusTextDebug:
    comment: str

@dataclass
class StatusTextEndOfPrecisionDescent:
    comment: str

@dataclass
class StatusTextQrCodeDetected:
    comment: str

@dataclass
class StatusTextQrCodeValue:
    qr_code: QRCodeType
    comment: str

@dataclass
class WaypointCompleted:
    waypoint_num: int

StatusTextMessage: TypeAlias = StatusTextDebug | StatusTextEndOfPrecisionDescent | \
    StatusTextQrCodeDetected | StatusTextQrCodeValue | WaypointCompleted | None

def parse(input: str) -> StatusTextMessage:
    try:
        message_type = int(input[0])
        if message_type == 0:
            return StatusTextDebug(comment=input[1:])
        elif message_type == 1:
            return StatusTextEndOfPrecisionDescent(comment=input[1:])
        elif message_type == 2:
            return StatusTextQrCodeDetected(comment=input[1:])
        elif message_type == 3:
            if "Unknown" in input[2:]:
                return None
            else:
                return StatusTextQrCodeValue(qr_code=QRCodeType(int(input[1])), comment=input[2:])
    except Exception:
        ...
    return None