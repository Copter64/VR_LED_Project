import numpy as np
import openvr

def extract_position(matrix):
    """Extracts position (translation) from a 4x4 transformation matrix."""
    return matrix[0][3], matrix[1][3], matrix[2][3]

def extract_orientation(matrix):
    """Extracts orientation (rotation) as a forward vector from a 4x4 transformation matrix."""
    # Forward vector is the third column of the matrix
    forward_vector = np.array([matrix[0][2], matrix[1][2], matrix[2][2]])
    return forward_vector

def is_button_pressed(vr_system, controller_index, button_id):
    """Checks if a specific button is pressed on a specific controller."""
    success, controller_state = vr_system.getControllerState(controller_index)
    if not success:
        return False
    # Check if the button is pressed
    button_mask = 1 << button_id
    return controller_state.ulButtonPressed & button_mask != 0

def rgb_to_hex(rgb):
    """
    Convert an RGB tuple to a HEX string.
    """
    return str('%02x%02x%02x' % rgb).upper()