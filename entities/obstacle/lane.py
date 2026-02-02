from pathlib import Path

import pygame
from pygame import Surface, Rect

from settings import Color
from paths import assetsPath
from .base import BaseObstacle, ObstacleType


class Obstacle(BaseObstacle):
    _texture: Surface | None = None
    _lowCache: Surface | None = None
    _highCache: Surface | None = None

    lowWidth: int = 120
    lowHeight: int = 100
    highWidth: int = 140
    highHeight: int = 110

    def __init__(self, x: int, groundY: int, obstacleType: ObstacleType) -> None:
        super().__init__()
        self.obstacleType = obstacleType

        self.image = self._getImage(obstacleType)
        y = groundY if obstacleType == ObstacleType.LOW else groundY - 60
        self.rect = self.image.get_rect(midbottom=(x, y))

    @classmethod
    def clearCache(cls) -> None:
        cls._texture = None
        cls._lowCache = None
        cls._highCache = None

    @classmethod
    def _loadTexture(cls) -> Surface | None:
        if cls._texture is None:
            try:
                path: Path = assetsPath / "lane.png"
                cls._texture = pygame.image.load(str(path)).convert_alpha()
            except (pygame.error, FileNotFoundError):
                cls._texture = None
        return cls._texture

    @classmethod
    def _getImage(cls, obstacleType: ObstacleType) -> Surface:
        return cls._getLowImage() if obstacleType == ObstacleType.LOW else cls._getHighImage()

    @classmethod
    def _createSurface(cls, w: int, h: int, bFlip: bool = False) -> Surface:
        surface = pygame.Surface((w, h), pygame.SRCALPHA)

        if (texture := cls._loadTexture()) is not None:
            tw, th = texture.get_width(), texture.get_height()
            scale = min(w / tw, h / th) * 0.95
            sw, sh = int(tw * scale), int(th * scale)

            scaled = pygame.transform.smoothscale(texture, (sw, sh))
            if bFlip:
                scaled = pygame.transform.flip(scaled, False, True)

            surface.blit(scaled, ((w - sw) // 2, (h - sh) // 2))
        else:
            surface = cls._createFallback(w, h, bFlip)

        return surface

    @classmethod
    def _getLowImage(cls) -> Surface:
        if cls._lowCache is None:
            cls._lowCache = cls._createSurface(cls.lowWidth, cls.lowHeight, bFlip=False)
        return cls._lowCache

    @classmethod
    def _getHighImage(cls) -> Surface:
        if cls._highCache is None:
            cls._highCache = cls._createSurface(cls.highWidth, cls.highHeight, bFlip=True)
        return cls._highCache

    @classmethod
    def _createFallback(cls, w: int, h: int, bFlip: bool) -> Surface:
        surface = pygame.Surface((w, h), pygame.SRCALPHA)

        if not bFlip:
            wood: Color = (139, 90, 43)
            darkWood: Color = (101, 67, 33)
            pygame.draw.rect(surface, wood, (10, 10, w - 20, h - 20))
            pygame.draw.rect(surface, darkWood, (10, 10, w - 20, h - 20), 4)
            pygame.draw.rect(surface, darkWood, (0, h - 20, 20, 20))
            pygame.draw.rect(surface, darkWood, (w - 20, h - 20, 20, 20))
        else:
            metal: Color = (150, 150, 160)
            darkMetal: Color = (100, 100, 110)
            pygame.draw.rect(surface, metal, (10, 10, w - 20, h - 20))
            pygame.draw.rect(surface, darkMetal, (10, 10, w - 20, h - 20), 4)
            pygame.draw.rect(surface, darkMetal, (0, 0, 20, 20))
            pygame.draw.rect(surface, darkMetal, (w - 20, 0, 20, 20))

        return surface

    def get_hitbox(self) -> Rect:
        return self.rect.inflate(-20, -15)
