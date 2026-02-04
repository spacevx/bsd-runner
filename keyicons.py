import pygame
from pygame import Surface
from pathlib import Path

from paths import assetsPath

keysPath = assetsPath / "tiles" / "keys"

_cache: dict[int, Surface] = {}
_scaledCache: dict[tuple[int, int], Surface] = {}

_TILE_MAP: dict[int, int] = {
    pygame.K_0: 94, pygame.K_1: 95, pygame.K_2: 96, pygame.K_3: 97, pygame.K_4: 98,
    pygame.K_5: 99, pygame.K_6: 100, pygame.K_7: 101, pygame.K_8: 102, pygame.K_9: 103,

    pygame.K_a: 110, pygame.K_b: 111, pygame.K_c: 112, pygame.K_d: 113, pygame.K_e: 114,
    pygame.K_f: 115, pygame.K_g: 116, pygame.K_h: 117, pygame.K_i: 118, pygame.K_j: 119,
    pygame.K_k: 120, pygame.K_l: 121, pygame.K_m: 122, pygame.K_n: 123, pygame.K_o: 124,
    pygame.K_p: 125, pygame.K_q: 126, pygame.K_r: 127, pygame.K_s: 128, pygame.K_t: 129,
    pygame.K_u: 130, pygame.K_v: 131, pygame.K_w: 132, pygame.K_x: 133, pygame.K_y: 134,
    pygame.K_z: 135,

    pygame.K_UP: 188, pygame.K_DOWN: 190, pygame.K_LEFT: 192, pygame.K_RIGHT: 194,

    pygame.K_SPACE: 235,
    pygame.K_RETURN: 200,
    pygame.K_ESCAPE: 201,
    pygame.K_TAB: 189,
    pygame.K_BACKSPACE: 191,
    pygame.K_DELETE: 198,
    pygame.K_INSERT: 199,
    pygame.K_HOME: 199,
    pygame.K_END: 199,

    pygame.K_LSHIFT: 234, pygame.K_RSHIFT: 234,
    pygame.K_LCTRL: 197, pygame.K_RCTRL: 197,
    pygame.K_LALT: 187, pygame.K_RALT: 187,
    pygame.K_CAPSLOCK: 196,

    pygame.K_F1: 202, pygame.K_F2: 203, pygame.K_F3: 202, pygame.K_F4: 203,
    pygame.K_F5: 202, pygame.K_F6: 203, pygame.K_F7: 202, pygame.K_F8: 203,
    pygame.K_F9: 202, pygame.K_F10: 203, pygame.K_F11: 202, pygame.K_F12: 203,
}


def _loadTile(tileIdx: int) -> Surface | None:
    if tileIdx in _cache:
        return _cache[tileIdx]

    path = keysPath / f"tile_{tileIdx:04d}.png"
    if not path.exists():
        return None

    surf = pygame.image.load(str(path)).convert_alpha()
    _cache[tileIdx] = surf
    return surf


def getKeyIcon(key: int, size: int = 32) -> Surface | None:
    tileIdx = _TILE_MAP.get(key)
    if tileIdx is None:
        return None

    cacheKey = (tileIdx, size)
    if cacheKey in _scaledCache:
        return _scaledCache[cacheKey]

    base = _loadTile(tileIdx)
    if base is None:
        return None

    scaled = pygame.transform.smoothscale(base, (size, size))
    _scaledCache[cacheKey] = scaled
    return scaled


def hasIcon(key: int) -> bool:
    return key in _TILE_MAP


def clearCache() -> None:
    _cache.clear()
    _scaledCache.clear()
