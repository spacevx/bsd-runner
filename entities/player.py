from enum import Enum, auto

import pygame
from pygame import Surface, Rect
from pygame.math import Vector2

from settings import Color
from entities.animation import AnimatedSprite, load_frames
from paths import assetsPath

framesPath = assetsPath / "player" / "frames"

class PlayerState(Enum):
    RUNNING = auto()
    JUMPING = auto()
    SLIDING = auto()


class Player(AnimatedSprite):
    GRAVITY: float = 1500.0
    JUMP_FORCE: float = -600.0
    SLIDE_DURATION: float = 0.5
    PLAYER_SCALE: float = 0.15

    def __init__(self, x: int, groundY: int) -> None:
        frames = load_frames(framesPath, scale=self.PLAYER_SCALE, fallback=self._create_fallback())
        super().__init__(x, groundY, frames)

        self.groundY: int = groundY
        self.velocity: Vector2 = Vector2(0, 0)
        self.state: PlayerState = PlayerState.RUNNING
        self.slideTimer: float = 0.0
        self.bOnGround: bool = True

    @staticmethod
    def _create_fallback() -> Surface:
        w, h = 40, 60
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        skin: Color = (210, 180, 140)
        shorts: Color = (200, 30, 30)
        shirt: Color = (255, 255, 255)

        pygame.draw.circle(surf, skin, (w // 2, 12), 10)
        pygame.draw.rect(surf, shirt, (w // 2 - 10, 22, 20, 18))
        pygame.draw.rect(surf, shorts, (w // 2 - 10, 38, 20, 12))
        pygame.draw.rect(surf, skin, (w // 2 - 8, 50, 6, 10))
        pygame.draw.rect(surf, skin, (w // 2 + 2, 50, 6, 10))
        pygame.draw.rect(surf, skin, (w // 2 - 18, 24, 8, 5))
        pygame.draw.rect(surf, skin, (w // 2 + 10, 24, 8, 5))

        return surf

    def _get_slide_image(self) -> Surface:
        return pygame.transform.rotate(self._get_frame(), 90)

    def set_ground_y(self, groundY: int) -> None:
        self.groundY = groundY
        if self.bOnGround:
            self.rect.bottom = groundY

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_z, pygame.K_w):
                self._jump()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._slide()

    def _jump(self) -> None:
        if self.bOnGround and self.state != PlayerState.SLIDING:
            self.velocity.y = self.JUMP_FORCE
            self.state = PlayerState.JUMPING
            self.bOnGround = False
            self.image = self._get_frame()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def _slide(self) -> None:
        if self.bOnGround and self.state == PlayerState.RUNNING:
            self.state = PlayerState.SLIDING
            self.slideTimer = self.SLIDE_DURATION
            self.image = self._get_slide_image()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def _end_slide(self) -> None:
        if self.state == PlayerState.SLIDING:
            self.state = PlayerState.RUNNING
            self.image = self._get_frame()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def get_hitbox(self) -> Rect:
        if self.state == PlayerState.SLIDING:
            return self.rect.inflate(-10, -5)
        return self.rect.inflate(-10, -10)

    def _update_image(self) -> None:
        if self.state == PlayerState.SLIDING:
            self.image = self._get_slide_image()
        else:
            self.image = self._get_frame()

    def update(self, dt: float) -> None:
        if self.update_animation(dt):
            self._update_image()

        if self.state == PlayerState.JUMPING:
            self.velocity.y += self.GRAVITY * dt
            self.rect.y += int(self.velocity.y * dt)

            if self.rect.bottom >= self.groundY:
                self.rect.bottom = self.groundY
                self.velocity.y = 0.0
                self.bOnGround = True
                self.state = PlayerState.RUNNING

        elif self.state == PlayerState.SLIDING:
            self.slideTimer -= dt
            if self.slideTimer <= 0:
                self._end_slide()