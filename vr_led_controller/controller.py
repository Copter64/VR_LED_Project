import json
import numpy as np
import openvr
from helpers import extract_position, extract_orientation, is_button_pressed
from led_manager import calculate_leds_to_light, set_leds
import config

CALIBRATION_FILE = "controller_calibration.json"

class Controller:
    def __init__(self, vr_system, device_index, color=(255, 255, 255)):
        self.vr_system = vr_system
        self.device_index = device_index
        self.color = color
        self.led_positions = {}
        self.calibration_offset = self.load_calibration_offset()

    def update_position(self):
        poses = self.vr_system.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
        )
        
        pose = poses[self.device_index]
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            self.position = extract_position(pose.mDeviceToAbsoluteTracking)
            raw_direction = extract_orientation(pose.mDeviceToAbsoluteTracking)

            # Apply calibration offset
            self.direction = raw_direction + self.calibration_offset
        else:
            self.position = None
            self.direction = None

    def check_inputs(self):
        if is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_Grip):
            self.color = (0, 255, 0)  # Green
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_ApplicationMenu):
            self.color = (0, 0, 255)  # Blue
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger):
            self.color = (255, 0, 0)  # Red

    def update_leds(self, led_positions):
        if self.position is not None and self.direction is not None:
            lit_leds = calculate_leds_to_light(self.position, self.direction, led_positions)
            for led in lit_leds:
                set_leds(led, self.color, fade_steps=240)

    def update(self, led_positions):
        self.update_position()
        self.check_inputs()
        self.update_leds(led_positions)

    def calibrate_direction(self, led_positions):
        """
        Calibration mode where the user selects a controller first,
        then points at the first LED and pulls the trigger again to set calibration.
        """
        print("Point at the first LED and pull the trigger again to calibrate direction.")

        first_led_index = min(led_positions.keys())
        first_led_position = np.array(led_positions[first_led_index])

        # Wait for the second trigger press
        while True:
            self.update_position()

            if self.position is None:
                continue

            if is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger):
                # Compute the offset between the controller's default direction and the corrected one
                corrected_direction = first_led_position - np.array(self.position)
                corrected_direction /= np.linalg.norm(corrected_direction)  # Normalize

                # Store the calibration offset
                self.calibration_offset = corrected_direction - extract_orientation(
                    self.vr_system.getDeviceToAbsoluteTrackingPose(
                        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
                    )[self.device_index].mDeviceToAbsoluteTracking
                )

                self.save_calibration_offset()
                print(f"Calibration complete for controller {self.device_index}. Offset saved.")
                break  # Exit after second trigger press




    def save_calibration_offset(self):
        """Save the calibration offset to a file."""
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        data[str(self.device_index)] = self.calibration_offset.tolist()

        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def load_calibration_offset(self):
        """Load the calibration offset from a file."""
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
                return np.array(data.get(str(self.device_index), [0, 0, 0]))  # Default: no offset
        except FileNotFoundError:
            return np.array([0, 0, 0])  # Default: no offset
