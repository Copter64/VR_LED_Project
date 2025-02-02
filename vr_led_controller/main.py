import asyncio
import openvr
import config
from led_manager import load_led_positions, calculate_leds_to_light, set_leds, fps_loop_ddp, fade_leds
from vr_manager import map_led_positions
from helpers import extract_position, extract_orientation, is_button_pressed
from controller import Controller
import time

async def main():
    """Main program to track multiple VR controllers independently with calibration mode."""
    openvr.init(openvr.VRApplication_Scene)

    try:
        vr_system = openvr.VRSystem()
        print("Do you want to map LEDs, load an existing map, or calibrate controllers? (map/load/calibrate)")
        choice = input().strip().lower()

        if choice == "map":
            led_positions = await map_led_positions(vr_system)
        elif choice in ["load", "calibrate"]:
            led_positions = load_led_positions()
            if not led_positions:
                print("No LED mapping data available. Exiting...")
                return
        else:
            print("Invalid choice. Exiting...")
            return

        # ✅ Start background tasks before calibration
        asyncio.create_task(fps_loop_ddp(fps=60))
        asyncio.create_task(fade_leds(fade_delay=0.05))
        await asyncio.sleep(0.1)  # Give tasks a moment to start

        controllers = []
        poses = vr_system.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
        )

        for device_index, pose in enumerate(poses):
            if pose.bDeviceIsConnected and pose.bPoseIsValid:
                device_class = vr_system.getTrackedDeviceClass(device_index)
                if device_class == openvr.TrackedDeviceClass_Controller:
                    controllers.append(Controller(vr_system, device_index))

        if choice == "calibrate":
            first_led_index = min(led_positions.keys())
            set_leds(first_led_index, (255, 255, 255))  # Light up LED 1 for calibration

            print("Press the trigger on the controller you want to calibrate.")
            selected_controller = None

            while selected_controller is None:
                for controller in controllers:
                    if is_button_pressed(controller.vr_system, controller.device_index, openvr.k_EButton_SteamVR_Trigger):
                        selected_controller = controller
                        print(f"Controller {controller.device_index} selected for calibration.")
                        break

            selected_controller.calibrate_direction(led_positions)

            # Turn off LED 1 after calibration
            set_leds(first_led_index, (0, 0, 0))
            return  # Exit calibration mode after one controller is calibrated

        print("Tracking controllers... Press Ctrl+C to stop.")

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
    
    # led_positions = load_led_positions()
    # first_led_index = min(led_positions.keys())
    # set_leds(first_led_index, (255, 255, 255))
    # print(set_leds(first_led_index, (255, 255, 255)))