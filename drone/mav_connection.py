from dataclasses import dataclass
from typing import Optional
from pymavlink import mavutil
from log import log
import globals


@dataclass
class MavConnectionClass:
    baud: int
    sourceComponent: int
    sourceSystem: int


def createMavConnection(
    connectionString: str,
    conf: Optional[MavConnectionClass] = None,
) -> None:
    if globals.master is not None:
        raise RuntimeError("MAVLink connection already exists.")

    log("Connecting to MAVLink...")
    if conf is not None:
        globals.master = mavutil.mavlink_connection(
            connectionString,
            baud=conf.baud,
            source_component=conf.sourceComponent,
            source_system=conf.sourceSystem,
        )
    else:
        globals.master = mavutil.mavlink_connection(connectionString)

    if globals.master is None:
        raise RuntimeError("Failed to establish MAVLink connection.")

    if not isinstance(globals.master, (mavutil.mavfile,)):
        raise RuntimeError("The MAVLink connection is not of a valid type.")

    log("Created MAVlink Connection")
