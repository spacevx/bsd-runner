import math
from typing import Callable, TYPE_CHECKING

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.font import Font

if TYPE_CHECKING:
    from entities.input.manager import InputEvent

import flags
import settings
from settings import width, height, GameState, ScreenSize
from strings import btnLevel1, btnLevel2, btnLevel2Locked, btnOptions, btnQuit
from screens.menu_bg import MenuBackground
from screens.ui import ModernButton


class MainMenu:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, setStateCallback: Callable[[GameState], None],
                 startLevelCallback: Callable[[int], None]) -> None:
        self.setState: Callable[[GameState], None] = setStateCallback
        self.startLevel: Callable[[int], None] = startLevelCallback
        self.screenSize: ScreenSize = (width, height)
        self.scale: float = min(width / self.baseW, height / self.baseH)

        self.menuBg = MenuBackground(self.screenSize)

        self.buttonFont: Font = pygame.font.Font(None, self._s(28))
        self.level1Btn: ModernButton
        self.level2Btn: ModernButton
        self.optionsBtn: ModernButton
        self.quitBtn: ModernButton
        self._createButtons()

        self.titleFont: Font = pygame.font.Font(None, self._s(160))

        self.time: float = 0.0
        self.titlePulse: float = 0.0

        self.focusedButtonIndex: int = 0
        self.buttons: list[ModernButton] = []
        self.bJoystickNavMode: bool = False
        self._updateButtonsList()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _updateButtonsList(self) -> None:
        self.buttons = [self.level1Btn, self.level2Btn, self.optionsBtn, self.quitBtn]

    def _navigateMenu(self, direction: int) -> None:
        self.focusedButtonIndex = (self.focusedButtonIndex + direction) % len(self.buttons)
        self._updateButtonFocus()

    def _updateButtonFocus(self) -> None:
        if not self.bJoystickNavMode:
            for btn in self.buttons:
                btn.bFocused = False
            return
        for i, btn in enumerate(self.buttons):
            btn.bFocused = (i == self.focusedButtonIndex)

    def _activateFocusedButton(self) -> None:
        if not self.bJoystickNavMode or not self.buttons:
            return
        focusedBtn = self.buttons[self.focusedButtonIndex]
        if focusedBtn == self.level1Btn:
            self.startLevel(1)
        elif focusedBtn == self.level2Btn and not self.level2Btn.bDisabled:
            self.startLevel(2)
        elif focusedBtn == self.optionsBtn:
            self.setState(GameState.OPTIONS)
        elif focusedBtn == self.quitBtn:
            self.setState(GameState.QUIT)

    def _getButtonRects(self) -> list[pygame.Rect]:
        w, h = self._s(420), self._s(65)
        cx = (self.screenSize[0] - w) // 2
        baseY = int(self.screenSize[1] * 0.48)
        gap = self._s(80)
        return [
            pygame.Rect(cx, baseY, w, h),
            pygame.Rect(cx, baseY + gap, w, h),
            pygame.Rect(cx, baseY + gap * 2, w, h),
            pygame.Rect(cx, baseY + gap * 3, w, h),
        ]

    def _createButtons(self) -> None:
        rects = self._getButtonRects()
        self.level1Btn = ModernButton(rects[0], btnLevel1, self.buttonFont, variant="primary")
        bLocked = not settings.bLevel2Unlocked and not flags.bUnlockAllLevels
        self.level2Btn = ModernButton(rects[1], btnLevel2Locked if bLocked else btnLevel2, self.buttonFont)
        self.level2Btn.setDisabled(bLocked)
        self.optionsBtn = ModernButton(rects[2], btnOptions, self.buttonFont)
        self.quitBtn = ModernButton(rects[3], btnQuit, self.buttonFont)
        self._updateButtonsList()

    def _refreshLevel2State(self) -> None:
        bLocked = not settings.bLevel2Unlocked and not flags.bUnlockAllLevels
        self.level2Btn.setText(btnLevel2Locked if bLocked else btnLevel2)
        self.level2Btn.setDisabled(bLocked)

    def _updateButtonPositions(self) -> None:
        rects = self._getButtonRects()
        for btn, rect in zip([self.level1Btn, self.level2Btn, self.optionsBtn, self.quitBtn], rects):
            btn.setPosition(rect.x, rect.y)
            btn.setDimensions(rect.width, rect.height)

    def _drawTitle(self, surf: Surface) -> None:
        w, h = self.screenSize
        cx, ty = w // 2, int(h * 0.18)
        text = "BSD Runner"
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
        self.buttonFont = pygame.font.Font(None, self._s(28))
        for btn in [self.level1Btn, self.level2Btn, self.optionsBtn, self.quitBtn]:
            btn.setFont(self.buttonFont)
        self.menuBg.onResize(newSize)
        self._updateButtonPositions()
        self.titleFont = pygame.font.Font(None, self._s(160))

    def handleEvent(self, event: Event, inputEvent: "InputEvent | None" = None) -> None:
        from entities.input.manager import InputEvent, GameAction, InputSource

        self._refreshLevel2State()

        if event.type == pygame.MOUSEMOTION:
            self.bJoystickNavMode = False
            self._updateButtonFocus()

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

        if self.level1Btn.handleEvent(event):
            self.startLevel(1)
        elif self.level2Btn.handleEvent(event):
            self.startLevel(2)
        elif self.optionsBtn.handleEvent(event):
            self.setState(GameState.OPTIONS)
        elif self.quitBtn.handleEvent(event):
            self.setState(GameState.QUIT)

    def update(self, dt: float) -> None:
        self.menuBg.update(dt)
        self.time += dt
        self.titlePulse += dt * 3

    def draw(self, screen: Surface) -> None:
        self.menuBg.draw(screen)
        self._drawTitle(screen)
        self.level1Btn.draw(screen)
        self.level2Btn.draw(screen)
        self.optionsBtn.draw(screen)
        self.quitBtn.draw(screen)
