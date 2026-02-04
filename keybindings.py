import pygame
from pygame import Surface


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
        self._defaults: dict[str, int] = {"jump": pygame.K_UP, "slide": pygame.K_DOWN}

    def reset(self) -> None:
        self.jump = self._defaults["jump"]
        self.slide = self._defaults["slide"]

    def getKeyName(self, key: int) -> str:
        return pygame.key.name(key).upper()

    def getKeyIcon(self, key: int, size: int = 32) -> Surface | None:
        from keyicons import getKeyIcon
        return getKeyIcon(key, size)


keyBindings = KeyBindings()
