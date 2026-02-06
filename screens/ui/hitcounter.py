from __future__ import annotations

from pygame import Surface

from screens.ui.primitives import glassPanel, tablerIcon


class HitCounter:
    def __init__(self, scale: float) -> None:
        self.scale = scale
        self._cachedHits: int = -1
        self._cachedMaxHits: int = -1
        self._cachedSurf: Surface | None = None

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def onResize(self, scale: float) -> None:
        self.scale = scale
        self._cachedHits = -1
        self._cachedMaxHits = -1
        self._cachedSurf = None

    def _drawHeart(self, surf: Surface, cx: int, cy: int, size: int, color: str) -> None:
        from pytablericons import FilledIcon  # type: ignore[import-untyped]
        icon = tablerIcon(FilledIcon.HEART, size, color)
        surf.blit(icon, (cx - size // 2, cy - size // 2))

    def draw(self, screen: Surface, x: int, y: int, hitCount: int, maxHits: int) -> None:
        if hitCount == self._cachedHits and maxHits == self._cachedMaxHits and self._cachedSurf is not None:
            screen.blit(self._cachedSurf, (x, y))
            return

        self._cachedHits = hitCount
        self._cachedMaxHits = maxHits

        boxW = self._s(170)
        boxH = self._s(56)
        surf = glassPanel(boxW, boxH, self.scale)

        heartSize = self._s(28)
        spacing = self._s(42)
        totalHeartsW = (maxHits - 1) * spacing + heartSize
        startX = (boxW - totalHeartsW) // 2 + heartSize // 2
        centerY = boxH // 2

        for i in range(maxHits):
            cx = startX + i * spacing
            color = '#32343F' if i < hitCount else '#DC3232'
            self._drawHeart(surf, cx, centerY, heartSize, color)

        self._cachedSurf = surf
        screen.blit(self._cachedSurf, (x, y))
