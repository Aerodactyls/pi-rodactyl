from multiprocessing import Process, Queue
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class PhaseType(Enum):
    SEARCH = 0
    TOWER = 1
    HAMMER_PICKUP = 2
    HAMMER_DROPOFF = 3
    HAT_DROPOFF = 4

class StateType(Enum):
    IDLE = 0
    ARM = 1
    ASCEND_MSA = 2
    NAVIGATE = 3
    #PRECISION_DESCENT = 4
    #ALIGN_NEXT_TO_TOWER = 5
    #DESCEND_NEXT_TO_TOWER = 6
    #CIRCLE_TOWER = 7
    PRECISION_LANDING = 8
    PAYLOAD_ACTION = 9
    ARM_TO_RTL = 10
    SEARCH_GRID = 11
    INSPECT_TOWER = 12
    DESCEND_POI = 13
    TOWER_INSPECTION_FINISHED = 14
    POI_ADJUSTMENT = 15

class HammerType(Enum):
    CLAW = 0
    BALLPEEN = 1
    UNKNOWN = 2

# Sent everytime a heartbeat is received from the drone, or atleast something
# on the mavlink connection. This is sent from the state machine process to the
# web server process.
class Heartbeat:
    ...

# Sent on a fixed interval or when one of these fields updates, this will
# update the UI about a lot of information. This is sent from the state machine
# process to the web server process.
@dataclass
class StateMachineData:
    phase: PhaseType
    state: StateType
    connected: bool

    known_hammer_type: HammerType
    tower_pos_found: bool
    claw_pickup_pos_found: bool
    ballpeen_pickup_pos_found: bool
    hammer_dropoff_pos_found: bool

# Sent to the state machine to tell it to connect to a mavlink connection on some
# local port. This is sent from the web server process to the state machine 
# process.
@dataclass
class Connect:
    port: int

# Sent to the state machine to tell it to disconnect from the mavlink connection.
# This is sent from the web server process to the state machine process.
class Disconnect:
    ...

# This is a command to the state machine process to change either the phase,
# the state, or the selected hammer type. If a field is set to None, then it
# won't be changed. This is sent from the web server process to the state 
# machine process.
@dataclass 
class ChangeCommand:
    new_phase: Optional[PhaseType] = None
    new_state: Optional[StateType] = None
    new_hammer_type: Optional[HammerType] = None

# This is a command to notify the UI that the state machine has encountered
# an error. This is sent from the state machine process to the web server
# process.
@dataclass
class MachineError:
    message: str
