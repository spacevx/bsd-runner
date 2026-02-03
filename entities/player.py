from enum import Enum, auto

import pygame
from pygame import Surface, Rect
from pygame.math import Vector2

from entities.animation import AnimatedSprite, loadFrames
from paths import assetsPath

framesPath = assetsPath / "player" / "frames"

class PlayerState(Enum):
    RUNNING = auto()
    JUMPING = auto()
    SLIDING = auto() # TODO: Fix Sliding, actually when sliding it's colliding with the chaser so it's make the player loose (bc of _checkCollisions)

class Player(AnimatedSprite):
    gravity: float = 1500.0
    jumpForce: float = -600.0
    slideDuration: float = 0.5
    playerScale: float = 0.15

    def __init__(self, x: int, groundY: int) -> None:
        frames = loadFrames(framesPath, scale=self.playerScale)[116:132]
        super().__init__(x, groundY, frames)

        self.groundY: int = groundY
        self.velocity: Vector2 = Vector2(0, 0)
        self.state: PlayerState = PlayerState.RUNNING
        self.slideTimer: float = 0.0
        self.bOnGround: bool = True

    def _getSlideImage(self) -> Surface:
        return pygame.transform.rotate(self._getFrame(), 90)

    def setGroundY(self, groundY: int) -> None:
        self.groundY = groundY
        if self.bOnGround:
            self.rect.bottom = groundY

    def handleInput(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_z, pygame.K_w):
                self._jump()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._slide()

    def _jump(self) -> None:
        if self.bOnGround and self.state != PlayerState.SLIDING:
            self.velocity.y = self.jumpForce
            self.state = PlayerState.JUMPING
            self.bOnGround = False
            self.image = self._getFrame()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    # TODO: Add frame animations when sliding (so a real animation) and not just changing the rotation of the image
    def _slide(self) -> None:
        if self.bOnGround and self.state == PlayerState.RUNNING:
            self.state = PlayerState.SLIDING
            self.slideTimer = self.slideDuration
            self.image = self._getSlideImage()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def _endSlide(self) -> None:
        if self.state == PlayerState.SLIDING:
            self.state = PlayerState.RUNNING
            self.image = self._getFrame()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def getHitbox(self) -> Rect:
        if self.state == PlayerState.SLIDING:
            return self.rect.inflate(-10, -5)
        return self.rect.inflate(-10, -10)

    def _updateImage(self) -> None:
        if self.state == PlayerState.SLIDING:
            self.image = self._getSlideImage()
        else:
            self.image = self._getFrame()

    # called each frame in game/screens
    def update(self, dt: float) -> None:
        if self.updateAnimation(dt):
            self._updateImage()

        if self.state == PlayerState.JUMPING:
            # TODO: Maybe Add animation when jumping? and not just changing the y vec lol
            self.velocity.y += self.gravity * dt
            self.rect.y += int(self.velocity.y * dt)

            if self.rect.bottom >= self.groundY:
                self.rect.bottom = self.groundY
                self.velocity.y = 0.0
                self.bOnGround = True
                self.state = PlayerState.RUNNING

        elif self.state == PlayerState.SLIDING:
            self.slideTimer -= dt
            if self.slideTimer <= 0:
                self._endSlide()
