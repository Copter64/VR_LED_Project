import asyncio
import openvr
import random
import audio_manager
from dataclasses import dataclass, field
from enum import Enum
from controller import Controller
from led_manager import (
    load_led_positions, 
    set_leds, 
    create_ddp_packet, 
    calculate_leds_to_light, 
    led_state
)
from helpers import is_button_pressed
from vr_manager import vr_system_handler
from config import NUM_LEDS, WLED_IP

# Global variables to hold the current cursor LED indices, the ship length during placement,
# and a frozen target for a fired shot.
cursor_leds = []
current_ship_length = None  # Set when a ship is being placed
frozen_target = None      # Set when a shot is fired to freeze the dynamic cursor
animation_active = False    # Global flag to indicate an animation is active.

# ---------- Game Data Structures ----------

class ShipType(Enum):
    CARRIER = "Carrier"
    BATTLESHIP = "Battleship"
    SUBMARINE = "Submarine"

@dataclass
class Color:
    red: int
    green: int
    blue: int

    def to_tuple(self):
        return (self.red, self.green, self.blue)

@dataclass
class Ship:
    shiptype: ShipType
    length: int = 0
    remaining: int = 0
    positions: list = field(default_factory=list)  # List of board cell indexes

    def __post_init__(self):
        
        if self.shiptype == ShipType.CARRIER:
            self.length = 6
        elif self.shiptype == ShipType.BATTLESHIP:
            self.length = 4
        elif self.shiptype == ShipType.SUBMARINE:
            self.length = 3
        self.remaining = self.length

@dataclass
class Player:
    name: str
    board: object = None  # Will be assigned a Board instance
    ships: list = field(default_factory=list)
    color: Color = field(default_factory=lambda: Color(0, 0, 255))  # Blue background

    def get_game_state(self):
        """
        Returns a dictionary representing the player's game state:
          - 'ships': mapping of ship type to the list of cell indexes where that ship is placed.
          - 'board': the board grid (with 'empty', 'ship', 'hit', or 'miss').
        """
        return {
            "ships": {ship.shiptype.value: ship.positions for ship in self.ships},
            "board": self.board.grid
        }

# ---------- Board Class for a 1D Game (Full LED Perimeter) ----------

class Board:
    def __init__(self, player_number, size):
        self.size = size  # Number of cells equals NUM_LEDS
        self.grid = ['empty'] * size  # Each cell: 'empty', 'ship', 'hit', or 'miss'
        self.ship_cells = {}  # Mapping from cell index to the Ship object
        self.player_number = player_number

    def can_place_ship(self, ship, start_index, orientation):
        if orientation == 'R':
            if start_index + ship.length > self.size:
                return False
            for i in range(start_index, start_index + ship.length):
                if self.grid[i] != 'empty':
                    return False
        else:  # orientation 'L'
            if start_index - ship.length + 1 < 0:
                return False
            for i in range(start_index - ship.length + 1, start_index + 1):
                if self.grid[i] != 'empty':
                    return False
        return True

    def place_ship(self, ship, start_index, orientation):
        if orientation == 'R':
            cells = list(range(start_index, start_index + ship.length))
        else:
            cells = list(range(start_index, start_index - ship.length, -1))
        for cell in cells:
            self.grid[cell] = 'ship'
            self.ship_cells[cell] = ship
        ship.positions = cells

    def receive_shot(self, cell_index):
        if self.grid[cell_index] in ['hit', 'miss', 'sunk']:
            return 'already'
        if self.grid[cell_index] == 'ship':
            self.grid[cell_index] = 'hit'
            ship = self.ship_cells.get(cell_index)
            if ship:
                ship.remaining -= 1
                if ship.remaining == 0:
                    for pos in ship.positions:
                        self.grid[pos] = 'sunk'
                    return 'sunk'
                return 'hit'
        else:
            self.grid[cell_index] = 'miss'
            return 'miss'

    def all_ships_sunk(self):
        return all(cell != 'ship' for cell in self.grid)

# ---------- VR Input Helper Functions ----------

async def wait_for_trigger(vr_system):
    """Wait until any connected controller has the trigger pressed."""
    while True:
        poses = vr_system.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
        )
        for device_index, pose in enumerate(poses):
            if pose.bDeviceIsConnected and pose.bPoseIsValid:
                if is_button_pressed(vr_system, device_index, openvr.k_EButton_SteamVR_Trigger):
                    return
        await asyncio.sleep(0.1)

async def get_ship_placement(vr_system, led_positions, valid_led_set):
    """
    Wait for the player to aim at a valid board cell and pull the trigger.
    Returns a tuple: (led_index, orientation)
    Orientation is 'R' (ship placed rightward) or 'L' (if grip held, placed leftward).
    Uses the LED indexes directly.
    """
    # Create Controller objects for all connected controllers.
    controllers = []
    poses = vr_system.getDeviceToAbsoluteTrackingPose(
        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
    )
    for device_index, pose in enumerate(poses):
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            if vr_system.getTrackedDeviceClass(device_index) == openvr.TrackedDeviceClass_Controller:
                controllers.append(Controller(vr_system, device_index))
                
    while True:
        for controller in controllers:
            controller.update_position()  # This applies the corrected yaw
            if controller.position is not None and controller.direction is not None:
                if is_button_pressed(controller.vr_system, controller.device_index, openvr.k_EButton_SteamVR_Trigger):
                    for led in calculate_leds_to_light(controller.position, controller.direction, led_positions):
                        if led in valid_led_set:
                            orientation = (
                                'L' if is_button_pressed(controller.vr_system, controller.device_index, openvr.k_EButton_Grip)
                                else 'R'
                            )
                            return led, orientation
        await asyncio.sleep(0.1)

async def get_fire_target(vr_system, led_positions, valid_led_set):
    """
    Wait for the player to aim at a valid opponent board cell and pull the trigger.
    Returns the LED index directly.
    """
    # Create Controller objects for all connected controllers.
    controllers = []
    poses = vr_system.getDeviceToAbsoluteTrackingPose(
        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
    )
    for device_index, pose in enumerate(poses):
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            if vr_system.getTrackedDeviceClass(device_index) == openvr.TrackedDeviceClass_Controller:
                controllers.append(Controller(vr_system, device_index))
                
    while True:
        for controller in controllers:
            controller.update_position()  # Ensure corrected yaw is applied
            if controller.position is not None and controller.direction is not None:
                if is_button_pressed(controller.vr_system, controller.device_index, openvr.k_EButton_SteamVR_Trigger):
                    for led in calculate_leds_to_light(controller.position, controller.direction, led_positions):
                        if led in valid_led_set:
                            return led
        await asyncio.sleep(0.1)

# ---------- Merged Display Update Functions ----------

async def animate_victory(board_size, duration_flash=0.5, duration_confetti=3.0, flash_color=(255, 255, 255), confetti_colors=None, steps=30):
    """
    Animate a victory sequence with a quick flash followed by a confetti effect.
    
    Args:
        board_size (int): Total number of LED cells.
        duration_flash (float): Duration of the flash effect in seconds.
        duration_confetti (float): Duration of the confetti effect in seconds.
        flash_color (tuple): RGB color for the flash.
        confetti_colors (list): List of RGB tuples to use for the confetti effect.
        steps (int): Number of animation steps for the confetti effect.
    """
    global animation_active
    if confetti_colors is None:
        confetti_colors = [
            (255, 0, 0),     # Red
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (255, 255, 0),   # Yellow
            (255, 0, 255),   # Magenta
            (0, 255, 255)    # Cyan
        ]
    
    animation_active = True

    # --- Flash Effect ---
    # Set all LEDs to the flash_color.
    for led in range(board_size):
        led_state[led] = [*flash_color, 0]
    await asyncio.sleep(duration_flash)

    # --- Confetti Effect ---
    confetti_step_delay = duration_confetti / steps
    for _ in range(steps):
        for led in range(board_size):
            # Randomly choose one of the confetti colors.
            color = random.choice(confetti_colors)
            led_state[led] = [*color, 0]
        await asyncio.sleep(confetti_step_delay)

    # Clear the animation flag so that normal display resumes.
    animation_active = False

async def animate_sunk_ship(ship_positions, board_size, duration=2.0, steps=20):
    """
    Animate a sunk ship with an explosion at ship_positions and an outward shockwave.
    """
    global animation_active
    animation_active = True
    step_delay = duration / steps
    for step in range(steps):
        # Calculate your shockwave effect here, updating led_state based on the distance from ship_positions.
        # For example, you might fade the color as the shockwave travels outwards.
        for led in range(board_size):
            # Compute a simple effect (customize as needed)
            min_dist = min(abs(led - pos) for pos in ship_positions)
            if min_dist <= step * (board_size // steps):
                brightness = max(0, 1.0 - (min_dist / (step * (board_size // steps) + 1)))
                # Update led_state[led] with your chosen explosion/shockwave color scaled by brightness.
                led_state[led] = [int(255 * brightness), int(255 * brightness), 0, 0]
        await asyncio.sleep(step_delay)
    animation_active = False

async def animate_hit_effect(cell_index, base_color=(255, 100, 20), duration=0.3, steps=5):
    """
    Briefly animates a hit effect on the target LED.
    
    Args:
        cell_index (int): LED index where the hit occurred.
        base_color (tuple): The base RGB color for the hit (default: warm orange).
        duration (float): Total duration of the animation in seconds.
        steps (int): Number of steps in the fade-out effect.
    """
    step_delay = duration / steps
    # Save the original state if needed (or simply use black/off for revert)
    for step in range(steps):
        factor = 1.0 - (step / steps)  # Fades from full color to off
        new_color = [int(base_color[i] * factor) for i in range(3)]
        led_state[cell_index] = [*new_color, 0]
        await asyncio.sleep(step_delay)
    # Optionally, clear the LED after animation
    led_state[cell_index] = [0, 0, 0, 0]

async def animate_miss_effect(cell_index, base_color=(255, 255, 255), duration=0.3, steps=5):
    """
    Briefly animates a miss effect on the target LED.
    
    Args:
        cell_index (int): LED index where the miss occurred.
        base_color (tuple): The base RGB color for the miss (default: white).
        duration (float): Total duration of the animation in seconds.
        steps (int): Number of steps in the fade-out effect.
    """
    step_delay = duration / steps
    for step in range(steps):
        factor = 1.0 - (step / steps)
        new_color = [int(base_color[i] * factor) for i in range(3)]
        led_state[cell_index] = [*new_color, 0]
        await asyncio.sleep(step_delay)
    led_state[cell_index] = [0, 0, 0, 0]

def update_display(game_manager):
    """
    Merges the status display and cursor updates:
      - For each cell in the target board (opponent’s board), map:
          * 'sunk' cells to red,
          * 'hit' cells (non-sunk) to warm white (255,200,150),
          * 'miss' cells to white,
          * and otherwise blue.
      - Then overlay the current cursor positions in yellow.
    Uses LED indexes directly.
    """
    board = game_manager.opponent.board
    for i in range(game_manager.board_size):
        status = board.grid[i]
        if status == 'sunk':
            color = (255, 0, 0)
        elif status == 'hit':
            color = (255, 100, 20)
        elif status == 'miss':
            color = (150, 255, 255)
        else:
            color = game_manager.opponent.color.to_tuple()  # Use the opponent's background color
        led_state[i] = [*color, 0]
    # Overlay the dynamic cursor if no target is frozen.
    global frozen_target
    if frozen_target is None:
        for led in cursor_leds:
            if isinstance(led, list):
                for cell in led:
                    if cell in range(game_manager.board_size):
                        led_state[cell] = [255, 255, 0, 0]
            else:
                if led in range(game_manager.board_size):
                    led_state[led] = [255, 255, 0, 0]

async def merged_ddp_loop(vr_system, led_positions, game_manager, fps=60):
    """
    Merged DDP loop that sends the updated LED state as DDP packets.
    """

    import socket
    udp_ip = WLED_IP
    udp_port = 4048
    delay = 1 / fps
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        if not animation_active:
            update_display(game_manager)
        pixel_data = bytearray()
        for i in range(NUM_LEDS):
            if i in led_state:
                r, g, b, _ = led_state[i]
                pixel_data.extend([r, g, b])
            else:
                pixel_data.extend([0, 0, 0])
        ddp_packet = create_ddp_packet(pixel_data)
        sock.sendto(ddp_packet, (udp_ip, udp_port))
        await asyncio.sleep(delay)

async def update_cursor_loop(vr_system, led_positions, valid_leds):
    """
    Continuously updates the global cursor_leds variable using Controller objects.
    When a ship is being placed (current_ship_length is set), the cursor expands to cover the ship's footprint.
    Otherwise, it returns a single LED index per controller.
    If a shot has been fired (frozen_target is set), dynamic updates are frozen.
    Uses LED indexes directly.
    """
    global current_ship_length, frozen_target
    controllers = []
    poses = vr_system.getDeviceToAbsoluteTrackingPose(
        openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount
    )
    for device_index, pose in enumerate(poses):
        if pose.bDeviceIsConnected and pose.bPoseIsValid:
            if vr_system.getTrackedDeviceClass(device_index) == openvr.TrackedDeviceClass_Controller:
                controllers.append(Controller(vr_system, device_index))
    while True:
        if frozen_target is not None:
            await asyncio.sleep(0.01)
            continue
        new_cursor_leds = []
        for controller in controllers:
            controller.update(led_positions)
            if controller.position is not None and controller.direction is not None:
                candidates = calculate_leds_to_light(controller.position, controller.direction, led_positions)
                if candidates:
                    start = candidates[0]
                    if current_ship_length is not None:
                        orientation = (
                            'L' if is_button_pressed(controller.vr_system, controller.device_index, openvr.k_EButton_Grip)
                            else 'R'
                        )
                        if orientation == 'R':
                            candidate_range = list(range(start, start + current_ship_length))
                        else:
                            candidate_range = list(range(start, start - current_ship_length, -1))
                        new_cursor_leds.append(candidate_range)
                    else:
                        new_cursor_leds.append(start)
        global cursor_leds
        cursor_leds = new_cursor_leds
        await asyncio.sleep(0.01)

# ---------- Game Manager ----------

class GameManager:
    def __init__(self, vr_system, led_positions, board_size):
        self.vr_system = vr_system
        self.led_positions = led_positions
        self.board_size = board_size
        self.player1 = Player(name="Player 1", board=Board(1, board_size), color=Color(50, 0, 255))
        self.player2 = Player(name="Player 2", board=Board(2, board_size), color=Color(0, 50, 255))
        self.current_player = self.player1
        self.opponent = self.player2
        self.inprogress = False
        self.ship_types = [ShipType.CARRIER, ShipType.BATTLESHIP, ShipType.SUBMARINE]

    def switch_turn(self):
        global frozen_target
        frozen_target = None
        if self.current_player == self.player1:
            self.current_player = self.player2
            self.opponent = self.player1
        else:
            self.current_player = self.player1
            self.opponent = self.player2

    async def place_ships(self):
        """
        Each player places their ships on the full LED perimeter.
        Instruct the non-active player to look away.
        The full ship size is previewed in green.
        Button events are sent directly to the game functions.
        """
        global current_ship_length
        valid_leds = set(range(self.board_size))
        for player in [self.player1, self.player2]:
            print(f"\n{player.name}, it's time to place your ships.")
            print("Make sure your opponent is not watching. When ready, press the trigger to begin.")
            await wait_for_trigger(self.vr_system)
            for led in valid_leds:
                set_leds(led, (0, 255, 100))
            await asyncio.sleep(1)
            for ship_type in self.ship_types:
                ship = Ship(shiptype=ship_type)
                current_ship_length = ship.length
                placed = False
                while not placed:
                    print(f"{player.name}: Place your {ship_type.value} (length {ship.length}).")
                    print("Aim at the starting cell and pull the trigger. Hold the grip button to place leftward; otherwise rightward.")
                    led, orientation = await get_ship_placement(self.vr_system, self.led_positions, valid_leds)
                    cell = led
                    candidate_cells = (list(range(cell, cell + ship.length))
                                       if orientation == 'R'
                                       else list(range(cell, cell - ship.length, -1)))
                    if player.board.can_place_ship(ship, cell, orientation):
                        for c in candidate_cells:
                            set_leds(c, (0, 255, 0))
                        await asyncio.sleep(1)
                        player.board.place_ship(ship, cell, orientation)
                        player.ships.append(ship)
                        print(f"{ship_type.value} placed at cell {cell} going {'left' if orientation=='L' else 'right'}.")
                        placed = True
                    else:
                        print("Invalid placement (out of bounds or overlapping). Try again.")
                    await asyncio.sleep(0.5)
                current_ship_length = None
            print(f"{player.name}, your ships have been placed. Keep them secret!")
            await asyncio.sleep(2)
            for led in valid_leds:
                set_leds(led, (0, 0, 255))
            print("Switch players now...\n")
            await asyncio.sleep(3)

    async def game_loop(self):
        global frozen_target
        valid_leds = set(range(self.board_size))
        while self.inprogress:
            print(f"{self.current_player.name}'s turn to fire. Aim and pull the trigger.")
            audio_manager.play_turn_start(self.current_player.name)  # Turn start sound
            
            target_led = await get_fire_target(self.vr_system, self.led_positions, valid_leds)
            cell = target_led
            result = self.opponent.board.receive_shot(cell)
            frozen_target = cell
            if result in ['hit', 'sunk']:
                color = (255, 0, 0) if result == 'sunk' else (255, 100, 20)
                set_leds(target_led, color)
                print(f"Hit at cell {cell}!")
                audio_manager.play_hit_sound()
                if result == 'hit':
                    await animate_hit_effect(target_led)
                if result == 'sunk':
                    print("Ship sunk!")
                    audio_manager.play_sunk_sound()
                    ship = self.opponent.board.ship_cells.get(cell)
                    if ship:
                        await animate_sunk_ship(ship.positions, self.board_size)
                await asyncio.sleep(2)
            elif result == 'miss':
                set_leds(target_led, (255, 255, 255))
                print(f"Miss at cell {cell}.")
                audio_manager.play_miss_sound()
                await animate_miss_effect(target_led)
                await asyncio.sleep(2)
            elif result == 'already':
                print("Already fired on that cell. Try again.")
                frozen_target = None
                await asyncio.sleep(.5)
                continue
            if self.opponent.board.all_ships_sunk():
                print(f"\n{self.current_player.name} wins! All enemy ships have been sunk.")
                audio_manager.play_victory_sound(self.current_player.name)
                await animate_victory(self.board_size)
                self.inprogress = False
                break
            self.switch_turn()
            await asyncio.sleep(1)


    def start_game(self):
        self.inprogress = True

    def end_game(self):
        self.inprogress = False
        print("Game over.")
        print(f"{self.player1.name} state: {self.player1.get_game_state()}")
        print(f"{self.player2.name} state: {self.player2.get_game_state()}")

    async def run(self):
        await self.place_ships()
        await self.game_loop()
        self.end_game()

# ---------- Main Function ----------

async def main():
    vr_system = await vr_system_handler()
    led_positions = load_led_positions()
    if not led_positions:
        print("No LED mapping data available. Exiting...")
        return
    board_size = NUM_LEDS
    game = GameManager(vr_system, led_positions, board_size)
    game.start_game()
    asyncio.create_task(merged_ddp_loop(vr_system, led_positions, game, fps=90))
    asyncio.create_task(update_cursor_loop(vr_system, led_positions, set(range(board_size))))
    await game.run()

if __name__ == "__main__":
    input("Please start SteamVR and press Enter to continue...")
    asyncio.run(main())
