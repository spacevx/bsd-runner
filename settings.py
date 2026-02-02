from enum import Enum, auto
from typing import Final

from strings import WINDOW_TITLE

WIDTH: Final[int] = 800
HEIGHT: Final[int] = 600
FPS: Final[int] = 60

TITLE: Final[str] = WINDOW_TITLE

Color = tuple[int, int, int]

BLACK: Final[Color] = (0, 0, 0)
WHITE: Final[Color] = (255, 255, 255)
RED: Final[Color] = (200, 30, 30)
RED_BRIGHT: Final[Color] = (255, 50, 50)
GOLD: Final[Color] = (255, 215, 0)
DARK_GRAY: Final[Color] = (25, 25, 30)
DARK_GRAY_LIGHT: Final[Color] = (40, 40, 50)


class GameState(Enum):
    MENU = auto()
    GAME = auto()
    OPTIONS = auto()
    QUIT = auto()
