from __future__ import annotations

import pygame
from pygame import Surface
from pygame.font import Font

_dirs4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_diag4 = [(-1, -1), (1, -1), (-1, 1), (1, 1)]


def _rect(rendered: Surface, x: int, y: int) -> pygame.Rect:
    return rendered.get_rect(center=(x, y))


def drawGlowTitle(
    surf: Surface, text: str, font: Font,
    cx: int, cy: int,
    mainColor: tuple[int, int, int],
    glowColor: tuple[int, int, int],
    shadowColor: tuple[int, int, int],
    glowSize: int,
    peakAlpha: int = 60,
    shadowOffset: int = 3,
    pulse: float = 1.0,
    bDiagonal: bool = False,
) -> None:
    rendered = font.render(text, True, mainColor)

    for offset in range(glowSize, 0, -2):
        alpha = int(peakAlpha * (1 - offset / glowSize) * pulse)
        glow = font.render(text, True, glowColor)
        glow.set_alpha(alpha)
        for dx, dy in _dirs4:
            surf.blit(glow, _rect(rendered, cx + dx * offset, cy + dy * offset))
        if bDiagonal:
            half = offset // 2
            for dx, dy in _diag4:
                surf.blit(glow, _rect(rendered, cx + dx * half, cy + dy * half))

    shadow = font.render(text, True, shadowColor)
    surf.blit(shadow, _rect(rendered, cx + shadowOffset, cy + shadowOffset))
    surf.blit(rendered, _rect(rendered, cx, cy))


def drawSectionHeader(
    surf: Surface, text: str, font: Font,
    cx: int, cy: int,
    color: tuple[int, int, int] = (255, 215, 0),
    glowAlpha: int = 40, glowDist: int = 2,
) -> None:
    glow = font.render(text, True, color)
    glow.set_alpha(glowAlpha)
    for dx, dy in _dirs4:
        surf.blit(glow, _rect(glow, cx + dx * glowDist, cy + dy * glowDist))
    main = font.render(text, True, color)
    surf.blit(main, _rect(main, cx, cy))
