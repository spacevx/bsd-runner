import random
from typing import Callable

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.sprite import Group

from settings import GameState, ScreenSize, width, height, white, gold, obstacleSpawnEvent
from entities import Player, PlayerState, Chaser, Obstacle, ObstacleType, TileSet, GroundTilemap, FallingCage, Ceiling, CageState, CeilingTileSet, CeilingTilemap
from strings import gameOver, gameRestart
from paths import assetsPath, screensPath

tilesPath = assetsPath / "tiles" / "ground"
ceilingTilesPath = assetsPath / "tiles" / "ceiling"


class GameScreen:
    baseW: int = 1920
    baseH: int = 1080

    scrollSpeedConst: float = 400.0
    groundRatio: float = 0.85
    obstacleMinDelay: float = 1.2
    obstacleMaxDelay: float = 2.5

    def __init__(self, setStateCallback: Callable[[GameState], None]) -> None:
        self.setState: Callable[[GameState], None] = setStateCallback
        self.screenSize: ScreenSize = (width, height)
        self.scale: float = min(width / self.baseW, height / self.baseH)

        Obstacle.clearCache()
        self._loadBackground()

        self.scrollX: float = 0.0
        self.scrollSpeed: float = self.scrollSpeedConst

        self.groundY: int = int(height * self.groundRatio)

        self.localPlayer: Player = Player(self._s(320), self.groundY)
        self.chaser: Chaser = Chaser(self._s(-200), self.groundY)

        self.allSprites: Group[pygame.sprite.Sprite] = pygame.sprite.Group()
        self.allSprites.add(self.localPlayer, self.chaser)

        self.obstacles: Group[Obstacle] = pygame.sprite.Group()
        self.obstacleSpawnDelay: float = 2.0
        self.lastObstacleType: ObstacleType | None = None

        self.ceiling: Ceiling = Ceiling(self.screenSize[0], self.screenSize[1])
        self.fallingCages: Group[FallingCage] = pygame.sprite.Group()

        self.score: int = 0
        self.bGameOver: bool = False

        self.invincibleTimer: float = 0.0
        self.invincibleDuration: float = 1.0

        self._createFonts()
        self._initTilemap()
        self._initCeilingTilemap()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _createFonts(self) -> None:
        self.font: pygame.font.Font = pygame.font.Font(None, self._s(96))
        self.smallFont: pygame.font.Font = pygame.font.Font(None, self._s(42))
        self.scoreFont: pygame.font.Font = pygame.font.Font(None, self._s(64))

    def _loadBackground(self) -> None:
        path = screensPath / "background.png"
        try:
            original: Surface = pygame.image.load(str(path)).convert()
            self.background: Surface = pygame.transform.scale(original, self.screenSize)
        except (pygame.error, FileNotFoundError):
            self.background = self._createFallbackBackground()
        self.bgWidth: int = self.background.get_width()

    def _createFallbackBackground(self) -> Surface:
        w, h = self.screenSize
        surface: Surface = pygame.Surface((w, h))

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
        self.tileset: TileSet = TileSet(tilesPath)
        self.groundTilemap: GroundTilemap = GroundTilemap(self.tileset, w, self.groundY, groundH)

    def _initCeilingTilemap(self) -> None:
        w = self.screenSize[0]
        self.ceilingTileset: CeilingTileSet = CeilingTileSet(ceilingTilesPath)
        self.ceilingTilemap: CeilingTilemap = CeilingTilemap(self.ceilingTileset, w, self.ceiling.height)

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self._loadBackground()
        self.groundY = int(newSize[1] * self.groundRatio)
        self.localPlayer.setGroundY(self.groundY)
        self.chaser.setGroundY(self.groundY)
        self._createFonts()
        groundH = newSize[1] - self.groundY
        self.groundTilemap.on_resize(newSize[0], self.groundY, groundH)
        self.ceiling.onResize(newSize[0])
        self.ceilingTilemap.on_resize(newSize[0], self.ceiling.height)

    def reset(self) -> None:
        Obstacle.clearCache()
        FallingCage.clearCache()
        self.groundY = int(self.screenSize[1] * self.groundRatio)

        self.localPlayer = Player(self._s(320), self.groundY)
        self.chaser = Chaser(self._s(-200), self.groundY)

        self.allSprites.empty()
        self.allSprites.add(self.localPlayer, self.chaser)

        self.obstacles.empty()
        self.fallingCages.empty()
        self._initCeilingTilemap()

        self.scrollX = 0.0
        self.score = 0
        self.bGameOver = False
        self.obstacleSpawnDelay = 2.0
        self.lastObstacleType = None
        self.invincibleTimer = 0.0

        pygame.time.set_timer(obstacleSpawnEvent, int(self.obstacleSpawnDelay * 1000))

    def handleEvent(self, event: Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.bGameOver:
                self.reset()
            elif not self.bGameOver:
                self.localPlayer.handleInput(event)

        elif event.type == obstacleSpawnEvent and not self.bGameOver:
            self._spawnObstacle()
            self.obstacleSpawnDelay = random.uniform(self.obstacleMinDelay, self.obstacleMaxDelay)
            pygame.time.set_timer(obstacleSpawnEvent, int(self.obstacleSpawnDelay * 1000))

    def _spawnObstacle(self) -> None:
        x: int = self.screenSize[0] + self._s(100)

        weights: list[float] = {
            ObstacleType.LOW: [0.3, 0.7],
            ObstacleType.HIGH: [0.7, 0.3],
            None: [0.5, 0.5]
        }[self.lastObstacleType]

        obsType: ObstacleType = random.choices([ObstacleType.LOW, ObstacleType.HIGH], weights=weights)[0]
        self.lastObstacleType = obsType

        obstacle: Obstacle = Obstacle(x, self.groundY, obsType)
        obstacle.speed = self.scrollSpeed
        self.obstacles.add(obstacle)

    def _spawnCageAt(self, x: int) -> None:
        ceilingY = self.ceiling.height
        cage = FallingCage(x, ceilingY, self.groundY, self.scrollSpeed)
        self.fallingCages.add(cage)

    def _collisionCallback(self, player: Player, obstacle: Obstacle) -> bool:
        playerHitbox: pygame.Rect = player.getHitbox()
        obstacleHitbox: pygame.Rect = obstacle.get_hitbox()

        if not playerHitbox.colliderect(obstacleHitbox):
            return False

        if obstacle.obstacleType == ObstacleType.LOW and player.state == PlayerState.JUMPING:
            if playerHitbox.bottom < obstacleHitbox.top + self._s(20):
                return False

        if obstacle.obstacleType == ObstacleType.HIGH and player.state == PlayerState.SLIDING:
            if playerHitbox.top > obstacleHitbox.bottom - self._s(15):
                return False

        return True

    def _cageCollisionCallback(self, player: Player, cage: FallingCage) -> bool:
        if cage.state not in (CageState.FALLING, CageState.GROUNDED):
            return False

        playerHitbox: pygame.Rect = player.getHitbox()
        cageHitbox: pygame.Rect = cage.get_hitbox()

        if not playerHitbox.colliderect(cageHitbox):
            return False

        if player.state == PlayerState.SLIDING:
            if playerHitbox.top > cageHitbox.bottom - self._s(30):
                return False

        return True

    def _checkCollisions(self) -> None:
        if self.invincibleTimer > 0:
            return

        hitObstacles: list[Obstacle] = pygame.sprite.spritecollide(
            self.localPlayer, self.obstacles, dokill=False, collided=self._collisionCallback
        )

        if hitObstacles:
            self.invincibleTimer = self.invincibleDuration
            self.chaser.onPlayerHit()
            hitObstacles[0].kill()

        hitCages: list[FallingCage] = pygame.sprite.spritecollide(
            self.localPlayer, self.fallingCages, dokill=False, collided=self._cageCollisionCallback
        )

        if hitCages:
            self.invincibleTimer = self.invincibleDuration
            self.chaser.onPlayerHit()
            hitCages[0].kill()

        if self.chaser.hasCaughtPlayer(self.localPlayer.getHitbox()):
            self.bGameOver = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)

    def update(self, dt: float) -> None:
        if self.bGameOver:
            return

        scrollDelta = self.scrollSpeed * dt
        self.scrollX += scrollDelta
        if self.scrollX >= self.bgWidth:
            self.scrollX -= self.bgWidth

        self.groundTilemap.update(scrollDelta)
        cageXs = self.ceilingTilemap.update(scrollDelta)
        for cx in cageXs:
            self._spawnCageAt(cx)
        self.score += int(self.scrollSpeed * dt * 0.1)

        if self.invincibleTimer > 0:
            self.invincibleTimer -= dt

        self.localPlayer.update(dt)

        self.chaser.setTarget(self.localPlayer.rect.centerx)
        self.chaser.update(dt)

        self.obstacles.update(dt)

        playerX = self.localPlayer.rect.centerx
        for cage in self.fallingCages:
            cage.update(dt, playerX)

        self._checkCollisions()

    def _drawGround(self, screen: Surface) -> None:
        self.groundTilemap.draw(screen)

    def _drawScrollingBackground(self, screen: Surface) -> None:
        x1: int = -int(self.scrollX)
        x2: int = x1 + self.bgWidth

        screen.blit(self.background, (x1, 0))
        screen.blit(self.background, (x2, 0))

    def draw(self, screen: Surface) -> None:
        self._drawScrollingBackground(screen)
        self._drawGround(screen)

        self.obstacles.draw(screen)

        for cage in self.fallingCages:
            cage.draw(screen)

        if not (self.invincibleTimer > 0 and int(self.invincibleTimer * 10) % 2 == 0):
            screen.blit(self.localPlayer.image, self.localPlayer.rect)

        screen.blit(self.chaser.image, self.chaser.rect)

        self.ceilingTilemap.draw(screen)

        self._drawUi(screen)

        if self.bGameOver:
            self._drawGameOver(screen)

    def _drawTextWithShadow(self, screen: Surface, text: str, font: pygame.font.Font,
                                color: tuple[int, int, int], pos: tuple[int, int], shadowOffset: int = 2) -> None:
        shadow: Surface = font.render(text, True, (0, 0, 0))
        surf: Surface = font.render(text, True, color)
        screen.blit(shadow, (pos[0] + shadowOffset, pos[1] + shadowOffset))
        screen.blit(surf, pos)

    def _drawUi(self, screen: Surface) -> None:
        scoreX, scoreY = self._s(30), self._s(25)
        scoreText = f"Score: {self.score}"

        boxW = self._s(280)
        boxH = self._s(60)
        boxSurf = pygame.Surface((boxW, boxH), pygame.SRCALPHA)
        pygame.draw.rect(boxSurf, (0, 0, 0, 120), (0, 0, boxW, boxH), border_radius=self._s(8))
        pygame.draw.rect(boxSurf, (255, 255, 255, 40), (0, 0, boxW, boxH), self._s(2), border_radius=self._s(8))
        screen.blit(boxSurf, (scoreX - self._s(10), scoreY - self._s(10)))

        self._drawTextWithShadow(screen, scoreText, self.scoreFont, white, (scoreX, scoreY), self._s(3))

        controlsText = "ESPACE: Sauter | BAS: Glisser"
        ctrlX = self._s(30)
        ctrlY = self.screenSize[1] - self._s(50)

        ctrlSurf = self.smallFont.render(controlsText, True, white)
        ctrlW, ctrlH = ctrlSurf.get_size()

        bgSurf = pygame.Surface((ctrlW + self._s(20), ctrlH + self._s(10)), pygame.SRCALPHA)
        pygame.draw.rect(bgSurf, (0, 0, 0, 100), bgSurf.get_rect(), border_radius=self._s(5))
        screen.blit(bgSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))

        self._drawTextWithShadow(screen, controlsText, self.smallFont, white, (ctrlX, ctrlY), self._s(2))

    def _drawGameOver(self, screen: Surface) -> None:
        w, h = self.screenSize
        overlay: Surface = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        cx, cy = w // 2, h // 2

        panelW, panelH = self._s(600), self._s(350)
        panel = pygame.Surface((panelW, panelH), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 35, 240), (0, 0, panelW, panelH), border_radius=self._s(15))
        pygame.draw.rect(panel, (139, 0, 0, 200), (0, 0, panelW, panelH), self._s(4), border_radius=self._s(15))
        screen.blit(panel, (cx - panelW // 2, cy - panelH // 2))

        titleSurf: Surface = self.font.render(gameOver, True, (255, 50, 50))
        titleRect = titleSurf.get_rect(center=(cx, cy - self._s(80)))

        for offset in range(self._s(15), 0, -3):
            glow = self.font.render(gameOver, True, (139, 0, 0))
            glow.set_alpha(int(40 * (1 - offset / self._s(15))))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow, titleSurf.get_rect(center=(cx + dx, cy - self._s(80) + dy)))

        shadow = self.font.render(gameOver, True, (50, 0, 0))
        screen.blit(shadow, titleSurf.get_rect(center=(cx + self._s(4), cy - self._s(76))))
        screen.blit(titleSurf, titleRect)

        scoreText = f"Score Final: {self.score}"
        scoreSurf: Surface = self.scoreFont.render(scoreText, True, gold)
        scoreRect = scoreSurf.get_rect(center=(cx, cy + self._s(10)))

        scoreShadow = self.scoreFont.render(scoreText, True, (100, 80, 0))
        screen.blit(scoreShadow, scoreSurf.get_rect(center=(cx + self._s(2), cy + self._s(12))))
        screen.blit(scoreSurf, scoreRect)

        restartSurf: Surface = self.smallFont.render(gameRestart, True, white)
        restartRect = restartSurf.get_rect(center=(cx, cy + self._s(90)))
        screen.blit(restartSurf, restartRect)
