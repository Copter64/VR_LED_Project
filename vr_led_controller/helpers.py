import numpy as np

def extract_position(matrix):
    """Extracts position (translation) from a 4x4 transformation matrix."""
    return matrix[0][3], matrix[1][3], matrix[2][3]


def extract_orientation(matrix):
    """Extracts orientation (rotation) as a forward vector from a 4x4 transformation matrix."""
    # Forward vector is the third column of the matrix
    forward_vector = np.array([matrix[0][0], matrix[1][0], matrix[2][0]])
    return forward_vector


def correct_yaw(orientation,hand=None):
    """
    Corrects the yaw of the provided orientation vector.
    
    The input orientation is assumed to be the raw 'front' vector.
    This function projects the vector onto the horizontal (XZ) plane,
    extracts its yaw angle, and then adds a fixed offset so that the
    resulting vector has the desired horizontal direction.
    
    Calibration notes:
      - With the previous calibration, a 0.855 rad offset (≈49°) made the ray come from the left.
      - Reducing the offset to 0.65 rad (≈37°) should shift the ray toward the front.
      
    You can further fine-tune the `yaw_offset` value as needed.
    """
    # Project the orientation onto the horizontal plane (ignore Y)
    horizontal = np.array([orientation[0], 0, orientation[2]])
    norm = np.linalg.norm(horizontal)
    if norm < 1e-6:
        horizontal = np.array([0, 0, -1])
        norm = 1.0
    horizontal = horizontal / norm

    # Compute the current yaw angle.
    # Using atan2(x, -z) because we assume -Z is forward.
    current_yaw = np.arctan2(horizontal[0], -horizontal[2])

    # Adjust the yaw offset: try reducing it from 0.855 to 0.65 radians.
    if hand == "left":
        yaw_offset = -1.52  # Fine-tune this value to get the desired front direction for the left controller.
        #1.54 left by a degree
        #1.4 right by 2 degrees
    elif hand == "right":
        yaw_offset = -1.72  # Fine-tune this value to get the desired front direction for the right controller.
    corrected_yaw = current_yaw + yaw_offset

    # Reconstruct the corrected horizontal unit vector.
    corrected_vector = np.array([np.sin(corrected_yaw), 0, -np.cos(corrected_yaw)])
    return corrected_vector

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