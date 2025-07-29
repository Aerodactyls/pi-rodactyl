from enum import Enum
from typing import Optional, Tuple, TypeVar, Generic
from math import radians
import logging
from logging.handlers import RotatingFileHandler
import datetime
import os
from pymavlink import mavutil
import time
from utils import *
from dataclasses import dataclass, field

from intraprocess_comms import PhaseType, HammerType, MachineError, StateType
from multiprocessing.connection import Connection
from companion_comms import *
from vehicle_data import *

# amount of time in seconds that are spent waiting
# after precision landing has finished
# in order to allow operators to confirm that the landing
# went well.
LANDING_CONFIRMATION_INTERVAL: float = 10

# the distance to move away from the tower
# when aligning next to it, in the north
# direction, in meters
ALIGN_TOWER_OFFSET: float = 2

# the vertical distance to lower by when next
# to the tower, after alignment, in meters
DESCEND_TOWER_ALT: float = 2

# the servo output port numbers for the payload
# system continous servos
PAYLOAD_SERVOS: list[int] = [12, 13]

# continous servo PWM values for the payload action.
# these are in microseconds. the values at an index
# correspond to the servo number in PAYLOAD_SERVOS.
# IMPORTANT NOTE: these are not the actual pwm values
# the servos will be set to, but the RC values that
# the servo controller will work with instead of the
# actual RC values given by the transmitter. essentially,
# these need to be set to the minimum and maximum values 
# of the RC channel that the servos are setup for.
PAYLOAD_CAPTURE_PWM: list[int] = [2380, 500]
PAYLOAD_RELEASE_PWM: list[int] = [500, 2270]
PAYLOAD_NEUTRAL_PWM: list[int] = [1433, 1391]

# the amount of time to hold the continous servos
# at a PWM value when capturing or releasing,
# in seconds
PAYLOAD_ACTUATION_TIME: float = 10

def default_modes() -> list[str]:
    return ["GUIDED"]

@dataclass
class BaseState:
    state_id: StateType
    runnable_in_disarm: bool
    allowed_modes: list[str] = field(default_factory=default_modes)

@dataclass(kw_only=True)
class RunResult:
    transition_to: Optional[BaseState]
    waiting: bool

# this is for all the state thats not the state machines
@dataclass(kw_only=True)
class GlobalData:
    phase: PhaseType
    hammer_type: HammerType
    master: mavutil.mavfile
    msa_feet: float

    last_known_position: Optional[Tuple[float, float]] = None # of the drone, (lat, lon) in degrees.
    last_known_alt: Optional[float] = None # of the drone, in meters relative to home.
    last_known_mode: Optional[int] = None
    tower_position: Optional[Tuple[float, float]] = None
    ballpeen_hammer_position: Optional[Tuple[float, float]] = None
    claw_hammer_position: Optional[Tuple[float, float]] = None
    hammer_dropoff_position: Optional[Tuple[float, float]] = None
    hat_dropoff_position: Optional[Tuple[float, float]] = None
    motors_armed: bool = False
    searchgrid_waypoints_done: int = 0

@dataclass(kw_only=True)
class StateMachine:
    state: BaseState
    global_data: GlobalData

@dataclass(kw_only=True)
class Idle(BaseState):
    runnable_in_disarm: bool = True
    state_id: StateType = StateType.IDLE

    def run(self) -> RunResult:
        return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class Arm(BaseState):
    global_data: GlobalData

    runnable_in_disarm: bool = True
    state_id: StateType = StateType.ARM

    def run(self) -> RunResult:
        if self.global_data.motors_armed:
            return RunResult(transition_to=AscendMSA(global_data=self.global_data), waiting=False)
        else:
            return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class AscendMSA(BaseState):
    global_data: GlobalData
    ascend_command_sent: bool = False

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.ASCEND_MSA

    def run(self) -> RunResult:
        if self.global_data.last_known_alt is None:
            print("No known altitude for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)
        if self.global_data.last_known_position is None:
            print("No known position for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)

        # we need to send the ascend command
        if not self.ascend_command_sent:
            # we send a position target first, and then a take off command.
            # this is so the ascend works when we're both in the air, and
            # landed. you have to send it in this order (pos target then takeoff),
            # otherwise the ascention wont work when landed.
            self.global_data.master.mav.set_position_target_global_int_send(
                0,  # Timestamp (ms since boot)
                TARGET_SYSTEM,
                TARGET_COMPONENT,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Coordinate frame
                POSITION_TYPEMASK,
                lat_int=int(self.global_data.last_known_position[0] * 1e7), 
                lon_int=int(self.global_data.last_known_position[1] * 1e7), 
                alt=feet_to_meters(self.global_data.msa_feet),  # Altitude in meters as a float
                vx=0, vy=0, vz=0,
                afx=0, afy=0, afz=0,
                yaw=0, yaw_rate=0
            )
            self.global_data.master.mav.command_long_send(
                TARGET_SYSTEM,
                TARGET_COMPONENT,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0, 0, 0, 0, 0, 0, 0,
                feet_to_meters(self.global_data.msa_feet)
            )
            
            self.ascend_command_sent = True
            return RunResult(transition_to=None, waiting=False)
        # we just need to wait until we've ascended
        else:
            alt_meters = self.global_data.last_known_alt
            if feet_to_meters(self.global_data.msa_feet) <= (alt_meters + 0.5):
                # we are close to or above our designated altitude
                if self.global_data.phase == PhaseType.SEARCH:
                    return RunResult(transition_to=SearchGrid(global_data=self.global_data, statustext_messages=[]), waiting=False)
                else:
                    return RunResult(transition_to=Navigate(global_data=self.global_data), waiting=False)

            return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class Navigate(BaseState):
    global_data: GlobalData
    navigate_command_sent: bool = False
    target: Optional[Tuple[float, float]] = None # lat and long in degrees

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.NAVIGATE

    def run(self) -> RunResult:
        if self.global_data.last_known_alt is None:
            print("No known altitude for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)
        if self.global_data.last_known_position is None:
            print("No known position for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)

        # if we're ever below our msa, then we should transition
        # back to ascend to msa
        if feet_to_meters(self.global_data.msa_feet) > (self.global_data.last_known_alt + 2):
            # we are close to or above our designated altitude
            return RunResult(transition_to=AscendMSA(global_data=self.global_data), waiting=False)

        # we need to send the navigate command
        if not self.navigate_command_sent:
            if self.global_data.phase == PhaseType.TOWER:
                self.target = self.global_data.tower_position
            elif self.global_data.phase == PhaseType.HAMMER_PICKUP:
                if self.global_data.hammer_type == HammerType.BALLPEEN:
                    self.target = self.global_data.ballpeen_hammer_position
                elif self.global_data.hammer_type == HammerType.CLAW:
                    self.target = self.global_data.claw_hammer_position
                else:
                    # TODO: error bro
                    self.target = None
            elif self.global_data.phase == PhaseType.HAMMER_DROPOFF:
                self.target = self.global_data.hammer_dropoff_position
            elif self.global_data.phase == PhaseType.HAT_DROPOFF:
                self.target = self.global_data.hat_dropoff_position
            else:
                # TODO: error bro
                self.target = None

            if self.target is not None:
                self.global_data.master.mav.set_position_target_global_int_send(
                    0,  # Timestamp (ms since boot)
                    TARGET_SYSTEM,
                    TARGET_COMPONENT,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Coordinate frame
                    POSITION_TYPEMASK,
                    lat_int=int(self.target[0] * 1e7),
                    lon_int=int(self.target[1] * 1e7),
                    alt=feet_to_meters(self.global_data.msa_feet),
                    vx=0, vy=0, vz=0,
                    afx=0, afy=0, afz=0,
                    yaw=0, yaw_rate=0
                )
            else:
                # send a message to the UI: No target set for navigate! Waiting for pilot to navigate manually...
                ...
            
            self.navigate_command_sent = True
            return RunResult(transition_to=None, waiting=False)
        # we just need to wait until we get to our destination
        else:
            if self.target is not None:
                try:
                    if distance_two(self.global_data.last_known_position, self.target) <= 0.25:
                        # its time to transition to the next state!
                        if self.global_data.phase == PhaseType.SEARCH:
                            return RunResult(transition_to=DescendPOI(global_data=self.global_data, statustext_messages=[]), waiting=False)
                        elif self.global_data.phase == PhaseType.TOWER:
                            return RunResult(transition_to=InspectTower(), waiting=False)
                        else:
                            return RunResult(transition_to=PrecisionLand(), waiting=False)
                except:
                    logging.warning("No known position for vehicle!")
            return RunResult(transition_to=None, waiting=True)
"""

@dataclass(kw_only=True)
class PrecisionDescent(BaseState):
    global_data: GlobalData
    statustext_messages: list[str]
    since_land_command_sent: Optional[float] = None
    precision_descent_command_sent: bool = False
    landing_finished: bool = False

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.PRECISION_DESCENT

    def run(self) -> RunResult:
        # we need to set the mode to land
        if self.since_land_command_sent is None:
            mode_id = self.global_data.master.mode_mapping()["LAND"] #TODO: what if this fails or returns None
            self.global_data.master.mav.set_mode_send(
                self.global_data.master.target_system,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )
            self.since_land_command_sent = time.time()
            # we can now run while disarmed, and in LAND
            self.allowed_modes.append("LAND")
            self.runnable_in_disarm = True

            return RunResult(transition_to=None, waiting=False)
        # we need to send the precision landing message
        elif not self.precision_descent_command_sent:
            # has it been 2 seconds since we went into land mode
            if (time.time() - self.since_land_command_sent) >= 2:
                self.global_data.master.mav.command_long_send(
                    self.global_data.master.target_system,
                    self.global_data.master.target_component,
                    mavutil.mavlink.MAV_CMD_USER_1,
                    4,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
                self.precision_descent_command_sent = True
                return RunResult(transition_to=None, waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)
        # we need to set the vehicle back to guided when we have
        # received word from the companion computer that the 
        # precision descent has finished
        elif not self.landing_finished:
            while len(self.statustext_messages) > 0:
                oldest = self.statustext_messages.pop(0)
                if isinstance(oldest, StatusTextEndOfPrecisionDescent):
                    mode_id = self.global_data.master.mode_mapping()["GUIDED"] # TODO: what if this fails or returns None
                    self.global_data.master.mav.set_mode_send(
                        self.global_data.master.target_system,
                        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                        mode_id
                    )
                    self.landing_finished = True
                    return RunResult(transition_to=None, waiting=False)
            return RunResult(transition_to=None, waiting=True)
        # we need to ensure we're back in guided
        # before moving onto the next state
        else:
            if self.global_data.last_known_mode == self.global_data.master.mode_mapping()["GUIDED"]:
                return RunResult(transition_to=AlignTower(global_data=self.global_data), waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)
        
# This state should be capable of running in Land mode, aswell as 
# Guided mode!
@dataclass(kw_only=True)
class PrecisionLand(BaseState):
    global_data: GlobalData
    since_land_command_sent: Optional[float] = None
    precision_land_command_sent: bool = False
    return_guided_command_sent: bool = False
    since_landing_finished: Optional[float] = None

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.PRECISION_LANDING

    def run(self) -> RunResult:
        # what are we targetting? we should be doing this check first in the run
        # because if we're in an invalid phase or hammer type we should exit out
        # without setting it to land mode.
        if self.global_data.phase == PhaseType.HAMMER_PICKUP:
            if self.global_data.hammer_type == HammerType.BALLPEEN:
                param = 1
            elif self.global_data.hammer_type == HammerType.CLAW:
                param = 2
            else:
                #self.global_data.ui_pipe.send(MachineError("No hammer type, not precision landing."))
                return RunResult(transition_to=Idle(), waiting=False)
        elif self.global_data.phase == PhaseType.HAMMER_DROPOFF:
            param = 3
        elif self.global_data.phase == PhaseType.HAT_DROPOFF:
            param = 7
        else:
            #self.global_data.ui_pipe.send(MachineError("No correct target, not precision landing."))
            return RunResult(transition_to=Idle(), waiting=False)

        # we need to set the mode to land
        if self.since_land_command_sent is None:
            mode_id = self.global_data.master.mode_mapping()["LAND"] #TODO: what if this fails or returns None
            self.global_data.master.mav.set_mode_send(
                self.global_data.master.target_system,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )
            self.since_land_command_sent = time.time()
            # we can now run while disarmed, and in LAND
            self.allowed_modes.append("LAND")
            self.runnable_in_disarm = True

            return RunResult(transition_to=None, waiting=False)
        # we need to send the precision landing message
        elif not self.precision_land_command_sent:
            # has it been 2 seconds since we went into land mode
            if (time.time() - self.since_land_command_sent) >= 2:
                self.global_data.master.mav.command_long_send(
                    self.global_data.master.target_system,
                    self.global_data.master.target_component,
                    mavutil.mavlink.MAV_CMD_USER_1,
                    param,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                )
                self.precision_land_command_sent = True
                return RunResult(transition_to=None, waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)
        # we need to set the vehicle back to guided when we are disarmed
        elif self.since_landing_finished is None:
            if not self.global_data.master.motors_armed(): # we're ready to set it
                mode_id = self.global_data.master.mode_mapping()["GUIDED"] # TODO: what if this fails or returns None
                self.global_data.master.mav.set_mode_send(
                    self.global_data.master.target_system,
                    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    mode_id
                )
                self.since_landing_finished = time.time()
                return RunResult(transition_to=None, waiting=False)
            else: # we're still waiting for precision landing to finish
                return RunResult(transition_to=None, waiting=True)
        # we need to ensure we're back in guided, and wait some seconds
        # (to allow operators to confirm a good landing) before
        # moving onto the next state
        else:
            if self.global_data.last_known_mode == self.global_data.master.mode_mapping()["GUIDED"] \
            and (time.time() - self.since_landing_finished) >= LANDING_CONFIRMATION_INTERVAL:
                return RunResult(transition_to=PayloadAction(global_data=self.global_data), waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)

"""

@dataclass(kw_only=True)
class ArmToRTL(BaseState):
    global_data: GlobalData
    armed: bool = False
    ascend_command_sent: bool = False

    runnable_in_disarm: bool = True
    state_id: StateType = StateType.ARM_TO_RTL

    def run(self) -> RunResult:
        if self.global_data.last_known_alt is None:
            print("No known altitude for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)
        if self.global_data.last_known_position is None:
            print("No known position for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)

        # we need to wait until we're armed
        if not self.armed:
            if self.global_data.motors_armed:
                self.armed = True
                return RunResult(transition_to=None, waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)
        # we need to send command to ascend/takeoffs
        elif not self.ascend_command_sent:
            # we send a position target first, and then a take off command.
            # this is so the ascend works when we're both in the air, and
            # landed. you have to send it in this order (pos target then takeoff),
            # otherwise the ascention wont work when landed.
            self.global_data.master.mav.set_position_target_global_int_send(
                0,  # Timestamp (ms since boot)
                TARGET_SYSTEM,
                TARGET_COMPONENT,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # Coordinate frame
                POSITION_TYPEMASK,
                lat_int=int(self.global_data.last_known_position[0] * 1e7), 
                lon_int=int(self.global_data.last_known_position[1] * 1e7), 
                alt=feet_to_meters(self.global_data.msa_feet),  # Altitude in meters as a float
                vx=0, vy=0, vz=0,
                afx=0, afy=0, afz=0,
                yaw=0, yaw_rate=0
            )
            self.global_data.master.mav.command_long_send(
                TARGET_SYSTEM,
                TARGET_COMPONENT,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0, 0, 0, 0, 0, 0, 0,
                feet_to_meters(self.global_data.msa_feet)
            )

            self.ascend_command_sent = True
            return RunResult(transition_to=None, waiting=False)
        # we need to wait until we've ascended, then RTL
        else:
            alt_meters = self.global_data.last_known_alt
            if feet_to_meters(self.global_data.msa_feet) <= (alt_meters + 0.5):
                # we are close to or above our designated altitude
                # set the mode to RTL
                mode_id = mode_mapping["RTL"]
                self.global_data.master.mav.set_mode_send(
                    TARGET_SYSTEM,
                    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    mode_id
                ) 
                return RunResult(transition_to=Idle(), waiting=True)
            return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class PayloadAction(BaseState):
    global_data: GlobalData
    since_payload_action: Optional[float] = None

    runnable_in_disarm: bool = True
    state_id: StateType = StateType.PAYLOAD_ACTION

    def run(self) -> RunResult:
        # figure out our next phase, next state, and whether
        # or not we need to capture or release with the payload
        # system
        next_phase: PhaseType
        next_state: type[Arm] | type[ArmToRTL]
        payload_action_pwm: list[int]
        if self.global_data.phase == PhaseType.HAMMER_PICKUP:
            next_phase = PhaseType.HAMMER_DROPOFF
            next_state = Arm
            payload_action_pwm = PAYLOAD_CAPTURE_PWM
        elif self.global_data.phase == PhaseType.HAMMER_DROPOFF:
            next_phase = PhaseType.HAMMER_DROPOFF # don't change the phase, there is no next phase
            next_state = ArmToRTL
            payload_action_pwm = PAYLOAD_RELEASE_PWM
        elif self.global_data.phase == PhaseType.HAT_DROPOFF:
            next_phase = PhaseType.TOWER
            next_state = ArmToRTL
            payload_action_pwm = PAYLOAD_RELEASE_PWM
        else:
            # TODO: throw an error i guess
            return RunResult(transition_to=Idle(), waiting=True)

        # we need to actuate the payload system
        if self.since_payload_action is None:
            for i in range(len(PAYLOAD_SERVOS)):
                """
                self.global_data.master.mav.command_long_send(
                    self.global_data.master.target_system, self.global_data.master.target_component,
                    mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
                    0,            # first transmission of this command
                    PAYLOAD_SERVOS[i],  # servo instance
                    payload_action_pwm[i], # PWM pulse-width
                    0,0,0,0,0     # unused parameters
                )
                """
            self.since_payload_action = time.time()
            return RunResult(transition_to=None, waiting=False)
        # we need to wait the payload actuation time,
        # and then set all the servos back to neutral,
        # and move onto the next state and phase
        else:
            if (time.time() - self.since_payload_action) >= PAYLOAD_ACTUATION_TIME:
                self.global_data.phase = next_phase
                # set all the servos back to neutral
                for i in range(len(PAYLOAD_SERVOS)):
                    """
                    self.global_data.master.mav.command_long_send(
                        self.global_data.master.target_system, self.global_data.master.target_component,
                        mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
                        0,            # first transmission of this command
                        PAYLOAD_SERVOS[i],  # servo instance
                        PAYLOAD_NEUTRAL_PWM[i], # PWM pulse-width
                        0,0,0,0,0     # unused parameters
                    )
                    """
                return RunResult(transition_to=next_state(global_data=self.global_data), waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)
        
"""

@dataclass(kw_only=True)
class AlignTower(BaseState):
    global_data: GlobalData
    since_align_command_sent: Optional[float] = None

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.ALIGN_NEXT_TO_TOWER

    def run(self) -> RunResult:
        # we need to send the align command
        if self.since_align_command_sent is None:
            self.global_data.master.mav.set_position_target_local_ned_send(
                0,  # Timestamp (ms since boot)
                self.global_data.master.target_system,
                self.global_data.master.target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,  # Coordinate frame
                POSITION_TYPEMASK & YAW_TYPEMASK,
                x=ALIGN_TOWER_OFFSET,
                y=0,
                z=0, 
                vx=0, vy=0, vz=0,
                afx=0, afy=0, afz=0,
                yaw=radians(180), # point south
                yaw_rate=0 
            )
            self.since_align_command_sent = time.time()
            return RunResult(transition_to=None, waiting=False)
        # we can wait 7 seconds for alignment to finish
        else:
            if (time.time() - self.since_align_command_sent) >= 7:
                return RunResult(transition_to=DescendTower(global_data=self.global_data), waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)

# NOTE: this is not descending onto the tower,
# this is descending next to the tower after aligning
# next to it. 
@dataclass(kw_only=True)
class DescendTower(BaseState):
    global_data: GlobalData
    since_descend_command_sent: Optional[float] = None

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.DESCEND_NEXT_TO_TOWER

    def run(self) -> RunResult:
        # we need to send the descend command
        if self.since_descend_command_sent is None:
            self.global_data.master.mav.set_position_target_local_ned_send(
                0,  # Timestamp (ms since boot)
                self.global_data.master.target_system,
                self.global_data.master.target_component,
                mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,  # Coordinate frame
                POSITION_TYPEMASK & YAW_TYPEMASK,
                x=0,
                y=0,
                z=DESCEND_TOWER_ALT,
                vx=0, vy=0, vz=0,
                afx=0, afy=0, afz=0,
                yaw=radians(180), # point south
                yaw_rate=0 
            )
            self.since_descend_command_sent = time.time()
            return RunResult(transition_to=None, waiting=False)
        # we can wait 5 seconds for descent to finish
        else:
            if (time.time() - self.since_descend_command_sent) >= 5:
                return RunResult(transition_to=CircleTower(global_data=self.global_data, statustext_messages=[]), waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class CircleTower(BaseState):
    global_data: GlobalData
    statustext_messages: list[StatusTextMessage]
    circle_command_sent: bool = False
    hammer_type_set: bool = False

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.CIRCLE_TOWER

    def run(self) -> RunResult:
        # we need to set the flight mode to circle
        if not self.circle_command_sent:
            # set the mode to circle
            mode_id = self.global_data.master.mode_mapping()["CIRCLE"] #TODO: what if this fails or returns None
            self.global_data.master.mav.set_mode_send(
                self.global_data.master.target_system,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )
            # we can now run while CIRCLE
            self.allowed_modes.append("CIRCLE")
            self.circle_command_sent = True
            return RunResult(transition_to=None, waiting=True)
        # we need to wait until we've picked up our hammer type
        elif not self.hammer_type_set:
            while len(self.statustext_messages) > 0:
                oldest = self.statustext_messages.pop(0)
                if isinstance(oldest, StatusTextQrCodeValue):
                    if oldest.qr_code == QRCodeType.BALL_HAMMMER_PICKUP or oldest.qr_code == QRCodeType.CLAW_HAMMER_PICKUP:
                        # the hammer type has been found! it's already been set in
                        # global data in the main loop, so we should move on. 
                        self.hammer_type_set = True
                        # set our flight mode back to Guided
                        mode_id = self.global_data.master.mode_mapping()["GUIDED"] #TODO: what if this fails or returns None
                        self.global_data.master.mav.set_mode_send(
                            self.global_data.master.target_system,
                            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                            mode_id
                        )  
                        return RunResult(transition_to=None, waiting=False)
            return RunResult(transition_to=None, waiting=True)
        # we need to wait until our mode is back to guided
        else:
            mode_id = self.global_data.master.mode_mapping()["GUIDED"] #TODO: what if this fails or returns None
            if self.global_data.last_known_mode == mode_id:
                return RunResult(transition_to=ArmToRTL(global_data=self.global_data), waiting=False)
            else:
                return RunResult(transition_to=None, waiting=True)

"""

@dataclass(kw_only=True)
class SearchGrid(BaseState):
    global_data: GlobalData
    statustext_messages: list[StatusTextMessage]
    start_mission_sent: bool = False

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.SEARCH_GRID
    allowed_modes: list[str] = field(default_factory=default_modes)

    def run(self) -> RunResult:
        if self.global_data.last_known_alt is None:
            print("No known altitude for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)

        # we need to start the mission
        if not self.start_mission_sent:
            # but first check if we're below the msa. then we should
            # back to ascend to msa
            if feet_to_meters(self.global_data.msa_feet) > (self.global_data.last_known_alt + 2):
                # we are close to or above our designated altitude
                return RunResult(transition_to=AscendMSA(global_data=self.global_data), waiting=False)

            self.global_data.master.mav.command_long_send(
                TARGET_SYSTEM,
                TARGET_COMPONENT,
                mavutil.mavlink.MAV_CMD_MISSION_START,
                0, 
                0, 0, 0, 0, 0, 0, 0
            )
            # set the current mission item to the one last completed,
            # making sure not to do -1
            self.global_data.master.mav.mission_set_current_send(
                TARGET_SYSTEM,
                TARGET_COMPONENT,
                max(self.global_data.searchgrid_waypoints_done - 1, 0)
            )
            self.allowed_modes.append("AUTO")
            self.start_mission_sent = True
            return RunResult(transition_to=None, waiting=False)
        # we need to just wait, and when a
        # waypoint is completed then save that
        else:
            while len(self.statustext_messages) > 0:
                oldest = self.statustext_messages.pop(0)
                if isinstance(oldest, WaypointCompleted):
                    self.global_data.searchgrid_waypoints_done = oldest.waypoint_num
            return RunResult(transition_to=None, waiting=True)


def pilot_control_modes() -> list[str]:
    return ["GUIDED", "LOITER"]

@dataclass(kw_only=True)
class PrecisionLand(BaseState):
    runnable_in_disarm: bool = True
    state_id: StateType = StateType.PRECISION_LANDING
    allowed_modes: list[str] = field(default_factory=pilot_control_modes)

    def run(self) -> RunResult:
        return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class InspectTower(BaseState):
    runnable_in_disarm: bool = False
    state_id: StateType = StateType.INSPECT_TOWER
    allowed_modes: list[str] = field(default_factory=pilot_control_modes)

    def run(self) -> RunResult:
        return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class TowerInspectionFinished(BaseState):
    global_data: GlobalData

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.TOWER_INSPECTION_FINISHED
    allowed_modes: list[str] = field(default_factory=pilot_control_modes)

    def run(self) -> RunResult:
        self.global_data.phase = PhaseType.HAMMER_PICKUP
        return RunResult(transition_to=ArmToRTL(global_data=self.global_data), waiting=False)

def poi_adjustment_modes() -> list[str]:
    return ["AUTO", "LOITER", "LAND"]

@dataclass(kw_only=True)
class POIAdjustment(BaseState):
    global_data: GlobalData
    loiter_command_sent: bool = False

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.POI_ADJUSTMENT
    allowed_modes: list[str] = field(default_factory=poi_adjustment_modes)

    def run(self) -> RunResult:
        # we need to set the flight mode
        # to loiter
        if not self.loiter_command_sent:
            mode_id = mode_mapping["LOITER"]
            self.global_data.master.mav.set_mode_send(
                TARGET_SYSTEM,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )  
            self.allowed_modes.append("LOITER")
            self.loiter_command_sent = True
            return RunResult(transition_to=None, waiting=False)
        # we just wait
        else:
            return RunResult(transition_to=None, waiting=True)

@dataclass(kw_only=True)
class DescendPOI(BaseState):
    global_data: GlobalData
    statustext_messages: list[StatusTextMessage]
    land_command_sent: bool = False
    loiter_command_sent: bool = False

    runnable_in_disarm: bool = False
    state_id: StateType = StateType.DESCEND_POI
    allowed_modes: list[str] = field(default_factory=pilot_control_modes)

    def run(self) -> RunResult:
        if self.global_data.last_known_alt is None:
            print("No known altitude for the vehicle!")
            return RunResult(transition_to=Idle(), waiting=False)

        # we need to set the flight mode
        # to land
        if not self.land_command_sent:
            mode_id = mode_mapping["LAND"]
            self.global_data.master.mav.set_mode_send(
                TARGET_SYSTEM,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )  
            self.allowed_modes.append("LAND")
            self.land_command_sent = True
            return RunResult(transition_to=None, waiting=False)
        # we need to set the flight mode
        # to loiter if we get below 20 ft
        # or if we decode a valid qr code
        elif not self.loiter_command_sent:
            while len(self.statustext_messages) > 0:
                oldest = self.statustext_messages.pop(0)
                if isinstance(oldest, StatusTextQrCodeValue):
                    mode_id = mode_mapping["LOITER"]
                    self.global_data.master.mav.set_mode_send(
                        TARGET_SYSTEM,
                        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                        mode_id
                    )  
                    self.allowed_modes.append("LOITER")
                    self.loiter_command_sent = True
                    return RunResult(transition_to=None, waiting=False)
            if self.global_data.last_known_alt <= feet_to_meters(20):
                mode_id = mode_mapping["LOITER"]
                self.global_data.master.mav.set_mode_send(
                    TARGET_SYSTEM,
                    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    mode_id
                )  
                self.allowed_modes.append("LOITER")
                self.loiter_command_sent = True
                return RunResult(transition_to=None, waiting=False)

            return RunResult(transition_to=None, waiting=True)
        # we need to just wait as the 
        # operators figure it out
        else:   
            return RunResult(transition_to=None, waiting=True)


def construct_state(state_type: StateType, global_data: GlobalData) -> BaseState:
    if state_type == StateType.IDLE:
        return Idle()
    elif state_type == StateType.ARM:
        return Arm(global_data=global_data)
    elif state_type == StateType.ASCEND_MSA:
        return AscendMSA(global_data=global_data)
    elif state_type == StateType.NAVIGATE:
        return Navigate(global_data=global_data)
    # elif state_type == StateType.PRECISION_DESCENT:
    #     return PrecisionDescent(global_data=global_data, statustext_messages=[])
    # elif state_type == StateType.ALIGN_NEXT_TO_TOWER:
    #     return AlignTower(global_data=global_data)
    # elif state_type == StateType.DESCEND_NEXT_TO_TOWER:
    #     return DescendTower(global_data=global_data)
    # elif state_type == StateType.CIRCLE_TOWER:
    #     return CircleTower(global_data=global_data, statustext_messages=[])
    # elif state_type == StateType.PRECISION_LANDING:
    #     return PrecisionLand(global_data=global_data)
    elif state_type == StateType.PAYLOAD_ACTION:
        return PayloadAction(global_data=global_data)
    elif state_type == StateType.ARM_TO_RTL:
        return ArmToRTL(global_data=global_data) 
    elif state_type == StateType.SEARCH_GRID:
        return SearchGrid(global_data=global_data, statustext_messages=[]) 
    elif state_type == StateType.INSPECT_TOWER:
        return InspectTower() 
    elif state_type == StateType.TOWER_INSPECTION_FINISHED:
        return TowerInspectionFinished(global_data=global_data)
    elif state_type == StateType.DESCEND_POI:
        return DescendPOI(global_data=global_data, statustext_messages=[])
    elif state_type == StateType.POI_ADJUSTMENT:
        return POIAdjustment(global_data=global_data)
    else:
        print("uh oh") # TODO: actual error
        return Idle()