import asyncio
import openvr
# from config import current_color
from led_manager import load_led_positions, fps_loop_ddp, fade_leds
from vr_manager import map_led_positions
# from helpers import extract_position, extract_orientation, is_button_pressed
from controller import Controller
from helpers import get_tracked_controllers


async def main():
    """Main program to track multiple VR controllers independently."""
    openvr.init(openvr.VRApplication_Scene)
        
    try:
        vr_system = openvr.VRSystem()
        
        print("Starting fps_loop_ddp...")
        asyncio.create_task(fps_loop_ddp(fps=60))
        asyncio.create_task(fade_leds(fade_delay=0.05))
        # Start background tasks for LED updates
        print("LED update tasks created.")
        
        print("What would you like to do: \n1. Startup Main Application\n2. Map LED Positions\n3. Calibrate Controller Direction")
        choice = input().strip().lower()
        
        if choice == "1":
            led_positions = load_led_positions()
            if not led_positions:
                print("No LED mapping data available. Exiting...")
                return
        elif choice == "2":
            led_positions = await map_led_positions(vr_system)
            return
        elif choice == "3":
            # Create controllers before calibration
            controllers = [
                Controller(vr_system, device_index)
                for device_index, _ in get_tracked_controllers(vr_system)
            ]
            # Assume using first controller for calibration
            if controllers:
                controller = controllers[0]  # Pick first controller
                await controller.calibrate_hit_line()
            else:
                print("No VR controllers detected. Cannot calibrate.")
            return
        else:
            print("Invalid choice. Exiting...")
            return

        print("Tracking controllers... Press Ctrl+C to stop.")

        # Initialize controllers dynamically
        controllers = [
            Controller(vr_system, device_index)
            for device_index, _ in get_tracked_controllers(vr_system)
        ]

        # Main loop to track all controllers
        while True:
            for controller in controllers:
                controller.update(led_positions)

            await asyncio.sleep(0.01)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # openvr.shutdown()
        print("VR system shut down.")

if __name__ == "__main__":
    asyncio.run(main())