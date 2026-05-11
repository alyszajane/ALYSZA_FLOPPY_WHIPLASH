"""constant variable in the game
"""

from os.path import join
import pygame
from tools import Tools

pygame.init()
clock = pygame.time.Clock()


display_info = pygame.display.Info()
WINDOW_WIDTH, WINDOW_HEIGHT = display_info.current_w, display_info.current_h
FLOOR_HEIGHT = 145
BEST_SCORE = 0
PIPE_GAP = 200
MAINMENU_ACTIVE = True
GAME_TICK = 30

WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption('Flappy Bird')

toolkit = Tools(WINDOW, join('data', 'sprites.png'))
world, bird_images, messages, buttons, numbers_img, scoreboard_img, icon = toolkit.load_images()
pygame.display.set_icon(icon)

# Load ribbon image for trail effect
try:
    ribbon_image = pygame.image.load(join('data', 'ribbon.png')).convert_alpha()
except FileNotFoundError:
    print("Warning: ribbon.png not found. Trail effect disabled.")
    ribbon_image = None

