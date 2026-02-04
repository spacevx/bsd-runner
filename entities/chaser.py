from enum import Enum, auto

from pygame import Rect
from pygame.sprite import Group

from entities.animation import AnimatedSprite, AnimationFrame, loadFrames
from entities.obstacle.cage import FallingCage, CageState
from entities.player import getRunningHeight
from paths import assetsPath

playerRunningFramesPath = assetsPath / "player" / "running" / "frames"
chaserRunningFramesPath = assetsPath / "chaser" / "running" / "frames"
chaserJumpingFramesPath = assetsPath / "chaser" / "jumping"


class ChaserState(Enum):
    RUNNING = auto()
    JUMPING = auto()
    ON_CAGE = auto()
    JUMPING_OFF = auto()


class Chaser(AnimatedSprite):
    baseSpeed: float = 150.0
    speedBoostOnHit: float = 50.0
    approachOnHit: int = 80
    followOffset: int = 250
    playerScale: float = 0.15

    gravity: float = 1100.0
    jumpForce: float = -850.0
    jumpOffForce: float = -300.0
    cageDetectionRange: float = 550.0
    jumpScaleMult: float = 1.5

    def __init__(self, x: int, groundY: int) -> None:
        targetHeight = getRunningHeight(self.playerScale)
        runningFrames = loadFrames(chaserRunningFramesPath, targetHeight=targetHeight)
        runningHeight = runningFrames[0].surface.get_height()
        jumpingTargetHeight = int(runningHeight * self.jumpScaleMult)
        jumpingFrames = loadFrames(chaserJumpingFramesPath, targetHeight=jumpingTargetHeight)

        super().__init__(x, groundY, runningFrames)

        self.runningFrames = runningFrames
        self.jumpingFrames = jumpingFrames
        self.groundY: int = groundY
        self.posX: float = float(x)
        self.targetX: int = x
        self.speed: float = self.baseSpeed

        self.state: ChaserState = ChaserState.RUNNING
        self.velocityY: float = 0.0
        self.bOnGround: bool = True
        self.currentCage: FallingCage | None = None

    def setGroundY(self, groundY: int) -> None:
        self.groundY = groundY
        if self.bOnGround:
            self.rect.bottom = groundY

    def setTarget(self, playerX: int) -> None:
        self.targetX = playerX - self.followOffset

    def onPlayerHit(self) -> None:
        self.speed += self.speedBoostOnHit
        self.posX += self.approachOnHit

    def hasCaughtPlayer(self, playerRect: Rect) -> bool:
        return self.rect.colliderect(playerRect)

    def _setFrames(self, frames: list[AnimationFrame]) -> None:
        self.frames = frames
        self.frameIdx = 0
        self.animTimer = 0.0

    def _jump(self) -> None:
        if self.bOnGround:
            self._setFrames(self.jumpingFrames)
            self.velocityY = self.jumpForce
            self.state = ChaserState.JUMPING
            self.bOnGround = False

    def _jumpOff(self) -> None:
        self._setFrames(self.jumpingFrames)
        self.velocityY = self.jumpOffForce
        self.state = ChaserState.JUMPING_OFF
        self.currentCage = None

    def _findCageToJumpOn(self, cages: Group[FallingCage]) -> FallingCage | None:
        for cage in cages:
            if cage.state not in (CageState.FALLING, CageState.GROUNDED):
                continue

            cageCenterX = cage.rect.centerx
            chaserCenterX = self.rect.centerx
            dist = cageCenterX - chaserCenterX

            if 0 < dist < self.cageDetectionRange:
                return cage
        return None

    def _checkLandOnCage(self, cages: Group[FallingCage]) -> FallingCage | None:
        for cage in cages:
            if cage.state not in (CageState.FALLING, CageState.GROUNDED):
                continue

            bOverCage = cage.rect.left < self.rect.centerx < cage.rect.right
            bFallingOnto = self.velocityY > 0
            bAtCageTop = self.rect.bottom >= cage.rect.top and self.rect.bottom <= cage.rect.top + 30

            if bOverCage and bFallingOnto and bAtCageTop:
                return cage
        return None

    def _shouldJumpOff(self) -> bool:
        if self.currentCage is None:
            return True

        chaserX = self.rect.centerx
        cageRight = self.currentCage.rect.right - 20
        return chaserX >= cageRight

    def _updateImage(self) -> None:
        oldMidbottom = self.rect.midbottom
        self.image = self._getFrame()
        self.rect = self.image.get_rect(midbottom=oldMidbottom)

    def update(self, dt: float, cages: Group[FallingCage] | None = None) -> None:
        if self.updateAnimation(dt):
            self._updateImage()

        if self.state == ChaserState.RUNNING:
            if cages:
                targetCage = self._findCageToJumpOn(cages)
                if targetCage:
                    self._jump()

        elif self.state == ChaserState.JUMPING:
            self.velocityY += self.gravity * dt
            self.rect.y += int(self.velocityY * dt)

            if cages:
                landedCage = self._checkLandOnCage(cages)
                if landedCage:
                    self.rect.bottom = landedCage.rect.top
                    self.velocityY = 0.0
                    self._setFrames(self.runningFrames)
                    self.state = ChaserState.ON_CAGE
                    self.currentCage = landedCage

            if self.rect.bottom >= self.groundY:
                self.rect.bottom = self.groundY
                self.velocityY = 0.0
                self.bOnGround = True
                self._setFrames(self.runningFrames)
                self.state = ChaserState.RUNNING

        elif self.state == ChaserState.ON_CAGE:
            if self.currentCage:
                self.rect.bottom = self.currentCage.rect.top

            if self._shouldJumpOff():
                self._jumpOff()

        elif self.state == ChaserState.JUMPING_OFF:
            self.velocityY += self.gravity * dt
            self.rect.y += int(self.velocityY * dt)

            if self.rect.bottom >= self.groundY:
                self.rect.bottom = self.groundY
                self.velocityY = 0.0
                self.bOnGround = True
                self._setFrames(self.runningFrames)
                self.state = ChaserState.RUNNING

        if (diff := self.targetX - self.posX) > 0:
            self.posX += min(self.speed * dt, diff)
        elif diff < 0:
            self.posX -= min(self.speed * 0.5 * dt, -diff)

        self.posX = min(self.posX, self.targetX + self.followOffset - 50)

        if self.state == ChaserState.ON_CAGE and self.currentCage:
            self.rect.midbottom = (int(self.posX), self.currentCage.rect.top)
        elif self.state in (ChaserState.JUMPING, ChaserState.JUMPING_OFF):
            self.rect.centerx = int(self.posX)
        else:
            self.rect.midbottom = (int(self.posX), self.groundY)
