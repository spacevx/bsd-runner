import random

import pygame
from pygame.event import Event
from pygame.sprite import Group

from settings import ScreenSize, obstacleSpawnEvent
from entities import Obstacle, ObstacleType, FallingCage


class ObstacleSpawner:
    baseW: int = 1920
    baseH: int = 1080

    obstacleMinDelay: float = 1.2
    obstacleMaxDelay: float = 2.5

    def __init__(self, screenSize: ScreenSize, groundY: int, scrollSpeed: float) -> None:
        self.screenSize = screenSize
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)
        self.groundY = groundY
        self.scrollSpeed = scrollSpeed
        self.obstacleSpawnDelay: float = 2.0
        self.lastObstacleType: ObstacleType | None = None

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def onResize(self, newSize: ScreenSize, groundY: int) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self.groundY = groundY

    def handleEvent(self, event: Event, obstacles: Group[Obstacle], bGameOver: bool) -> None:
        if event.type == obstacleSpawnEvent and not bGameOver:
            self._spawnObstacle(obstacles)
            self.obstacleSpawnDelay = random.uniform(self.obstacleMinDelay, self.obstacleMaxDelay)
            pygame.time.set_timer(obstacleSpawnEvent, int(self.obstacleSpawnDelay * 1000))

    def _spawnObstacle(self, obstacles: Group[Obstacle]) -> None:
        x = self.screenSize[0] + self._s(100)

        weights: list[float] = {
            ObstacleType.LOW: [0.3, 0.7],
            ObstacleType.HIGH: [0.7, 0.3],
            None: [0.5, 0.5]
        }[self.lastObstacleType]

        obsType = random.choices([ObstacleType.LOW, ObstacleType.HIGH], weights=weights)[0]
        self.lastObstacleType = obsType

        obstacle = Obstacle(x, self.groundY, obsType)
        obstacle.speed = self.scrollSpeed
        obstacles.add(obstacle)

    def spawnCageAt(self, x: int, ceilingY: int, cages: Group[FallingCage]) -> None:
        cage = FallingCage(x, ceilingY, self.groundY, self.scrollSpeed)
        cages.add(cage)

    def reset(self) -> None:
        self.obstacleSpawnDelay = 2.0
        self.lastObstacleType = None
        pygame.time.set_timer(obstacleSpawnEvent, int(self.obstacleSpawnDelay * 1000))
