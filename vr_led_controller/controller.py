import openvr
from led_manager import calculate_leds_to_light, set_leds, load_led_positions
from helpers import extract_position, extract_orientation, is_button_pressed
from config import FADETIME
import asyncio
import json
import numpy as np
import math


def extract_yaw_pitch_roll(matrix):
    """Extracts yaw, pitch, and roll from a 4x4 transformation matrix."""
    # Forward vector (Z-direction)
    forward = np.array([matrix[0][2], matrix[1][2], matrix[2][2]])
    up = np.array([matrix[0][1], matrix[1][1], matrix[2][1]])
    
    # Compute yaw (Z-axis rotation)
    yaw = math.atan2(forward[0], forward[2])

    # Compute pitch (X-axis rotation)
    pitch = math.asin(-forward[1])  # Up/down rotation

    # Compute roll (Y-axis rotation)
    roll = math.atan2(up[0], up[1])  # Side-to-side tilt

    return np.array([yaw, pitch, roll])  # Return rotations in radians1


def get_controller_orientation(matrix):
    """
    Extracts the front and bottom direction of the VR controller.
    
    Args:
        matrix (4x4 array): SteamVR transformation matrix.

    Returns:
        tuple: (front_vector, bottom_vector)
    """
    forward_vector = np.array([matrix[0][2], matrix[1][2], matrix[2][2]])  # Forward direction
    up_vector = np.array([matrix[0][1], matrix[1][1], matrix[2][1]])  # Up direction
    bottom_vector = -up_vector  # The bottom is opposite of the up vector

    return forward_vector, bottom_vector



def calculate_rotation_offset(controller_position, controller_direction, led_position):
    """
    Compute the yaw and pitch rotation offset needed to align the controller's aiming direction to the LED.

    Args:
        controller_position (np.array): The current position of the controller.
        controller_direction (np.array): The controller's forward direction.
        led_position (np.array): The position of the LED being aimed at.

    Returns:
        tuple: (offset_yaw, offset_pitch) in radians
    """
    # Compute the vector from the controller to the LED
    to_led_vector = led_position - controller_position
    to_led_vector /= np.linalg.norm(to_led_vector)  # Normalize

    # Compute yaw offset (horizontal rotation)
    yaw_controller = math.atan2(controller_direction[2], controller_direction[0])
    yaw_led = math.atan2(to_led_vector[2], to_led_vector[0])
    offset_yaw = yaw_led - yaw_controller  # How much we need to rotate horizontally

    # Compute pitch offset (vertical rotation)
    pitch_controller = math.asin(controller_direction[1])  # Up/down angle
    pitch_led = math.asin(to_led_vector[1])  # LED's vertical angle
    offset_pitch = pitch_led - pitch_controller  # How much we need to rotate up/down

    return offset_yaw, offset_pitch


def load_calibration_offset():
    """Load yaw, pitch, and roll offsets from calibration_data.json."""
    try:
        with open("calibration_data.json", "r") as f:
            data = json.load(f)
            return (
                data.get("offset_yaw", 0),  # Default to 0 if missing
                data.get("offset_pitch", 0),
                data.get("offset_roll", 0)
            )
    except (FileNotFoundError, KeyError):
        return 0, 0, 0  # Default to no rotation offset
    
def apply_rotation_offset(direction, offset_yaw, offset_pitch):
    """Apply yaw and pitch offsets to the aiming direction."""
    original_yaw = math.atan2(direction[2], direction[0])
    original_pitch = math.asin(direction[1])  # Up/down angle

    # Apply yaw and pitch offsets
    adjusted_yaw = original_yaw - offset_yaw
    adjusted_pitch = original_pitch - offset_pitch

    # Convert back to direction vector
    adjusted_direction = np.array([
        math.cos(adjusted_pitch) * math.cos(adjusted_yaw),  # X component
        math.sin(adjusted_pitch),  # Y component (vertical aim)
        math.cos(adjusted_pitch) * math.sin(adjusted_yaw)   # Z component
    ])

    return adjusted_direction


class Controller:
    def __init__(self, vr_system, device_index, color=(255, 255, 255)):
        """
        Represents a VR controller that can interact with LEDs.

        Args:
            vr_system (object): OpenVR system object.
            device_index (int): Index of the controller in VR tracking.
            color (tuple): Default RGB color for this controller.
        """
        self.vr_system = vr_system
        self.device_index = device_index
        self.color = color
        self.led_positions = {}

    def update_position(self):
        """Updates the controller's position and orientation in 3D space."""
        poses = self.vr_system.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
        )
        
        pose = poses[self.device_index]
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            self.position = extract_position(pose.mDeviceToAbsoluteTracking)
            self.direction = extract_orientation(pose.mDeviceToAbsoluteTracking)
        else:
            self.position = None
            self.direction = None

def update_leds(self, led_positions):
    """Determine which LEDs to light up based on the controller's adjusted aiming direction in 2D (XZ plane)."""
    if self.position is not None and self.direction is not None:
        # ✅ Load yaw offset but ignore pitch
        offset_yaw, _, _ = load_calibration_offset()
        
        # ✅ Apply rotation offset only to Yaw (XZ plane)
        adjusted_direction = apply_rotation_offset_2d(self.direction, offset_yaw)

        # ✅ Use only X and Z coordinates (ignore Y)
        controller_position_2d = np.array([self.position[0], self.position[2]])  # X, Z only
        adjusted_direction_2d = np.array([adjusted_direction[0], adjusted_direction[2]])  # X, Z only

        # ✅ Determine LEDs to light up based on adjusted aiming direction
        lit_leds = calculate_leds_to_light(controller_position_2d, adjusted_direction_2d, led_positions)

        for led in lit_leds:
            set_leds(led, self.color)  # Light up LEDs based on adjusted aim


    def update(self, led_positions):
        """Run all update functions in sequence."""
        self.update_position()
        self.update_leds(led_positions)
        
    def check_inputs(self):
        """Check button inputs to change color."""
        if is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger) and is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_Grip) and is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_ApplicationMenu):
            self.color = (255, 255, 255)  # White
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_Grip) and is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_ApplicationMenu):
            self.color = (255, 0, 255)  # Pink
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger) and is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_ApplicationMenu):
            self.color = (255, 255, 0)  # Yellow
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_Grip) and is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger):
            self.color = (0, 255, 255)  # Cyan
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_Grip):
            self.color = (0, 255, 0)  # Green
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_ApplicationMenu):
            self.color = (0, 0, 255)  # Blue
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger):
            self.color = (255, 0, 0)  # Red
    
    async def calibrate_hit_line(self):
        """Calibrate the aiming direction for the hit line using front vs. bottom detection."""
        print("Starting hit line calibration... Aim at LED 10 and pull the trigger.")

        led_positions = load_led_positions()
        if not led_positions:
            print("No LED mapping data available. Exiting calibration...")
            return
        
        reference_led = 10  # Fixed reference LED
        if str(reference_led) not in led_positions:
            print("LED 10 is not in the mapped positions. Exiting...")
            return

        led_position = np.array(led_positions[str(reference_led)])

        while True:
            self.update_position()

            if self.position is not None:
                # Extract the front and bottom vectors
                forward_vector, bottom_vector = get_controller_orientation(
                    self.vr_system.getDeviceToAbsoluteTrackingPose(
                        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
                    )[self.device_index].mDeviceToAbsoluteTracking
                )

                # Ensure we're using the front, not bottom
                if np.dot(forward_vector, bottom_vector) > 0:
                    print("⚠️ Warning: You may be aiming with the bottom of the controller. Flip the controller!")

                set_leds(reference_led, (255, 255, 255))  

                if is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger):
                    print("Calibration complete! Calculating offsets...")

                    # Compute yaw and pitch offset based on correct front orientation
                    offset_yaw, offset_pitch = calculate_rotation_offset(
                        np.array(self.position), forward_vector, led_position
                    )

                    # Save calibration data
                    calibration_data = {
                        "offset_yaw": offset_yaw,
                        "offset_pitch": offset_pitch
                    }

                    with open("calibration_data.json", "w") as f:
                        json.dump(calibration_data, f, indent=4)

                    print(f"Final Calibration Saved! Offsets (degrees): "
                        f"Yaw: {math.degrees(offset_yaw):.2f}, "
                        f"Pitch: {math.degrees(offset_pitch):.2f}")

                    set_leds(reference_led, (0, 0, 0))
                    break

            await asyncio.sleep(0.01)

