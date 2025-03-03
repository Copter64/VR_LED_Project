import asyncio
# from config import current_color
from led_manager import load_led_positions, fps_loop_ddp, fade_leds
from vr_manager import map_led_positions, vr_cursor_loop, vr_system_handler
# from helpers import extract_position, extract_orientation, is_button_pressed



async def main():
        
    try:
        
        vr_system = await vr_system_handler()
        led_positions = {}
        
        asyncio.create_task(fps_loop_ddp(fps=60))
        asyncio.create_task(fade_leds(fade_delay=0.05))
        # Start background tasks for LED updates and fading
        
        print("Do you want to map LEDs or load an existing map? (map/load)")
        choice = input().strip().lower()

        if choice == "map":
            led_positions = await map_led_positions(vr_system)
        elif choice == "load":
            led_positions = load_led_positions()
            if not led_positions:
                print("No LED mapping data available. Exiting...")
                return
            await vr_cursor_loop(vr_system, led_positions)
        else:
            print("Invalid choice. Exiting...")
            return


    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # openvr.shutdown()
        print("VR system shut down.")

if __name__ == "__main__":
    asyncio.run(main())