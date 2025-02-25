import openvr
from led_manager import calculate_leds_to_light, set_leds
from helpers import extract_position, extract_orientation, is_button_pressed,correct_yaw
from config import FADETIME,DEFAULT_COLOR

class Controller():
    def __init__(self, vr_system, device_index, color=DEFAULT_COLOR):
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

    def update_position(self, offset_distance=0.1):
        poses = self.vr_system.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
        )
        pose = poses[self.device_index]
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            self.position = extract_position(pose.mDeviceToAbsoluteTracking)
            # Extract the raw orientation from the controller's matrix.
            raw_orientation = extract_orientation(pose.mDeviceToAbsoluteTracking)
            # Correct only the yaw using our calibration helper.
            role = self.vr_system.getControllerRoleForTrackedDeviceIndex(self.device_index)
            if role == openvr.TrackedControllerRole_RightHand:
                self.direction = correct_yaw(raw_orientation,hand="right")  # Perform right-hand yaw adjustments
            elif role == openvr.TrackedControllerRole_LeftHand:
                self.direction = correct_yaw(raw_orientation,hand="left")  # Perform left-hand yaw adjustments
            else:
                self.direction = raw_orientation
            
            self.front_position = (
                self.position[0] + self.direction[0] * offset_distance,
                self.position[1] + self.direction[1] * offset_distance,
                self.position[2] + self.direction[2] * offset_distance,
            )
        else:
            self.position = None
            self.direction = None
            self.front_position = None



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
            
    def set_color_input(self):
        color_list = list(self.color)
        if is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_SteamVR_Trigger):
            color_list[0] += 1
            if color_list[0] > 255:
                color_list[0] = 0
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_Grip):
            color_list[1] += 1
            if color_list[1] > 255:
                color_list[1] = 0
        elif is_button_pressed(self.vr_system, self.device_index, openvr.k_EButton_ApplicationMenu):
            color_list[2] += 1
            if color_list[2] > 255:
                color_list[2] = 0
        print(f"Color Combo: Red:{color_list[0]}, Green:{color_list[1]}, Blue:{color_list[2]}")   
        self.color = tuple(color_list)

    def update_leds(self, led_positions):
        """Determine which LEDs to light up based on the controller's position and direction."""
        if self.position is not None and self.direction is not None:
            lit_leds = calculate_leds_to_light(self.position, self.direction, led_positions)
            for led in lit_leds:
                set_leds(led, self.color, fade_steps=FADETIME)  # Smooth transition


    def update(self, led_positions):
        """Run all update functions in sequence."""
        self.update_position()
        self.set_color_input()
        self.update_leds(led_positions)
