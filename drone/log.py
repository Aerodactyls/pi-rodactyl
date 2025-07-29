import globals
import datetime
import logging


def getFullFormattedCurrentTime() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = setup_logger(
    "main",
    f"{globals.WORKING_DIRECTORY}/logs/{getFullFormattedCurrentTime()}.log",
    level=logging.DEBUG,
)

exposureLogger = setup_logger(
    "exposure",
    f"{globals.WORKING_DIRECTORY}/logs/exposure-{getFullFormattedCurrentTime()}.log",
    level=logging.DEBUG,
)


def getFormattedCurrentTime() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def log(message, isExposureTuning=False) -> None:
    print(f"[{getFormattedCurrentTime()}] {message}")
    if isExposureTuning:
        exposureLogger.debug(message)
        return
    logger.debug(message)
