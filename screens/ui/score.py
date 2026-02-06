from __future__ import annotations

import pygame
from pygame import Surface
from pygame.font import Font

from screens.ui.primitives import glassPanel, drawTextWithShadow


class ScoreDisplay:
    def __init__(self, scale: float) -> None:
        self.scale = scale
        self.displayScore: float = 0.0
        self._cachedVal: int = -1
        self._cachedSurf: Surface | None = None
        self._cachedBoxSurf: Surface | None = None

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def reset(self) -> None:
        self.displayScore = 0.0
        self._cachedVal = -1
        self._cachedSurf = None
        self._cachedBoxSurf = None

    def onResize(self, scale: float) -> None:
        self.scale = scale
        self._cachedVal = -1
        self._cachedSurf = None
        self._cachedBoxSurf = None

    def draw(self, screen: Surface, x: int, y: int, score: int, dt: float, font: Font) -> None:
        if self._cachedBoxSurf is None:
            self._cachedBoxSurf = glassPanel(self._s(260), self._s(56), self.scale)

        screen.blit(self._cachedBoxSurf, (x, y))

        t = min(1.0, 1.0 - 0.04 ** dt)
        self.displayScore = pygame.math.lerp(self.displayScore, float(score), t)
        if abs(self.displayScore - score) < 1.0:
            self.displayScore = float(score)
        shown = int(self.displayScore)

        if shown != self._cachedVal:
            self._cachedVal = shown
            boxW = self._cachedBoxSurf.get_width()
            boxH = self._cachedBoxSurf.get_height()
            self._cachedSurf = pygame.Surface((boxW, boxH), pygame.SRCALPHA)
            drawTextWithShadow(self._cachedSurf, f"Score: {shown}", font,
                               (240, 240, 245), (self._s(10), self._s(10)), self._s(2))

        if self._cachedSurf:
            screen.blit(self._cachedSurf, (x, y))
