from enum import Enum, auto
from typing import Final

import pygame

from strings import windowTitle

width: Final[int] = 1920
height: Final[int] = 1080
minWidth: Final[int] = 640
minHeight: Final[int] = 480
fps: Final[int] = 60

title: Final[str] = windowTitle

displayFlags: Final[int] = pygame.RESIZABLE

Color = tuple[int, int, int]
ScreenSize = tuple[int, int]

black: Final[Color] = (0, 0, 0)
white: Final[Color] = (255, 255, 255)
red: Final[Color] = (200, 30, 30)
redBright: Final[Color] = (255, 50, 50)
gold: Final[Color] = (255, 215, 0)
darkGray: Final[Color] = (25, 25, 30)
darkGrayLight: Final[Color] = (40, 40, 50)


class GameState(Enum):
    MENU = auto()
    GAME = auto()
    OPTIONS = auto()
    QUIT = auto()


obstacleSpawnEvent: Final[int] = pygame.USEREVENT + 1
