import os
import pygame

pygame.mixer.init()

# Get the directory of the current file (audio_manager.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Create the full path to the sounds folder (assuming it's in the same folder as battleship.py)
SOUNDS_FOLDER = os.path.join(BASE_DIR, "sounds")

def play_sound(file_path, volume=1.0):
    """Helper function to load and play a sound file."""
    try:
        sound = pygame.mixer.Sound(file_path)
        sound.set_volume(volume)
        sound.play()
    except Exception as e:
        print(f"Error playing sound {file_path}: {e}")

def play_hit_sound():
    play_sound(os.path.join(SOUNDS_FOLDER, "hit.wav"))

def play_miss_sound():
    play_sound(os.path.join(SOUNDS_FOLDER, "miss.wav"))


def play_sunk_sound(shiptype):
    if shiptype == "CARRIER":
        play_sound(os.path.join(SOUNDS_FOLDER, "carrier_sunk.wav"))
    if shiptype == "BATTLESHIP":
        play_sound(os.path.join(SOUNDS_FOLDER, "battleship_sunk.wav"))
    if shiptype == "CRUISER":
        play_sound(os.path.join(SOUNDS_FOLDER, "cruiser_sunk.wav"))
    if shiptype == "SUBMARINE":
        play_sound(os.path.join(SOUNDS_FOLDER, "submarine_sunk.wav"))
    if shiptype == "DESTROYER":
        play_sound(os.path.join(SOUNDS_FOLDER, "destroyer_sunk.wav"))
        

def play_turn_start(player_name):
    if player_name == "Player 1":
        play_sound(os.path.join(SOUNDS_FOLDER, "player1_fire.wav"))
    if player_name == "Player 2":
        play_sound(os.path.join(SOUNDS_FOLDER, "player2_fire.wav"))
    

def play_victory_sound(player_name):
    if player_name == "Player 1":
        play_sound(os.path.join(SOUNDS_FOLDER, "player1_victory.wav"))
    if player_name == "Player 2":
        play_sound(os.path.join(SOUNDS_FOLDER, "player2_victory.wav"))
