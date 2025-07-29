from enums import StatusTextMessage
from status_text import sendStatusText
from pymavlink import mavutil
from log import log
from exposure_tuning import runExposureTuner
import globals


_prevServoValues: dict[int, float] = {}


def requestServoOutputRaw():
    if globals.master is None:
        raise RuntimeError("Cannot request message without mavlink connection.")

    message = globals.master.mav.command_long_encode(
        globals.master.target_system,  # Target system ID
        globals.master.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
        0,  # Confirmation
        # param1: Message ID to be streamed
        mavutil.mavlink.MAVLINK_MSG_ID_SERVO_OUTPUT_RAW,
        100000,  # param2: Interval in microseconds
        0,  # param3 (unused)
        0,  # param4 (unused)
        0,  # param5 (unused)
        0,  # param5 (unused)
        0,  # param6 (unused)
    )

    sendStatusText("Requesting SERVO_OUTPUT_RAW", StatusTextMessage.DEBUG)

    globals.master.mav.send(message)


def receivedServoOutputRaw(servoValues: dict) -> None:
    global _prevServoValues
    changedNumbers: list[int] = []

    for key in servoValues:
        if not isinstance(key, str):
            log(f"Invalid key type: {key} ({type(key)})")
            continue
        if not key.startswith("servo") or not key.endswith("_raw"):
            continue
        if not isinstance(servoValues[key], (int, float)):
            sendStatusText(
                f"Invalid servo value type for {key}: {type(servoValues[key])}",
                StatusTextMessage.DEBUG,
            )
            continue

        servoNumber = int(key.removeprefix("servo").removesuffix("_raw"))

        if servoNumber < 1 or servoNumber > 16:
            sendStatusText(
                f"Invalid servo number: {servoNumber}", StatusTextMessage.DEBUG
            )
            continue

        if (
            _prevServoValues.get(servoNumber) is not None
            and _prevServoValues[servoNumber] != servoValues[key]
        ):
            changedNumbers.append(servoNumber)

        _prevServoValues[servoNumber] = servoValues[key]

    for servoNumber in changedNumbers:
        match servoNumber:
            case globals.EXPOSURE_TUNING_SERVO_PORT:
                sendStatusText(
                    f"Exposure tuning toggling, new servo: {servoValues[f'servo{servoNumber}_raw']}",
                    StatusTextMessage.DEBUG,
                )
                runExposureTuner()
            case globals.PRECISION_LANDING_SERVO_PORT:
                sendStatusText(
                    "Precision landing toggling, disabled",
                    StatusTextMessage.DEBUG,
                )
                pass
            # case _:
            #     sendStatusText(
            #         f"Unknown Servo Port: {servoNumber} at {servoValues[f'servo{servoNumber}_raw']}",
            #         StatusTextMessage.DEBUG,
            #     )
