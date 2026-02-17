import socketio
import vgamepad as vg
import time

# Standard Python Socket.IO client
sio = socketio.Client()

# --- MULTIPLAYER STATE ---
# Dictionary to store gamepad instances: { player_id: vg.VX360Gamepad }
controllers = {}

# Dictionary to store joystick states: { player_id: { 'LX': 0.0, ... } }
joystick_states = {}

def get_controller(player_id):
    """Retrieve or create a controller for the given player_id."""
    if player_id not in controllers:
        try:
            print(f"Assigning new controller for Player {player_id}...")
            # Create a new virtual Xbox 360 controller
            controllers[player_id] = vg.VX360Gamepad()
            # Initialize joystick state
            joystick_states[player_id] = {
                'LX': 0.0, 'LY': 0.0,
                'RX': 0.0, 'RY': 0.0
            }
            print(f"Controller assigned for Player {player_id}")
            
            # Optional: Wake up controller with a tiny rumble (not supported by vgamepad directly easily, but we can log)
        except Exception as e:
            print(f"Failed to create controller for Player {player_id}: {e}")
            return None
    
    return controllers[player_id]

@sio.event
def connect():
    print("Python Receiver Connected!")

@sio.event
def connect_error(data):
    print("The connection failed!")

@sio.event
def disconnect():
    print("Disconnected from server")

@sio.on('controller-input')
def on_message(data):
    try:
        # Get Player ID (default to 1 if missing for backward compatibility)
        player_id = int(data.get('player', 1))
        
        gamepad = get_controller(player_id)
        if not gamepad:
            return

        msg_type = data.get('type')
        
        # --- AXIS HANDLING (Joysticks) ---
        if msg_type == 'AXIS':
            axis = data.get('axis')
            value = float(data.get('value', 0))
            
            # Update local state for this player
            if axis in joystick_states[player_id]:
                joystick_states[player_id][axis] = value
            
            # Get current state
            state = joystick_states[player_id]
            
            # Update Virtual Gamepad
            gamepad.left_joystick_float(x_value_float=state['LX'], y_value_float=state['LY'])
            gamepad.right_joystick_float(x_value_float=state['RX'], y_value_float=state['RY'])
            gamepad.update()

        # --- BUTTON HANDLING ---
        elif msg_type == 'BUTTON':
            btn_name = data.get('button')
            val = data.get('value') # 1 or 0
            
            # Triggers (L2/R2)
            if btn_name == 'XUSB_GAMEPAD_LEFT_TRIGGER':
                gamepad.left_trigger_float(float(val))
                gamepad.update()
                return
            elif btn_name == 'XUSB_GAMEPAD_RIGHT_TRIGGER':
                gamepad.right_trigger_float(float(val))
                gamepad.update()
                return

            # Button Mapping
            btn_map = {
                'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                'DPAD_UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                'DPAD_DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                'DPAD_LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                'DPAD_RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
                'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                'BACK': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                'LB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                'RB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                'GUIDE': vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE
            }

            if btn_name in btn_map:
                target_btn = btn_map[btn_name]
                if val == 1:
                    gamepad.press_button(target_btn)
                else:
                    gamepad.release_button(target_btn)
                gamepad.update()

    except Exception as e:
        print(f"Error processing input: {e}")

def main():
    # Pre-initialize Player 1 so it shows up in Windows immediately
    print("Pre-initializing Player 1 Controller...")
    get_controller(1)

    while True:
        try:
            # Connect to the local Node.js server
            sio.connect('http://localhost:3000')
            sio.wait()
        except Exception as e:
            print(f"Connection Error: {e}, retrying in 3s...")
            time.sleep(3)

if __name__ == '__main__':
    main()
