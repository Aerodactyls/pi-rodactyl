import json
import os
from log import log
from typing import Optional
from status_text import sendStatusText, StatusTextMessage
import globals


_data: Optional[globals.Data] = None


def loadOrCreateData() -> None:
    global _data
    if os.path.exists(globals.DATA_FILE):
        try:
            with open(globals.DATA_FILE, "r") as f:
                loaded: globals.Data = json.load(f)
                if (
                    globals.EXPOSURE_TUNING_TIME not in loaded
                    or globals.EXPOSURE_TUNING_ISO not in loaded
                ):
                    sendStatusText(
                        "Config file missing keys, creating default config",
                        StatusTextMessage.DEBUG,
                    )
                else:
                    _data = loaded
                    sendStatusText(
                        "Config file loaded successfully.", StatusTextMessage.DEBUG
                    )
                    return
        except (json.JSONDecodeError, IOError) as e:
            log(f"Error reading config file: {e}")

    sendStatusText(
        f"Config file {globals.DATA_FILE} not found, creating default config.",
        StatusTextMessage.DEBUG,
    )
    _data = _createDefaultData()


def _createDefaultData() -> globals.Data:
    default: globals.Data = globals.DEFAULT_CONFIG.copy()
    _saveData(default)
    sendStatusText(
        "Config file not found. Created default config.", StatusTextMessage.DEBUG
    )
    return default


def _saveData(cfg: globals.Data) -> None:
    try:
        with open(globals.DATA_FILE, "w") as f:
            json.dump(cfg, f, indent=4)
    except IOError as e:
        sendStatusText(f"Error saving config file: {e}", StatusTextMessage.DEBUG)


def getExposureTuningTimeData() -> int:
    global _data
    if _data is None:
        sendStatusText(
            "Config doesnt exist. Call loadOrCreateConfig() first.",
            StatusTextMessage.DEBUG,
        )
        return globals.DEFAULT_VALUE

    return _data[globals.EXPOSURE_TUNING_TIME]


def setExposureTuningTimeData(value: int) -> None:
    global _data
    if _data is None:
        sendStatusText(
            "Config doesnt exist. Call loadOrCreateConfig() first.",
            StatusTextMessage.DEBUG,
        )
        return

    if _data[globals.EXPOSURE_TUNING_TIME] == value:
        sendStatusText("same data not changing time", StatusTextMessage.DEBUG)
        return

    _data[globals.EXPOSURE_TUNING_TIME] = int(value)
    _saveData(_data)
    sendStatusText(f"ET timing set to {value} in file", StatusTextMessage.DEBUG)


def getExposureTuningIsoData() -> int:
    global _data
    if _data is None:
        sendStatusText(
            "Config doesnt exist. Call loadOrCreateConfig() first.",
            StatusTextMessage.DEBUG,
        )
        return globals.DEFAULT_VALUE

    return _data[globals.EXPOSURE_TUNING_ISO]


def setExposureTuningIsoData(value: int) -> None:
    global _data
    if _data is None:
        sendStatusText(
            "Config doesnt exist. Call loadOrCreateConfig() first.",
            StatusTextMessage.DEBUG,
        )
        return

    if _data[globals.EXPOSURE_TUNING_ISO] == value:
        sendStatusText("same data not changing iso", StatusTextMessage.DEBUG)
        return

    _data[globals.EXPOSURE_TUNING_ISO] = value
    _saveData(_data)
    sendStatusText(f"ET iso set to {value} in file", StatusTextMessage.DEBUG)


# if __name__ == "__main__":
#     loadOrCreateConfig()
#
#     log(getConfigExposureTuningSensitivity())
#     setConfigExposureTuningSensitivity(50)
#     log(getConfigExposureTuningSensitivity())
