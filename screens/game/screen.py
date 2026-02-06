from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.sprite import Group

if TYPE_CHECKING:
    from entities.input.manager import InputEvent

import random
from enum import Enum, auto

import flags
from keybindings import keyBindings
from levels import LevelConfig, level1Config
from settings import GameState, ScreenSize, width, height, obstacleSpawnEvent
from entities import (
    Player, PlayerState, Chaser, Obstacle, FallingCage, Ceiling,
    TileSet, GroundTilemap, CeilingTileSet, CeilingTilemap
)
from entities.obstacle.cage import CageState
from paths import assetsPath

from .hud import HUD
from .spawner import ObstacleSpawner
from .collision import GameCollision

tilesPath = assetsPath / "tiles" / "ground"
ceilingTilesPath = assetsPath / "tiles" / "ceiling"


class EasterEggMode(Enum):
    OFF = 0
    MIRROR = auto()
    INVERTED = auto()


class GameScreen:
    baseW: int = 1280
    baseH: int = 720
    groundRatio: float = 1.0
    ceilingRatio: float = 0.0542
    cageDodgeScore: int = 150

    def __init__(self, setStateCallback: Callable[[GameState], None],
                 levelConfig: LevelConfig = level1Config) -> None:
        self.setState = setStateCallback
        self.levelConfig = levelConfig
        self.screenSize: ScreenSize = (width, height)
        self.scale = min(width / self.baseW, height / self.baseH)

        Obstacle.setDir(levelConfig.obstacleDir)
        self._loadBackground()

        self.dt: float = 0.0
        self.scrollX: float = 0.0
        self.scrollSpeed: float = levelConfig.scrollSpeed
        self.groundY = int(height * self.groundRatio)
        self.ceilingY = int(height * self.ceilingRatio)

        self.localPlayer = self._createPlayer()
        self.chaser: Chaser | None = self._createChaser()

        self.allSprites: Group[Any] = pygame.sprite.Group()
        self.allSprites.add(self.localPlayer)
        if self.chaser:
            self.allSprites.add(self.chaser)

        self.obstacles: Group[Any] = pygame.sprite.Group()
        self.ceiling = Ceiling(self.screenSize[0], self.screenSize[1], self.ceilingY)
        self.fallingCages: Group[Any] = pygame.sprite.Group()

        self.score: int = 0
        self.bGameOver: bool = False
        self.hitCount: int = 0
        self.slowdownTimer: float = 0.0
        self.bChaserCatching: bool = False
        self.bPlayerTackled: bool = False
        self.tackleTimer: float = 0.0
        self.tackleDuration: float = 2.0
        self._tackledImage: Surface | None = None

        self.bPlayerTrapped: bool = False
        self.trappedTimer: float = 0.0
        self.trappedDuration: float = 4.0
        self.trappingCage: FallingCage | None = None

        self.bFinaleArmed: bool = False
        self.bChaserTrapped: bool = False
        self.bLevelComplete: bool = False
        self.finaleCage: FallingCage | None = None

        self.laserBeams: list[Any] = []
        self.disintegrationEffects: list[Any] = []

        self.tileset: TileSet | None = None
        self.groundTilemap: GroundTilemap | None = None
        self.ceilingTileset: CeilingTileSet | None = None
        self.ceilingTilemap: CeilingTilemap | None = None

        if levelConfig.bHasGroundTiles:
            self._initTilemap()
        if levelConfig.bHasCeilingTiles:
            self._initCeilingTilemap()

        self._eeStep: int = 0
        self._eeHeld: set[str] = set()
        self._eeMode: EasterEggMode = EasterEggMode.OFF

        self._headEeJumps: int = 0
        self._headEeTimer: float = 0.0
        self._bHeadEeActive: bool = False

        self.hud = HUD(self.screenSize, bDoubleJump=levelConfig.bDoubleJump,
                       bSlideEnabled=levelConfig.bSlideEnabled,
                       bFallingCages=levelConfig.bFallingCages,
                       bShowHitCounter=levelConfig.bGeometricObstacles)
        self.spawner = ObstacleSpawner(
            self.screenSize, self.groundY, self.scrollSpeed,
            levelConfig.obstacleMinDelay, levelConfig.obstacleMaxDelay,
            levelConfig.bGeometricObstacles
        )
        self.gameCollision = GameCollision(self.screenSize)

    def _createPlayer(self) -> Player:
        cfg = self.levelConfig
        return Player(
            self._s(320), self.groundY,
            gravity=cfg.gravity, jumpForce=cfg.jumpForce,
            bDoubleJump=cfg.bDoubleJump, doubleJumpForce=cfg.doubleJumpForce,
            bSlideEnabled=cfg.bSlideEnabled,
            coyoteTime=cfg.coyoteTime, jumpBuffer=cfg.jumpBuffer,
            bLaserEnabled=cfg.bLaserEnabled, laserCooldown=cfg.laserCooldown
        )

    def _createChaser(self) -> Chaser | None:
        if flags.bDisableChaser or not self.levelConfig.bHasChaser:
            return None
        return Chaser(self._s(-200), self.groundY, framesPath=self.levelConfig.chaserFramesPath)

    def _fireLaser(self) -> None:
        from entities.laser import LaserBeam
        from entities.player import PlayerState

        if not self.levelConfig.bLaserEnabled:
            return

        playerX = self.localPlayer.rect.right
        if self.localPlayer.state == PlayerState.SLIDING:
            eyeY = self.localPlayer.rect.centery + self._s(10)
        else:
            eyeY = self.localPlayer.rect.top + self._s(60)
        laserRange = self.levelConfig.laserRange

        hitObstacle = self.gameCollision.checkLaserHit(
            playerX, eyeY, self.obstacles, laserRange
        )

        endX = playerX + int(laserRange)
        if hitObstacle:
            endX = hitObstacle.rect.left
            if hasattr(hitObstacle, 'takeDamage'):
                if hitObstacle.takeDamage(1):
                    from entities.obstacle.geometric import GeometricObstacle
                    from entities.disintegration import DisintegrationEffect
                    if isinstance(hitObstacle, GeometricObstacle):
                        self.disintegrationEffects.append(DisintegrationEffect(hitObstacle))
                    hitObstacle.kill()
                    self.score += 100

        beam = LaserBeam(playerX, eyeY, endX, eyeY)
        self.laserBeams.append(beam)

    def _updateLasers(self, dt: float) -> None:
        for beam in self.laserBeams[:]:
            beam.update(dt)
            if beam.bDone:
                self.laserBeams.remove(beam)

    def _updateDisintegrations(self, dt: float) -> None:
        for fx in self.disintegrationEffects[:]:
            fx.update(dt)
            if fx.bDone:
                self.disintegrationEffects.remove(fx)

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _loadBackground(self) -> None:
        path = self.levelConfig.backgroundPath
        try:
            original = pygame.image.load(str(path)).convert()
            self.background = pygame.transform.scale(original, self.screenSize)
        except (pygame.error, FileNotFoundError):
            self.background = self._createFallbackBackground()
        self.bgWidth = self.background.get_width()

    def _createFallbackBackground(self) -> Surface:
        w, h = self.screenSize
        surface = pygame.Surface((w, h))

        for y in range(int(h * self.groundRatio)):
            t = y / (h * self.groundRatio)
            r = int(100 + 35 * t)
            g = int(160 + 46 * t)
            b = int(220 + 35 * (1 - t))
            pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

        return surface.convert()

    def _initTilemap(self) -> None:
        w, h = self.screenSize
        groundH = h - self.groundY
        self.tileset = TileSet(tilesPath)
        self.groundTilemap = GroundTilemap(self.tileset, w, self.groundY, groundH)

    def _initCeilingTilemap(self) -> None:
        w = self.screenSize[0]
        self.ceilingTileset = CeilingTileSet(ceilingTilesPath)
        self.ceilingTilemap = CeilingTilemap(self.ceilingTileset, w, self.ceiling.height)

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self._loadBackground()
        self.groundY = int(newSize[1] * self.groundRatio)
        self.ceilingY = int(newSize[1] * self.ceilingRatio)

        self.localPlayer.setGroundY(self.groundY)
        if self.chaser:
            self.chaser.setGroundY(self.groundY)

        if self.groundTilemap:
            groundH = newSize[1] - self.groundY
            self.groundTilemap.on_resize(newSize[0], self.groundY, groundH)
        self.ceiling.onResize(newSize[0], self.ceilingY)
        if self.ceilingTilemap:
            self.ceilingTilemap.on_resize(newSize[0], self.ceiling.height)

        self.hud.onResize(newSize)
        self.spawner.onResize(newSize, self.groundY)
        self.gameCollision.onResize(newSize)

    def reset(self) -> None:
        cfg = self.levelConfig
        Obstacle.setDir(cfg.obstacleDir)
        FallingCage.clearCache()
        self.groundY = int(self.screenSize[1] * self.groundRatio)
        self.ceilingY = int(self.screenSize[1] * self.ceilingRatio)

        self.localPlayer = self._createPlayer()
        self.chaser = self._createChaser()

        self.allSprites.empty()
        self.allSprites.add(self.localPlayer)
        if self.chaser:
            self.allSprites.add(self.chaser)

        self.obstacles.empty()
        self.fallingCages.empty()
        if cfg.bHasCeilingTiles:
            self._initCeilingTilemap()

        self.scrollX = 0.0
        self.scrollSpeed = cfg.scrollSpeed
        self.score = 0
        self.bGameOver = False
        self.hitCount = 0
        self.slowdownTimer = 0.0
        self.bChaserCatching = False
        self.bPlayerTackled = False
        self.tackleTimer = 0.0
        self._tackledImage = None

        self.bPlayerTrapped = False
        self.trappedTimer = 0.0
        self.trappingCage = None

        self.bFinaleArmed = False
        self.bChaserTrapped = False
        self.bLevelComplete = False
        self.finaleCage = None
        self.disintegrationEffects = []

        self._eeStep = 0
        self._eeHeld.clear()
        self._eeMode = EasterEggMode.OFF
        self._headEeJumps = 0
        self._headEeTimer = 0.0
        self._bHeadEeActive = False

        self.spawner.reset()
        self.hud.resetGameOverCache()

    def handleEvent(self, event: Event, inputEvent: "InputEvent | None" = None) -> None:
        from entities.input.manager import InputEvent, GameAction

        bCanRestart = self.bGameOver or self.bLevelComplete
        if inputEvent:
            if inputEvent.action == GameAction.RESTART and inputEvent.bPressed and bCanRestart:
                self.reset()
                return

        if event.type == pygame.KEYDOWN:
            if event.key == keyBindings.restart and bCanRestart:
                self.reset()
            elif not self.bGameOver and not self.bLevelComplete:
                if event.key == keyBindings.shoot:
                    if self.localPlayer.shoot():
                        self._fireLaser()
                else:
                    self.localPlayer.handleInput(event, inputEvent)
        elif inputEvent and not self.bGameOver and not self.bLevelComplete:
            if inputEvent.action == GameAction.SHOOT and inputEvent.bPressed:
                if self.localPlayer.shoot():
                    self._fireLaser()
            else:
                self.localPlayer.handleInput(event, inputEvent)

        if inputEvent:
            name = inputEvent.action.name
            if inputEvent.bPressed:
                self._eeHeld.add(name)
            else:
                self._eeHeld.discard(name)

            if inputEvent.bPressed:
                if self._eeStep == 0 and name == "JUMP" and "SLIDE" not in self._eeHeld:
                    self._eeStep = 1
                elif self._eeStep == 1 and self._eeHeld >= {"JUMP", "SLIDE"}:
                    self._eeStep = 2
                elif self._eeStep == 2 and name == "SLIDE" and "JUMP" not in self._eeHeld:
                    self._eeMode = random.choice([EasterEggMode.MIRROR, EasterEggMode.INVERTED]) if self._eeMode == EasterEggMode.OFF else EasterEggMode.OFF
                    self._eeStep = 0
                elif name not in ("JUMP", "SLIDE"):
                    self._eeStep = 0

                if name == "JUMP" and not self._bHeadEeActive and self._headEeTimer < 10.0:
                    self._headEeJumps += 1
                    if self._headEeJumps >= 5:
                        self._bHeadEeActive = True
                        self.spawner.bHeadMode = True

        self.spawner.handleEvent(event, self.obstacles, self.bGameOver or self.bFinaleArmed)

    def update(self, dt: float) -> None:
        self.dt = dt
        if self.bGameOver or self.bLevelComplete:
            return

        if self.bChaserTrapped:
            self._updateFinale(dt)
            return

        if self.bPlayerTrapped:
            self._updateTrapped(dt)
            return

        if self.bPlayerTackled:
            self._updateTackled(dt)
            return

        if not self._bHeadEeActive:
            self._headEeTimer += dt

        if self.bChaserCatching:
            self._updateChaserCatching(dt)
            return

        cfg = self.levelConfig
        if cfg.bSpeedGrowth:
            self.scrollSpeed = min(self.scrollSpeed + cfg.speedGrowth * dt, cfg.maxSpeed)
            self.spawner.scrollSpeed = self.scrollSpeed

        boostMult = 2.2 if self.localPlayer.isBoostActive() else 1.0
        slowMult = cfg.slowdownMult if self.slowdownTimer > 0 else 1.0
        scrollDelta = self.scrollSpeed * dt * boostMult * slowMult
        self.scrollX += scrollDelta
        if self.scrollX >= self.bgWidth:
            self.scrollX -= self.bgWidth

        if self.groundTilemap:
            self.groundTilemap.update(scrollDelta)

        if self.ceilingTilemap and cfg.bFallingCages:
            cageXs = self.ceilingTilemap.update(scrollDelta)
            if not self.finaleCage:
                for cx in cageXs:
                    if self.spawner.canSpawnCage():
                        self.spawner.spawnCageAt(cx, self.ceiling.height, self.fallingCages)
                        if self.bFinaleArmed:
                            self.finaleCage = self.fallingCages.sprites()[-1]
        elif self.ceilingTilemap:
            self.ceilingTilemap.update(scrollDelta)

        if not cfg.bGeometricObstacles:
            self.score += int(self.scrollSpeed * dt * 0.1 * slowMult)

        if self.slowdownTimer > 0:
            self.slowdownTimer -= dt

        self.localPlayer.update(dt)
        self._updateLasers(dt)
        self._updateDisintegrations(dt)
        if self.chaser:
            self.chaser.setTarget(self.localPlayer.rect.centerx)
            self.chaser.update(dt, self.fallingCages, self.obstacles)
        self.obstacles.update(dt)

        playerX = self.localPlayer.rect.centerx
        chaserX = self.chaser.rect.centerx if self.chaser else None
        for cage in self.fallingCages:
            cage.update(dt, chaserX if cage is self.finaleCage else playerX)

        self._handleCollisions()
        self._checkDodgeScore()
        self._updateFinale(dt)

    def _updateFinale(self, dt: float) -> None:
        if not self.chaser and self.score >= self.levelConfig.finaleScore and not self.bLevelComplete:
            self.bLevelComplete = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)
            return

        if not self.bFinaleArmed and self.score >= self.levelConfig.finaleScore and self.chaser:
            self.bFinaleArmed = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)

        if self.finaleCage and not self.bChaserTrapped and self.chaser:
            if self.finaleCage.state in (CageState.FALLING, CageState.GROUNDED):
                if self.finaleCage.rect.bottom >= self.chaser.rect.top:
                    self.chaser.trap()
                    self.finaleCage.trapPlayer(self.chaser.rect.centerx)
                    self.bChaserTrapped = True

        if self.bChaserTrapped and not self.bLevelComplete and self.finaleCage:
            self.localPlayer.update(dt)
            self.finaleCage.update(dt)
            if self.localPlayer.state != PlayerState.SLIDING:
                self.bLevelComplete = True

    def _updateTrapped(self, dt: float) -> None:
        self.trappedTimer -= dt
        self.localPlayer.update(dt)
        if self.trappingCage:
            self.trappingCage.update(dt)
            self.localPlayer.rect.centerx = self.trappingCage.rect.centerx
            self.localPlayer.rect.bottom = self.groundY
        if self.trappedTimer <= 0:
            self.bGameOver = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)

    def _updateChaserCatching(self, dt: float) -> None:
        self.localPlayer.update(dt)
        if self.chaser:
            self.chaser.update(dt, None, None)
            if self.chaser.hasCaughtPlayer(self.localPlayer.rect):
                self.localPlayer.tackle()
                self.bChaserCatching = False
                self.bPlayerTackled = True
                self.tackleTimer = self.tackleDuration
                self._tackledImage = pygame.transform.rotate(self.localPlayer.image, -90)

    def _updateTackled(self, dt: float) -> None:
        self.tackleTimer -= dt
        if self.chaser:
            self.chaser.rect.centerx = self.localPlayer.rect.centerx
        if self.tackleTimer <= 0:
            self.bGameOver = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)

    def _handleCollisions(self) -> None:
        bInvincible = self.slowdownTimer > 0
        result = self.gameCollision.check(
            self.localPlayer, self.chaser, self.obstacles, self.fallingCages, bInvincible
        )

        cfg = self.levelConfig
        if result.bHitObstacle:
            self.hitCount += 1
            self.slowdownTimer = cfg.slowdownDuration
            if self.chaser:
                self.chaser.onPlayerHit()
            if self.hitCount >= cfg.maxHits:
                if self.chaser and not self.bFinaleArmed:
                    self.bChaserCatching = True
                    self.chaser.startCatching(self.localPlayer.rect.centerx)
                    pygame.time.set_timer(obstacleSpawnEvent, 0)
                elif not self.chaser:
                    self.bGameOver = True
                    pygame.time.set_timer(obstacleSpawnEvent, 0)

        if result.bHitCage and result.trappingCage and result.trappingCage is not self.finaleCage:
            self.bPlayerTrapped = True
            self.trappedTimer = self.trappedDuration
            self.trappingCage = result.trappingCage
            self.trappingCage.trapPlayer(self.localPlayer.rect.centerx)
            self.localPlayer.trap()
            pygame.time.set_timer(obstacleSpawnEvent, 0)

        if result.bCaught:
            self.bGameOver = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)

    def _checkDodgeScore(self) -> None:
        playerLeft = self.localPlayer.rect.left
        for obstacle in self.obstacles:
            if not obstacle.bScored and obstacle.rect.right < playerLeft:
                obstacle.bScored = True
                self.score += self.levelConfig.laneDodgeScore

        for cage in self.fallingCages:
            if not cage.bScored and cage.state == CageState.GROUNDED:
                cage.bScored = True
                self.score += self.cageDodgeScore

    def draw(self, screen: Surface) -> None:
        self._drawScrollingBackground(screen)
        if self.groundTilemap:
            self.groundTilemap.draw(screen)
        self.obstacles.draw(screen)

        for fx in self.disintegrationEffects:
            fx.draw(screen)

        for beam in self.laserBeams:
            beam.draw(screen)

        if self.bPlayerTackled and self._tackledImage:
            rotatedRect = self._tackledImage.get_rect(midbottom=(self.localPlayer.rect.centerx, self.groundY))
            screen.blit(self._tackledImage, rotatedRect)
        else:
            screen.blit(self.localPlayer.image, self.localPlayer.rect)

        if self.finaleCage and self.bChaserTrapped:
            self.finaleCage.draw(screen)

        if self.chaser:
            screen.blit(self.chaser.image, self.chaser.rect)
        if self.ceilingTilemap:
            self.ceilingTilemap.draw(screen)

        for cage in self.fallingCages:
            if cage is self.finaleCage and self.bChaserTrapped:
                continue
            cage.draw(screen)

        self.hud.draw(screen, self.score, self.bGameOver, self.dt, self.hitCount,
                      self.levelConfig.maxHits, self.bLevelComplete)

        if self._eeMode == EasterEggMode.MIRROR:
            screen.blit(pygame.transform.flip(screen, True, False), (0, 0))
        elif self._eeMode == EasterEggMode.INVERTED:
            white = Surface(screen.get_size())
            white.fill((255, 255, 255))
            white.blit(screen, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
            screen.blit(white, (0, 0))

    def _drawScrollingBackground(self, screen: Surface) -> None:
        x1 = -int(self.scrollX)
        x2 = x1 + self.bgWidth
        screen.blit(self.background, (x1, 0))
        screen.blit(self.background, (x2, 0))
