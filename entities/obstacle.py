from enum import Enum, auto
from pathlib import Path

import pygame
from pygame import Surface, Rect
from pygame.sprite import Sprite

from settings import Color

ASSETS_PATH: Path = Path(__file__).parent.parent / "assets"


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

    def __init__(self, x: int, ground_y: int, obstacle_type: ObstacleType) -> None:
        super().__init__()
        self.obstacle_type = obstacle_type
        self.speed = 400.0

        self.image: Surface = self._get_image(obstacle_type)
        y = ground_y if obstacle_type == ObstacleType.LOW else ground_y - 60
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
                path: Path = ASSETS_PATH / "lane.png"
                cls._texture = pygame.image.load(str(path)).convert_alpha()
            except (pygame.error, FileNotFoundError):
                cls._texture = None
        return cls._texture

    @classmethod
    def _get_image(cls, obstacle_type: ObstacleType) -> Surface:
        return cls._get_low_image() if obstacle_type == ObstacleType.LOW else cls._get_high_image()

    @classmethod
    def _create_obstacle_surface(cls, width: int, height: int, flip: bool = False) -> Surface:
        surface: Surface = pygame.Surface((width, height), pygame.SRCALPHA)

        if (texture := cls._load_texture()) is not None:
            tw, th = texture.get_width(), texture.get_height()
            scale_factor: float = min(width / tw, height / th) * 0.95
            w, h = int(tw * scale_factor), int(th * scale_factor)

            scaled: Surface = pygame.transform.smoothscale(texture, (w, h))
            if flip:
                scaled = pygame.transform.flip(scaled, False, True)

            x_off, y_off = (width - w) // 2, (height - h) // 2
            surface.blit(scaled, (x_off, y_off))
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
            wood_color: Color = (139, 90, 43)
            dark_wood: Color = (101, 67, 33)
            pygame.draw.rect(surface, wood_color, (10, 10, width - 20, height - 20))
            pygame.draw.rect(surface, dark_wood, (10, 10, width - 20, height - 20), 4)
            pygame.draw.rect(surface, dark_wood, (0, height - 20, 20, 20))
            pygame.draw.rect(surface, dark_wood, (width - 20, height - 20, 20, 20))
        else:
            metal_color: Color = (150, 150, 160)
            dark_metal: Color = (100, 100, 110)
            pygame.draw.rect(surface, metal_color, (10, 10, width - 20, height - 20))
            pygame.draw.rect(surface, dark_metal, (10, 10, width - 20, height - 20), 4)
            pygame.draw.rect(surface, dark_metal, (0, 0, 20, 20))
            pygame.draw.rect(surface, dark_metal, (width - 20, 0, 20, 20))

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

    def __init__(self, x: int, ceiling_y: int, ground_y: int, scroll_speed: float = 400.0) -> None:
        super().__init__()
        self.obstacle_type = ObstacleType.FALLING_CAGE
        self.speed = scroll_speed
        self.state = CageState.HANGING
        self.ceiling_y = ceiling_y
        self.ground_y = ground_y

        self.warning_timer: float = 0.0
        self.shake_offset: float = 0.0
        self.grounded_timer: float = 0.0
        self.fall_velocity: float = 0.0

        self.image: Surface = self._get_cage_image()
        self.chain_image: Surface = self._get_chain_image(ground_y - ceiling_y - self.HEIGHT)
        self.rect: Rect = self.image.get_rect(midtop=(x, ceiling_y))
        self.chain_rect: Rect = self.chain_image.get_rect(midbottom=(x, self.rect.top))

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
        dark_metal: Color = (80, 80, 90)
        highlight: Color = (160, 160, 170)

        bar_w = 8
        spacing = 20
        frame_h = 15

        pygame.draw.rect(surface, metal, (0, 0, w, frame_h))
        pygame.draw.rect(surface, dark_metal, (0, 0, w, frame_h), 3)
        pygame.draw.line(surface, highlight, (5, 3), (w - 5, 3), 2)

        pygame.draw.rect(surface, metal, (0, h - frame_h, w, frame_h))
        pygame.draw.rect(surface, dark_metal, (0, h - frame_h, w, frame_h), 3)

        for x_pos in range(spacing, w - spacing // 2, spacing):
            pygame.draw.rect(surface, metal, (x_pos - bar_w // 2, frame_h, bar_w, h - frame_h * 2))
            pygame.draw.line(surface, highlight, (x_pos - bar_w // 2 + 1, frame_h + 5),
                           (x_pos - bar_w // 2 + 1, h - frame_h - 5), 1)
            pygame.draw.line(surface, dark_metal, (x_pos + bar_w // 2 - 1, frame_h + 5),
                           (x_pos + bar_w // 2 - 1, h - frame_h - 5), 2)

        pygame.draw.rect(surface, metal, (0, frame_h, bar_w, h - frame_h * 2))
        pygame.draw.rect(surface, metal, (w - bar_w, frame_h, bar_w, h - frame_h * 2))

        return surface

    @classmethod
    def _create_chain_surface(cls, height: int) -> Surface:
        w = cls.CHAIN_WIDTH * 3
        surface: Surface = pygame.Surface((w, max(1, height)), pygame.SRCALPHA)

        chain_color: Color = (100, 100, 110)
        highlight: Color = (140, 140, 150)
        link_h = 12
        link_w = cls.CHAIN_WIDTH

        cx = w // 2
        for y in range(0, height, link_h):
            pygame.draw.ellipse(surface, chain_color, (cx - link_w // 2, y, link_w, link_h), 2)
            pygame.draw.line(surface, highlight, (cx - link_w // 2 + 1, y + 2),
                           (cx - link_w // 2 + 1, y + link_h - 2), 1)

        return surface

    def trigger_fall(self) -> None:
        if self.state == CageState.HANGING:
            self.state = CageState.WARNING
            self.warning_timer = self.WARNING_DURATION

    def get_hitbox(self) -> Rect:
        return self.rect.inflate(-30, -20)

    def update(self, dt: float, player_x: int | None = None) -> None:
        self.rect.x -= int(self.speed * dt)
        self.chain_rect.centerx = self.rect.centerx

        if self.state == CageState.HANGING:
            if player_x is not None:
                dist = self.rect.centerx - player_x
                if 0 < dist < self.TRIGGER_DISTANCE:
                    self.trigger_fall()

        elif self.state == CageState.WARNING:
            self.warning_timer -= dt
            self.shake_offset = (pygame.time.get_ticks() % 100 - 50) * 0.1
            if self.warning_timer <= 0:
                self.state = CageState.FALLING
                self.fall_velocity = 200.0

        elif self.state == CageState.FALLING:
            self.fall_velocity += 2000.0 * dt
            self.fall_velocity = min(self.fall_velocity, self.FALL_SPEED)
            self.rect.y += int(self.fall_velocity * dt)

            if self.rect.bottom >= self.ground_y:
                self.rect.bottom = self.ground_y
                self.state = CageState.GROUNDED
                self.grounded_timer = self.GROUNDED_DURATION

        elif self.state == CageState.GROUNDED:
            self.grounded_timer -= dt
            if self.grounded_timer <= 0 or self.rect.right < -50:
                self.kill()

        chain_len = self.rect.top - self.ceiling_y
        if chain_len > 0:
            self.chain_image = self._get_chain_image(chain_len)
            self.chain_rect = self.chain_image.get_rect(midbottom=(self.rect.centerx, self.rect.top))
        else:
            self.chain_image = pygame.Surface((1, 1), pygame.SRCALPHA)

        if self.rect.right < -50:
            self.kill()

    def draw(self, surface: Surface) -> None:
        if self.chain_image.get_height() > 1:
            surface.blit(self.chain_image, self.chain_rect)

        draw_x = self.rect.x
        if self.state == CageState.WARNING:
            draw_x += int(self.shake_offset)

        surface.blit(self.image, (draw_x, self.rect.y))

        if self.state == CageState.WARNING:
            warn_surf = pygame.Surface((self.WIDTH + 20, self.ground_y - self.rect.bottom), pygame.SRCALPHA)
            alpha = max(0, min(255, int(80 + 40 * abs(self.shake_offset))))
            warn_color = (255, 50, 50, alpha)
            pygame.draw.rect(warn_surf, warn_color, warn_surf.get_rect())
            surface.blit(warn_surf, (self.rect.x - 10, self.rect.bottom))


class Ceiling:
    HEIGHT: int = 60

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.width = screen_width
        self.height = self.HEIGHT
        self.image = self._create_surface(screen_width)
        self.rect = self.image.get_rect(topleft=(0, 0))

    def _create_surface(self, width: int) -> Surface:
        surface = pygame.Surface((width, self.height), pygame.SRCALPHA)

        beam_color: Color = (50, 45, 40)
        dark_beam: Color = (30, 28, 25)
        highlight: Color = (70, 65, 60)

        pygame.draw.rect(surface, beam_color, (0, 0, width, self.height))
        pygame.draw.rect(surface, dark_beam, (0, self.height - 8, width, 8))
        pygame.draw.line(surface, highlight, (0, 5), (width, 5), 2)

        rafter_spacing = 200
        for x in range(0, width + rafter_spacing, rafter_spacing):
            pygame.draw.rect(surface, dark_beam, (x - 15, 0, 30, self.height))
            pygame.draw.line(surface, highlight, (x - 14, 0), (x - 14, self.height - 10), 1)

        return surface

    def on_resize(self, new_width: int) -> None:
        self.width = new_width
        self.image = self._create_surface(new_width)
        self.rect = self.image.get_rect(topleft=(0, 0))

    def draw(self, screen: Surface) -> None:
        screen.blit(self.image, self.rect)
