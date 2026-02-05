import math
import sys
from typing import Any, Callable

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.font import Font

from settings import GameState, ScreenSize
from keybindings import keyBindings
from strings import (
    optionsTitle, optionsControls, optionsJump, optionsSlide,
    optionsReset, optionsBack, optionsPressKey,
    optionsController, optionsJoyJump, optionsJoySlide,
    optionsJoyReset, optionsNoController, optionsPressButton
)

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
        self.normalBg: tuple[int, int, int] = normalBg
        self.hoverBg: tuple[int, int, int] = hoverBg
        self.activeBg: tuple[int, int, int] = activeBg
        self.textColor: tuple[int, int, int] = textColor
        self.borderColor: tuple[int, int, int] = borderColor
        self.borderWidth: int = borderWidth
        self.bHovered: bool = False
        self.bPressed: bool = False

    def setText(self, text: str) -> None:
        self.text = text

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


class OptionsScreen:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: ScreenSize, setStateCallback: Callable[[GameState], None]) -> None:
        self.setState: Callable[[GameState], None] = setStateCallback
        self.screenSize: ScreenSize = screenSize
        self.scale: float = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)

        self.bBrowser: bool = _BROWSER

        self.manager: Any = None
        if not self.bBrowser:
            self.manager = UIManager(self.screenSize, theme_path=None)
            self._setupTheme()

        self.bgCache: Surface | None = None
        self.vignetteCache: Surface | None = None
        self.panelCache: Surface | None = None
        self._buildCaches()

        self.jumpBtn: _SimpleButton
        self.slideBtn: _SimpleButton
        self.resetBtn: Any = None
        self.backBtn: Any = None
        self.buttonFont: Font = pygame.font.Font(None, self._s(28))
        self.labelFont: Font = pygame.font.Font(None, self._s(32))

        self._createKeyButtons()
        self._createActionButtons()

        self.titleFont: Font = pygame.font.Font(None, self._s(120))
        self.sectionFont: Font = pygame.font.Font(None, self._s(48))

        self.time: float = 0.0
        self.titlePulse: float = 0.0

        self.bListeningJump: bool = False
        self.bListeningSlide: bool = False

        self.controllerLabel: _SimpleButton | None = None
        self.joyJumpBtn: _SimpleButton | None = None
        self.joySlideBtn: _SimpleButton | None = None
        self.joyResetBtn: Any = None
        self.bWaitingForJoyInput: bool = False
        self.pendingJoyAction: Any = None
        self._createJoystickButtons()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _setupTheme(self) -> None:
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

    def _getKeyButtonRects(self) -> tuple[pygame.Rect, pygame.Rect]:
        w, h = self.screenSize
        cx = w // 2
        baseY = int(h * 0.45)
        gap = self._s(80)
        btnW, btnH = self._s(80), self._s(60)
        labelOffset = self._s(120)

        jumpRect = pygame.Rect(cx + labelOffset - btnW // 2, baseY, btnW, btnH)
        slideRect = pygame.Rect(cx + labelOffset - btnW // 2, baseY + gap, btnW, btnH)
        return jumpRect, slideRect

    def _getActionButtonRects(self) -> tuple[pygame.Rect, pygame.Rect]:
        w, h = self.screenSize
        cx = w // 2
        baseY = int(h * 0.75)
        btnW, btnH = self._s(220), self._s(60)
        gap = self._s(40)

        resetRect = pygame.Rect(cx - btnW - gap // 2, baseY, btnW, btnH)
        backRect = pygame.Rect(cx + gap // 2, baseY, btnW, btnH)
        return resetRect, backRect

    def _createKeyButtons(self) -> None:
        jumpRect, slideRect = self._getKeyButtonRects()

        self.jumpBtn = _SimpleButton(
            jumpRect, keyBindings.getKeyName(keyBindings.jump), self.buttonFont,
            normalBg=(42, 42, 53), hoverBg=(58, 58, 69), activeBg=(74, 74, 85),
            borderColor=(255, 215, 0)
        )

        self.slideBtn = _SimpleButton(
            slideRect, keyBindings.getKeyName(keyBindings.slide), self.buttonFont,
            normalBg=(42, 42, 53), hoverBg=(58, 58, 69), activeBg=(74, 74, 85),
            borderColor=(255, 215, 0)
        )

    def _createActionButtons(self) -> None:
        resetRect, backRect = self._getActionButtonRects()

        if self.bBrowser:
            self.resetBtn = _SimpleButton(resetRect, optionsReset, self.buttonFont)
            self.backBtn = _SimpleButton(backRect, optionsBack, self.buttonFont)
        else:
            self.resetBtn = UIButton(
                relative_rect=resetRect, text=optionsReset,
                manager=self.manager, object_id=ObjectID(object_id="#reset_btn")
            )
            self.backBtn = UIButton(
                relative_rect=backRect, text=optionsBack,
                manager=self.manager, object_id=ObjectID(object_id="#back_btn")
            )

    def _createJoystickButtons(self) -> None:
        from entities.input.manager import InputManager, GameAction
        from entities.input.joybindings import JoyBindings
        from entities.input.joyicons import JoyIcons

        w, h = self.screenSize
        cx = w // 2
        baseY = int(h * 0.45)
        gap = self._s(80)
        labelX = cx - self._s(200)
        btnX = cx + self._s(50)
        btnW, btnH = self._s(200), self._s(60)

        joyBaseY = baseY + gap * 3

        self.controllerLabel = _SimpleButton(
            pygame.Rect(labelX, joyBaseY - gap, btnW, btnH // 2),
            self._getControllerStatusText(),
            pygame.font.Font(None, self._s(24)),
            normalBg=(30, 30, 35), hoverBg=(30, 30, 35), activeBg=(30, 30, 35),
            borderColor=(80, 80, 90), borderWidth=2
        )

        self.joyJumpBtn = _SimpleButton(
            pygame.Rect(btnX, joyBaseY, btnW, btnH),
            self._getJoyBindingText(GameAction.JUMP),
            self.buttonFont,
            normalBg=(42, 42, 53), hoverBg=(58, 58, 69), activeBg=(74, 74, 85),
            borderColor=(255, 215, 0)
        )

        self.joySlideBtn = _SimpleButton(
            pygame.Rect(btnX, joyBaseY + gap, btnW, btnH),
            self._getJoyBindingText(GameAction.SLIDE),
            self.buttonFont,
            normalBg=(42, 42, 53), hoverBg=(58, 58, 69), activeBg=(74, 74, 85),
            borderColor=(255, 215, 0)
        )

        joyResetRect = pygame.Rect(btnX, joyBaseY + gap * 2, btnW, btnH)
        if self.bBrowser:
            self.joyResetBtn = _SimpleButton(joyResetRect, optionsJoyReset, self.buttonFont)
        else:
            self.joyResetBtn = UIButton(
                relative_rect=joyResetRect, text=optionsJoyReset,
                manager=self.manager, object_id=ObjectID(object_id="#joy_reset_btn")
            )

    def _getControllerStatusText(self) -> str:
        from entities.input.manager import InputManager
        im = InputManager()
        if im.bJoystickConnected:
            return f"{optionsController}: {im.getJoystickName()}"
        return optionsNoController

    def _getJoyBindingText(self, action: "GameAction") -> str:
        from entities.input.joybindings import JoyBindings
        from entities.input.joyicons import JoyIcons

        binding = JoyBindings().getBinding(action)
        if binding and binding.button is not None:
            name = JoyIcons().getButtonName(binding.button)
            return f"{action.name}: {name}"
        return f"{action.name}: Not Set"

    def _updateKeyButtons(self) -> None:
        if self.bListeningJump:
            self.jumpBtn.setText(optionsPressKey)
        else:
            self.jumpBtn.setText(keyBindings.getKeyName(keyBindings.jump))

        if self.bListeningSlide:
            self.slideBtn.setText(optionsPressKey)
        else:
            self.slideBtn.setText(keyBindings.getKeyName(keyBindings.slide))

    def _updateJoyButtons(self) -> None:
        from entities.input.manager import GameAction

        if self.controllerLabel:
            self.controllerLabel.setText(self._getControllerStatusText())
        if self.joyJumpBtn:
            if self.bWaitingForJoyInput and self.pendingJoyAction == GameAction.JUMP:
                self.joyJumpBtn.setText(optionsPressButton)
            else:
                self.joyJumpBtn.setText(self._getJoyBindingText(GameAction.JUMP))
        if self.joySlideBtn:
            if self.bWaitingForJoyInput and self.pendingJoyAction == GameAction.SLIDE:
                self.joySlideBtn.setText(optionsPressButton)
            else:
                self.joySlideBtn.setText(self._getJoyBindingText(GameAction.SLIDE))

    def _updateButtonPositions(self) -> None:
        jumpRect, slideRect = self._getKeyButtonRects()
        resetRect, backRect = self._getActionButtonRects()

        self.jumpBtn.setPosition(jumpRect.x, jumpRect.y)
        self.jumpBtn.setDimensions(jumpRect.width, jumpRect.height)
        self.slideBtn.setPosition(slideRect.x, slideRect.y)
        self.slideBtn.setDimensions(slideRect.width, slideRect.height)

        if self.bBrowser:
            self.resetBtn.setPosition(resetRect.x, resetRect.y)
            self.resetBtn.setDimensions(resetRect.width, resetRect.height)
            self.backBtn.setPosition(backRect.x, backRect.y)
            self.backBtn.setDimensions(backRect.width, backRect.height)
        else:
            self.resetBtn.set_relative_position((resetRect.x, resetRect.y))
            self.resetBtn.set_dimensions((resetRect.width, resetRect.height))
            self.backBtn.set_relative_position((backRect.x, backRect.y))
            self.backBtn.set_dimensions((backRect.width, backRect.height))

    def _buildCaches(self) -> None:
        w, h = self.screenSize
        self.bgCache = self._createGradientBg(w, h)
        self.vignetteCache = self._createVignette(w, h)
        self.panelCache = self._createPanel()

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

    def _createPanel(self) -> Surface:
        panelW, panelH = self._s(600), self._s(280)
        surf = pygame.Surface((panelW, panelH), pygame.SRCALPHA)
        pygame.draw.rect(surf, (30, 30, 35, 220), (0, 0, panelW, panelH), border_radius=self._s(15))
        pygame.draw.rect(surf, (139, 0, 0, 180), (0, 0, panelW, panelH), self._s(3), border_radius=self._s(15))
        return surf.convert_alpha()

    def _drawTitle(self, surf: Surface) -> None:
        w, h = self.screenSize
        cx, ty = w // 2, int(h * 0.15)
        text = optionsTitle
        pulse = 0.9 + 0.1 * math.sin(self.titlePulse)

        for offset in range(self._s(15), 0, -2):
            alpha = int(60 * (1 - offset / self._s(15)) * pulse)
            glowSurf = self.titleFont.render(text, True, (139, 0, 0))
            glowSurf.set_alpha(alpha)
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                rect = glowSurf.get_rect(center=(cx + dx, ty + dy))
                surf.blit(glowSurf, rect)

        shadow = self.titleFont.render(text, True, (20, 0, 0))
        shadowRect = shadow.get_rect(center=(cx + self._s(4), ty + self._s(4)))
        surf.blit(shadow, shadowRect)

        titleSurf = self.titleFont.render(text, True, (220, 220, 230))
        titleRect = titleSurf.get_rect(center=(cx, ty))
        surf.blit(titleSurf, titleRect)

    def _drawControlsPanel(self, surf: Surface) -> None:
        w, h = self.screenSize
        cx = w // 2

        if self.panelCache:
            panelW, panelH = self.panelCache.get_size()
            panelX = cx - panelW // 2
            panelY = int(h * 0.35)
            surf.blit(self.panelCache, (panelX, panelY))

        sectionY = int(h * 0.38)
        sectionSurf = self.sectionFont.render(optionsControls, True, (255, 215, 0))
        sectionRect = sectionSurf.get_rect(center=(cx, sectionY))
        surf.blit(sectionSurf, sectionRect)

        baseY = int(h * 0.45)
        gap = self._s(80)
        labelX = cx - self._s(120)

        jumpLabelSurf = self.labelFont.render(optionsJump, True, (255, 255, 255))
        jumpLabelRect = jumpLabelSurf.get_rect(midright=(labelX, baseY + self._s(30)))
        surf.blit(jumpLabelSurf, jumpLabelRect)

        slideLabelSurf = self.labelFont.render(optionsSlide, True, (255, 255, 255))
        slideLabelRect = slideLabelSurf.get_rect(midright=(labelX, baseY + gap + self._s(30)))
        surf.blit(slideLabelSurf, slideLabelRect)

        joyBaseY = baseY + gap * 3
        joySectionSurf = self.sectionFont.render(optionsController, True, (200, 200, 255))
        joySectionRect = joySectionSurf.get_rect(midleft=(labelX - self._s(80), joyBaseY - gap + self._s(15)))
        surf.blit(joySectionSurf, joySectionRect)

        joyJumpLabelSurf = self.labelFont.render(optionsJoyJump, True, (255, 255, 255))
        joyJumpLabelRect = joyJumpLabelSurf.get_rect(midright=(labelX, joyBaseY + self._s(30)))
        surf.blit(joyJumpLabelSurf, joyJumpLabelRect)

        joySlideLabelSurf = self.labelFont.render(optionsJoySlide, True, (255, 255, 255))
        joySlideLabelRect = joySlideLabelSurf.get_rect(midright=(labelX, joyBaseY + gap + self._s(30)))
        surf.blit(joySlideLabelSurf, joySlideLabelRect)

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)

        self.buttonFont = pygame.font.Font(None, self._s(28))
        self.labelFont = pygame.font.Font(None, self._s(32))

        if not self.bBrowser:
            self.manager.set_window_resolution(newSize)
            self._setupTheme()

        self.jumpBtn.font = self.buttonFont
        self.slideBtn.font = self.buttonFont

        if self.bBrowser:
            self.resetBtn.font = self.buttonFont
            self.backBtn.font = self.buttonFont

        self._buildCaches()
        self._updateButtonPositions()
        self._updateKeyButtons()
        self.titleFont = pygame.font.Font(None, self._s(120))
        self.sectionFont = pygame.font.Font(None, self._s(48))

    def handleEvent(self, event: Event, inputEvent: "InputEvent | None" = None) -> None:
        from entities.input.manager import InputEvent, GameAction
        from entities.input.joybindings import JoyBindings, JoyBinding

        if self.bWaitingForJoyInput and event.type == pygame.JOYBUTTONDOWN:
            if self.pendingJoyAction:
                JoyBindings().setBinding(self.pendingJoyAction, JoyBinding(button=event.button))
                JoyBindings().saveConfig()
            self.bWaitingForJoyInput = False
            self.pendingJoyAction = None
            self._updateJoyButtons()
            return

        if self.bListeningJump or self.bListeningSlide:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.bListeningJump = False
                    self.bListeningSlide = False
                else:
                    if self.bListeningJump:
                        keyBindings.jump = event.key
                        self.bListeningJump = False
                    elif self.bListeningSlide:
                        keyBindings.slide = event.key
                        self.bListeningSlide = False
                self._updateKeyButtons()
                return

        if self.jumpBtn.handleEvent(event):
            self.bListeningJump = True
            self._updateKeyButtons()
            return

        if self.slideBtn.handleEvent(event):
            self.bListeningSlide = True
            self._updateKeyButtons()
            return

        if self.joyJumpBtn and self.joyJumpBtn.handleEvent(event):
            self.bWaitingForJoyInput = True
            self.pendingJoyAction = GameAction.JUMP
            self._updateJoyButtons()
            return

        if self.joySlideBtn and self.joySlideBtn.handleEvent(event):
            self.bWaitingForJoyInput = True
            self.pendingJoyAction = GameAction.SLIDE
            self._updateJoyButtons()
            return

        if self.bBrowser:
            if self.resetBtn.handleEvent(event):
                keyBindings.reset()
                self._updateKeyButtons()
            elif self.backBtn.handleEvent(event):
                self.setState(GameState.MENU)
            elif self.joyResetBtn and self.joyResetBtn.handleEvent(event):
                JoyBindings().resetToDefaults()
                JoyBindings().saveConfig()
                self._updateJoyButtons()
        else:
            self.manager.process_events(event)
            if pygame_gui and event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.resetBtn:
                    keyBindings.reset()
                    self._updateKeyButtons()
                elif event.ui_element == self.backBtn:
                    self.setState(GameState.MENU)
                elif event.ui_element == self.joyResetBtn:
                    JoyBindings().resetToDefaults()
                    JoyBindings().saveConfig()
                    self._updateJoyButtons()

    def update(self, dt: float) -> None:
        self.time += dt
        self.titlePulse += dt * 3

        if self.controllerLabel:
            self.controllerLabel.setText(self._getControllerStatusText())

        if not self.bBrowser:
            self.manager.update(dt)

    def draw(self, screen: Surface) -> None:
        if self.bgCache:
            screen.blit(self.bgCache, (0, 0))
        if self.vignetteCache:
            screen.blit(self.vignetteCache, (0, 0))

        self._drawTitle(screen)
        self._drawControlsPanel(screen)

        self.jumpBtn.draw(screen)
        self.slideBtn.draw(screen)

        if self.controllerLabel:
            self.controllerLabel.draw(screen)
        if self.joyJumpBtn:
            self.joyJumpBtn.draw(screen)
        if self.joySlideBtn:
            self.joySlideBtn.draw(screen)

        if self.bBrowser:
            self.resetBtn.draw(screen)
            self.backBtn.draw(screen)
            if self.joyResetBtn:
                self.joyResetBtn.draw(screen)
        else:
            self.manager.draw_ui(screen)
