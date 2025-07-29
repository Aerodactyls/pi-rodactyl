import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import multiprocessing
from multiprocessing import Pipe
import sys
import os

# import main.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ground/src')))
from main import main_loop
from intraprocess_comms import *

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

ui_pipe_parent, ui_pipe_child = Pipe(duplex=True)

def data_emitter():
    with app.app_context():
        print("data_emitter started", flush=True)
        while True:
            try:
                if ui_pipe_parent.poll():
                    message = ui_pipe_parent.recv()
                    print(f"index.py: got message {type(message)}", flush=True)
                    
                    if isinstance(message, StateMachineData):
                        data = {
                            "type": "state_machine_data",
                            "data": {
                                "phase": message.phase.value,
                                "state": message.state.value,
                                "connected": message.connected,
                                "known_hammer_type": message.known_hammer_type.value,
                                "tower_pos_found": message.tower_pos_found,
                                "claw_pickup_pos_found": message.claw_pickup_pos_found,
                                "ballpeen_pickup_pos_found": message.ballpeen_pickup_pos_found,
                                "hammer_dropoff_pos_found": message.hammer_dropoff_pos_found,
                            }
                        }
                        socketio.emit('data_update', data)
                    elif isinstance(message, Heartbeat):
                        data = {
                            "type": "heartbeat",
                            "data": {}
                        }
                        socketio.emit('data_update', data)
                    elif isinstance(message, MachineError):
                        print(f"Machine error received: {message.message}", flush=True)
                        socketio.emit('machine_error', {"message": message.message})
                eventlet.sleep(0.1)
            except Exception as e:
                print(f"Error in data_emitter: {e}", flush=True)
                eventlet.sleep(1)

def start_main_loop(pipe_conn):
    try:
        main_loop(pipe_conn)
    except Exception as e:
        print(f"Error in main_loop: {e}")

@socketio.on('send_command')
def handle_command(data):
    print(f"Received command: {data}", flush=True)
    try:
        command_type = data.get('type')
        if command_type == 'change_command':
            command_data = data.get('data', {})
            
            change_command = ChangeCommand(
                new_phase=PhaseType(command_data.get('new_phase')) if command_data.get('new_phase') is not None else None,
                new_state=StateType(command_data.get('new_state')) if command_data.get('new_state') is not None else None,
                new_hammer_type=HammerType(command_data.get('new_hammer_type')) if command_data.get('new_hammer_type') is not None else None
            )
            
            ui_pipe_parent.send(change_command)
            
            emit('command_response', {'status': 'success', 'message': 'Command sent successfully'})
        elif command_type == 'connect':
            command_data = data.get('data', {})
            
            connect_command = Connect(port=command_data.get('port', 14550))
            
            ui_pipe_parent.send(connect_command)
            
            emit('command_response', {'status': 'success', 'message': 'Connect command sent'})
        elif command_type == 'disconnect':
            disconnect_command = Disconnect()
            
            ui_pipe_parent.send(disconnect_command)
            
            emit('command_response', {'status': 'success', 'message': 'Disconnect command sent'})
        else:
            emit('command_response', {'status': 'error', 'message': 'Unknown command type'})
    except Exception as e:
        print(f"Error handling command: {e}", flush=True)
        emit('command_response', {'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    main_process = multiprocessing.Process(target=start_main_loop, args=(ui_pipe_child,))
    main_process.daemon = True
    main_process.start()

    eventlet.spawn(data_emitter)
    
    socketio.run(app, debug=True, port=5328, host='0.0.0.0')