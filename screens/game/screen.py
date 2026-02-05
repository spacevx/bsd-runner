from __future__ import annotations

from typing import Callable, TYPE_CHECKING

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
    Player, Chaser, Obstacle, FallingCage, Ceiling,
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
    cageDodgeScore: int = 150

    def __init__(self, setStateCallback: Callable[[GameState], None],
                 levelConfig: LevelConfig = level1Config) -> None:
        self.setState = setStateCallback
        self.levelConfig = levelConfig
        self.screenSize: ScreenSize = (width, height)
        self.scale = min(width / self.baseW, height / self.baseH)

        Obstacle.setDir(levelConfig.obstacleDir)
        self._loadBackground()

        self.scrollX: float = 0.0
        self.scrollSpeed: float = levelConfig.scrollSpeed
        self.groundY = int(height * self.groundRatio)

        self.localPlayer = self._createPlayer()
        self.chaser: Chaser | None = self._createChaser()

        self.allSprites: Group[pygame.sprite.Sprite] = pygame.sprite.Group()
        self.allSprites.add(self.localPlayer)
        if self.chaser:
            self.allSprites.add(self.chaser)

        self.obstacles: Group[Obstacle] = pygame.sprite.Group()
        self.ceiling = Ceiling(self.screenSize[0], self.screenSize[1])
        self.fallingCages: Group[FallingCage] = pygame.sprite.Group()

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

        self.bFinaleTriggered: bool = False
        self.bChaserTrapped: bool = False
        self.bLevelComplete: bool = False
        self.finaleCage: FallingCage | None = None

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

        self.hud = HUD(self.screenSize, bDoubleJump=levelConfig.bDoubleJump,
                       bSlideEnabled=levelConfig.bSlideEnabled)
        self.spawner = ObstacleSpawner(
            self.screenSize, self.groundY, self.scrollSpeed,
            levelConfig.obstacleMinDelay, levelConfig.obstacleMaxDelay
        )
        self.gameCollision = GameCollision(self.screenSize)

    def _createPlayer(self) -> Player:
        cfg = self.levelConfig
        return Player(
            self._s(320), self.groundY,
            gravity=cfg.gravity, jumpForce=cfg.jumpForce,
            bDoubleJump=cfg.bDoubleJump, doubleJumpForce=cfg.doubleJumpForce,
            bSlideEnabled=cfg.bSlideEnabled,
            coyoteTime=cfg.coyoteTime, jumpBuffer=cfg.jumpBuffer
        )

    def _createChaser(self) -> Chaser | None:
        if flags.bDisableChaser:
            return None
        return Chaser(self._s(-200), self.groundY, framesPath=self.levelConfig.chaserFramesPath)

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

        self.localPlayer.setGroundY(self.groundY)
        if self.chaser:
            self.chaser.setGroundY(self.groundY)

        if self.groundTilemap:
            groundH = newSize[1] - self.groundY
            self.groundTilemap.on_resize(newSize[0], self.groundY, groundH)
        self.ceiling.onResize(newSize[0])
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

        self.bFinaleTriggered = False
        self.bChaserTrapped = False
        self.bLevelComplete = False
        self.finaleCage = None

        self._eeStep = 0
        self._eeHeld.clear()
        self._eeMode = EasterEggMode.OFF

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
                self.localPlayer.handleInput(event, inputEvent)
        elif inputEvent and not self.bGameOver and not self.bLevelComplete:
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

        self.spawner.handleEvent(event, self.obstacles, self.bGameOver or self.bFinaleTriggered)

    def update(self, dt: float) -> None:
        if self.bGameOver or self.bLevelComplete:
            return

        if self.bPlayerTrapped:
            self._updateTrapped(dt)
            return

        if self.bPlayerTackled:
            self._updateTackled(dt)
            return

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
            if not self.bFinaleTriggered:
                for cx in cageXs:
                    if self.spawner.canSpawnCage():
                        self.spawner.spawnCageAt(cx, self.ceiling.height, self.fallingCages)
        elif self.ceilingTilemap:
            self.ceilingTilemap.update(scrollDelta)

        self.score += int(self.scrollSpeed * dt * 0.1 * slowMult)

        if self.slowdownTimer > 0:
            self.slowdownTimer -= dt

        self.localPlayer.update(dt)
        if self.chaser:
            self.chaser.setTarget(self.localPlayer.rect.centerx)
            self.chaser.update(dt, self.fallingCages, self.obstacles)
        self.obstacles.update(dt)

        playerX = self.localPlayer.rect.centerx
        for cage in self.fallingCages:
            cage.update(dt, playerX)

        self._handleCollisions()
        self._checkDodgeScore()
        self._updateFinale(dt)

    def _updateFinale(self, dt: float) -> None:
        if not self.bFinaleTriggered and self.score >= self.levelConfig.finaleScore and self.chaser:
            self.bFinaleTriggered = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)
            cage = FallingCage(int(self.chaser.rect.centerx), self.ceiling.height, self.groundY, 0.0)
            cage.triggerFall()
            self.finaleCage = cage

        if self.finaleCage and not self.bChaserTrapped:
            self.finaleCage.update(dt)
            if self.chaser:
                self.finaleCage.rect.centerx = self.chaser.rect.centerx
                self.finaleCage.chainRect.centerx = self.chaser.rect.centerx

            if self.finaleCage.state in (CageState.FALLING, CageState.GROUNDED) and self.chaser:
                if self.finaleCage.rect.bottom >= self.chaser.rect.top:
                    self.chaser.trap()
                    self.finaleCage.rect.bottom = self.groundY
                    self.bChaserTrapped = True
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
            if self.hitCount >= cfg.maxHits and self.chaser and not self.bFinaleTriggered:
                self.bChaserCatching = True
                self.chaser.startCatching(self.localPlayer.rect.centerx)
                pygame.time.set_timer(obstacleSpawnEvent, 0)

        if result.bHitCage and result.trappingCage:
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

        if self.bPlayerTackled and self._tackledImage:
            rotatedRect = self._tackledImage.get_rect(midbottom=(self.localPlayer.rect.centerx, self.groundY))
            screen.blit(self._tackledImage, rotatedRect)
        else:
            screen.blit(self.localPlayer.image, self.localPlayer.rect)

        if self.chaser:
            screen.blit(self.chaser.image, self.chaser.rect)
        if self.ceilingTilemap:
            self.ceilingTilemap.draw(screen)

        for cage in self.fallingCages:
            cage.draw(screen)
        if self.finaleCage:
            self.finaleCage.draw(screen)

        self.hud.draw(screen, self.score, self.bGameOver, self.hitCount,
                      self.levelConfig.maxHits, self.bLevelComplete)

        if self._eeMode == EasterEggMode.MIRROR:
            screen.blit(pygame.transform.flip(screen, True, False), (0, 0))
        elif self._eeMode == EasterEggMode.INVERTED:
            screen.blit(pygame.transform.invert(screen), (0, 0))

    def _drawScrollingBackground(self, screen: Surface) -> None:
        x1 = -int(self.scrollX)
        x2 = x1 + self.bgWidth
        screen.blit(self.background, (x1, 0))
        screen.blit(self.background, (x2, 0))
