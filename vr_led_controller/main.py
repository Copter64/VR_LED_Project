import asyncio
import openvr
from config import current_color
from led_manager import load_led_positions, calculate_leds_to_light, set_leds, fps_loop_ddp, fade_leds
from vr_manager import map_led_positions
from helpers import extract_position, extract_orientation, is_button_pressed

async def main():
    """Main program to map LEDs and light them up based on controller position."""
    openvr.init(openvr.VRApplication_Scene)
    try:
        vr_system = openvr.VRSystem()
        print("Do you want to map LEDs or load an existing map? (map/load)")
        choice = input().strip().lower()

        if choice == "map":
            led_positions = await map_led_positions(vr_system)
        elif choice == "load":
            led_positions = load_led_positions()

            if not led_positions:
                print("No LED mapping data available. Exiting...")
                return
        else:
            print("Invalid choice. Exiting...")
            return

        print("Point your controller to light up LEDs. Press Ctrl+C to stop.")

        # Initialize current_color
        current_color = (255, 0, 100)  # Default color

        # Start FPS loop and fading logic
        asyncio.create_task(fps_loop_ddp(fps=60))
        asyncio.create_task(fade_leds(fade_delay=0.05))

        while True:
            poses = vr_system.getDeviceToAbsoluteTrackingPose(
                openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
            )

            for device_index, pose in enumerate(poses):
                if pose.bDeviceIsConnected and pose.bPoseIsValid:
                    device_class = vr_system.getTrackedDeviceClass(device_index)

                    if device_class == openvr.TrackedDeviceClass_Controller:
                        matrix = pose.mDeviceToAbsoluteTracking
                        position = extract_position(matrix)
                        direction = extract_orientation(matrix)

                        # Check for button presses to change color
                        if is_button_pressed(vr_system, device_index, openvr.k_EButton_Grip):
                            current_color = (0, 255, 0)  # Green
                        elif is_button_pressed(vr_system, device_index, openvr.k_EButton_ApplicationMenu):
                            current_color = (0, 0, 255)  # Blue
                        elif is_button_pressed(vr_system, device_index, openvr.k_EButton_SteamVR_Trigger):
                            current_color = (255, 0, 0)  # Red

                        # Calculate which LEDs to light up
                        lit_leds = calculate_leds_to_light(position, direction, led_positions)

                        # Update shared state with new LEDs
                        for led in lit_leds:
                            set_leds(led, current_color, fade_steps=20)

            await asyncio.sleep(0.01)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        openvr.shutdown()

if __name__ == "__main__":
    asyncio.run(main())