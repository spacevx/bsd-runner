from __future__ import annotations

import pygame
from pygame import Surface, Rect
from pygame.event import Event
from pygame.font import Font

_secTopN = (28, 30, 38)
_secBotN = (18, 20, 26)
_secTopH = (38, 40, 50)
_secBotH = (28, 30, 38)
_secTopP = (14, 15, 20)
_secBotP = (10, 11, 16)
_secBorder = (50, 52, 65)
_secBorderH = (180, 50, 50)
_secBorderP = (200, 40, 40)

_priTopN = (170, 30, 40)
_priBotN = (120, 15, 25)
_priTopH = (195, 45, 55)
_priBotH = (150, 25, 35)
_priTopP = (100, 12, 18)
_priBotP = (75, 8, 12)
_priBorder = (200, 60, 70)
_priBorderH = (235, 90, 100)
_priBorderP = (160, 25, 35)

_disTopN = (22, 23, 28)
_disBotN = (15, 16, 20)
_disBorder = (35, 37, 45)
_disText = (90, 92, 100)

_textColor = (240, 240, 245)
_textShadow = (0, 0, 0)
_shadowAlpha = 70
_glowAlpha = 22
_cornerR = 10
_shadowOff = 3


def _gradientRect(w: int, h: int, top: tuple[int, int, int], bot: tuple[int, int, int], alpha: int, cr: int) -> Surface:
    surf = Surface((w, h), pygame.SRCALPHA)
    if w < 1 or h < 1:
        return surf
    grad = Surface((1, 2), pygame.SRCALPHA)
    grad.set_at((0, 0), (*top, alpha))
    grad.set_at((0, 1), (*bot, alpha))
    stretched = pygame.transform.smoothscale(grad, (w, h))
    mask = Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=cr)
    stretched.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(stretched, (0, 0))
    return surf


class ModernButton:
    def __init__(
        self,
        rect: Rect,
        text: str,
        font: Font,
        variant: str = "secondary",
    ) -> None:
        self.rect = rect
        self.text = text
        self.font = font
        self.variant = variant
        self.bHovered: bool = False
        self.bPressed: bool = False
        self.bFocused: bool = False
        self.bDisabled: bool = False

        self._normalSurf: Surface | None = None
        self._hoverSurf: Surface | None = None
        self._pressedSurf: Surface | None = None
        self._disabledSurf: Surface | None = None
        self._shadowSurf: Surface | None = None
        self._glowSurf: Surface | None = None
        self._dirty: bool = True

    def setText(self, text: str) -> None:
        if self.text != text:
            self.text = text
            self._dirty = True

    def setFont(self, font: Font) -> None:
        self.font = font
        self._dirty = True

    def setPosition(self, x: int, y: int) -> None:
        self.rect.x = x
        self.rect.y = y

    def setDimensions(self, w: int, h: int) -> None:
        if self.rect.width != w or self.rect.height != h:
            self.rect.width = w
            self.rect.height = h
            self._dirty = True

    def setDisabled(self, bDisabled: bool) -> None:
        if self.bDisabled != bDisabled:
            self.bDisabled = bDisabled
            self._dirty = True

    def handleEvent(self, event: Event) -> bool:
        if self.bDisabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.bHovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.bPressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.bPressed and self.rect.collidepoint(event.pos):
                self.bPressed = False
                return True
            self.bPressed = False
        return False

    def _build(self) -> None:
        w, h = self.rect.size
        cr = max(1, _cornerR * min(w, h) // 65)

        if self.variant == "primary":
            topN, botN = _priTopN, _priBotN
            topH, botH = _priTopH, _priBotH
            topP, botP = _priTopP, _priBotP
            borderN, borderH, borderP = _priBorder, _priBorderH, _priBorderP
        else:
            topN, botN = _secTopN, _secBotN
            topH, botH = _secTopH, _secBotH
            topP, botP = _secTopP, _secBotP
            borderN, borderH, borderP = _secBorder, _secBorderH, _secBorderP

        bgAlpha = 240 if self.variant == "primary" else 230

        self._normalSurf = self._renderState(w, h, cr, topN, botN, bgAlpha, borderN)
        self._hoverSurf = self._renderState(w, h, cr, topH, botH, bgAlpha, borderH)
        self._pressedSurf = self._renderState(w, h, cr, topP, botP, bgAlpha, borderP, bPressed=True)
        self._disabledSurf = self._renderState(w, h, cr, _disTopN, _disBotN, 200, _disBorder, textColor=_disText)

        sw, sh = w + 6, h + 6
        self._shadowSurf = Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(self._shadowSurf, (0, 0, 0, _shadowAlpha), (0, _shadowOff, w + 6, h), border_radius=cr + 2)

        gw, gh = w + 4, h + 4
        self._glowSurf = Surface((gw, gh), pygame.SRCALPHA)
        glowColor = _secBorderH if self.variant == "secondary" else _priBorderH
        pygame.draw.rect(self._glowSurf, (*glowColor, _glowAlpha), (0, 0, gw, gh), border_radius=cr + 2)

        self._dirty = False

    def _renderState(
        self, w: int, h: int, cr: int,
        top: tuple[int, int, int], bot: tuple[int, int, int],
        alpha: int, border: tuple[int, int, int],
        bPressed: bool = False,
        textColor: tuple[int, int, int] = _textColor,
    ) -> Surface:
        surf = Surface((w, h), pygame.SRCALPHA)
        bg = _gradientRect(w, h, top, bot, alpha, cr)
        surf.blit(bg, (0, 0))
        pygame.draw.rect(surf, border, (0, 0, w, h), 1, border_radius=cr)

        shadow = self.font.render(self.text, True, _textShadow)
        main = self.font.render(self.text, True, textColor)
        cx, cy = w // 2, h // 2
        pressOff = 1 if bPressed else 0

        sRect = shadow.get_rect(center=(cx + 1, cy + 1 + pressOff))
        surf.blit(shadow, sRect)
        mRect = main.get_rect(center=(cx, cy + pressOff))
        surf.blit(main, mRect)

        return surf

    def draw(self, screen: Surface) -> None:
        if self._dirty or self._normalSurf is None:
            self._build()

        assert self._shadowSurf is not None
        assert self._glowSurf is not None
        assert self._normalSurf is not None
        assert self._hoverSurf is not None
        assert self._pressedSurf is not None

        screen.blit(self._shadowSurf, (self.rect.x - 3, self.rect.y - 1))

        if self.bDisabled:
            assert self._disabledSurf is not None
            screen.blit(self._disabledSurf, self.rect)
            return

        bHighlight = self.bHovered or self.bFocused
        if bHighlight and not self.bPressed:
            screen.blit(self._glowSurf, (self.rect.x - 2, self.rect.y - 2))

        if self.bPressed:
            screen.blit(self._pressedSurf, self.rect)
        elif bHighlight:
            screen.blit(self._hoverSurf, self.rect)
        else:
            screen.blit(self._normalSurf, self.rect)
