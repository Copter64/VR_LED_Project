import numpy as np
import openvr
import time

# Dictionary to store the last press time for each button
last_press_times = {}

def extract_position(matrix):
    """Extracts position (translation) from a 4x4 transformation matrix."""
    return matrix[0][3], matrix[1][3], matrix[2][3]

def extract_orientation(matrix):
    """Extracts orientation (rotation) as a forward vector from a 4x4 transformation matrix."""
    # Forward vector is the third column of the matrix
    forward_vector = np.array([matrix[0][2], matrix[1][2], matrix[2][2]])
    return forward_vector

def is_button_pressed(vr_system, controller_index, button_id, debounce_time=0.5):
    """Checks if a specific button is pressed on a specific controller, with debounce."""
    global last_press_times

    success, controller_state = vr_system.getControllerState(controller_index)
    if not success:
        return False

    # Check if the button is pressed
    button_mask = 1 << button_id
    if controller_state.ulButtonPressed & button_mask:
        current_time = time.time()

        # Use last press time for debouncing
        last_press = last_press_times.get((controller_index, button_id), 0)

        if current_time - last_press > debounce_time:
            last_press_times[(controller_index, button_id)] = current_time  # Update last press time
            return True  # Valid press detected

    return False  # Button not pressed or within debounce time

def rgb_to_hex(rgb):
    """
    Convert an RGB tuple to a HEX string.
    """
    return str('%02x%02x%02x' % rgb).upper()