from enum import Enum, auto

WIDTH = 800
HEIGHT = 600
FPS = 60

from strings import WINDOW_TITLE
TITLE = WINDOW_TITLE

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (200, 30, 30)
RED_BRIGHT = (255, 50, 50)
GOLD = (255, 215, 0)
DARK_GRAY = (25, 25, 30)
DARK_GRAY_LIGHT = (40, 40, 50)


class GameState(Enum):
    MENU = auto()
    GAME = auto()
    OPTIONS = auto()
    QUIT = auto()
