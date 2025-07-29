from enum import Enum


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


class StatusTextMessage(Enum):
    """
    Enum representing different status text messages.
    """

    DEBUG = 0
    END_OF_PRECISION_DESCENT = 1
    QR_CODE_DETECTED = 2
    QR_CODE_VALUE = 3

    def __str__(self) -> str:
        match self:
            case StatusTextMessage.DEBUG:
                return "Debug message"
            case StatusTextMessage.END_OF_PRECISION_DESCENT:
                return "Precision descent ended"
            case StatusTextMessage.QR_CODE_DETECTED:
                return "QR Code detected"
            case StatusTextMessage.QR_CODE_VALUE:
                return "QR Code value"
            case _:
                return "Unknown QR Code Type"
