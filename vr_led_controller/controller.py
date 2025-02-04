import openvr
from led_manager import calculate_leds_to_light, set_leds
from helpers import extract_position, extract_orientation, is_button_pressed
import config

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

    def update_leds(self, led_positions):
        """Determine which LEDs to light up based on the controller's position and direction."""
        if self.position is not None and self.direction is not None:
            lit_leds = calculate_leds_to_light(self.position, self.direction, led_positions)
            for led in lit_leds:
                set_leds(led, self.color, fade_steps=60)  # Smooth transition


    def update(self, led_positions):
        """Run all update functions in sequence."""
        self.update_position()
        self.check_inputs()
        self.update_leds(led_positions)
