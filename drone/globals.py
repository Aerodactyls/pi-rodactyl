import depthai
from typing import Optional
from pymavlink import mavutil
from apscheduler.schedulers.background import BackgroundScheduler

pipeline: Optional[depthai.Pipeline] = None
controlQueue: Optional[depthai.DataInputQueue] = None
device: Optional[depthai.Device] = None
master: Optional[mavutil.mavfile] = None
isArmed: bool = False
heartbeatFailed: bool = False
scheduler = BackgroundScheduler()

exposureFrameRunning: bool = False
precisionLandingRunning: bool = False


WORKING_DIRECTORY: str = "/home/pi/pi-rodactyl/drone"
# WORKING_DIRECTORY: str = "./"

HEARTBEAT_TIMEOUT: float = 5
EXPOSURE_TUNING_SERVO_PORT: int = 8
VIDEO_RESOLUTION: int = 1000

Data = dict[str, int]

EXPOSURE_TUNING_TIME: str = "exposureTuningTime"
EXPOSURE_TUNING_ISO: str = "exposureTuningIso"
DATA_FILE: str = f"{WORKING_DIRECTORY}/data.json"
DEFAULT_VALUE: int = -1

DEFAULT_CONFIG: Data = {
    EXPOSURE_TUNING_TIME: DEFAULT_VALUE,
    EXPOSURE_TUNING_ISO: DEFAULT_VALUE,
}

PRECISION_LANDING_SERVO_PORT: int = 14
