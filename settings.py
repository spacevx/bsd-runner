from enum import Enum, auto
from typing import Final

import pygame

from strings import WINDOW_TITLE

WIDTH: Final[int] = 1920
HEIGHT: Final[int] = 1080
MIN_WIDTH: Final[int] = 640
MIN_HEIGHT: Final[int] = 480
FPS: Final[int] = 60

TITLE: Final[str] = WINDOW_TITLE

DISPLAY_FLAGS: Final[int] = pygame.RESIZABLE

Color = tuple[int, int, int]
ScreenSize = tuple[int, int]

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


OBSTACLE_SPAWN_EVENT: Final[int] = pygame.USEREVENT + 1
