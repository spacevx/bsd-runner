from abc import abstractmethod
from enum import Enum, auto

import pygame
from pygame import Surface, Rect
from pygame.sprite import Sprite


class ObstacleType(Enum):
    LOW = auto()
    HIGH = auto()
    FALLING_CAGE = auto()


class BaseObstacle(Sprite):
    obstacleType: ObstacleType
    speed: float
    image: Surface
    rect: Rect

    def __init__(self) -> None:
        super().__init__()
        self.speed = 400.0

    @abstractmethod
    def get_hitbox(self) -> Rect:
        pass

    def update(self, dt: float) -> None:
        self.rect.x -= int(self.speed * dt)
        if self.rect.right < -50:
            self.kill()
