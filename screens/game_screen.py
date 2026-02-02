import random
from pathlib import Path
from typing import Callable

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.sprite import Group

from settings import GameState, ScreenSize, WIDTH, HEIGHT, WHITE, GOLD, OBSTACLE_SPAWN_EVENT
from entities import Player, PlayerState, Chaser, Obstacle, ObstacleType, TileSet, GroundTilemap, FallingCage, Ceiling, CageState, CeilingTileSet, CeilingTilemap
from strings import GAME_OVER, GAME_RESTART

ASSETS_PATH: Path = Path(__file__).parent
TILES_PATH: Path = Path(__file__).parent.parent / "assets" / "tiles" / "ground"
CEILING_TILES_PATH: Path = Path(__file__).parent.parent / "assets" / "tiles" / "ceiling"


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

        Obstacle.clear_cache()
        self._load_background()

        self.scroll_x: float = 0.0
        self.scroll_speed: float = self.SCROLL_SPEED

        self.ground_y: int = int(HEIGHT * self.GROUND_RATIO)

        self.player: Player = Player(self._s(320), self.ground_y)
        self.chaser: Chaser = Chaser(self._s(-200), self.ground_y)

        self.all_sprites: Group[pygame.sprite.Sprite] = pygame.sprite.Group()
        self.all_sprites.add(self.player, self.chaser)

        self.obstacles: Group[Obstacle] = pygame.sprite.Group()
        self.obstacle_spawn_delay: float = 2.0
        self.last_obstacle_type: ObstacleType | None = None

        self.ceiling: Ceiling = Ceiling(self.screen_size[0], self.screen_size[1])
        self.falling_cages: Group[FallingCage] = pygame.sprite.Group()

        self.score: int = 0
        self.game_over: bool = False

        self.invincible_timer: float = 0.0
        self.invincible_duration: float = 1.0

        self._create_fonts()
        self._init_tilemap()
        self._init_ceiling_tilemap()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _create_fonts(self) -> None:
        self.font: pygame.font.Font = pygame.font.Font(None, self._s(96))
        self.small_font: pygame.font.Font = pygame.font.Font(None, self._s(42))
        self.score_font: pygame.font.Font = pygame.font.Font(None, self._s(64))

    def _load_background(self) -> None:
        path: Path = ASSETS_PATH / "background.png"
        try:
            original: Surface = pygame.image.load(str(path)).convert()
            self.background: Surface = pygame.transform.scale(original, self.screen_size)
        except (pygame.error, FileNotFoundError):
            self.background = self._create_fallback_background()
        self.bg_width: int = self.background.get_width()

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
        ground_h = h - self.ground_y
        self.tileset: TileSet = TileSet(TILES_PATH)
        self.ground_tilemap: GroundTilemap = GroundTilemap(self.tileset, w, self.ground_y, ground_h)

    def _init_ceiling_tilemap(self) -> None:
        w = self.screen_size[0]
        self.ceiling_tileset: CeilingTileSet = CeilingTileSet(CEILING_TILES_PATH)
        self.ceiling_tilemap: CeilingTilemap = CeilingTilemap(self.ceiling_tileset, w, self.ceiling.HEIGHT)

    def on_resize(self, new_size: ScreenSize) -> None:
        self.screen_size = new_size
        self.scale = min(new_size[0] / self.BASE_W, new_size[1] / self.BASE_H)
        self._load_background()
        self.ground_y = int(new_size[1] * self.GROUND_RATIO)
        self.player.set_ground_y(self.ground_y)
        self.chaser.set_ground_y(self.ground_y)
        self._create_fonts()
        ground_h = new_size[1] - self.ground_y
        self.ground_tilemap.on_resize(new_size[0], self.ground_y, ground_h)
        self.ceiling.on_resize(new_size[0])
        self.ceiling_tilemap.on_resize(new_size[0], self.ceiling.HEIGHT)

    def reset(self) -> None:
        Obstacle.clear_cache()
        FallingCage.clear_cache()
        self.ground_y = int(self.screen_size[1] * self.GROUND_RATIO)

        self.player = Player(self._s(320), self.ground_y)
        self.chaser = Chaser(self._s(-200), self.ground_y)

        self.all_sprites.empty()
        self.all_sprites.add(self.player, self.chaser)

        self.obstacles.empty()
        self.falling_cages.empty()
        self._init_ceiling_tilemap()

        self.scroll_x = 0.0
        self.score = 0
        self.game_over = False
        self.obstacle_spawn_delay = 2.0
        self.last_obstacle_type = None
        self.invincible_timer = 0.0

        pygame.time.set_timer(OBSTACLE_SPAWN_EVENT, int(self.obstacle_spawn_delay * 1000))

    def handle_event(self, event: Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.game_over:
                self.reset()
            elif not self.game_over:
                self.player.handle_input(event)

        elif event.type == OBSTACLE_SPAWN_EVENT and not self.game_over:
            self._spawn_obstacle()
            self.obstacle_spawn_delay = random.uniform(self.OBSTACLE_MIN_DELAY, self.OBSTACLE_MAX_DELAY)
            pygame.time.set_timer(OBSTACLE_SPAWN_EVENT, int(self.obstacle_spawn_delay * 1000))

    def _spawn_obstacle(self) -> None:
        x: int = self.screen_size[0] + self._s(100)

        weights: list[float] = {
            ObstacleType.LOW: [0.3, 0.7],
            ObstacleType.HIGH: [0.7, 0.3],
            None: [0.5, 0.5]
        }[self.last_obstacle_type]

        obstacle_type: ObstacleType = random.choices([ObstacleType.LOW, ObstacleType.HIGH], weights=weights)[0]
        self.last_obstacle_type = obstacle_type

        obstacle: Obstacle = Obstacle(x, self.ground_y, obstacle_type)
        obstacle.speed = self.scroll_speed
        self.obstacles.add(obstacle)

    def _spawn_cage_at(self, x: int) -> None:
        ceiling_y = self.ceiling.height
        cage = FallingCage(x, ceiling_y, self.ground_y, self.scroll_speed)
        self.falling_cages.add(cage)

    def _collision_callback(self, player: Player, obstacle: Obstacle) -> bool:
        player_hitbox: pygame.Rect = player.get_hitbox()
        obstacle_hitbox: pygame.Rect = obstacle.get_hitbox()

        if not player_hitbox.colliderect(obstacle_hitbox):
            return False

        if obstacle.obstacle_type == ObstacleType.LOW and player.state == PlayerState.JUMPING:
            if player_hitbox.bottom < obstacle_hitbox.top + self._s(20):
                return False

        if obstacle.obstacle_type == ObstacleType.HIGH and player.state == PlayerState.SLIDING:
            if player_hitbox.top > obstacle_hitbox.bottom - self._s(15):
                return False

        return True

    def _cage_collision_callback(self, player: Player, cage: FallingCage) -> bool:
        if cage.state not in (CageState.FALLING, CageState.GROUNDED):
            return False

        player_hitbox: pygame.Rect = player.get_hitbox()
        cage_hitbox: pygame.Rect = cage.get_hitbox()

        if not player_hitbox.colliderect(cage_hitbox):
            return False

        if player.state == PlayerState.SLIDING:
            if player_hitbox.top > cage_hitbox.bottom - self._s(30):
                return False

        return True

    def _check_collisions(self) -> None:
        if self.invincible_timer > 0:
            return

        hit_obstacles: list[Obstacle] = pygame.sprite.spritecollide(
            self.player, self.obstacles, dokill=False, collided=self._collision_callback
        )

        if hit_obstacles:
            self.invincible_timer = self.invincible_duration
            self.chaser.on_player_hit()
            hit_obstacles[0].kill()

        hit_cages: list[FallingCage] = pygame.sprite.spritecollide(
            self.player, self.falling_cages, dokill=False, collided=self._cage_collision_callback
        )

        if hit_cages:
            self.invincible_timer = self.invincible_duration
            self.chaser.on_player_hit()
            hit_cages[0].kill()

        if self.chaser.has_caught_player(self.player.get_hitbox()):
            self.game_over = True
            pygame.time.set_timer(OBSTACLE_SPAWN_EVENT, 0)

    def update(self, dt: float) -> None:
        if self.game_over:
            return

        scroll_delta = self.scroll_speed * dt
        self.scroll_x += scroll_delta
        if self.scroll_x >= self.bg_width:
            self.scroll_x -= self.bg_width

        self.ground_tilemap.update(scroll_delta)
        cage_xs = self.ceiling_tilemap.update(scroll_delta)
        for cx in cage_xs:
            self._spawn_cage_at(cx)
        self.score += int(self.scroll_speed * dt * 0.1)

        if self.invincible_timer > 0:
            self.invincible_timer -= dt

        self.player.update(dt)

        self.chaser.set_target(self.player.rect.centerx)
        self.chaser.update(dt)

        self.obstacles.update(dt)

        player_x = self.player.rect.centerx
        for cage in self.falling_cages:
            cage.update(dt, player_x)

        self._check_collisions()

    def _draw_ground(self, screen: Surface) -> None:
        self.ground_tilemap.draw(screen)

    def _draw_scrolling_background(self, screen: Surface) -> None:
        x1: int = -int(self.scroll_x)
        x2: int = x1 + self.bg_width

        screen.blit(self.background, (x1, 0))
        screen.blit(self.background, (x2, 0))

    def draw(self, screen: Surface) -> None:
        self._draw_scrolling_background(screen)
        self._draw_ground(screen)

        self.obstacles.draw(screen)

        for cage in self.falling_cages:
            cage.draw(screen)

        if not (self.invincible_timer > 0 and int(self.invincible_timer * 10) % 2 == 0):
            screen.blit(self.player.image, self.player.rect)

        screen.blit(self.chaser.image, self.chaser.rect)

        self.ceiling_tilemap.draw(screen)

        self._draw_ui(screen)

        if self.game_over:
            self._draw_game_over(screen)

    def _draw_text_with_shadow(self, screen: Surface, text: str, font: pygame.font.Font,
                                color: tuple[int, int, int], pos: tuple[int, int], shadow_offset: int = 2) -> None:
        shadow: Surface = font.render(text, True, (0, 0, 0))
        surf: Surface = font.render(text, True, color)
        screen.blit(shadow, (pos[0] + shadow_offset, pos[1] + shadow_offset))
        screen.blit(surf, pos)

    def _draw_ui(self, screen: Surface) -> None:
        score_x, score_y = self._s(30), self._s(25)
        score_text = f"Score: {self.score}"

        box_w = self._s(280)
        box_h = self._s(60)
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (0, 0, 0, 120), (0, 0, box_w, box_h), border_radius=self._s(8))
        pygame.draw.rect(box_surf, (255, 255, 255, 40), (0, 0, box_w, box_h), self._s(2), border_radius=self._s(8))
        screen.blit(box_surf, (score_x - self._s(10), score_y - self._s(10)))

        self._draw_text_with_shadow(screen, score_text, self.score_font, WHITE, (score_x, score_y), self._s(3))

        controls_text = "ESPACE: Sauter | BAS: Glisser"
        ctrl_x = self._s(30)
        ctrl_y = self.screen_size[1] - self._s(50)

        ctrl_surf = self.small_font.render(controls_text, True, WHITE)
        ctrl_w, ctrl_h = ctrl_surf.get_size()

        bg_surf = pygame.Surface((ctrl_w + self._s(20), ctrl_h + self._s(10)), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 100), bg_surf.get_rect(), border_radius=self._s(5))
        screen.blit(bg_surf, (ctrl_x - self._s(10), ctrl_y - self._s(5)))

        self._draw_text_with_shadow(screen, controls_text, self.small_font, WHITE, (ctrl_x, ctrl_y), self._s(2))

    def _draw_game_over(self, screen: Surface) -> None:
        w, h = self.screen_size
        overlay: Surface = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        cx, cy = w // 2, h // 2

        panel_w, panel_h = self._s(600), self._s(350)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 35, 240), (0, 0, panel_w, panel_h), border_radius=self._s(15))
        pygame.draw.rect(panel, (139, 0, 0, 200), (0, 0, panel_w, panel_h), self._s(4), border_radius=self._s(15))
        screen.blit(panel, (cx - panel_w // 2, cy - panel_h // 2))

        title_surf: Surface = self.font.render(GAME_OVER, True, (255, 50, 50))
        title_rect = title_surf.get_rect(center=(cx, cy - self._s(80)))

        for offset in range(self._s(15), 0, -3):
            glow = self.font.render(GAME_OVER, True, (139, 0, 0))
            glow.set_alpha(int(40 * (1 - offset / self._s(15))))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow, title_surf.get_rect(center=(cx + dx, cy - self._s(80) + dy)))

        shadow = self.font.render(GAME_OVER, True, (50, 0, 0))
        screen.blit(shadow, title_surf.get_rect(center=(cx + self._s(4), cy - self._s(76))))
        screen.blit(title_surf, title_rect)

        score_text = f"Score Final: {self.score}"
        score_surf: Surface = self.score_font.render(score_text, True, GOLD)
        score_rect = score_surf.get_rect(center=(cx, cy + self._s(10)))

        score_shadow = self.score_font.render(score_text, True, (100, 80, 0))
        screen.blit(score_shadow, score_surf.get_rect(center=(cx + self._s(2), cy + self._s(12))))
        screen.blit(score_surf, score_rect)

        restart_surf: Surface = self.small_font.render(GAME_RESTART, True, WHITE)
        restart_rect = restart_surf.get_rect(center=(cx, cy + self._s(90)))
        screen.blit(restart_surf, restart_rect)
