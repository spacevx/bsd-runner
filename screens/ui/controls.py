from __future__ import annotations

from dataclasses import dataclass

import pygame
from pygame import Surface
from pygame.font import Font

from screens.ui.primitives import glassPanel


@dataclass
class ControlHint:
    icon: Surface | None
    fallbackText: str
    label: str


def buildControlsPanel(hints: list[ControlHint], font: Font, scale: float) -> Surface:
    def _s(val: int) -> int:
        return max(1, int(val * scale))

    iconSize = _s(36)
    iconGap = _s(8)
    pad = _s(10)
    sepGap = _s(20)
    textColor = (240, 240, 245)
    sepColor = (80, 82, 95)

    labels = [font.render(h.label, True, textColor) for h in hints]
    sep = font.render("|", True, sepColor)

    totalW = 0
    for i, (hint, label) in enumerate(zip(hints, labels)):
        if i > 0:
            totalW += sepGap + sep.get_width() + sepGap
        if hint.icon:
            totalW += iconSize
        else:
            fb = font.render(hint.fallbackText, True, textColor)
            totalW += fb.get_width()
        totalW += iconGap + label.get_width()

    boxH = iconSize + _s(10)
    bg = glassPanel(totalW + pad * 2, boxH, scale)

    x = pad
    centerY = boxH // 2

    for i, (hint, label) in enumerate(zip(hints, labels)):
        if i > 0:
            x += sepGap
            bg.blit(sep, (x, centerY - sep.get_height() // 2))
            x += sep.get_width() + sepGap

        if hint.icon:
            bg.blit(hint.icon, (x, centerY - iconSize // 2))
            x += iconSize + iconGap
        else:
            fb = font.render(hint.fallbackText, True, textColor)
            bg.blit(fb, (x, centerY - fb.get_height() // 2))
            x += fb.get_width() + iconGap

        bg.blit(label, (x, centerY - label.get_height() // 2))
        x += label.get_width()

    return bg
