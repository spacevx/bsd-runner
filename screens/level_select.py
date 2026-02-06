from typing import Callable, TYPE_CHECKING

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.font import Font
if TYPE_CHECKING:
    from entities.input.manager import InputEvent

import flags
import settings
from settings import GameState, ScreenSize, lastCompletedLevel
from levels import levelConfigs
from strings import levelSelectTitle, levelTarget, optionsBack
from screens.menu_bg import MenuBackground
from pytablericons import OutlineIcon  # type: ignore[import-untyped]
from screens.ui import Button, tablerIcon, drawGlowTitle
from screens.ui.levelcard import buildLevelCard

_goldColor = (255, 215, 0)


class LevelSelectScreen:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: ScreenSize,
                 setStateCallback: Callable[[GameState], None],
                 startLevelCallback: Callable[[int], None]) -> None:
        self.setState = setStateCallback
        self.startLevel = startLevelCallback
        self.screenSize: ScreenSize = screenSize
        self.scale: float = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)

        lvl = lastCompletedLevel()
        cfg = levelConfigs.get(lvl) if lvl else None
        self.menuBg = MenuBackground(
            screenSize,
            cfg.backgroundPath if cfg else None,
            cfg.bHasCeilingTiles if cfg else True,
        )

        self.titleFont: Font = Font(None, self._s(80))
        self.numberFont: Font = Font(None, self._s(60))
        self.nameFont: Font = Font(None, self._s(28))
        self.infoFont: Font = Font(None, self._s(22))
        self.buttonFont: Font = Font(None, self._s(28))

        self.backBtn: Button = self._createBackButton()

        self.levelIds: list[int] = sorted(levelConfigs.keys())
        self.cardRects: list[pygame.Rect] = []
        self.hoveredCard: int = -1
        self.focusRow: int = 0
        self.focusCol: int = 0
        self.bJoystickNavMode: bool = False

        self.currentPage: int = 0
        self.totalPages: int = 1
        self.cols: int = 2
        self.rows: int = 2
        self.perPage: int = 4

        self.chevronLeftRect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.chevronRightRect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        self._cachedCards: dict[tuple[int, str, bool], Surface] = {}

        self._computeLayout()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _createBackButton(self) -> Button:
        w, h = self._s(220), self._s(55)
        x = (self.screenSize[0] - w) // 2
        y = int(self.screenSize[1] * 0.88)
        return Button(pygame.Rect(x, y, w, h), optionsBack, self.buttonFont)

    def _computeLayout(self) -> None:
        screenW, screenH = self.screenSize
        cardW = self._s(240)
        cardH = self._s(170)
        gap = self._s(30)

        self.cols = max(2, min(4, screenW // self._s(280)))

        gridTop = int(screenH * 0.28)
        gridBot = int(screenH * 0.82)
        availH = gridBot - gridTop
        self.rows = max(1, (availH + gap) // (cardH + gap))

        self.perPage = self.cols * self.rows
        n = len(self.levelIds)
        self.totalPages = max(1, (n + self.perPage - 1) // self.perPage)
        self.currentPage = min(self.currentPage, self.totalPages - 1)

        pageIds = self._pageIds()
        nPage = len(pageIds)
        nRows = (nPage + self.cols - 1) // self.cols

        totalGridW = self.cols * cardW + (self.cols - 1) * gap
        totalGridH = nRows * cardH + max(0, nRows - 1) * gap
        startX = (screenW - totalGridW) // 2
        startY = gridTop + (availH - totalGridH) // 2

        self.cardRects = []
        for i in range(nPage):
            r, c = divmod(i, self.cols)
            x = startX + c * (cardW + gap)
            y = startY + r * (cardH + gap)
            self.cardRects.append(pygame.Rect(x, y, cardW, cardH))

        chevSize = self._s(48)
        chevY = gridTop + availH // 2 - chevSize // 2
        chevMargin = self._s(20)
        self.chevronLeftRect = pygame.Rect(chevMargin, chevY, chevSize, chevSize)
        self.chevronRightRect = pygame.Rect(screenW - chevMargin - chevSize, chevY, chevSize, chevSize)

    def _pageIds(self) -> list[int]:
        start = self.currentPage * self.perPage
        return self.levelIds[start:start + self.perPage]

    def _getLevelState(self, levelId: int) -> str:
        if settings.bIsLevelCompleted(levelId):
            return "completed"
        if settings.bIsLevelUnlocked(levelId) or flags.bUnlockAllLevels:
            return "available"
        return "locked"

    def _buildCardSurf(self, levelId: int, state: str, bHighlight: bool) -> Surface:
        key = (levelId, state, bHighlight)
        if key in self._cachedCards:
            return self._cachedCards[key]

        cfg = levelConfigs[levelId]
        idx = self._pageIds().index(levelId)
        w, h = self.cardRects[idx].size

        surf = buildLevelCard(
            w, h, levelId, cfg.name, cfg.finaleScore,
            state, bHighlight,
            self.numberFont, self.nameFont, self.infoFont,
            self.scale, levelTarget.format(score=cfg.finaleScore),
        )
        self._cachedCards[key] = surf
        return surf

    def _invalidateCache(self) -> None:
        self._cachedCards.clear()

    def _setPage(self, page: int) -> None:
        clamped = max(0, min(page, self.totalPages - 1))
        if clamped != self.currentPage:
            self.currentPage = clamped
            self._computeLayout()
            self._invalidateCache()

    def _focusedIndex(self) -> int:
        return self.focusRow * self.cols + self.focusCol

    def _clampFocus(self) -> None:
        pageIds = self._pageIds()
        n = len(pageIds)
        if n == 0:
            self.focusRow = self.focusCol = 0
            return
        nRows = (n + self.cols - 1) // self.cols
        self.focusRow = min(self.focusRow, nRows - 1)
        lastRowCols = n - self.focusRow * self.cols
        self.focusCol = min(self.focusCol, lastRowCols - 1)

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)

        self.titleFont = Font(None, self._s(80))
        self.numberFont = Font(None, self._s(60))
        self.nameFont = Font(None, self._s(28))
        self.infoFont = Font(None, self._s(22))
        self.buttonFont = Font(None, self._s(28))

        self.menuBg.onResize(newSize)
        self.backBtn = self._createBackButton()
        self._computeLayout()
        self._invalidateCache()

    def handleEvent(self, event: Event, inputEvent: "InputEvent | None" = None) -> None:
        from entities.input.manager import GameAction, InputSource

        if event.type == pygame.MOUSEMOTION:
            self.bJoystickNavMode = False
            oldHover = self.hoveredCard
            self.hoveredCard = -1
            for i, rect in enumerate(self.cardRects):
                if rect.collidepoint(event.pos):
                    self.hoveredCard = i
                    break
            if oldHover != self.hoveredCard:
                self._invalidateCache()

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.chevronLeftRect.collidepoint(event.pos):
                self._setPage(self.currentPage - 1)
            elif self.chevronRightRect.collidepoint(event.pos):
                self._setPage(self.currentPage + 1)
            else:
                pageIds = self._pageIds()
                for i, rect in enumerate(self.cardRects):
                    if rect.collidepoint(event.pos) and i < len(pageIds):
                        lid = pageIds[i]
                        if self._getLevelState(lid) != "locked":
                            self.startLevel(lid)
                        break

        if inputEvent:
            if inputEvent.source == InputSource.JOYSTICK and not self.bJoystickNavMode:
                self.bJoystickNavMode = True
                self._invalidateCache()

            if inputEvent.bPressed:
                pageIds = self._pageIds()
                nPage = len(pageIds)
                nRows = (nPage + self.cols - 1) // self.cols if nPage else 0

                if inputEvent.action == GameAction.MENU_RIGHT:
                    if self.focusCol < self.cols - 1 and self._focusedIndex() + 1 < nPage:
                        self.focusCol += 1
                    elif self.currentPage < self.totalPages - 1:
                        self._setPage(self.currentPage + 1)
                        self.focusCol = 0
                        self._clampFocus()
                    self._invalidateCache()

                elif inputEvent.action == GameAction.MENU_LEFT:
                    if self.focusCol > 0:
                        self.focusCol -= 1
                    elif self.currentPage > 0:
                        self._setPage(self.currentPage - 1)
                        pageIds = self._pageIds()
                        nPage = len(pageIds)
                        nRows = (nPage + self.cols - 1) // self.cols if nPage else 0
                        self.focusRow = min(self.focusRow, nRows - 1)
                        lastRowCols = nPage - self.focusRow * self.cols
                        self.focusCol = min(self.cols - 1, lastRowCols - 1)
                    self._invalidateCache()

                elif inputEvent.action == GameAction.MENU_DOWN:
                    if self.focusRow < nRows - 1:
                        self.focusRow += 1
                        self._clampFocus()
                    self._invalidateCache()

                elif inputEvent.action == GameAction.MENU_UP:
                    if self.focusRow > 0:
                        self.focusRow -= 1
                        self._clampFocus()
                    self._invalidateCache()

                elif inputEvent.action in (GameAction.MENU_CONFIRM, GameAction.JUMP):
                    if self.bJoystickNavMode:
                        idx = self._focusedIndex()
                        if 0 <= idx < nPage:
                            lid = pageIds[idx]
                            if self._getLevelState(lid) != "locked":
                                self.startLevel(lid)

                elif inputEvent.action in (GameAction.MENU_BACK, GameAction.SLIDE):
                    self.setState(GameState.MENU)

        if self.backBtn.handleEvent(event):
            self.setState(GameState.MENU)

    def update(self, dt: float) -> None:
        self.menuBg.update(dt)

    def _drawTitle(self, screen: Surface) -> None:
        cx = self.screenSize[0] // 2
        ty = int(self.screenSize[1] * 0.15)
        text = levelSelectTitle

        drawGlowTitle(screen, text, self.titleFont, cx, ty,
                      _goldColor, (180, 150, 0), (0, 0, 0),
                      self._s(12), peakAlpha=50, shadowOffset=self._s(3))

    def _drawChevrons(self, screen: Surface) -> None:
        if self.totalPages <= 1:
            return

        chevSize = self._s(40)

        if self.currentPage > 0:
            leftIcon = tablerIcon(OutlineIcon.CHEVRON_LEFT, chevSize, '#FFFFFF')
            screen.blit(leftIcon, leftIcon.get_rect(center=self.chevronLeftRect.center))

        if self.currentPage < self.totalPages - 1:
            rightIcon = tablerIcon(OutlineIcon.CHEVRON_RIGHT, chevSize, '#FFFFFF')
            screen.blit(rightIcon, rightIcon.get_rect(center=self.chevronRightRect.center))

    def _drawPageDots(self, screen: Surface) -> None:
        if self.totalPages <= 1:
            return

        dotR = self._s(5)
        gap = self._s(16)
        totalW = self.totalPages * dotR * 2 + (self.totalPages - 1) * gap
        startX = (self.screenSize[0] - totalW) // 2 + dotR
        dotY = int(self.screenSize[1] * 0.84)

        for i in range(self.totalPages):
            cx = startX + i * (dotR * 2 + gap)
            color = _goldColor if i == self.currentPage else (50, 52, 60)
            pygame.draw.circle(screen, color, (cx, dotY), dotR)

    def draw(self, screen: Surface) -> None:
        self.menuBg.draw(screen)
        self._drawTitle(screen)

        pageIds = self._pageIds()
        for i, lid in enumerate(pageIds):
            state = self._getLevelState(lid)
            bHighlight = (
                (self.hoveredCard == i and not self.bJoystickNavMode)
                or (self._focusedIndex() == i and self.bJoystickNavMode)
            )
            cardSurf = self._buildCardSurf(lid, state, bHighlight)
            screen.blit(cardSurf, self.cardRects[i])

        self._drawChevrons(screen)
        self._drawPageDots(screen)
        self.backBtn.draw(screen)
