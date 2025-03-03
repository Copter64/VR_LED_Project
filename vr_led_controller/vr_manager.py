import openvr
import time
import json
from helpers import extract_position, is_button_pressed
from led_manager import set_leds
from config import NUM_LEDS, LED_MAPPING_FILE, ENABLE_DEBUG
import asyncio
from controller import Controller

async def vr_system_handler():
    """Initialize the OpenVR system and return the VR system object."""
    openvr.init(openvr.VRApplication_Overlay)
    vr_system = openvr.VRSystem()
    await asyncio.sleep(0)  # Allow other tasks to run
    return vr_system

async def map_led_positions(vr_system):
    """Map the physical positions of LEDs using the controller."""
    mapped_positions = {}
    current_led = 0
    debounce_time = 0.5  # Time (in seconds) to wait before allowing the next trigger press
    last_trigger_time = 0  # Tracks the last time the trigger was pressed

    print("Starting LED mapping...")
    print("Point at each LED and pull the trigger to save its position. Press Ctrl+C to exit.")

    try:
        while current_led < NUM_LEDS:
            # Light up only the current LED
            print(f"Lighting up LED {current_led} for mapping...")

            while True:

                poses = vr_system.getDeviceToAbsoluteTrackingPose(
                    openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
                )
                await asyncio.sleep(0)  # Allow other tasks to run
                set_leds(current_led, (255, 255, 255))  # White color for mapping


                for device_index, pose in enumerate(poses):
                    if pose.bDeviceIsConnected and pose.bPoseIsValid:
                        device_class = vr_system.getTrackedDeviceClass(device_index)

                        if device_class == openvr.TrackedDeviceClass_Controller:
                            matrix = pose.mDeviceToAbsoluteTracking
                            position = extract_position(matrix)

                            if ENABLE_DEBUG:
                                print(f"LED {current_led}: Controller Position: {position}")

                            # Check if the trigger is pressed and debounce
                            if is_button_pressed(vr_system, device_index, openvr.k_EButton_SteamVR_Trigger):
                                current_time = time.time()
                                if current_time - last_trigger_time > debounce_time:
                                    # Save position and move to next LED
                                    mapped_positions[current_led] = position
                                    print(f"Mapped LED {current_led} to position {position}")

                                    # Turn off the current LED
                                    set_leds(current_led, (0, 0, 0))  # Turn off the current LED

                                    # Move to the next LED
                                    current_led += 1
                                    last_trigger_time = current_time  # Update debounce timer
                                    break

                if current_led >= NUM_LEDS:
                    break

    except KeyboardInterrupt:
        print("Mapping interrupted. Saving progress...")

    # Save mapping to a file
    with open(LED_MAPPING_FILE, 'w') as f:
        json.dump(mapped_positions, f, indent=4)
    print("LED mapping saved.")
    return mapped_positions

async def vr_cursor_loop(vr_system, led_positions):
    """Display a cursor on the controller to indicate the current LED position."""
    print("Tracking controllers... Press Ctrl+C to stop.")

        # Initialize controllers dynamically
    controllers = []
    poses = vr_system.getDeviceToAbsoluteTrackingPose(
        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
    )

    for device_index, pose in enumerate(poses):
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            device_class = vr_system.getTrackedDeviceClass(device_index)
            if device_class == openvr.TrackedDeviceClass_Controller:
                controllers.append(Controller(vr_system, device_index))

    # Main loop to track all controllers
    while True:
        for controller in controllers:
            controller.update(led_positions)

        await asyncio.sleep(0.01)