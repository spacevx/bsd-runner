from pathlib import Path

import pygame
from pygame import Surface, Rect

from settings import Color
from paths import assetsPath
from .base import BaseObstacle


class Obstacle(BaseObstacle):
    _texture: Surface | None = None
    _cache: Surface | None = None

    bodyWidth: int = 150
    bodyHeight: int = 50

    def __init__(self, x: int, groundY: int) -> None:
        super().__init__()
        self.image = self._getImage()
        self.rect = self.image.get_rect(midbottom=(x, groundY))

    @classmethod
    def clearCache(cls) -> None:
        cls._texture = None
        cls._cache = None

    @classmethod
    def _loadTexture(cls) -> Surface | None:
        if cls._texture is None:
            try:
                path: Path = assetsPath / "obstacles" / "bodies" / "body.png"
                cls._texture = pygame.image.load(str(path)).convert_alpha()
            except (pygame.error, FileNotFoundError):
                cls._texture = None
        return cls._texture

    @classmethod
    def _getImage(cls) -> Surface:
        if cls._cache is None:
            cls._cache = cls._createSurface(cls.bodyWidth, cls.bodyHeight)
        return cls._cache

    @classmethod
    def _createSurface(cls, w: int, h: int) -> Surface:
        surface = pygame.Surface((w, h), pygame.SRCALPHA)

        if (texture := cls._loadTexture()) is not None:
            tw, th = texture.get_width(), texture.get_height()
            scale = min(w / tw, h / th) * 0.95
            sw, sh = int(tw * scale), int(th * scale)
            scaled = pygame.transform.smoothscale(texture, (sw, sh))
            surface.blit(scaled, ((w - sw) // 2, (h - sh) // 2))
        else:
            surface = cls._createFallback(w, h)

        return surface

    @classmethod
    def _createFallback(cls, w: int, h: int) -> Surface:
        surface = pygame.Surface((w, h), pygame.SRCALPHA)

        bodyColor: Color = (80, 40, 40)
        darkColor: Color = (50, 25, 25)
        outlineColor: Color = (30, 15, 15)

        pygame.draw.ellipse(surface, bodyColor, (0, 0, w, h))
        pygame.draw.ellipse(surface, darkColor, (0, 0, w, h), 3)

        headRadius = h // 2
        headX = w - headRadius - 5
        headY = h // 2
        pygame.draw.circle(surface, bodyColor, (headX, headY), headRadius)
        pygame.draw.circle(surface, outlineColor, (headX, headY), headRadius, 2)

        armW, armH = w // 4, h // 5
        pygame.draw.ellipse(surface, darkColor, (10, h // 2 - armH // 2, armW, armH))

        return surface

    def get_hitbox(self) -> Rect:
        return self.rect.inflate(-20, -10)
