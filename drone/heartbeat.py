from enums import StatusTextMessage
import globals
from status_text import sendStatusText
import time

_lastHeartbeatTime: float = time.time()


def setupHeartbeatChecker() -> None:
    # schedule.every().second.do(_printHeartbeatStatus)
    globals.scheduler.add_job(_printHeartbeatStatus, "interval", seconds=5)


def receivedHeartbeat() -> None:
    global _lastHeartbeatTime
    _lastHeartbeatTime = time.time()
    if globals.master is None:
        raise RuntimeError("Cannot have recived heartbeat without master")
    globals.isArmed = globals.master.motors_armed()


def _printHeartbeatStatus() -> None:
    global lastHeartbeatPrintTime, _lastHeartbeatTime
    if globals.heartbeatFailed:
        return

    currentTime: float = time.time()

    if _lastHeartbeatTime - currentTime > globals.HEARTBEAT_TIMEOUT:
        globals.heartbeatFailed = True
        sendStatusText("Heartbeat Failed, error", StatusTextMessage.DEBUG)
        return

    sendStatusText("Heartbeat", StatusTextMessage.DEBUG)
