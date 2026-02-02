from enum import Enum, auto
from pathlib import Path

import pygame
from pygame import Surface, Rect
from pygame.sprite import Sprite

from settings import Color
from paths import assetsPath


class ObstacleType(Enum):
    LOW = auto()
    HIGH = auto()
    FALLING_CAGE = auto()


class CageState(Enum):
    HANGING = auto()
    WARNING = auto()
    FALLING = auto()
    GROUNDED = auto()


class Obstacle(Sprite):
    _texture: Surface | None = None
    _low_image_cache: Surface | None = None
    _high_image_cache: Surface | None = None

    LOW_WIDTH: int = 120
    LOW_HEIGHT: int = 100
    HIGH_WIDTH: int = 140
    HIGH_HEIGHT: int = 110

    def __init__(self, x: int, groundY: int, obstacleType: ObstacleType) -> None:
        super().__init__()
        self.obstacle_type = obstacleType
        self.speed = 400.0

        self.image: Surface = self._get_image(obstacleType)
        y = groundY if obstacleType == ObstacleType.LOW else groundY - 60
        self.rect: Rect = self.image.get_rect(midbottom=(x, y))

    @classmethod
    def clear_cache(cls) -> None:
        cls._texture = None
        cls._low_image_cache = None
        cls._high_image_cache = None

    @classmethod
    def _load_texture(cls) -> Surface | None:
        if cls._texture is None:
            try:
                path: Path = assetsPath / "lane.png"
                cls._texture = pygame.image.load(str(path)).convert_alpha()
            except (pygame.error, FileNotFoundError):
                cls._texture = None
        return cls._texture

    @classmethod
    def _get_image(cls, obstacleType: ObstacleType) -> Surface:
        return cls._get_low_image() if obstacleType == ObstacleType.LOW else cls._get_high_image()

    @classmethod
    def _create_obstacle_surface(cls, width: int, height: int, flip: bool = False) -> Surface:
        surface: Surface = pygame.Surface((width, height), pygame.SRCALPHA)

        if (texture := cls._load_texture()) is not None:
            tw, th = texture.get_width(), texture.get_height()
            scaleFactor: float = min(width / tw, height / th) * 0.95
            w, h = int(tw * scaleFactor), int(th * scaleFactor)

            scaled: Surface = pygame.transform.smoothscale(texture, (w, h))
            if flip:
                scaled = pygame.transform.flip(scaled, False, True)

            xOff, yOff = (width - w) // 2, (height - h) // 2
            surface.blit(scaled, (xOff, yOff))
        else:
            surface = cls._create_fallback(width, height, flip)

        return surface

    @classmethod
    def _get_low_image(cls) -> Surface:
        if (cached := cls._low_image_cache) is None:
            cls._low_image_cache = cached = cls._create_obstacle_surface(cls.LOW_WIDTH, cls.LOW_HEIGHT, flip=False)
        return cached

    @classmethod
    def _get_high_image(cls) -> Surface:
        if (cached := cls._high_image_cache) is None:
            cls._high_image_cache = cached = cls._create_obstacle_surface(cls.HIGH_WIDTH, cls.HIGH_HEIGHT, flip=True)
        return cached

    @classmethod
    def _create_fallback(cls, width: int, height: int, flip: bool) -> Surface:
        surface: Surface = pygame.Surface((width, height), pygame.SRCALPHA)

        if not flip:
            woodColor: Color = (139, 90, 43)
            darkWood: Color = (101, 67, 33)
            pygame.draw.rect(surface, woodColor, (10, 10, width - 20, height - 20))
            pygame.draw.rect(surface, darkWood, (10, 10, width - 20, height - 20), 4)
            pygame.draw.rect(surface, darkWood, (0, height - 20, 20, 20))
            pygame.draw.rect(surface, darkWood, (width - 20, height - 20, 20, 20))
        else:
            metalColor: Color = (150, 150, 160)
            darkMetal: Color = (100, 100, 110)
            pygame.draw.rect(surface, metalColor, (10, 10, width - 20, height - 20))
            pygame.draw.rect(surface, darkMetal, (10, 10, width - 20, height - 20), 4)
            pygame.draw.rect(surface, darkMetal, (0, 0, 20, 20))
            pygame.draw.rect(surface, darkMetal, (width - 20, 0, 20, 20))

        return surface

    def get_hitbox(self) -> Rect:
        return self.rect.inflate(-20, -15)

    def update(self, dt: float) -> None:
        self.rect.x -= int(self.speed * dt)
        if self.rect.right < -50:
            self.kill()


class FallingCage(Sprite):
    _cage_cache: Surface | None = None
    _chain_cache: Surface | None = None

    WIDTH: int = 160
    HEIGHT: int = 140
    CHAIN_WIDTH: int = 8
    FALL_SPEED: float = 1200.0
    WARNING_DURATION: float = 0.6
    TRIGGER_DISTANCE: float = 600.0
    GROUNDED_DURATION: float = 0.8

    def __init__(self, x: int, ceilingY: int, groundY: int, scrollSpeed: float = 400.0) -> None:
        super().__init__()
        self.obstacle_type = ObstacleType.FALLING_CAGE
        self.speed = scrollSpeed
        self.state = CageState.HANGING
        self.ceilingY = ceilingY
        self.groundY = groundY

        self.warningTimer: float = 0.0
        self.shakeOffset: float = 0.0
        self.groundedTimer: float = 0.0
        self.fallVelocity: float = 0.0

        self.image: Surface = self._get_cage_image()
        self.chainImage: Surface = self._get_chain_image(groundY - ceilingY - self.HEIGHT)
        self.rect: Rect = self.image.get_rect(midtop=(x, ceilingY))
        self.chainRect: Rect = self.chainImage.get_rect(midbottom=(x, self.rect.top))

    @classmethod
    def clear_cache(cls) -> None:
        cls._cage_cache = None
        cls._chain_cache = None

    @classmethod
    def _get_cage_image(cls) -> Surface:
        if cls._cage_cache is None:
            cls._cage_cache = cls._create_cage_surface()
        return cls._cage_cache

    @classmethod
    def _get_chain_image(cls, height: int) -> Surface:
        return cls._create_chain_surface(height)

    @classmethod
    def _create_cage_surface(cls) -> Surface:
        w, h = cls.WIDTH, cls.HEIGHT
        surface: Surface = pygame.Surface((w, h), pygame.SRCALPHA)

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
    def _create_chain_surface(cls, height: int) -> Surface:
        w = cls.CHAIN_WIDTH * 3
        surface: Surface = pygame.Surface((w, max(1, height)), pygame.SRCALPHA)

        chainColor: Color = (100, 100, 110)
        highlight: Color = (140, 140, 150)
        linkH = 12
        linkW = cls.CHAIN_WIDTH

        cx = w // 2
        for y in range(0, height, linkH):
            pygame.draw.ellipse(surface, chainColor, (cx - linkW // 2, y, linkW, linkH), 2)
            pygame.draw.line(surface, highlight, (cx - linkW // 2 + 1, y + 2),
                           (cx - linkW // 2 + 1, y + linkH - 2), 1)

        return surface

    def trigger_fall(self) -> None:
        if self.state == CageState.HANGING:
            self.state = CageState.WARNING
            self.warningTimer = self.WARNING_DURATION

    def get_hitbox(self) -> Rect:
        return self.rect.inflate(-30, -20)

    def update(self, dt: float, playerX: int | None = None) -> None:
        self.rect.x -= int(self.speed * dt)
        self.chainRect.centerx = self.rect.centerx

        if self.state == CageState.HANGING:
            if playerX is not None:
                dist = self.rect.centerx - playerX
                if 0 < dist < self.TRIGGER_DISTANCE:
                    self.trigger_fall()

        elif self.state == CageState.WARNING:
            self.warningTimer -= dt
            self.shakeOffset = (pygame.time.get_ticks() % 100 - 50) * 0.1
            if self.warningTimer <= 0:
                self.state = CageState.FALLING
                self.fallVelocity = 200.0

        elif self.state == CageState.FALLING:
            self.fallVelocity += 2000.0 * dt
            self.fallVelocity = min(self.fallVelocity, self.FALL_SPEED)
            self.rect.y += int(self.fallVelocity * dt)

            if self.rect.bottom >= self.groundY:
                self.rect.bottom = self.groundY
                self.state = CageState.GROUNDED
                self.groundedTimer = self.GROUNDED_DURATION

        elif self.state == CageState.GROUNDED:
            self.groundedTimer -= dt
            if self.groundedTimer <= 0 or self.rect.right < -50:
                self.kill()

        chainLen = self.rect.top - self.ceilingY
        if chainLen > 0:
            self.chainImage = self._get_chain_image(chainLen)
            self.chainRect = self.chainImage.get_rect(midbottom=(self.rect.centerx, self.rect.top))
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
            warnSurf = pygame.Surface((self.WIDTH + 20, self.groundY - self.rect.bottom), pygame.SRCALPHA)
            alpha = max(0, min(255, int(80 + 40 * abs(self.shakeOffset))))
            warnColor = (255, 50, 50, alpha)
            pygame.draw.rect(warnSurf, warnColor, warnSurf.get_rect())
            surface.blit(warnSurf, (self.rect.x - 10, self.rect.bottom))


class Ceiling:
    HEIGHT: int = 60

    def __init__(self, screenWidth: int, screenHeight: int) -> None:
        self.width = screenWidth
        self.height = self.HEIGHT
        self.image = self._create_surface(screenWidth)
        self.rect = self.image.get_rect(topleft=(0, 0))

    def _create_surface(self, width: int) -> Surface:
        surface = pygame.Surface((width, self.height), pygame.SRCALPHA)

        beamColor: Color = (50, 45, 40)
        darkBeam: Color = (30, 28, 25)
        highlight: Color = (70, 65, 60)

        pygame.draw.rect(surface, beamColor, (0, 0, width, self.height))
        pygame.draw.rect(surface, darkBeam, (0, self.height - 8, width, 8))
        pygame.draw.line(surface, highlight, (0, 5), (width, 5), 2)

        rafterSpacing = 200
        for x in range(0, width + rafterSpacing, rafterSpacing):
            pygame.draw.rect(surface, darkBeam, (x - 15, 0, 30, self.height))
            pygame.draw.line(surface, highlight, (x - 14, 0), (x - 14, self.height - 10), 1)

        return surface

    def on_resize(self, newWidth: int) -> None:
        self.width = newWidth
        self.image = self._create_surface(newWidth)
        self.rect = self.image.get_rect(topleft=(0, 0))

    def draw(self, screen: Surface) -> None:
        screen.blit(self.image, self.rect)
