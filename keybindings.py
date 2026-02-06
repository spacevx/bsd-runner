from typing import TYPE_CHECKING

import pygame
from pygame import Surface

if TYPE_CHECKING:
    from entities.input.manager import GameAction


class KeyBindings:
    _instance: "KeyBindings | None" = None

    def __new__(cls) -> "KeyBindings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.jump: int = pygame.K_UP
        self.slide: int = pygame.K_DOWN
        self.shoot: int = pygame.K_x
        self.restart: int = pygame.K_r
        self._defaults: dict[str, int] = {"jump": pygame.K_UP, "slide": pygame.K_DOWN, "shoot": pygame.K_x, "restart": pygame.K_r}

    def reset(self) -> None:
        self.jump = self._defaults["jump"]
        self.slide = self._defaults["slide"]
        self.shoot = self._defaults["shoot"]
        self.restart = self._defaults["restart"]

    def getKeyName(self, key: int) -> str:
        return pygame.key.name(key).upper()

    def getKeyIcon(self, key: int, size: int = 32) -> Surface | None:
        from keyicons import getKeyIcon
        return getKeyIcon(key, size)

    def getActionForKey(self, key: int) -> "GameAction | None":
        from entities.input.manager import GameAction

        if key == self.jump:
            return GameAction.JUMP
        elif key == self.slide:
            return GameAction.SLIDE
        elif key == self.shoot:
            return GameAction.SHOOT
        elif key in (pygame.K_SPACE, pygame.K_z, pygame.K_w):
            return GameAction.JUMP
        elif key == pygame.K_s:
            return GameAction.SLIDE
        elif key == self.restart:
            return GameAction.RESTART
        elif key == pygame.K_ESCAPE:
            return GameAction.PAUSE
        elif key == pygame.K_RETURN:
            return GameAction.MENU_CONFIRM
        elif key == pygame.K_UP:
            return GameAction.MENU_UP
        elif key == pygame.K_DOWN:
            return GameAction.MENU_DOWN
        elif key == pygame.K_LEFT:
            return GameAction.MENU_LEFT
        elif key == pygame.K_RIGHT:
            return GameAction.MENU_RIGHT
        return None


keyBindings = KeyBindings()
