from dataclasses import dataclass, field
from pathlib import Path
from typing import Final
import random

import pygame
from pygame import Surface

TILE_SIZE: Final[int] = 64


@dataclass(slots=True)
class Tile:
    id: int
    surface: Surface
    solid: bool = False


class TileSet:
    def __init__(self, path: Path) -> None:
        self.tiles: dict[int, Tile] = {}
        if path.exists() and path.is_dir():
            self._load_tiles(path)
        if not self.tiles:
            self._create_fallback_tiles()

    def _load_tiles(self, path: Path) -> None:
        pngs = sorted(path.glob("*.png"))
        for i, p in enumerate(pngs):
            try:
                surf = pygame.image.load(str(p)).convert()
                self.tiles[i] = Tile(id=i, surface=surf, solid=True)
            except pygame.error:
                pass

    def _create_fallback_tiles(self) -> None:
        base_r, base_g, base_b = 139, 69, 19
        for i in range(4):
            surf = Surface((TILE_SIZE, TILE_SIZE))
            r = base_r + random.randint(-15, 15)
            g = base_g + random.randint(-10, 10)
            b = base_b + random.randint(-8, 8)
            surf.fill((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))

            for _ in range(random.randint(3, 7)):
                x = random.randint(0, TILE_SIZE - 8)
                y = random.randint(0, TILE_SIZE - 4)
                w = random.randint(6, 14)
                h = random.randint(2, 5)
                shade = random.randint(-30, 30)
                cr = max(0, min(255, r + shade))
                cg = max(0, min(255, g + shade))
                cb = max(0, min(255, b + shade))
                pygame.draw.rect(surf, (cr, cg, cb), (x, y, w, h))

            self.tiles[i] = Tile(id=i, surface=surf.convert(), solid=True)

    def get(self, tile_id: int) -> Tile | None:
        return self.tiles.get(tile_id)


class GroundTilemap:
    BUFFER_COLUMNS: int = 3

    def __init__(self, tileset: TileSet, screen_w: int, ground_y: int, ground_h: int) -> None:
        self.tileset = tileset
        self.screen_w = screen_w
        self.ground_y = ground_y
        self.ground_h = ground_h
        self.scroll_offset: float = 0.0
        self.pattern: list[int] = []
        self.strip_cache: dict[int, Surface] = {}
        self._setup()

    def _setup(self) -> None:
        cols_needed = (self.screen_w // TILE_SIZE) + self.BUFFER_COLUMNS + 2
        self.pattern = self._generate_pattern(cols_needed)
        self._build_strip_cache()

    def _generate_pattern(self, length: int = 0) -> list[int]:
        if not self.tileset.tiles:
            return [0] * length
        tile_ids = list(self.tileset.tiles.keys())
        weights = [3] + [1] * (len(tile_ids) - 1) if len(tile_ids) > 1 else [1]
        return random.choices(tile_ids, weights=weights, k=length)

    def _build_strip_cache(self) -> None:
        self.strip_cache.clear()
        for tile_id, tile in self.tileset.tiles.items():
            self.strip_cache[tile_id] = tile.surface

    def update(self, scroll_delta: float) -> None:
        self.scroll_offset += scroll_delta

        while self.scroll_offset >= TILE_SIZE:
            self.scroll_offset -= TILE_SIZE
            self.pattern.pop(0)
            if self.tileset.tiles:
                tile_ids = list(self.tileset.tiles.keys())
                self.pattern.append(random.choice(tile_ids))

    def draw(self, screen: Surface) -> None:
        x = -int(self.scroll_offset)
        for tile_id in self.pattern:
            if x > self.screen_w:
                break
            if (tile := self.strip_cache.get(tile_id)):
                screen.blit(tile, (x, self.ground_y))
            x += TILE_SIZE

    def on_resize(self, screen_w: int, ground_y: int, ground_h: int) -> None:
        self.screen_w = screen_w
        self.ground_y = ground_y
        self.ground_h = ground_h
        self._setup()


@dataclass(slots=True)
class DecorSprite:
    x: float
    y: int
    surface: Surface


class DecorLayer:
    def __init__(self, tileset: TileSet, ground_y: int) -> None:
        self.tileset = tileset
        self.ground_y = ground_y
        self.sprites: list[DecorSprite] = []

    def add(self, sprite: DecorSprite) -> None:
        self.sprites.append(sprite)

    def spawn_random(self, x: float) -> None:
        if not self.tileset.tiles:
            return
        tile = random.choice(list(self.tileset.tiles.values()))
        y = self.ground_y - tile.surface.get_height()
        self.sprites.append(DecorSprite(x=x, y=y, surface=tile.surface))

    def update(self, scroll_speed: float, dt: float) -> None:
        delta = scroll_speed * dt
        for s in self.sprites:
            s.x -= delta
        self.sprites = [s for s in self.sprites if s.x + s.surface.get_width() > 0]

    def draw(self, screen: Surface) -> None:
        for s in self.sprites:
            screen.blit(s.surface, (int(s.x), s.y))

    def set_ground_y(self, ground_y: int) -> None:
        self.ground_y = ground_y


class CeilingTileSet:
    def __init__(self, path: Path) -> None:
        self.tiles: dict[int, Tile] = {}
        if path.exists() and path.is_dir():
            self._load_tiles(path)
        if not self.tiles:
            self._create_fallback_tiles()

    def _load_tiles(self, path: Path) -> None:
        pngs = sorted(path.glob("*.png"))
        for i, p in enumerate(pngs):
            try:
                surf = pygame.image.load(str(p)).convert()
                self.tiles[i] = Tile(id=i, surface=surf, solid=True)
            except pygame.error:
                pass

    def _create_fallback_tiles(self) -> None:
        base_r, base_g, base_b = 50, 45, 40
        for i in range(4):
            surf = Surface((TILE_SIZE, TILE_SIZE))
            r = base_r + random.randint(-10, 10)
            g = base_g + random.randint(-8, 8)
            b = base_b + random.randint(-8, 8)
            surf.fill((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))

            for _ in range(random.randint(2, 5)):
                x = random.randint(0, TILE_SIZE - 10)
                y = random.randint(0, TILE_SIZE - 6)
                w = random.randint(8, 20)
                h = random.randint(3, 8)
                shade = random.randint(-20, 20)
                cr = max(0, min(255, r + shade))
                cg = max(0, min(255, g + shade))
                cb = max(0, min(255, b + shade))
                pygame.draw.rect(surf, (cr, cg, cb), (x, y, w, h))

            highlight = (min(255, r + 20), min(255, g + 20), min(255, b + 20))
            pygame.draw.line(surf, highlight, (0, 2), (TILE_SIZE, 2), 1)

            self.tiles[i] = Tile(id=i, surface=surf.convert(), solid=True)

    def get(self, tile_id: int) -> Tile | None:
        return self.tiles.get(tile_id)


@dataclass(slots=True)
class CeilingTileData:
    tile_id: int
    has_cage: bool = False
    cage_spawned: bool = False


class CeilingTilemap:
    BUFFER_COLUMNS: int = 3
    CAGE_CHANCE: float = 0.12
    MIN_TILES_BETWEEN_CAGES: int = 4

    def __init__(self, tileset: CeilingTileSet, screen_w: int, ceiling_h: int = 60) -> None:
        self.tileset = tileset
        self.screen_w = screen_w
        self.ceiling_h = ceiling_h
        self.scroll_offset: float = 0.0
        self.pattern: list[CeilingTileData] = []
        self.strip_cache: dict[int, Surface] = {}
        self._tiles_since_cage: int = self.MIN_TILES_BETWEEN_CAGES
        self._setup()

    def _setup(self) -> None:
        cols_needed = (self.screen_w // TILE_SIZE) + self.BUFFER_COLUMNS + 2
        self.pattern = self._generate_pattern(cols_needed)
        self._build_strip_cache()

    def _generate_pattern(self, length: int = 0) -> list[CeilingTileData]:
        if not self.tileset.tiles:
            return [CeilingTileData(tile_id=0) for _ in range(length)]
        tile_ids = list(self.tileset.tiles.keys())
        weights = [3] + [1] * (len(tile_ids) - 1) if len(tile_ids) > 1 else [1]
        tiles = random.choices(tile_ids, weights=weights, k=length)
        return [CeilingTileData(tile_id=t) for t in tiles]

    def _build_strip_cache(self) -> None:
        self.strip_cache.clear()
        for tile_id, tile in self.tileset.tiles.items():
            orig = tile.surface
            if orig.get_height() != self.ceiling_h:
                scaled = pygame.transform.scale(orig, (TILE_SIZE, self.ceiling_h))
                self.strip_cache[tile_id] = scaled
            else:
                self.strip_cache[tile_id] = orig

    def _maybe_add_cage(self, tile_data: CeilingTileData) -> None:
        if self._tiles_since_cage >= self.MIN_TILES_BETWEEN_CAGES:
            if random.random() < self.CAGE_CHANCE:
                tile_data.has_cage = True
                self._tiles_since_cage = 0
                return
        self._tiles_since_cage += 1

    def _append_new_tile(self) -> None:
        if self.tileset.tiles:
            tile_ids = list(self.tileset.tiles.keys())
            new_tile = CeilingTileData(tile_id=random.choice(tile_ids))
            self._maybe_add_cage(new_tile)
            self.pattern.append(new_tile)

    def update(self, scroll_delta: float) -> list[int]:
        self.scroll_offset += scroll_delta
        cage_spawn_xs: list[int] = []

        while self.scroll_offset >= TILE_SIZE:
            self.scroll_offset -= TILE_SIZE
            self.pattern.pop(0)
            self._append_new_tile()

        spawn_threshold = self.screen_w + TILE_SIZE
        x = -int(self.scroll_offset)
        for tile_data in self.pattern:
            if x > spawn_threshold:
                break
            if tile_data.has_cage and not tile_data.cage_spawned:
                if x + TILE_SIZE > self.screen_w:
                    cage_x = x + TILE_SIZE // 2
                    cage_spawn_xs.append(cage_x)
                    tile_data.cage_spawned = True
            x += TILE_SIZE

        return cage_spawn_xs

    def draw(self, screen: Surface) -> None:
        x = -int(self.scroll_offset)
        for tile_data in self.pattern:
            if x > self.screen_w:
                break
            if (tile := self.strip_cache.get(tile_data.tile_id)):
                screen.blit(tile, (x, 0))
            x += TILE_SIZE

    def on_resize(self, screen_w: int, ceiling_h: int | None = None) -> None:
        self.screen_w = screen_w
        if ceiling_h is not None:
            self.ceiling_h = ceiling_h
        self._setup()
