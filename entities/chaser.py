import pygame
from pygame import Surface, Rect
from pygame.sprite import Sprite

from settings import Color


class Chaser(Sprite):
    baseSpeed: float = 150.0
    speedBoostOnHit: float = 50.0
    approachOnHit: int = 80
    followOffset: int = 150
    width: int = 140
    height: int = 95

    def __init__(self, x: int, groundY: int) -> None:
        super().__init__()

        self.image: Surface = self._createImage()
        self.rect: Rect = self.image.get_rect(midbottom=(x, groundY))

        self.groundY = groundY
        self.posX = float(x)
        self.targetX = x
        self.speed = self.baseSpeed

    def _createImage(self) -> Surface:
        surface: Surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        bodyColor: Color = (80, 50, 30)
        hornColor: Color = (200, 180, 150)

        pygame.draw.ellipse(surface, bodyColor, (10, 25, 110, 55))
        pygame.draw.circle(surface, bodyColor, (110, 45), 28)
        pygame.draw.polygon(surface, hornColor, [(120, 25), (140, 8), (130, 30)])
        pygame.draw.polygon(surface, hornColor, [(120, 65), (140, 82), (130, 60)])
        pygame.draw.circle(surface, (0, 0, 0), (124, 40), 5)
        pygame.draw.circle(surface, (255, 0, 0), (124, 40), 3)
        pygame.draw.rect(surface, bodyColor, (16, 75, 12, 20))
        pygame.draw.rect(surface, bodyColor, (40, 75, 12, 20))
        pygame.draw.rect(surface, bodyColor, (70, 75, 12, 20))
        pygame.draw.rect(surface, bodyColor, (94, 75, 12, 20))
        pygame.draw.ellipse(surface, bodyColor, (0, 35, 25, 15))

        return surface

    def setGroundY(self, groundY: int) -> None:
        self.groundY = groundY
        self.rect.bottom = groundY

    def setTarget(self, playerX: int) -> None:
        self.targetX = playerX - self.followOffset

    def onPlayerHit(self) -> None:
        self.speed += self.speedBoostOnHit
        self.posX += self.approachOnHit

    def hasCaughtPlayer(self, playerRect: Rect) -> bool:
        return self.rect.colliderect(playerRect)

    def update(self, dt: float) -> None:
        if (diff := self.targetX - self.posX) > 0:
            self.posX += min(self.speed * dt, diff)
        elif diff < 0:
            self.posX -= min(self.speed * 0.5 * dt, -diff)

        self.posX = min(self.posX, self.targetX + self.followOffset - 50)
        self.rect.midbottom = (int(self.posX), self.groundY)
