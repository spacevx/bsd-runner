from __future__ import annotations

import pygame
from pygame import Surface
from pygame.font import Font

from screens.ui.primitives import _gradientRect, tablerIcon

_cardTopAvail = (30, 32, 42)
_cardBotAvail = (18, 20, 28)
_cardBorderAvail = (170, 30, 40)
_cardBorderHover = (235, 90, 100)

_cardTopLocked = (22, 23, 28)
_cardBotLocked = (15, 16, 20)
_cardBorderLocked = (35, 37, 45)

_cardTopCompleted = (25, 35, 30)
_cardBotCompleted = (15, 22, 18)
_cardBorderCompleted = (40, 150, 60)
_cardBorderCompletedHover = (60, 200, 90)

_textColor = (240, 240, 245)
_dimText = (90, 92, 100)


def buildLevelCard(
    w: int, h: int, levelId: int, name: str, finaleScore: int,
    state: str, bHighlight: bool,
    numberFont: Font, nameFont: Font, infoFont: Font,
    scale: float, targetLabel: str,
) -> Surface:
    from pytablericons import OutlineIcon, FilledIcon  # type: ignore[import-untyped]

    def _s(val: int) -> int:
        return max(1, int(val * scale))

    cr = _s(12)

    if state == "locked":
        top, bot = _cardTopLocked, _cardBotLocked
        border = _cardBorderLocked
        textCol = _dimText
    elif state == "completed":
        top, bot = _cardTopCompleted, _cardBotCompleted
        border = _cardBorderCompletedHover if bHighlight else _cardBorderCompleted
        textCol = _textColor
    else:
        top, bot = _cardTopAvail, _cardBotAvail
        border = _cardBorderHover if bHighlight else _cardBorderAvail
        textCol = _textColor

    surf = _gradientRect(w, h, top, bot, 220, cr)
    bw = _s(2) if bHighlight else 1
    pygame.draw.rect(surf, border, (0, 0, w, h), bw, border_radius=cr)

    if bHighlight and state != "locked":
        glowSurf = Surface((w + 4, h + 4), pygame.SRCALPHA)
        pygame.draw.rect(glowSurf, (*border, 25), (0, 0, w + 4, h + 4), border_radius=cr + 2)
        surf.blit(glowSurf, (-2, -2))

    cx = w // 2
    y = _s(30)

    numText = str(levelId)
    numSurf = numberFont.render(numText, True, textCol)
    numShadow = numberFont.render(numText, True, (0, 0, 0))
    surf.blit(numShadow, numShadow.get_rect(center=(cx + 2, y + 2)))
    surf.blit(numSurf, numSurf.get_rect(center=(cx, y)))

    y += _s(38)
    nameSurf = nameFont.render(name, True, textCol)
    nameShadow = nameFont.render(name, True, (0, 0, 0))
    surf.blit(nameShadow, nameShadow.get_rect(center=(cx + 1, y + 1)))
    surf.blit(nameSurf, nameSurf.get_rect(center=(cx, y)))

    y += _s(34)
    iconSize = _s(28)
    if state == "completed":
        icon = tablerIcon(FilledIcon.CIRCLE_CHECK, iconSize, '#32DC50')
    elif state == "locked":
        icon = tablerIcon(OutlineIcon.LOCK, iconSize, '#5A5C64')
    else:
        icon = tablerIcon(OutlineIcon.PLAYER_PLAY, iconSize, '#EA5A64')
    surf.blit(icon, icon.get_rect(center=(cx, y)))

    y += _s(30)
    targetCol = _dimText if state == "locked" else (180, 180, 190)
    targetSurf = infoFont.render(targetLabel, True, targetCol)
    surf.blit(targetSurf, targetSurf.get_rect(center=(cx, y)))

    return surf
