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
        baseR, baseG, baseB = 139, 69, 19
        for i in range(4):
            surf = Surface((TILE_SIZE, TILE_SIZE))
            r = baseR + random.randint(-15, 15)
            g = baseG + random.randint(-10, 10)
            b = baseB + random.randint(-8, 8)
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

    def get(self, tileId: int) -> Tile | None:
        return self.tiles.get(tileId)


class GroundTilemap:
    BUFFER_COLUMNS: int = 3

    def __init__(self, tileset: TileSet, screenW: int, groundY: int, groundH: int) -> None:
        self.tileset = tileset
        self.screenW = screenW
        self.groundY = groundY
        self.groundH = groundH
        self.scrollOffset: float = 0.0
        self.pattern: list[int] = []
        self.stripCache: dict[int, Surface] = {}
        self._setup()

    def _setup(self) -> None:
        colsNeeded = (self.screenW // TILE_SIZE) + self.BUFFER_COLUMNS + 2
        self.pattern = self._generate_pattern(colsNeeded)
        self._build_strip_cache()

    def _generate_pattern(self, length: int = 0) -> list[int]:
        if not self.tileset.tiles:
            return [0] * length
        tileIds = list(self.tileset.tiles.keys())
        weights = [3] + [1] * (len(tileIds) - 1) if len(tileIds) > 1 else [1]
        return random.choices(tileIds, weights=weights, k=length)

    def _build_strip_cache(self) -> None:
        self.stripCache.clear()
        for tileId, tile in self.tileset.tiles.items():
            self.stripCache[tileId] = tile.surface

    def update(self, scrollDelta: float) -> None:
        self.scrollOffset += scrollDelta

        while self.scrollOffset >= TILE_SIZE:
            self.scrollOffset -= TILE_SIZE
            self.pattern.pop(0)
            if self.tileset.tiles:
                tileIds = list(self.tileset.tiles.keys())
                self.pattern.append(random.choice(tileIds))

    def draw(self, screen: Surface) -> None:
        x = -int(self.scrollOffset)
        for tileId in self.pattern:
            if x > self.screenW:
                break
            if (tile := self.stripCache.get(tileId)):
                screen.blit(tile, (x, self.groundY))
            x += TILE_SIZE

    def on_resize(self, screenW: int, groundY: int, groundH: int) -> None:
        self.screenW = screenW
        self.groundY = groundY
        self.groundH = groundH
        self._setup()


@dataclass(slots=True)
class DecorSprite:
    x: float
    y: int
    surface: Surface


class DecorLayer:
    def __init__(self, tileset: TileSet, groundY: int) -> None:
        self.tileset = tileset
        self.groundY = groundY
        self.sprites: list[DecorSprite] = []

    def add(self, sprite: DecorSprite) -> None:
        self.sprites.append(sprite)

    def spawn_random(self, x: float) -> None:
        if not self.tileset.tiles:
            return
        tile = random.choice(list(self.tileset.tiles.values()))
        y = self.groundY - tile.surface.get_height()
        self.sprites.append(DecorSprite(x=x, y=y, surface=tile.surface))

    def update(self, scrollSpeed: float, dt: float) -> None:
        delta = scrollSpeed * dt
        for s in self.sprites:
            s.x -= delta
        self.sprites = [s for s in self.sprites if s.x + s.surface.get_width() > 0]

    def draw(self, screen: Surface) -> None:
        for s in self.sprites:
            screen.blit(s.surface, (int(s.x), s.y))

    def set_ground_y(self, groundY: int) -> None:
        self.groundY = groundY


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
        baseR, baseG, baseB = 50, 45, 40
        for i in range(4):
            surf = Surface((TILE_SIZE, TILE_SIZE))
            r = baseR + random.randint(-10, 10)
            g = baseG + random.randint(-8, 8)
            b = baseB + random.randint(-8, 8)
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

    def get(self, tileId: int) -> Tile | None:
        return self.tiles.get(tileId)


@dataclass(slots=True)
class CeilingTileData:
    tileId: int
    hasCage: bool = False
    cageSpawned: bool = False


class CeilingTilemap:
    BUFFER_COLUMNS: int = 3
    CAGE_CHANCE: float = 0.12
    MIN_TILES_BETWEEN_CAGES: int = 4

    def __init__(self, tileset: CeilingTileSet, screenW: int, ceilingH: int = 60) -> None:
        self.tileset = tileset
        self.screenW = screenW
        self.ceilingH = ceilingH
        self.scrollOffset: float = 0.0
        self.pattern: list[CeilingTileData] = []
        self.stripCache: dict[int, Surface] = {}
        self._tilesSinceCage: int = self.MIN_TILES_BETWEEN_CAGES
        self._setup()

    def _setup(self) -> None:
        colsNeeded = (self.screenW // TILE_SIZE) + self.BUFFER_COLUMNS + 2
        self.pattern = self._generate_pattern(colsNeeded)
        self._build_strip_cache()

    def _generate_pattern(self, length: int = 0) -> list[CeilingTileData]:
        if not self.tileset.tiles:
            return [CeilingTileData(tileId=0) for _ in range(length)]
        tileIds = list(self.tileset.tiles.keys())
        weights = [3] + [1] * (len(tileIds) - 1) if len(tileIds) > 1 else [1]
        tiles = random.choices(tileIds, weights=weights, k=length)
        return [CeilingTileData(tileId=t) for t in tiles]

    def _build_strip_cache(self) -> None:
        self.stripCache.clear()
        for tileId, tile in self.tileset.tiles.items():
            orig = tile.surface
            if orig.get_height() != self.ceilingH:
                scaled = pygame.transform.scale(orig, (TILE_SIZE, self.ceilingH))
                self.stripCache[tileId] = scaled
            else:
                self.stripCache[tileId] = orig

    def _maybe_add_cage(self, tileData: CeilingTileData) -> None:
        if self._tilesSinceCage >= self.MIN_TILES_BETWEEN_CAGES:
            if random.random() < self.CAGE_CHANCE:
                tileData.hasCage = True
                self._tilesSinceCage = 0
                return
        self._tilesSinceCage += 1

    def _append_new_tile(self) -> None:
        if self.tileset.tiles:
            tileIds = list(self.tileset.tiles.keys())
            newTile = CeilingTileData(tileId=random.choice(tileIds))
            self._maybe_add_cage(newTile)
            self.pattern.append(newTile)

    def update(self, scrollDelta: float) -> list[int]:
        self.scrollOffset += scrollDelta
        cageSpawnXs: list[int] = []

        while self.scrollOffset >= TILE_SIZE:
            self.scrollOffset -= TILE_SIZE
            self.pattern.pop(0)
            self._append_new_tile()

        spawnThreshold = self.screenW + TILE_SIZE
        x = -int(self.scrollOffset)
        for tileData in self.pattern:
            if x > spawnThreshold:
                break
            if tileData.hasCage and not tileData.cageSpawned:
                if x + TILE_SIZE > self.screenW:
                    cageX = x + TILE_SIZE // 2
                    cageSpawnXs.append(cageX)
                    tileData.cageSpawned = True
            x += TILE_SIZE

        return cageSpawnXs

    def draw(self, screen: Surface) -> None:
        x = -int(self.scrollOffset)
        for tileData in self.pattern:
            if x > self.screenW:
                break
            if (tile := self.stripCache.get(tileData.tileId)):
                screen.blit(tile, (x, 0))
            x += TILE_SIZE

    def on_resize(self, screenW: int, ceilingH: int | None = None) -> None:
        self.screenW = screenW
        if ceilingH is not None:
            self.ceilingH = ceilingH
        self._setup()
