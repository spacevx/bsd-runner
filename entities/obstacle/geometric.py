import math
import pygame
from pygame import Surface, Rect

from .base import BaseObstacle


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
        baseSizes = {"triangle": 60, "square": 50, "hexagon": 70}
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

        if shape == "triangle":
            points = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 3)
        elif shape == "square":
            rect = pygame.Rect(cx - size // 2, cy - size // 2, size, size)
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, (255, 255, 255), rect, 3)
        elif shape == "hexagon":
            points = [(cx + size * math.cos(math.radians(60 * i)),
                      cy + size * math.sin(math.radians(60 * i))) for i in range(6)]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 3)

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
