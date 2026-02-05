from enum import Enum, auto
from typing import TYPE_CHECKING

import pygame
from pygame import Rect, Surface
from pygame.math import Vector2

if TYPE_CHECKING:
    from entities.input.manager import InputEvent

import settings
from entities.animation import AnimatedSprite, AnimationFrame, loadFrames
from keybindings import keyBindings
from paths import assetsPath

# Assets path for frames (running / sliding / trapped)
runningFramesPath = assetsPath / "player" / "running" / "frames"
slidingFramesPath = assetsPath / "player" / "sliding" / "frames"
trappedFramesPath = assetsPath / "player" / "trapped"
jumpSoundPath = assetsPath / "songs" / "jump.ogg"
_jumpSound: pygame.mixer.Sound | None = None
slideSoundPath = assetsPath / "songs" / "cartoon-slide.ogg"
_slideSound: pygame.mixer.Sound | None = None

_cachedRunningHeight: int | None = None

def getRunningHeight(scale: float = 0.15) -> int:
    global _cachedRunningHeight
    if _cachedRunningHeight is None:
        frames = loadFrames(runningFramesPath, scale=scale, frameSlice=slice(116, 117))
        _cachedRunningHeight = frames[0].surface.get_height()
    return _cachedRunningHeight

class PlayerState(Enum):
    RUNNING = auto()
    JUMPING = auto()
    SLIDING = auto()
    TRAPPED = auto()
    TACKLED = auto()


class Player(AnimatedSprite):
    gravity: float = 1100.0
    jumpForce: float = -650.0
    slideDuration: float = 0.5
    slideCooldown: float = 0.8
    playerScale: float = 0.15
    slideScaleMult: float = 2.0
    trappedScaleMult: float = 1.2
    slideImmunityWindow: float = 0.8

    def __init__(self, x: int, groundY: int) -> None:
        # Please don't remove the slice on the frames here, some frames are invalid, so if you took/render all the frames for running
        # It's going to create a small bug where the running animation will broke for 1seconds (so 1000 frames) like static player
        runningFrames = loadFrames(runningFramesPath, scale=self.playerScale, frameSlice=slice(116, 132))
        self.runningHeight: int = runningFrames[0].surface.get_height()
        slidingTargetHeight = int(self.runningHeight * self.slideScaleMult)
        slidingFrames = loadFrames(slidingFramesPath, targetHeight=slidingTargetHeight)
        self.slidingHeight: int = slidingFrames[0].surface.get_height()
        self.slideYOffset: int = (self.slidingHeight - self.runningHeight) // 2
        trappedTargetHeight = int(self.runningHeight * self.trappedScaleMult)
        trappedFrames = loadFrames(trappedFramesPath, targetHeight=trappedTargetHeight)
        super().__init__(x, groundY, runningFrames)

        self.runningFrames: list[AnimationFrame] = runningFrames
        self.slidingFrames: list[AnimationFrame] = slidingFrames
        self.trappedFrames: list[AnimationFrame] = trappedFrames
        self.groundY: int = groundY
        self.velocity: Vector2 = Vector2(0, 0)
        self.state: PlayerState = PlayerState.RUNNING
        self.slideTimer: float = 0.0
        self.slideBoostTimer: float = 0.0
        self.slideCooldownTimer: float = 0.0
        self.bOnGround: bool = True

    # Used for setting the frames of the player (runnning, sliding, trapped) check animation.py for more info
    def _setFrames(self, frames: list[AnimationFrame]) -> None:
        self.frames = frames
        self.frameIdx = 0
        self.animTimer = 0.0

    def setGroundY(self, groundY: int) -> None:
        self.groundY = groundY
        if self.bOnGround:
            self.rect.bottom = groundY

    def handleInput(self, event: pygame.event.Event, inputEvent: "InputEvent | None" = None) -> None:
        from entities.input.manager import GameAction, InputEvent

        if inputEvent:
            if inputEvent.action == GameAction.JUMP and inputEvent.bPressed:
                self._jump()
            elif inputEvent.action == GameAction.SLIDE and inputEvent.bPressed:
                self._slide()

        if event.type == pygame.KEYDOWN:
            if event.key == keyBindings.jump:
                self._jump()
            elif event.key == keyBindings.slide:
                self._slide()

    def _jump(self) -> None:
        global _jumpSound
        if self.bOnGround and self.state != PlayerState.SLIDING:
            if _jumpSound is None:
                _jumpSound = pygame.mixer.Sound(jumpSoundPath)
            if settings.bSoundEnabled:
                _jumpSound.play()
            self.velocity.y = self.jumpForce
            self.state = PlayerState.JUMPING
            self.bOnGround = False
            self.image = self._getFrame()
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def _slide(self) -> None:
        global _slideSound
        if self.bOnGround and self.state == PlayerState.RUNNING and self.slideCooldownTimer <= 0:
            if _slideSound is None:
                _slideSound = pygame.mixer.Sound(slideSoundPath)
            if settings.bSoundEnabled:
                _slideSound.play()
            self.state = PlayerState.SLIDING
            self.slideTimer = self.slideDuration
            self.slideBoostTimer = self.slideDuration
            self.slideCooldownTimer = self.slideCooldown
            oldCenterx = self.rect.centerx
            self._setFrames(self.slidingFrames)
            self.image = self._getFrame()
            self.rect = self.image.get_rect(centerx=oldCenterx, bottom=self.groundY + self.slideYOffset)

    def _endSlide(self) -> None:
        if self.state == PlayerState.SLIDING:
            self.state = PlayerState.RUNNING
            oldCenterx = self.rect.centerx
            self._setFrames(self.runningFrames)
            self.image = self._getFrame()
            self.rect = self.image.get_rect(centerx=oldCenterx, bottom=self.groundY)

    def trap(self) -> None:
        if self.state == PlayerState.SLIDING:
            self._endSlide()
        self._setFrames(self.trappedFrames)
        self.state = PlayerState.TRAPPED
        self.image = self._getFrame()
        self.rect = self.image.get_rect(centerx=self.rect.centerx, bottom=self.groundY)

    def tackle(self) -> None:
        if self.state == PlayerState.SLIDING:
            self._endSlide()
        self.state = PlayerState.TACKLED
        self.velocity = Vector2(0, 0)
        self.bOnGround = True
        self.rect.bottom = self.groundY

    def getHitbox(self) -> Rect:
        if self.state == PlayerState.SLIDING:
            return self.rect.inflate(-20, -200)
        return self.rect.inflate(-10, -10)

    def _updateImage(self) -> None:
        self.image = self._getFrame()

    # When working on this, when playing with the frames don't forget to put them in cache, else ur game will freeze since
    # it's trying to render each frames
    def update(self, dt: float) -> None:
        if self.updateAnimation(dt):
            self._updateImage()

        if self.state == PlayerState.JUMPING:
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

        if self.slideBoostTimer > 0:
            self.slideBoostTimer -= dt
        if self.slideCooldownTimer > 0:
            self.slideCooldownTimer -= dt

    def isBoostActive(self) -> bool:
        return self.slideBoostTimer > 0

    def isInImmunityWindow(self) -> bool:
        if self.state != PlayerState.SLIDING:
            return False
        timeInSlide = self.slideDuration - self.slideTimer
        return timeInSlide <= self.slideImmunityWindow
