from pymavlink import mavutil
import logging
from logging.handlers import RotatingFileHandler
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from typing import Optional
import datetime
import os
import time
import re

from intraprocess_comms import *
from state import *
from txtPull import pull, get_numerical_pois
from vehicle_data import mode_mapping

# Begin logging

# initialize what file this error will be coming from. incase we will have more
logger = logging.getLogger(__name__)
# using now() to get current time
now = datetime.datetime.now()

# Format it to include the year and time in AM/PM format
formatted_time = now.strftime("%Y-%m-%d %I-%M-%S %p")
filename = f"{formatted_time}.txt"

# Define the folder and filename
if not os.path.isdir("logs"):
    os.makedirs("logs")
log_folder = "logs"
log_file = os.path.join(log_folder, filename)

# handlers
rotating_file_handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=10)
terminal = logging.StreamHandler()
# create format for log
log_format = logging.Formatter("%(asctime)s - %(name)s -  %(levelname)s - %(message)s")

# add the handlers all to the logger
rotating_file_handler.setFormatter(log_format)
terminal.setFormatter(log_format)
logger.setLevel(logging.DEBUG)
logger.addHandler(rotating_file_handler)
logger.addHandler(terminal)

def construct_data(global_data: GlobalData, state_machine: StateMachine, connected: bool) -> StateMachineData:
    return StateMachineData(
        phase=global_data.phase,
        state=state_machine.state.state_id,
        connected=connected,
        known_hammer_type=global_data.hammer_type,
        tower_pos_found=global_data.tower_position is not None,
        claw_pickup_pos_found=global_data.claw_hammer_position is not None,
        ballpeen_pickup_pos_found=global_data.ballpeen_hammer_position is not None,
        hammer_dropoff_pos_found=global_data.hammer_dropoff_position is not None
    )

def main_loop(ui_pipe: Connection) -> None:
    # this is a mock mavlink connection that we use
    # before connecting, and after disconnecting. 
    # doing any kind of receiving or sending on this
    # will result in exceptions.
    master = mavutil.mavfile(None, None)
    connected: bool = False

    # Make global data
    global_data = GlobalData(phase=PhaseType.SEARCH, hammer_type=HammerType.UNKNOWN, master=master, msa_feet=50)

    # Initiate state machine 
    state_machine = StateMachine(state=Idle(), global_data=global_data)

    # intiate some timers
    time_since_poi_update = time.time()
    POI_UPDATE_INTERVAL = 1 # in seconds
    time_since_data_update = time.time()
    DATA_UPDATE_INTERVAL = 1 # in seconds

    while True:
        # if multiple conditions in this iteration of the loop
        # trigger a send of StateMachineData, then the newest
        # data written to this variable will be sent at the end
        # of the iteration. this is helpful during situations where
        # perhaps the UI changes the state, triggering a data send,
        # but the state was invalid and its instantly set back to Idle,
        # triggering another data send.
        data_to_send: Optional[StateMachineData] = None

        # receive all possible mavlink messages
        if connected:
            try:
                while True:
                    msg = master.recv_match()
                    if msg is None:
                        break
                    elif msg.get_type() == "GLOBAL_POSITION_INT":
                        global_data.last_known_position = (float(msg.lat) / 1e7, float(msg.lon) / 1e7)
                        global_data.last_known_alt = float(msg.relative_alt) / 1000
                    elif msg.get_type() == "HEARTBEAT":
                        if msg.type == 2:
                            global_data.last_known_mode = msg.custom_mode
                            global_data.motors_armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                            ui_pipe.send(Heartbeat())
                    elif msg.get_type() == "STATUSTEXT":
                        # parse communications from the companion computer
                        candidates = msg.text.split("~~")
                        if len(candidates) == 2:
                            parsed = parse(candidates[1])
                            if parsed is not None:
                                # add it to the current states message list, if it has one
                                if hasattr(state_machine.state, "statustext_messages") and isinstance(state_machine.state.statustext_messages, list):
                                    state_machine.state.statustext_messages.append(parsed)
                                
                                # if its a qr code reading, lets update some values
                                if isinstance(parsed, StatusTextQrCodeValue):
                                    if parsed.qr_code == QRCodeType.TOWER_HAMMER_BALL:
                                        global_data.hammer_type = HammerType.BALLPEEN
                                        data_to_send = construct_data(global_data, state_machine, connected)
                                    elif parsed.qr_code == QRCodeType.TOWER_HAMMER_CLAW:
                                        global_data.hammer_type = HammerType.CLAW
                                        data_to_send = construct_data(global_data, state_machine, connected)

                        # parse mission waypoints getting completed
                        if msg.text[:9] == "Mission: ":
                            if hasattr(state_machine.state, "statustext_messages") and isinstance(state_machine.state.statustext_messages, list):
                                # find all integers in the text string with regex
                                nums = re.findall('\\d+', msg.text)
                                if len(nums) > 0:
                                    # it's most likely the first number
                                    state_machine.state.statustext_messages.append(WaypointCompleted(waypoint_num=int(nums[0])))

            except Exception as e:
                # TODO: this might be thrown if the other end has closed
                print('it failed bro: {0}'.format(e))

        # receive all messages from ui_pipe
        try:
            while ui_pipe.poll():
                message = ui_pipe.recv()
                if isinstance(message, Connect):
                    if not connected:
                        master = mavutil.mavlink_connection("udpin:localhost:" + str(message.port))
                        print("connecting on port " + str(message.port))
                        global_data.master = master
                        connected = True
                    else:
                        print("already connected??")
                elif isinstance(message, Disconnect):
                    if connected:
                        master.close()
                        master = mavutil.mavfile(None, None)
                        print("disconnecting.")
                        global_data.master = master
                        connected = False
                    else:
                        print("already disconnected bud")
                elif isinstance(message, ChangeCommand):
                    if message.new_hammer_type is not None:
                        global_data.hammer_type = message.new_hammer_type
                    if message.new_phase is not None:
                        global_data.phase = message.new_phase
                    if message.new_state is not None:
                        state_machine.state = construct_state(message.new_state, global_data)
                else:
                    print("unknown message sent")
                    ...
                # send a new StateMachineData to show the changes
                data_to_send = construct_data(global_data, state_machine, connected)
        except Exception as e:
            # TODO: this might be thrown if the other end has closed
            ...

        # send StateMachineData on a fixed interval
        if (time.time() - time_since_data_update) >= DATA_UPDATE_INTERVAL:
            #data_to_send = construct_data(global_data, state_machine, connected)
            time_since_data_update = time.time()

        if not isinstance(state_machine.state, Idle):
            # if we're disconnected, we should go to idle
            if not connected:
                state_machine.state = Idle()
                print("we're disconnected, going to idle")
                # send a new StateMachineData to show the changes
                data_to_send = construct_data(global_data, state_machine, connected)
            # ensure the state can run in our flight mode
            elif global_data.last_known_mode is not None:
                allowed_modes_ints = map(mode_mapping.get, state_machine.state.allowed_modes)
                if global_data.last_known_mode not in allowed_modes_ints:
                    state_machine.state = Idle()
                    print("mode not allowed, going to idle")
                    print("current mode:" + str(global_data.last_known_mode))
                    # send a new StateMachineData to show the changes
                    data_to_send = construct_data(global_data, state_machine, connected)
            # ensure the state can run in our arm status
            elif not global_data.motors_armed and not state_machine.state.runnable_in_disarm:
                state_machine.state = Idle()
                print("disarmed not allowed, going to idle")
                # send a new StateMachineData to show the changes
                data_to_send = construct_data(global_data, state_machine, connected)

        # update POIs
        if (time.time() - time_since_poi_update) >= POI_UPDATE_INTERVAL:
            global_data.tower_position = None
            global_data.ballpeen_hammer_position = None
            global_data.claw_hammer_position = None
            global_data.hammer_dropoff_position = None

            try:
                pois = pull()
                for key in pois:
                    # ignore capitalization
                    name = key.lower()

                    if "tower" in name:
                        global_data.tower_position = pois[key]
                    elif "ball" in name:
                        global_data.ballpeen_hammer_position = pois[key]
                    elif "claw" in name:
                        global_data.claw_hammer_position = pois[key]
                    elif "drop" in name and "hammer" in name:
                        global_data.hammer_dropoff_position = pois[key]
                    elif "hat" in name:
                        global_data.hat_dropoff_position = pois[key]
            except Exception:
                # TODO: handle poi update error
                ...
            time_since_poi_update = time.time()

        try:
            while True:
                result = state_machine.state.run()
                if result.transition_to is not None:
                    state_machine.state = result.transition_to
                    # send a new StateMachineData to show the changes
                    data_to_send = construct_data(global_data, state_machine, connected)
                if result.waiting:
                    # if waiting is false, then we run() again instantly
                    # if waiting is true, then we move on and do another
                    # iteration of the main loop, including the delay
                    break
        except Exception as e:
            logger.error("Error on run: %s", e)

        # update UI with latest data
        try:
            if data_to_send is not None:
                ui_pipe.send(data_to_send)
        except Exception as e:
            # TODO: this might be thrown if the other end has closed
            ...


        # delay between iterations
        time.sleep(1 / 30)  
"""

if __name__ == "__main__":
    (conn1, conn2) = Pipe(duplex=True)

    from companion_comms import *

    p = Process(target=main_loop, args=(conn1,))
    p.start()
    while True:
        try:
            while conn2.poll():
                message = conn2.recv()
                if isinstance(message, StateMachineData):
                    print("---------")
                    print("State: " + str(message.state))
                    print("Phase: " + str(message.phase))
                    print("Hammer Type: " + str(message.known_hammer_type))
                    print("Connected: " + str(message.connected))
                    print("---------")
                elif isinstance(message, Heartbeat):
                    print("HB.")
            new = input().upper()
            if new == "C":
                conn2.send(Connect(14552))
            elif new == "D":
                conn2.send(Disconnect())
            elif new[0:2] == "P=":
                conn2.send(ChangeCommand(new_phase=PhaseType[new[2:]]))
            elif new[0:2] == "H=":
                conn2.send(ChangeCommand(new_hammer_type=HammerType[new[2:]]))
            elif new != "":
                conn2.send(ChangeCommand(new_state=StateType[new]))
        except Exception as e:
            print("error dumbass")
"""