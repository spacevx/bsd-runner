import math
from typing import Callable, TYPE_CHECKING

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.font import Font

if TYPE_CHECKING:
    from entities.input.manager import InputEvent

import config
import settings
from settings import GameState, ScreenSize
from keybindings import keyBindings
from strings import (
    optionsTitle, optionsControls, optionsJump, optionsSlide, optionsRestart,
    optionsReset, optionsBack, optionsPressKey, optionsSound
)
from levels import levelConfigs, level1Config
from screens.menu_bg import MenuBackground
from screens.ui import Button, drawGlowTitle, drawSectionHeader

_bindingDefs: list[tuple[str, str]] = [
    (optionsJump, "jump"),
    (optionsSlide, "slide"),
    (optionsRestart, "restart"),
]


class OptionsScreen:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: ScreenSize, setStateCallback: Callable[[GameState], None]) -> None:
        self.setState: Callable[[GameState], None] = setStateCallback
        self.screenSize: ScreenSize = screenSize
        self.scale: float = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)

        self.menuBg = self._createMenuBg(screenSize)

        self.panelSurf: Surface | None = None

        self.buttonFont: Font = pygame.font.Font(None, self._s(28))
        self.labelFont: Font = pygame.font.Font(None, self._s(32))

        self.iconSize: int = self._s(50)
        self._icons: list[Surface | None] = [None] * len(_bindingDefs)
        self._iconRects: list[pygame.Rect] = [pygame.Rect(0, 0, 0, 0) for _ in _bindingDefs]
        self._hovered: list[bool] = [False] * len(_bindingDefs)
        self._listeningIdx: int = -1

        self._soundPanelSurf: Surface | None = None
        self._soundPanelY: int = 0
        self._soundPanelH: int = 0
        self._soundToggleRect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self._soundHovered: bool = False

        self.resetBtn: Button
        self.backBtn: Button

        self._loadKeyIcons()
        self._computeLayout()
        self._createActionButtons()

        self.titleFont: Font = pygame.font.Font(None, self._s(120))
        self.sectionFont: Font = pygame.font.Font(None, self._s(48))

        self.time: float = 0.0
        self.titlePulse: float = 0.0

    @staticmethod
    def _createMenuBg(screenSize: ScreenSize) -> MenuBackground:
        levelId = settings.lastCompletedLevel() or 1
        cfg = levelConfigs.get(levelId, level1Config)
        return MenuBackground(screenSize, backgroundPath=cfg.backgroundPath,
                              bHasCeilingTiles=cfg.bHasCeilingTiles)

    def refreshBackground(self) -> None:
        self.menuBg = self._createMenuBg(self.screenSize)

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _computeLayout(self) -> None:
        w, h = self.screenSize
        cx = w // 2

        labels = [self.labelFont.render(label, True, (240, 240, 245)) for label, _ in _bindingDefs]
        maxLabelW = max(l.get_width() for l in labels)

        rowH = self._s(60)
        iconGap = self._s(30)
        padX = self._s(50)
        headerH = self._s(65)
        padBottom = self._s(20)

        contentW = maxLabelW + iconGap + self.iconSize
        self._panelW = contentW + padX * 2
        self._panelH = headerH + len(_bindingDefs) * rowH + padBottom
        self._panelX = cx - self._panelW // 2
        self._panelY = int(h * 0.35)

        self._labelX = self._panelX + padX
        iconCenterX = self._labelX + maxLabelW + iconGap + self.iconSize // 2

        self._rowCentersY: list[int] = []
        for i in range(len(_bindingDefs)):
            rowCY = self._panelY + headerH + i * rowH + rowH // 2
            self._rowCentersY.append(rowCY)
            sz = self.iconSize
            self._iconRects[i] = pygame.Rect(
                iconCenterX - sz // 2, rowCY - sz // 2, sz, sz
            )

        soundGap = self._s(20)
        soundPadX = self._s(40)
        soundRowH = self._s(50)
        soundHeaderH = self._s(55)
        soundPadBottom = self._s(15)

        soundLabel = self.labelFont.render(optionsSound, True, (240, 240, 245))
        toggleW = self._s(70)
        toggleGap = self._s(30)
        soundContentW = soundLabel.get_width() + toggleGap + toggleW
        self._soundPanelW = soundContentW + soundPadX * 2
        self._soundPanelH = soundHeaderH + soundRowH + soundPadBottom
        self._soundPanelX = cx - self._soundPanelW // 2
        self._soundPanelY = self._panelY + self._panelH + soundGap

        self._soundLabelX = self._soundPanelX + soundPadX
        soundRowCY = self._soundPanelY + soundHeaderH + soundRowH // 2
        self._soundRowCY = soundRowCY

        toggleH = self._s(32)
        toggleX = self._soundLabelX + soundLabel.get_width() + toggleGap
        self._soundToggleRect = pygame.Rect(toggleX, soundRowCY - toggleH // 2, toggleW, toggleH)

    def _getActionButtonRects(self) -> tuple[pygame.Rect, pygame.Rect]:
        w, h = self.screenSize
        cx = w // 2
        baseY = self._soundPanelY + self._soundPanelH + self._s(30)
        btnW, btnH = self._s(220), self._s(55)
        gap = self._s(40)

        resetRect = pygame.Rect(cx - btnW - gap // 2, baseY, btnW, btnH)
        backRect = pygame.Rect(cx + gap // 2, baseY, btnW, btnH)
        return resetRect, backRect

    def _loadKeyIcons(self) -> None:
        for i, (_, attr) in enumerate(_bindingDefs):
            key: int = getattr(keyBindings, attr)
            self._icons[i] = keyBindings.getKeyIcon(key, self.iconSize)

    def _createActionButtons(self) -> None:
        resetRect, backRect = self._getActionButtonRects()
        self.resetBtn = Button(resetRect, optionsReset, self.buttonFont)
        self.backBtn = Button(backRect, optionsBack, self.buttonFont)

    def _updateButtonPositions(self) -> None:
        self._computeLayout()
        resetRect, backRect = self._getActionButtonRects()

        for btn, rect in [(self.resetBtn, resetRect), (self.backBtn, backRect)]:
            btn.setPosition(rect.x, rect.y)
            btn.setDimensions(rect.width, rect.height)

    def _buildPanelSurf(self) -> None:
        pw, ph = self._panelW, self._panelH
        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        cr = self._s(12)
        pygame.draw.rect(surf, (15, 17, 24, 200), (0, 0, pw, ph), border_radius=cr)
        pygame.draw.rect(surf, (45, 48, 60), (0, 0, pw, ph), 1, border_radius=cr)
        self.panelSurf = surf

    def _drawTitle(self, surf: Surface) -> None:
        w, h = self.screenSize
        cx, ty = w // 2, int(h * 0.15)
        text = optionsTitle
        pulse = 0.9 + 0.1 * math.sin(self.titlePulse)

        drawGlowTitle(surf, text, self.titleFont, cx, ty,
                      (220, 220, 230), (139, 0, 0), (20, 0, 0),
                      self._s(15), shadowOffset=self._s(4), pulse=pulse)

    def _drawControlsPanel(self, surf: Surface) -> None:
        w = self.screenSize[0]
        cx = w // 2

        if self.panelSurf is None:
            self._buildPanelSurf()

        assert self.panelSurf is not None
        surf.blit(self.panelSurf, (self._panelX, self._panelY))

        sectionY = self._panelY + self._s(30)
        drawSectionHeader(surf, optionsControls, self.sectionFont, cx, sectionY)

        for i, (label, attr) in enumerate(_bindingDefs):
            rowCY = self._rowCentersY[i]

            labelSurf = self.labelFont.render(label, True, (240, 240, 245))
            labelRect = labelSurf.get_rect(midleft=(self._labelX, rowCY))
            surf.blit(labelSurf, labelRect)

            key: int = getattr(keyBindings, attr)
            self._drawKeyIcon(
                surf, self._icons[i], self._iconRects[i],
                self._listeningIdx == i, self._hovered[i],
                keyBindings.getKeyName(key),
            )

    def _buildSoundPanelSurf(self) -> None:
        pw, ph = self._soundPanelW, self._soundPanelH
        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        cr = self._s(12)
        pygame.draw.rect(surf, (15, 17, 24, 200), (0, 0, pw, ph), border_radius=cr)
        pygame.draw.rect(surf, (45, 48, 60), (0, 0, pw, ph), 1, border_radius=cr)
        self._soundPanelSurf = surf

    def _drawSoundPanel(self, surf: Surface) -> None:
        w = self.screenSize[0]
        cx = w // 2

        if self._soundPanelSurf is None:
            self._buildSoundPanelSurf()

        assert self._soundPanelSurf is not None
        surf.blit(self._soundPanelSurf, (self._soundPanelX, self._soundPanelY))

        sectionY = self._soundPanelY + self._s(25)
        drawSectionHeader(surf, optionsSound, self.sectionFont, cx, sectionY)

        labelSurf = self.labelFont.render(optionsSound, True, (240, 240, 245))
        labelRect = labelSurf.get_rect(midleft=(self._soundLabelX, self._soundRowCY))
        surf.blit(labelSurf, labelRect)

        self._drawToggle(surf, self._soundToggleRect, settings.bSoundEnabled, self._soundHovered)

    def _drawToggle(self, surf: Surface, rect: pygame.Rect, bOn: bool, bHovered: bool) -> None:
        cr = rect.height // 2
        bgColor = (40, 140, 50) if bOn else (60, 62, 75)
        pygame.draw.rect(surf, bgColor, rect, border_radius=cr)

        if bHovered:
            highlight = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(highlight, (255, 255, 255, 20), highlight.get_rect(), border_radius=cr)
            surf.blit(highlight, rect.topleft)

        pygame.draw.rect(surf, (80, 82, 95), rect, 1, border_radius=cr)

        knobR = rect.height // 2 - self._s(4)
        knobX = rect.right - knobR - self._s(5) if bOn else rect.left + knobR + self._s(5)
        knobY = rect.centery
        pygame.draw.circle(surf, (240, 240, 245), (knobX, knobY), knobR)

    def _drawKeyIcon(self, surf: Surface, icon: Surface | None, rect: pygame.Rect,
                      bListening: bool, bHovered: bool, fallbackText: str) -> None:
        pad = self._s(4)
        if bHovered or bListening:
            highlight = pygame.Surface((rect.width + pad * 2, rect.height + pad * 2), pygame.SRCALPHA)
            cr = self._s(6)
            color = (255, 215, 0, 50) if bListening else (255, 255, 255, 30)
            pygame.draw.rect(highlight, color, highlight.get_rect(), border_radius=cr)
            surf.blit(highlight, (rect.x - pad, rect.y - pad))

        if bListening:
            listenSurf = self.buttonFont.render(optionsPressKey, True, (255, 215, 0))
            listenRect = listenSurf.get_rect(center=rect.center)
            surf.blit(listenSurf, listenRect)
        elif icon:
            surf.blit(icon, rect)
        else:
            textSurf = self.labelFont.render(fallbackText, True, (240, 240, 245))
            textRect = textSurf.get_rect(center=rect.center)
            surf.blit(textSurf, textRect)

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)

        self.buttonFont = pygame.font.Font(None, self._s(28))
        self.labelFont = pygame.font.Font(None, self._s(32))

        for btn in [self.resetBtn, self.backBtn]:
            btn.setFont(self.buttonFont)

        self.iconSize = self._s(50)
        self.menuBg.onResize(newSize)
        self.panelSurf = None
        self._soundPanelSurf = None
        self._updateButtonPositions()
        self._loadKeyIcons()
        self.titleFont = pygame.font.Font(None, self._s(120))
        self.sectionFont = pygame.font.Font(None, self._s(48))

    def handleEvent(self, event: Event, inputEvent: "InputEvent | None" = None) -> None:
        if self._listeningIdx >= 0:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:
                    attr = _bindingDefs[self._listeningIdx][1]
                    setattr(keyBindings, attr, event.key)
                self._listeningIdx = -1
                self._loadKeyIcons()
                return

        if event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._iconRects):
                self._hovered[i] = rect.collidepoint(event.pos)
            self._soundHovered = self._soundToggleRect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._soundToggleRect.collidepoint(event.pos):
                settings.bSoundEnabled = not settings.bSoundEnabled
                config.save()
                return
            for i, rect in enumerate(self._iconRects):
                if rect.collidepoint(event.pos):
                    self._listeningIdx = i
                    return

        if self.resetBtn.handleEvent(event):
            keyBindings.reset()
            self._loadKeyIcons()
            config.save()
        elif self.backBtn.handleEvent(event):
            config.save()
            self.setState(GameState.MENU)

    def update(self, dt: float) -> None:
        self.menuBg.update(dt)
        self.time += dt
        self.titlePulse += dt * 3

    def draw(self, screen: Surface) -> None:
        self.menuBg.draw(screen)
        self._drawTitle(screen)
        self._drawControlsPanel(screen)
        self._drawSoundPanel(screen)
        self.resetBtn.draw(screen)
        self.backBtn.draw(screen)
