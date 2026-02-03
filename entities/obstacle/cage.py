from enum import Enum, auto

import pygame
from pygame import Surface, Rect

from settings import Color
from .base import BaseObstacle, ObstacleType


class CageState(Enum):
    HANGING = auto()
    WARNING = auto()
    FALLING = auto()
    GROUNDED = auto()
    TRAPPED = auto()


class FallingCage(BaseObstacle):
    _cageCache: Surface | None = None
    _chainCache: Surface | None = None

    cageWidth: int = 180
    cageHeight: int = 220
    chainWidth: int = 8
    fallSpeed: float = 1200.0
    warningDuration: float = 0.6
    triggerDistance: float = 200.0
    groundedDuration: float = 0.8

    def __init__(self, x: int, ceilingY: int, groundY: int, scrollSpeed: float = 400.0) -> None:
        super().__init__()
        self.obstacleType = ObstacleType.FALLING_CAGE
        self.speed = scrollSpeed
        self.state = CageState.HANGING
        self.ceilingY = ceilingY
        self.groundY = groundY

        self.warningTimer: float = 0.0
        self.shakeOffset: float = 0.0
        self.groundedTimer: float = 0.0
        self.fallVelocity: float = 0.0

        self.image = self._getCageImage()
        self.rect = self.image.get_rect(midtop=(x, ceilingY))
        self.chainImage = self._getChainImage(self.rect.top)
        self.chainRect = self.chainImage.get_rect(midtop=(x, 0))

    @classmethod
    def clearCache(cls) -> None:
        cls._cageCache = None
        cls._chainCache = None

    @classmethod
    def _getCageImage(cls) -> Surface:
        if cls._cageCache is None:
            cls._cageCache = cls._createCageSurface()
        return cls._cageCache

    @classmethod
    def _getChainImage(cls, height: int) -> Surface:
        return cls._createChainSurface(height)

    @classmethod
    def _createCageSurface(cls) -> Surface:
        w, h = cls.cageWidth, cls.cageHeight
        surface = pygame.Surface((w, h), pygame.SRCALPHA)

        metal: Color = (120, 120, 130)
        darkMetal: Color = (80, 80, 90)
        highlight: Color = (160, 160, 170)

        barW = 8
        spacing = 20
        frameH = 15

        pygame.draw.rect(surface, metal, (0, 0, w, frameH))
        pygame.draw.rect(surface, darkMetal, (0, 0, w, frameH), 3)
        pygame.draw.line(surface, highlight, (5, 3), (w - 5, 3), 2)

        pygame.draw.rect(surface, metal, (0, h - frameH, w, frameH))
        pygame.draw.rect(surface, darkMetal, (0, h - frameH, w, frameH), 3)

        for xPos in range(spacing, w - spacing // 2, spacing):
            pygame.draw.rect(surface, metal, (xPos - barW // 2, frameH, barW, h - frameH * 2))
            pygame.draw.line(surface, highlight, (xPos - barW // 2 + 1, frameH + 5),
                           (xPos - barW // 2 + 1, h - frameH - 5), 1)
            pygame.draw.line(surface, darkMetal, (xPos + barW // 2 - 1, frameH + 5),
                           (xPos + barW // 2 - 1, h - frameH - 5), 2)

        pygame.draw.rect(surface, metal, (0, frameH, barW, h - frameH * 2))
        pygame.draw.rect(surface, metal, (w - barW, frameH, barW, h - frameH * 2))

        return surface

    @classmethod
    def _createChainSurface(cls, height: int) -> Surface:
        w = cls.chainWidth * 3
        surface = pygame.Surface((w, max(1, height)), pygame.SRCALPHA)

        chainColor: Color = (100, 100, 110)
        highlight: Color = (140, 140, 150)
        linkH = 12
        linkW = cls.chainWidth

        cx = w // 2
        for y in range(0, height, linkH):
            pygame.draw.ellipse(surface, chainColor, (cx - linkW // 2, y, linkW, linkH), 2)
            pygame.draw.line(surface, highlight, (cx - linkW // 2 + 1, y + 2),
                           (cx - linkW // 2 + 1, y + linkH - 2), 1)

        return surface

    def triggerFall(self) -> None:
        if self.state == CageState.HANGING:
            self.state = CageState.WARNING
            self.warningTimer = self.warningDuration

    def trapPlayer(self, playerX: int) -> None:
        self.state = CageState.TRAPPED
        self.speed = 0
        self.rect.centerx = playerX
        self.rect.bottom = self.groundY
        self.chainRect.centerx = self.rect.centerx

    def get_hitbox(self) -> Rect:
        return self.rect.inflate(-30, -20)

    def update(self, dt: float, playerX: int | None = None) -> None:
        if self.state == CageState.TRAPPED:
            chainLen = self.rect.top
            if chainLen > 0 and chainLen != self.chainImage.get_height():
                self.chainImage = self._getChainImage(chainLen)
                self.chainRect = self.chainImage.get_rect(midtop=(self.rect.centerx, 0))
            return

        self.rect.x -= int(self.speed * dt)
        self.chainRect.centerx = self.rect.centerx

        if self.state == CageState.HANGING:
            if playerX is not None:
                dist = self.rect.centerx - playerX
                if 0 < dist < self.triggerDistance:
                    self.triggerFall()

        elif self.state == CageState.WARNING:
            self.warningTimer -= dt
            self.shakeOffset = (pygame.time.get_ticks() % 100 - 50) * 0.1
            if self.warningTimer <= 0:
                self.state = CageState.FALLING
                self.fallVelocity = 200.0

        elif self.state == CageState.FALLING:
            self.fallVelocity += 2000.0 * dt
            self.fallVelocity = min(self.fallVelocity, self.fallSpeed)
            self.rect.y += int(self.fallVelocity * dt)

            if self.rect.bottom >= self.groundY:
                self.rect.bottom = self.groundY
                self.state = CageState.GROUNDED
                self.groundedTimer = self.groundedDuration

        elif self.state == CageState.GROUNDED:
            self.groundedTimer -= dt
            if self.groundedTimer <= 0 or self.rect.right < -50:
                self.kill()

        chainLen = self.rect.top
        if chainLen > 0:
            if chainLen != self.chainImage.get_height():
                self.chainImage = self._getChainImage(chainLen)
            self.chainRect = self.chainImage.get_rect(midtop=(self.rect.centerx, 0))
        else:
            self.chainImage = pygame.Surface((1, 1), pygame.SRCALPHA)

        if self.rect.right < -50:
            self.kill()

    def draw(self, surface: Surface) -> None:
        if self.chainImage.get_height() > 1:
            surface.blit(self.chainImage, self.chainRect)

        drawX = self.rect.x
        if self.state == CageState.WARNING:
            drawX += int(self.shakeOffset)

        surface.blit(self.image, (drawX, self.rect.y))

        if self.state == CageState.WARNING:
            warnSurf = pygame.Surface((self.cageWidth + 20, self.groundY - self.rect.bottom), pygame.SRCALPHA)
            alpha = max(0, min(255, int(80 + 40 * abs(self.shakeOffset))))
            warnColor = (255, 50, 50, alpha)
            pygame.draw.rect(warnSurf, warnColor, warnSurf.get_rect())
            surface.blit(warnSurf, (self.rect.x - 10, self.rect.bottom))
