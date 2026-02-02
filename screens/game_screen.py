import random
from typing import Callable

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.sprite import Group

from settings import GameState, ScreenSize, WIDTH, HEIGHT, WHITE, GOLD, OBSTACLE_SPAWN_EVENT
from entities import Player, PlayerState, Chaser, Obstacle, ObstacleType, TileSet, GroundTilemap, FallingCage, Ceiling, CageState, CeilingTileSet, CeilingTilemap
from strings import GAME_OVER, GAME_RESTART
from paths import assetsPath, screensPath

tilesPath = assetsPath / "tiles" / "ground"
ceilingTilesPath = assetsPath / "tiles" / "ceiling"


class GameScreen:
    BASE_W: int = 1920
    BASE_H: int = 1080

    SCROLL_SPEED: float = 400.0
    GROUND_RATIO: float = 0.85
    OBSTACLE_MIN_DELAY: float = 1.2
    OBSTACLE_MAX_DELAY: float = 2.5

    def __init__(self, set_state_callback: Callable[[GameState], None]) -> None:
        self.set_state: Callable[[GameState], None] = set_state_callback
        self.screen_size: ScreenSize = (WIDTH, HEIGHT)
        self.scale: float = min(WIDTH / self.BASE_W, HEIGHT / self.BASE_H)

        Obstacle.clearCache()
        self._load_background()

        self.scrollX: float = 0.0
        self.scrollSpeed: float = self.SCROLL_SPEED

        self.groundY: int = int(HEIGHT * self.GROUND_RATIO)

        self.localPlayer: Player = Player(self._s(320), self.groundY)
        self.chaser: Chaser = Chaser(self._s(-200), self.groundY)

        self.allSprites: Group[pygame.sprite.Sprite] = pygame.sprite.Group()
        self.allSprites.add(self.localPlayer, self.chaser)

        self.obstacles: Group[Obstacle] = pygame.sprite.Group()
        self.obstacleSpawnDelay: float = 2.0
        self.lastObstacleType: ObstacleType | None = None

        self.ceiling: Ceiling = Ceiling(self.screen_size[0], self.screen_size[1])
        self.fallingCages: Group[FallingCage] = pygame.sprite.Group()

        self.score: int = 0
        self.bGameOver: bool = False

        self.invincibleTimer: float = 0.0
        self.invincibleDuration: float = 1.0

        self._create_fonts()
        self._init_tilemap()
        self._init_ceiling_tilemap()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _create_fonts(self) -> None:
        self.font: pygame.font.Font = pygame.font.Font(None, self._s(96))
        self.smallFont: pygame.font.Font = pygame.font.Font(None, self._s(42))
        self.scoreFont: pygame.font.Font = pygame.font.Font(None, self._s(64))

    def _load_background(self) -> None:
        path = screensPath / "background.png"
        try:
            original: Surface = pygame.image.load(str(path)).convert()
            self.background: Surface = pygame.transform.scale(original, self.screen_size)
        except (pygame.error, FileNotFoundError):
            self.background = self._create_fallback_background()
        self.bgWidth: int = self.background.get_width()

    def _create_fallback_background(self) -> Surface:
        w, h = self.screen_size
        surface: Surface = pygame.Surface((w, h))

        for y in range(int(h * self.GROUND_RATIO)):
            t = y / (h * self.GROUND_RATIO)
            r = int(100 + 35 * t)
            g = int(160 + 46 * t)
            b = int(220 + 35 * (1 - t))
            pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

        return surface.convert()

    def _init_tilemap(self) -> None:
        w, h = self.screen_size
        groundH = h - self.groundY
        self.tileset: TileSet = TileSet(tilesPath)
        self.groundTilemap: GroundTilemap = GroundTilemap(self.tileset, w, self.groundY, groundH)

    def _init_ceiling_tilemap(self) -> None:
        w = self.screen_size[0]
        self.ceilingTileset: CeilingTileSet = CeilingTileSet(ceilingTilesPath)
        self.ceilingTilemap: CeilingTilemap = CeilingTilemap(self.ceilingTileset, w, self.ceiling.HEIGHT)

    def on_resize(self, new_size: ScreenSize) -> None:
        self.screen_size = new_size
        self.scale = min(new_size[0] / self.BASE_W, new_size[1] / self.BASE_H)
        self._load_background()
        self.groundY = int(new_size[1] * self.GROUND_RATIO)
        self.localPlayer.set_ground_y(self.groundY)
        self.chaser.set_ground_y(self.groundY)
        self._create_fonts()
        groundH = new_size[1] - self.groundY
        self.groundTilemap.on_resize(new_size[0], self.groundY, groundH)
        self.ceiling.onResize(new_size[0])
        self.ceilingTilemap.on_resize(new_size[0], self.ceiling.HEIGHT)

    def reset(self) -> None:
        Obstacle.clearCache()
        FallingCage.clearCache()
        self.groundY = int(self.screen_size[1] * self.GROUND_RATIO)

        self.localPlayer = Player(self._s(320), self.groundY)
        self.chaser = Chaser(self._s(-200), self.groundY)

        self.allSprites.empty()
        self.allSprites.add(self.localPlayer, self.chaser)

        self.obstacles.empty()
        self.fallingCages.empty()
        self._init_ceiling_tilemap()

        self.scrollX = 0.0
        self.score = 0
        self.bGameOver = False
        self.obstacleSpawnDelay = 2.0
        self.lastObstacleType = None
        self.invincibleTimer = 0.0

        pygame.time.set_timer(OBSTACLE_SPAWN_EVENT, int(self.obstacleSpawnDelay * 1000))

    def handle_event(self, event: Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.bGameOver:
                self.reset()
            elif not self.bGameOver:
                self.localPlayer.handle_input(event)

        elif event.type == OBSTACLE_SPAWN_EVENT and not self.bGameOver:
            self._spawn_obstacle()
            self.obstacleSpawnDelay = random.uniform(self.OBSTACLE_MIN_DELAY, self.OBSTACLE_MAX_DELAY)
            pygame.time.set_timer(OBSTACLE_SPAWN_EVENT, int(self.obstacleSpawnDelay * 1000))

    def _spawn_obstacle(self) -> None:
        x: int = self.screen_size[0] + self._s(100)

        weights: list[float] = {
            ObstacleType.LOW: [0.3, 0.7],
            ObstacleType.HIGH: [0.7, 0.3],
            None: [0.5, 0.5]
        }[self.lastObstacleType]

        obstacleType: ObstacleType = random.choices([ObstacleType.LOW, ObstacleType.HIGH], weights=weights)[0]
        self.lastObstacleType = obstacleType

        obstacle: Obstacle = Obstacle(x, self.groundY, obstacleType)
        obstacle.speed = self.scrollSpeed
        self.obstacles.add(obstacle)

    def _spawn_cage_at(self, x: int) -> None:
        ceilingY = self.ceiling.height
        cage = FallingCage(x, ceilingY, self.groundY, self.scrollSpeed)
        self.fallingCages.add(cage)

    def _collision_callback(self, player: Player, obstacle: Obstacle) -> bool:
        playerHitbox: pygame.Rect = player.get_hitbox()
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

    def _cage_collision_callback(self, player: Player, cage: FallingCage) -> bool:
        if cage.state not in (CageState.FALLING, CageState.GROUNDED):
            return False

        playerHitbox: pygame.Rect = player.get_hitbox()
        cageHitbox: pygame.Rect = cage.get_hitbox()

        if not playerHitbox.colliderect(cageHitbox):
            return False

        if player.state == PlayerState.SLIDING:
            if playerHitbox.top > cageHitbox.bottom - self._s(30):
                return False

        return True

    def _check_collisions(self) -> None:
        if self.invincibleTimer > 0:
            return

        hitObstacles: list[Obstacle] = pygame.sprite.spritecollide(
            self.localPlayer, self.obstacles, dokill=False, collided=self._collision_callback
        )

        if hitObstacles:
            self.invincibleTimer = self.invincibleDuration
            self.chaser.on_player_hit()
            hitObstacles[0].kill()

        hitCages: list[FallingCage] = pygame.sprite.spritecollide(
            self.localPlayer, self.fallingCages, dokill=False, collided=self._cage_collision_callback
        )

        if hitCages:
            self.invincibleTimer = self.invincibleDuration
            self.chaser.on_player_hit()
            hitCages[0].kill()

        if self.chaser.has_caught_player(self.localPlayer.get_hitbox()):
            self.bGameOver = True
            pygame.time.set_timer(OBSTACLE_SPAWN_EVENT, 0)

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
            self._spawn_cage_at(cx)
        self.score += int(self.scrollSpeed * dt * 0.1)

        if self.invincibleTimer > 0:
            self.invincibleTimer -= dt

        self.localPlayer.update(dt)

        self.chaser.set_target(self.localPlayer.rect.centerx)
        self.chaser.update(dt)

        self.obstacles.update(dt)

        playerX = self.localPlayer.rect.centerx
        for cage in self.fallingCages:
            cage.update(dt, playerX)

        self._check_collisions()

    def _draw_ground(self, screen: Surface) -> None:
        self.groundTilemap.draw(screen)

    def _draw_scrolling_background(self, screen: Surface) -> None:
        x1: int = -int(self.scrollX)
        x2: int = x1 + self.bgWidth

        screen.blit(self.background, (x1, 0))
        screen.blit(self.background, (x2, 0))

    def draw(self, screen: Surface) -> None:
        self._draw_scrolling_background(screen)
        self._draw_ground(screen)

        self.obstacles.draw(screen)

        for cage in self.fallingCages:
            cage.draw(screen)

        if not (self.invincibleTimer > 0 and int(self.invincibleTimer * 10) % 2 == 0):
            screen.blit(self.localPlayer.image, self.localPlayer.rect)

        screen.blit(self.chaser.image, self.chaser.rect)

        self.ceilingTilemap.draw(screen)

        self._draw_ui(screen)

        if self.bGameOver:
            self._draw_game_over(screen)

    def _draw_text_with_shadow(self, screen: Surface, text: str, font: pygame.font.Font,
                                color: tuple[int, int, int], pos: tuple[int, int], shadowOffset: int = 2) -> None:
        shadow: Surface = font.render(text, True, (0, 0, 0))
        surf: Surface = font.render(text, True, color)
        screen.blit(shadow, (pos[0] + shadowOffset, pos[1] + shadowOffset))
        screen.blit(surf, pos)

    def _draw_ui(self, screen: Surface) -> None:
        scoreX, scoreY = self._s(30), self._s(25)
        scoreText = f"Score: {self.score}"

        boxW = self._s(280)
        boxH = self._s(60)
        boxSurf = pygame.Surface((boxW, boxH), pygame.SRCALPHA)
        pygame.draw.rect(boxSurf, (0, 0, 0, 120), (0, 0, boxW, boxH), border_radius=self._s(8))
        pygame.draw.rect(boxSurf, (255, 255, 255, 40), (0, 0, boxW, boxH), self._s(2), border_radius=self._s(8))
        screen.blit(boxSurf, (scoreX - self._s(10), scoreY - self._s(10)))

        self._draw_text_with_shadow(screen, scoreText, self.scoreFont, WHITE, (scoreX, scoreY), self._s(3))

        controlsText = "ESPACE: Sauter | BAS: Glisser"
        ctrlX = self._s(30)
        ctrlY = self.screen_size[1] - self._s(50)

        ctrlSurf = self.smallFont.render(controlsText, True, WHITE)
        ctrlW, ctrlH = ctrlSurf.get_size()

        bgSurf = pygame.Surface((ctrlW + self._s(20), ctrlH + self._s(10)), pygame.SRCALPHA)
        pygame.draw.rect(bgSurf, (0, 0, 0, 100), bgSurf.get_rect(), border_radius=self._s(5))
        screen.blit(bgSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))

        self._draw_text_with_shadow(screen, controlsText, self.smallFont, WHITE, (ctrlX, ctrlY), self._s(2))

    def _draw_game_over(self, screen: Surface) -> None:
        w, h = self.screen_size
        overlay: Surface = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        cx, cy = w // 2, h // 2

        panelW, panelH = self._s(600), self._s(350)
        panel = pygame.Surface((panelW, panelH), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 35, 240), (0, 0, panelW, panelH), border_radius=self._s(15))
        pygame.draw.rect(panel, (139, 0, 0, 200), (0, 0, panelW, panelH), self._s(4), border_radius=self._s(15))
        screen.blit(panel, (cx - panelW // 2, cy - panelH // 2))

        titleSurf: Surface = self.font.render(GAME_OVER, True, (255, 50, 50))
        titleRect = titleSurf.get_rect(center=(cx, cy - self._s(80)))

        for offset in range(self._s(15), 0, -3):
            glow = self.font.render(GAME_OVER, True, (139, 0, 0))
            glow.set_alpha(int(40 * (1 - offset / self._s(15))))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow, titleSurf.get_rect(center=(cx + dx, cy - self._s(80) + dy)))

        shadow = self.font.render(GAME_OVER, True, (50, 0, 0))
        screen.blit(shadow, titleSurf.get_rect(center=(cx + self._s(4), cy - self._s(76))))
        screen.blit(titleSurf, titleRect)

        scoreText = f"Score Final: {self.score}"
        scoreSurf: Surface = self.scoreFont.render(scoreText, True, GOLD)
        scoreRect = scoreSurf.get_rect(center=(cx, cy + self._s(10)))

        scoreShadow = self.scoreFont.render(scoreText, True, (100, 80, 0))
        screen.blit(scoreShadow, scoreSurf.get_rect(center=(cx + self._s(2), cy + self._s(12))))
        screen.blit(scoreSurf, scoreRect)

        restartSurf: Surface = self.smallFont.render(GAME_RESTART, True, WHITE)
        restartRect = restartSurf.get_rect(center=(cx, cy + self._s(90)))
        screen.blit(restartSurf, restartRect)
