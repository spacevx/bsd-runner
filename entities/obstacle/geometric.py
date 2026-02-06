import math
from pathlib import Path

import pygame
import pygame.gfxdraw
from pygame import Surface, Rect

from .base import BaseObstacle
from paths import assetsPath


class GeometricObstacle(BaseObstacle):
    _cache: dict[tuple[str, int, tuple[int, int, int]], Surface] = {}
    rotationSpeed: float = 90.0

    def __init__(self, x: int, groundY: int, scale: float = 1.0,
                 shapeType: str = "triangle", color: tuple[int, int, int] = (0, 255, 255),
                 posY: int | None = None) -> None:
        super().__init__()
        self.scale = scale
        self.shapeType = shapeType
        self.color = color
        self.rotation = 0.0
        self.health = 1

        size = self._getSizeForShape(shapeType, scale)
        self.image = self._getImage(shapeType, size, color)
        y = posY if posY is not None else groundY
        self.rect = self.image.get_rect(centerx=x, bottom=y)

    def _getSizeForShape(self, shape: str, scale: float) -> int:
        baseSizes = {"triangle": 60, "square": 70, "hexagon": 70}
        return max(1, int(baseSizes.get(shape, 50) * scale))

    @classmethod
    def _getImage(cls, shape: str, size: int, color: tuple[int, int, int]) -> Surface:
        key = (shape, size, color)
        if key not in cls._cache:
            cls._cache[key] = cls._renderShape(shape, size, color)
        return cls._cache[key]

    @classmethod
    def _renderShape(cls, shape: str, size: int, color: tuple[int, int, int]) -> Surface:
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        cx, cy = size, size
        white = (255, 255, 255)

        if shape == "triangle":
            p = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)]
            pygame.gfxdraw.filled_trigon(surf, *p[0], *p[1], *p[2], color)
            pygame.gfxdraw.aatrigon(surf, *p[0], *p[1], *p[2], white)
        elif shape == "square":
            l, t = cx - size // 2, cy - size // 2
            r, b = l + size, t + size
            pts = [(l, t), (r, t), (r, b), (l, b)]
            pygame.gfxdraw.filled_polygon(surf, pts, color)
            pygame.gfxdraw.aapolygon(surf, pts, white)
        elif shape == "hexagon":
            pts = [(int(cx + size * math.cos(math.radians(60 * i))),
                    int(cy + size * math.sin(math.radians(60 * i)))) for i in range(6)]
            pygame.gfxdraw.filled_polygon(surf, pts, color)
            pygame.gfxdraw.aapolygon(surf, pts, white)

        return surf

    def update(self, dt: float) -> None:
        super().update(dt)
        self.rotation += self.rotationSpeed * dt
        if self.rotation >= 360:
            self.rotation -= 360

    def getHitbox(self) -> Rect:
        return self.rect.inflate(-10, -10)

    def takeDamage(self, damage: int = 1) -> bool:
        self.health -= damage
        return self.health <= 0


class HeadObstacle(GeometricObstacle):
    _headCache: Surface | None = None
    rotationSpeed: float = 120.0

    def __init__(self, x: int, groundY: int, scale: float = 1.0,
                 posY: int | None = None) -> None:
        BaseObstacle.__init__(self)
        self.scale = scale
        self.shapeType = "head"
        self.color = (255, 255, 255)
        self.rotation = 0.0
        self.health = 1

        self._originalImage = self._loadHead(scale)
        self.image = self._originalImage
        y = posY if posY is not None else groundY
        self.rect = self.image.get_rect(centerx=x, bottom=y)

    @classmethod
    def _loadHead(cls, scale: float) -> Surface:
        if cls._headCache is None:
            path = assetsPath / "level3" / "head.png"
            cls._headCache = pygame.image.load(str(path)).convert_alpha()
        raw = cls._headCache
        targetH = max(1, int(120 * scale))
        ratio = targetH / raw.get_height()
        targetW = max(1, int(raw.get_width() * ratio))
        return pygame.transform.smoothscale(raw, (targetW, targetH))

    def update(self, dt: float) -> None:
        BaseObstacle.update(self, dt)
        self.rotation += self.rotationSpeed * dt
        if self.rotation >= 360:
            self.rotation -= 360
        self.image = pygame.transform.rotate(self._originalImage, self.rotation)
        center = self.rect.center
        self.rect = self.image.get_rect(center=center)
