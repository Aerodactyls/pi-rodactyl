from enums import StatusTextMessage
from mav_connection import createMavConnection, MavConnectionClass
from heartbeat import receivedHeartbeat, setupHeartbeatChecker
from pipeline import createPipeline
from exposure_tuning import setupExposureTuningFromFile
from qr_codes import checkQrCodes
from status_text import sendStatusText
from data import loadOrCreateData
from servo_ports import requestServoOutputRaw, receivedServoOutputRaw
from log import log
import globals
from typing import Any
import time
import depthai
import signal
import sys
from pymavlink import mavutil

connectionString: str = "/dev/ttyS0"
createMavConnection(
    connectionString,
    MavConnectionClass(500000, 191, 1),
)

if globals.master is None:
    raise RuntimeError("Failed to create MAVLink connection.")  # unreachable

createPipeline()

if globals.pipeline is None:
    raise RuntimeError("Failed to create DepthAI pipeline.")

log("Waiting for first heartbeat")
globals.master.wait_heartbeat()
log("First heartbeat received")

sendStatusText("First Heartbeat Status Message", StatusTextMessage.DEBUG)
sendStatusText("Created Pipeline & Mavlink Connection", StatusTextMessage.DEBUG)

loadOrCreateData()

ok = True


def signalHandling(_sig, _frame):
    global ok
    sendStatusText("Ctrl+C received, shutting down", StatusTextMessage.DEBUG)
    ok = False


signal.signal(signal.SIGINT, signalHandling)

with depthai.Device(globals.pipeline) as d:
    globals.device = d
    sendStatusText("DepthAI device created", StatusTextMessage.DEBUG)

    globals.controlQueue = globals.device.getInputQueue("control", maxSize=60)  # type: ignore

    ctrl = depthai.CameraControl()
    ctrl.setAutoExposureLock(True)
    globals.controlQueue.send(ctrl)

    setupExposureTuningFromFile()

    setupHeartbeatChecker()
    requestServoOutputRaw()
    checkQrCodes()

    globals.scheduler.start()
    while ok:
        if globals.heartbeatFailed:
            sendStatusText("Exiting due to failed heartbeat", StatusTextMessage.DEBUG)
            break

        message: Any = globals.master.recv_match(blocking=False)

        while message is not None and ok:
            match message.get_type():
                case "HEARTBEAT":
                    # if message.type == 2:
                    if message.type == mavutil.mavlink.MAV_TYPE_QUADROTOR:
                        receivedHeartbeat()
                case "SERVO_OUTPUT_RAW":
                    receivedServoOutputRaw(message.to_dict())

            message = globals.master.recv_match(blocking=False)
        time.sleep(0.01)
    sendStatusText("Shutting down", StatusTextMessage.DEBUG)
    globals.scheduler.shutdown()

sendStatusText("Exiting", StatusTextMessage.DEBUG)
time.sleep(1)
sys.exit(0)
