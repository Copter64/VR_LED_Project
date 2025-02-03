import asyncio
import openvr
from config import current_color
from led_manager import load_led_positions, calculate_leds_to_light, set_leds, fps_loop_ddp, fade_leds
from vr_manager import map_led_positions
from helpers import extract_position, extract_orientation, is_button_pressed
from controller import Controller

async def main():
    """Main program to track multiple VR controllers independently."""
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

        print("Tracking controllers... Press Ctrl+C to stop.")

        # Start background tasks for LED updates
        asyncio.create_task(fps_loop_ddp(fps=60))
        asyncio.create_task(fade_leds(fade_delay=0.05))

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

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        openvr.shutdown()

if __name__ == "__main__":
    asyncio.run(main())