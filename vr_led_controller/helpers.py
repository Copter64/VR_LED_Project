import numpy as np
import openvr
import time

def extract_position(matrix):
    """Extracts position (translation) from a 4x4 transformation matrix."""
    return matrix[0][3], matrix[1][3], matrix[2][3]

def extract_orientation(matrix):
    """Extracts orientation (rotation) as a forward vector from a 4x4 transformation matrix."""
    # Forward vector is the third column of the matrix
    forward_vector = np.array([matrix[0][2], matrix[1][2], matrix[2][2]])
    return forward_vector

# Dictionary to store the last press time for each button
last_press_times = {}

def is_button_pressed(vr_system, controller_index, button_id, debounce_time=0.5):
    """
    Checks if a specific button is pressed on a specific controller with debounce.

    Args:
        vr_system (object): OpenVR system object.
        controller_index (int): Index of the controller in VR tracking.
        button_id (int): OpenVR button ID (e.g., k_EButton_SteamVR_Trigger).
        debounce_time (float): Minimum time (seconds) between valid presses.

    Returns:
        bool: True if button is pressed and debounce time has passed, else False.
    """
    global last_press_times

    success, controller_state = vr_system.getControllerState(controller_index)
    if not success:
        return False

    button_mask = 1 << button_id
    current_time = time.time()

    # Check if button is pressed
    if controller_state.ulButtonPressed & button_mask:
        # Get last press time, default to 0 if first time
        last_press_time = last_press_times.get((controller_index, button_id), 0)

        # If enough time has passed, register the press and update timestamp
        if current_time - last_press_time > debounce_time:
            last_press_times[(controller_index, button_id)] = current_time
            return True

    return False  # Button not pressed or within debounce time

def rgb_to_hex(rgb):
    """
    Convert an RGB tuple to a HEX string.
    """
    return str('%02x%02x%02x' % rgb).upper()

def get_tracked_controllers(vr_system):
    """
    Get all tracked VR controllers and their poses.

    Args:
        vr_system (object): OpenVR system object.

    Returns:
        list: A list of tuples containing (device_index, pose_matrix) for controllers.
    """
    tracked_controllers = []
    
    # Get poses of all tracked devices
    poses = vr_system.getDeviceToAbsoluteTrackingPose(
        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
    )

    for device_index, pose in enumerate(poses):
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            device_class = vr_system.getTrackedDeviceClass(device_index)
            if device_class == openvr.TrackedDeviceClass_Controller:
                tracked_controllers.append((device_index, pose.mDeviceToAbsoluteTracking))

    return tracked_controllers
