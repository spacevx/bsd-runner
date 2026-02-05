import math
import sys
from typing import Any, Callable

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.font import Font

from settings import width, height, GameState, ScreenSize

_BROWSER: bool = sys.platform == "emscripten"

pygame_gui: Any = None
UIManager: Any = None
UIButton: Any = None
ObjectID: Any = None

if not _BROWSER:
    pygame_gui = __import__("pygame_gui")
    UIManager = getattr(__import__("pygame_gui", fromlist=["UIManager"]), "UIManager")
    UIButton = getattr(__import__("pygame_gui.elements", fromlist=["UIButton"]), "UIButton")
    ObjectID = getattr(__import__("pygame_gui.core", fromlist=["ObjectID"]), "ObjectID")


class _SimpleButton:
    """Pure pygame button for browser fallback."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: Font,
        normalBg: tuple[int, int, int] = (139, 0, 0),
        hoverBg: tuple[int, int, int] = (178, 34, 34),
        activeBg: tuple[int, int, int] = (220, 20, 60),
        textColor: tuple[int, int, int] = (255, 255, 255),
        borderColor: tuple[int, int, int] = (74, 74, 74),
        borderWidth: int = 3,
    ) -> None:
        self.rect: pygame.Rect = rect
        self.text: str = text
        self.font: Font = font
        self.normalBg = normalBg
        self.hoverBg = hoverBg
        self.activeBg = activeBg
        self.textColor = textColor
        self.borderColor = borderColor
        self.borderWidth = borderWidth
        self.bHovered: bool = False
        self.bPressed: bool = False

    def setPosition(self, x: int, y: int) -> None:
        self.rect.x = x
        self.rect.y = y

    def setDimensions(self, w: int, h: int) -> None:
        self.rect.width = w
        self.rect.height = h

    def handleEvent(self, event: Event) -> bool:
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

    def draw(self, screen: Surface) -> None:
        if self.bPressed:
            bg = self.activeBg
        elif self.bHovered:
            bg = self.hoverBg
        else:
            bg = self.normalBg

        pygame.draw.rect(screen, bg, self.rect, border_radius=4)
        pygame.draw.rect(screen, self.borderColor, self.rect, self.borderWidth, border_radius=4)

        textSurf = self.font.render(self.text, True, self.textColor)
        textRect = textSurf.get_rect(center=self.rect.center)
        screen.blit(textSurf, textRect)


class MainMenu:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, setStateCallback: Callable[[GameState], None]) -> None:
        self.setState: Callable[[GameState], None] = setStateCallback
        self.screenSize: ScreenSize = (width, height)
        self.scale: float = min(width / self.baseW, height / self.baseH)

        self.bBrowser: bool = _BROWSER

        self.manager: Any = None
        if not self.bBrowser:
            self.manager = UIManager(self.screenSize, theme_path=None)
            self._setupTheme()

        self.bgCache: Surface | None = None
        self.vignetteCache: Surface | None = None
        self.scanlinesCache: Surface | None = None
        self.octagonGlowCache: Surface | None = None
        self.fenceCache: tuple[Surface, Surface] | None = None

        self._buildCaches()

        self.startBtn: Any = None
        self.optionsBtn: Any = None
        self.quitBtn: Any = None
        self.buttonFont: Font | None = None

        if self.bBrowser:
            self.buttonFont = pygame.font.Font(None, self._s(28))
            self._createSimpleButtons()
        else:
            self._createButtons()

        self.titleFont: Font = pygame.font.Font(None, self._s(160))

        self.time: float = 0.0
        self.spotlightFlicker: float = 1.0
        self.titlePulse: float = 0.0

        self.focusedButtonIndex: int = 0
        self.buttons: list = []
        self.bJoystickNavMode: bool = False
        self._updateButtonsList()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _updateButtonsList(self) -> None:
        self.buttons = [self.startBtn, self.optionsBtn, self.quitBtn]

    def _navigateMenu(self, direction: int) -> None:
        self.focusedButtonIndex = (self.focusedButtonIndex + direction) % len(self.buttons)
        self._updateButtonFocus()

    def _updateButtonFocus(self) -> None:
        if not self.bJoystickNavMode:
            return
        if not self.bBrowser and self.manager:
            for i, btn in enumerate(self.buttons):
                if btn and i == self.focusedButtonIndex:
                    pass
                else:
                    pass

    def _activateFocusedButton(self) -> None:
        if not self.bJoystickNavMode or not self.buttons:
            return
        focusedBtn = self.buttons[self.focusedButtonIndex]
        if focusedBtn == self.startBtn:
            self.setState(GameState.GAME)
        elif focusedBtn == self.optionsBtn:
            self.setState(GameState.OPTIONS)
        elif focusedBtn == self.quitBtn:
            self.setState(GameState.QUIT)

    def _setupTheme(self) -> None:
        bw, bh = self._s(400), self._s(70)
        self.manager.get_theme().load_theme({
            "button": {
                "colours": {
                    "normal_bg": "#8B0000",
                    "hovered_bg": "#B22222",
                    "active_bg": "#DC143C",
                    "normal_border": "#4A4A4A",
                    "hovered_border": "#C0C0C0",
                    "active_border": "#FFD700",
                    "normal_text": "#FFFFFF",
                    "hovered_text": "#FFFFFF",
                    "active_text": "#FFFFFF"
                },
                "font": {
                    "name": "noto_sans",
                    "size": str(self._s(28)),
                    "bold": "1"
                },
                "misc": {
                    "shape": "rounded_rectangle",
                    "shape_corner_radius": "4",
                    "border_width": "3"
                }
            }
        })

    def _getButtonRects(self) -> list[pygame.Rect]:
        w, h = self._s(400), self._s(70)
        cx = (self.screenSize[0] - w) // 2
        baseY = int(self.screenSize[1] * 0.58)
        gap = self._s(90)
        return [
            pygame.Rect(cx, baseY, w, h),
            pygame.Rect(cx, baseY + gap, w, h),
            pygame.Rect(cx, baseY + gap * 2, w, h),
        ]

    def _createSimpleButtons(self) -> None:
        rects = self._getButtonRects()
        assert self.buttonFont is not None
        self.startBtn = _SimpleButton(rects[0], "COMMENCER LE JEU", self.buttonFont)
        self.optionsBtn = _SimpleButton(rects[1], "OPTIONS", self.buttonFont)
        self.quitBtn = _SimpleButton(rects[2], "QUITTER", self.buttonFont)
        self._updateButtonsList()

    def _createButtons(self) -> None:
        rects = self._getButtonRects()
        self.startBtn = UIButton(
            relative_rect=rects[0], text="COMMENCER LE JEU",
            manager=self.manager, object_id=ObjectID(object_id="#start_btn")
        )
        self.optionsBtn = UIButton(
            relative_rect=rects[1], text="OPTIONS",
            manager=self.manager, object_id=ObjectID(object_id="#options_btn")
        )
        self.quitBtn = UIButton(
            relative_rect=rects[2], text="QUITTER",
            manager=self.manager, object_id=ObjectID(object_id="#quit_btn")
        )
        self._updateButtonsList()

    def _updateButtonPositions(self) -> None:
        rects = self._getButtonRects()
        if self.bBrowser:
            for btn, rect in zip([self.startBtn, self.optionsBtn, self.quitBtn], rects):
                if btn:
                    btn.setPosition(rect.x, rect.y)
                    btn.setDimensions(rect.width, rect.height)
        else:
            for btn, rect in zip([self.startBtn, self.optionsBtn, self.quitBtn], rects):
                if btn:
                    btn.set_relative_position((rect.x, rect.y))
                    btn.set_dimensions((rect.width, rect.height))

    def _buildCaches(self) -> None:
        w, h = self.screenSize
        self.bgCache = self._createGradientBg(w, h)
        self.vignetteCache = self._createVignette(w, h)
        self.scanlinesCache = self._createScanlines(w, h)
        self.octagonGlowCache = self._createOctagonGlow(w, h)
        self.fenceCache = self._createFencePanels(w, h)

    def _createGradientBg(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h))
        for y in range(h):
            t = y / h
            r = int(5 + 35 * t * t)
            g = int(2 + 5 * t)
            b = int(5 + 8 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
        return surf.convert()

    def _createVignette(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        maxDist = math.hypot(cx, cy)
        for ring in range(0, int(maxDist), 4):
            t = ring / maxDist
            alpha = int(180 * (t ** 2.5))
            alpha = min(255, alpha)
            if alpha > 0:
                pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), int(maxDist - ring), 4)
        return surf.convert_alpha()

    def _createScanlines(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 3):
            pygame.draw.line(surf, (0, 0, 0, 25), (0, y), (w, y))
        return surf.convert_alpha()

    def _createOctagonGlow(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, int(h * 0.48)
        radius = self._s(280)

        for glowR in range(radius + self._s(60), radius, -2):
            alpha = int(15 * (1 - (glowR - radius) / self._s(60)))
            pts = [(cx + glowR * math.cos(math.pi / 8 + i * math.pi / 4),
                    cy + glowR * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
            pygame.draw.polygon(surf, (139, 0, 0, alpha), pts, self._s(3))

        ptsOuter = [(cx + radius * math.cos(math.pi / 8 + i * math.pi / 4),
                      cy + radius * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        pygame.draw.polygon(surf, (80, 80, 90), ptsOuter, self._s(4))

        innerR = radius - self._s(25)
        ptsInner = [(cx + innerR * math.cos(math.pi / 8 + i * math.pi / 4),
                      cy + innerR * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        pygame.draw.polygon(surf, (60, 60, 70), ptsInner, self._s(2))

        innerR2 = radius - self._s(50)
        ptsInner2 = [(cx + innerR2 * math.cos(math.pi / 8 + i * math.pi / 4),
                       cy + innerR2 * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        pygame.draw.polygon(surf, (45, 45, 55), ptsInner2, self._s(1))

        for i in range(8):
            angle = math.pi / 8 + i * math.pi / 4
            x1, y1 = cx + innerR2 * math.cos(angle), cy + innerR2 * math.sin(angle)
            x2, y2 = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
            pygame.draw.line(surf, (50, 50, 60), (x1, y1), (x2, y2), self._s(2))

        return surf.convert_alpha()

    def _createFencePanels(self, w: int, h: int) -> tuple[Surface, Surface]:
        panelW = self._s(120)
        left = pygame.Surface((panelW, h), pygame.SRCALPHA)
        right = pygame.Surface((panelW, h), pygame.SRCALPHA)

        spacing = self._s(18)
        wireColor = (50, 50, 60, 180)
        highlight = (70, 70, 80, 100)

        for surf, bFlip in [(left, False), (right, True)]:
            for y in range(-spacing, h + spacing, spacing):
                for x in range(-spacing, panelW + spacing, spacing):
                    x1, y1 = x, y
                    x2, y2 = x + spacing, y + spacing
                    pygame.draw.line(surf, wireColor, (x1, y1), (x2, y2), 1)
                    pygame.draw.line(surf, wireColor, (x2, y1), (x1, y2), 1)

            for x in range(0, panelW, spacing):
                for y in range(0, h, spacing):
                    pygame.draw.circle(surf, highlight, (x, y), 2)

            fadeW = panelW
            for i in range(fadeW):
                alpha = int(255 * (i / fadeW) if bFlip else 255 * (1 - i / fadeW))
                pygame.draw.line(surf, (0, 0, 0, alpha), (i, 0), (i, h))

        return left.convert_alpha(), right.convert_alpha()

    def _drawSpotlight(self, surf: Surface) -> None:
        w, h = self.screenSize
        cx = w // 2
        spotH = int(h * 0.5)
        spotSurf = pygame.Surface((w, spotH), pygame.SRCALPHA)

        intensity = 0.7 + 0.3 * self.spotlightFlicker

        for y in range(spotH):
            t = y / spotH
            spotWidth = int(self._s(50) + t * self._s(400))
            alpha = int(35 * intensity * (1 - t * 0.7))
            if alpha > 0 and spotWidth > 0:
                rect = pygame.Rect(cx - spotWidth // 2, y, spotWidth, 1)
                pygame.draw.rect(spotSurf, (255, 250, 240, alpha), rect)

        surf.blit(spotSurf, (0, 0), special_flags=pygame.BLEND_ADD)

    def _drawTitle(self, surf: Surface) -> None:
        w, h = self.screenSize
        cx, ty = w // 2, int(h * 0.18)
        text = "MMA"
        pulse = 0.9 + 0.1 * math.sin(self.titlePulse)

        for offset in range(self._s(20), 0, -2):
            alpha = int(80 * (1 - offset / self._s(20)) * pulse)
            glowSurf = self.titleFont.render(text, True, (139, 0, 0))
            glowSurf.set_alpha(alpha)
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                rect = glowSurf.get_rect(center=(cx + dx, ty + dy))
                surf.blit(glowSurf, rect)

        shadow = self.titleFont.render(text, True, (20, 0, 0))
        shadowRect = shadow.get_rect(center=(cx + self._s(5), ty + self._s(5)))
        surf.blit(shadow, shadowRect)

        base = self.titleFont.render(text, True, (180, 180, 190))
        baseRect = base.get_rect(center=(cx, ty))
        surf.blit(base, baseRect)

        gradientSurf = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        tw, th = base.get_size()
        for y in range(th):
            t = y / th
            if t < 0.5:
                r = int(220 + 35 * (1 - t * 2))
                g = int(220 + 35 * (1 - t * 2))
                b = int(230 + 25 * (1 - t * 2))
            else:
                r = int(150 + 70 * (t - 0.5) * 2)
                g = int(150 + 70 * (t - 0.5) * 2)
                b = int(160 + 70 * (t - 0.5) * 2)
            pygame.draw.line(gradientSurf, (r, g, b, 255), (0, y), (tw, y))

        mask = pygame.mask.from_surface(base)
        maskSurf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        gradientSurf.blit(maskSurf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(gradientSurf, baseRect)

        highlightSurf = pygame.Surface((tw, th // 3), pygame.SRCALPHA)
        for y in range(th // 3):
            alpha = int(60 * (1 - y / (th // 3)))
            pygame.draw.line(highlightSurf, (255, 255, 255, alpha), (0, y), (tw, y))
        highlightMasked = pygame.Surface((tw, th), pygame.SRCALPHA)
        highlightMasked.blit(highlightSurf, (0, 0))
        highlightMasked.blit(maskSurf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(highlightMasked, baseRect, special_flags=pygame.BLEND_ADD)

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        if not self.bBrowser:
            self.manager.set_window_resolution(newSize)
            self._setupTheme()
        else:
            self.buttonFont = pygame.font.Font(None, self._s(28))
            if self.startBtn:
                self.startBtn.font = self.buttonFont
            if self.optionsBtn:
                self.optionsBtn.font = self.buttonFont
            if self.quitBtn:
                self.quitBtn.font = self.buttonFont
        self._buildCaches()
        self._updateButtonPositions()
        self.titleFont = pygame.font.Font(None, self._s(160))

    def handleEvent(self, event: Event, inputEvent: "InputEvent | None" = None) -> None:
        from entities.input.manager import InputEvent, GameAction, InputSource

        if event.type == pygame.MOUSEMOTION:
            self.bJoystickNavMode = False

        if inputEvent:
            if inputEvent.source == InputSource.JOYSTICK:
                self.bJoystickNavMode = True

            if inputEvent.action == GameAction.MENU_DOWN and inputEvent.bPressed:
                self._navigateMenu(1)
            elif inputEvent.action == GameAction.MENU_UP and inputEvent.bPressed:
                self._navigateMenu(-1)
            elif inputEvent.action in (GameAction.MENU_CONFIRM, GameAction.JUMP) and inputEvent.bPressed:
                self._activateFocusedButton()
            elif inputEvent.action in (GameAction.MENU_BACK, GameAction.SLIDE) and inputEvent.bPressed:
                self.setState(GameState.MENU)

        if self.bBrowser:
            if self.startBtn and self.startBtn.handleEvent(event):
                self.setState(GameState.GAME)
            elif self.optionsBtn and self.optionsBtn.handleEvent(event):
                self.setState(GameState.OPTIONS)
            elif self.quitBtn and self.quitBtn.handleEvent(event):
                self.setState(GameState.QUIT)
        else:
            self.manager.process_events(event)
            if pygame_gui and event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.startBtn:
                    self.setState(GameState.GAME)
                elif event.ui_element == self.optionsBtn:
                    self.setState(GameState.OPTIONS)
                elif event.ui_element == self.quitBtn:
                    self.setState(GameState.QUIT)

    def update(self, dt: float) -> None:
        self.time += dt
        self.titlePulse += dt * 3
        self.spotlightFlicker = 0.85 + 0.15 * math.sin(self.time * 8) + 0.1 * math.sin(self.time * 13)
        if not self.bBrowser:
            self.manager.update(dt)

    def draw(self, screen: Surface) -> None:
        w, h = self.screenSize

        if self.bgCache:
            screen.blit(self.bgCache, (0, 0))
        if self.octagonGlowCache:
            screen.blit(self.octagonGlowCache, (0, 0))
        self._drawSpotlight(screen)

        if self.fenceCache:
            screen.blit(self.fenceCache[0], (0, 0))
            screen.blit(self.fenceCache[1], (w - self.fenceCache[1].get_width(), 0))

        if self.vignetteCache:
            screen.blit(self.vignetteCache, (0, 0))
        if self.scanlinesCache:
            screen.blit(self.scanlinesCache, (0, 0))

        self._drawTitle(screen)

        if self.bBrowser:
            if self.startBtn:
                self.startBtn.draw(screen)
            if self.optionsBtn:
                self.optionsBtn.draw(screen)
            if self.quitBtn:
                self.quitBtn.draw(screen)
        else:
            self.manager.draw_ui(screen)
