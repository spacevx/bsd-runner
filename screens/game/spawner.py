import random
import time

import pygame
from pygame.event import Event
from pygame.sprite import Group

from settings import ScreenSize, obstacleSpawnEvent
from entities import Obstacle, FallingCage


class ObstacleSpawner:
    baseW: int = 1920
    baseH: int = 1080

    obstacleMinDelay: float = 2.5
    obstacleMaxDelay: float = 5.0
    minGapBetweenTypes: float = 2.0

    def __init__(self, screenSize: ScreenSize, groundY: int, scrollSpeed: float) -> None:
        self.screenSize = screenSize
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)
        self.groundY = groundY
        self.scrollSpeed = scrollSpeed
        self.obstacleSpawnDelay: float = 3.0
        self.lastBodyTime: float = 0.0
        self.lastCageTime: float = 0.0

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def onResize(self, newSize: ScreenSize, groundY: int) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self.groundY = groundY

    def handleEvent(self, event: Event, obstacles: Group[Obstacle], bGameOver: bool) -> None:
        if event.type == obstacleSpawnEvent and not bGameOver:
            now = time.monotonic()
            if now - self.lastCageTime >= self.minGapBetweenTypes:
                self._spawnObstacle(obstacles)
                self.lastBodyTime = now
            self.obstacleSpawnDelay = random.uniform(self.obstacleMinDelay, self.obstacleMaxDelay)
            pygame.time.set_timer(obstacleSpawnEvent, int(self.obstacleSpawnDelay * 1000))

    def _spawnObstacle(self, obstacles: Group[Obstacle]) -> None:
        x = self.screenSize[0] + self._s(100)
        obstacle = Obstacle(x, self.groundY)
        obstacle.speed = self.scrollSpeed
        obstacles.add(obstacle)

    def canSpawnCage(self) -> bool:
        now = time.monotonic()
        return now - self.lastBodyTime >= self.minGapBetweenTypes

    def spawnCageAt(self, x: int, ceilingY: int, cages: Group[FallingCage]) -> None:
        self.lastCageTime = time.monotonic()
        cage = FallingCage(x, ceilingY, self.groundY, self.scrollSpeed)
        cages.add(cage)

    def reset(self) -> None:
        self.obstacleSpawnDelay = random.uniform(self.obstacleMinDelay, self.obstacleMaxDelay)
        self.lastBodyTime = 0.0
        self.lastCageTime = 0.0
        pygame.time.set_timer(obstacleSpawnEvent, int(self.obstacleSpawnDelay * 1000))
