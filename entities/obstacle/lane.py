import random
from pathlib import Path

import pygame
from pygame import Surface, Rect

from settings import Color
from paths import assetsPath
from entities.animation import loadFrames
from entities.player import getRunningHeight
from .base import BaseObstacle

playerRunningFramesPath = assetsPath / "player" / "running" / "frames"

# Those are called lanes but they are dead body on the ground, mispell name is because at the beginning it wasn't supposed to be
# dead bodies

_defaultDir: Path = assetsPath / "lanes"

class Obstacle(BaseObstacle):
    _textures: list[Surface] | None = None
    _cache: dict[tuple[int, int, int], Surface] = {}
    _playerHeight: int | None = None
    _obstacleDir: Path = _defaultDir

    playerScale: float = 0.15
    heightRatio: float = 0.7
    widthRatio: float = 1.8

    @classmethod
    def _getPlayerHeight(cls) -> int:
        if cls._playerHeight is None:
            cls._playerHeight = getRunningHeight(cls.playerScale)
        return cls._playerHeight

    def __init__(self, x: int, groundY: int, scale: float = 1.0) -> None:
        super().__init__()
        self.scale = scale
        textures = self._loadTextures()
        self.variant = random.randrange(len(textures)) if textures else -1
        playerH = self._getPlayerHeight()
        h = max(1, int(playerH * self.heightRatio * scale))
        w = max(1, int(h * self.widthRatio))
        self.image = self._getImage(w, h, self.variant)
        self.rect = self.image.get_rect(centerx=x, bottom=groundY)

    @classmethod
    def setDir(cls, path: Path) -> None:
        if path != cls._obstacleDir:
            cls._obstacleDir = path
            cls.clearCache()

    @classmethod
    def clearCache(cls) -> None:
        cls._textures = None
        cls._cache.clear()
        cls._playerHeight = None

    @classmethod
    def _loadTextures(cls) -> list[Surface]:
        if cls._textures is not None:
            return cls._textures

        paths = sorted(cls._obstacleDir.glob("*.png"))
        loaded: list[Surface] = []
        for p in paths:
            try:
                raw = pygame.image.load(str(p))
                if pygame.display.get_surface():
                    raw = raw.convert_alpha()
                loaded.append(cls._cropToContent(raw))
            except (pygame.error, FileNotFoundError):
                pass

        cls._textures = loaded
        return loaded

    # Took from a pygame forum, for a issue where the sprite couldn't be croped right
    @classmethod
    def _cropToContent(cls, surface: Surface) -> Surface:
        mask = pygame.mask.from_surface(surface, threshold=10)
        rects = mask.get_bounding_rects()
        if not rects:
            return surface

        minArea = 100
        significantRects = [r for r in rects if r.width * r.height >= minArea]

        if not significantRects:
            significantRects = rects

        contentRect = significantRects[0].copy()
        for r in significantRects[1:]:
            contentRect.union_ip(r)

        contentRect.inflate_ip(4, 4)
        contentRect.clamp_ip(surface.get_rect())
        cropped = pygame.Surface(contentRect.size, pygame.SRCALPHA)
        cropped.blit(surface, (0, 0), contentRect)
        return cropped

    @classmethod
    def _getImage(cls, w: int, h: int, variant: int) -> Surface:
        key = (w, h, variant)
        if key not in cls._cache:
            cls._cache[key] = cls._createSurface(w, h, variant)
        return cls._cache[key]

    @classmethod
    def _createSurface(cls, w: int, h: int, variant: int) -> Surface:
        textures = cls._loadTextures()
        texture = textures[variant] if 0 <= variant < len(textures) else None

        if texture is not None:
            tw, th = texture.get_width(), texture.get_height()
            srcRatio = tw / th
            tgtRatio = w / h

            if srcRatio > tgtRatio:
                sw = w
                sh = max(1, int(w / srcRatio))
            else:
                sh = h
                sw = max(1, int(h * srcRatio))

            scaled = pygame.transform.smoothscale(texture, (sw, sh))
            surface = pygame.Surface((w, h), pygame.SRCALPHA)
            blitX = (w - sw) // 2
            blitY = h - sh
            surface.blit(scaled, (blitX, blitY))
            return surface
        else:
            return cls._createFallback(w, h)

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

    def getHitbox(self) -> Rect:
        shrinkX = int(self.rect.width * 0.15)
        shrinkY = int(self.rect.height * 0.1)
        return self.rect.inflate(-shrinkX, -shrinkY)
