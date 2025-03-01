from controller import Controller
from led_manager import load_led_positions, fps_loop_ddp, fade_leds
from helpers import extract_position, extract_orientation, is_button_pressed
from dataclasses import dataclass
from enum import Enum

#Initial Game setup
#Cursor Class? - Where the player is pointing
def cursor():
    Controller().update_position()
    Controller().check_inputs()

@dataclass
class Color():
    red: int
    green: int
    blue: int
    
    def to_tuple(self):
        return (self.red, self.green, self.blue)

        
class ShipType(Enum):
    CARRIER = "Carrier"
    BATTLESHIP = "Battleship"
    SUBMARINE = "Submarine"

    
@dataclass(init=True)
class Ship():
    shiptype: ShipType
    placement: int = 0
    hits: int = 0
    
    def __post_init__(self):
        if self.shiptype == ShipType.CARRIER:
            self.hits = 5
        if self.shiptype == ShipType.BATTLESHIP:
            self.hits = 4
        if self.shiptype == ShipType.SUBMARINE:
            self.hits = 3
    

@dataclass
class Player():
    name: str = ""
    score: int = 0
    ships: list[Ship] = []
    color: Color = Color(100,100,0)



    #Player 1 Settings - background color and audio?
    #Player 2 settings - background color and audio?
 #Game async function - Contains the game loop and logic
@dataclass
class GameManger():
    inprogress: bool = False
    
    def start_game(self):
        #Starts the game
        pass
    
    def end_game(self):
        #Ends the game
        pass
    
    def wait_for_input(self):
        #Waits for player input
        pass
    
def main():
    #Main function to run the game
    manager = GameManger()
    manager.start_game()

    while manager.inprogress:
        try:
            cursor()
        except Exception as ex:
            print(ex)
        
    manager.end_game()
    
if __name__ == "__main__":
    main()
    # main()
    