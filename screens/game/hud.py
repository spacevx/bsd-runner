import pygame
from pygame import Surface
from pygame.font import Font

from keybindings import keyBindings
from settings import ScreenSize, white, gold
from strings import (
    gameOver, gameRestartKey, gameRestartButton, hudJump, hudSlide, hudDoubleJump,
    levelComplete, levelCompleteRestart, gameOverMenuKey, gameOverMenuButton
)
from screens.ui import _gradientRect, tablerIcon, drawTextWithShadow, glassPanel, drawGlowTitle
from screens.ui.controls import ControlHint, buildControlsPanel
from screens.ui.ecg import EcgMonitor
from screens.ui.score import ScoreDisplay
from screens.ui.hitcounter import HitCounter


class HUD:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: ScreenSize, bDoubleJump: bool = False,
                 bSlideEnabled: bool = True, bFallingCages: bool = True,
                 bShowHitCounter: bool = False) -> None:
        self.screenSize = screenSize
        self.bDoubleJump = bDoubleJump
        self.bSlideEnabled = bSlideEnabled
        self.bFallingCages = bFallingCages
        self.bShowHitCounter = bShowHitCounter or bFallingCages
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)
        self._createFonts()

        from entities.input.manager import InputManager
        from entities.input.joyicons import JoyIcons
        self.inputManager = InputManager()
        self.joyIcons = JoyIcons()

        self._scoreDisplay = ScoreDisplay(self.scale)
        self._hitCounter = HitCounter(self.scale)

        self._controlsSurf: Surface | None = None
        self._controlsInputSource: object = None
        self._controlsScreenSize: ScreenSize | None = None

        self._gameOverSurf: Surface | None = None
        self._gameOverScore: int = -1
        self._gameOverInputSource: object = None
        self._ecg = EcgMonitor(self.scale)

        self._levelCompleteSurf: Surface | None = None
        self._levelCompleteScore: int = -1
        self._levelCompleteInputSource: object = None

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _glassPanel(self, w: int, h: int) -> Surface:
        return glassPanel(w, h, self.scale)

    def _createFonts(self) -> None:
        self.font: Font = pygame.font.Font(None, self._s(96))
        self.smallFont: Font = pygame.font.Font(None, self._s(42))
        self.scoreFont: Font = pygame.font.Font(None, self._s(64))

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self._createFonts()
        self._ecg.onResize(self.scale)
        self._scoreDisplay.onResize(self.scale)
        self._hitCounter.onResize(self.scale)
        self._invalidateAll()

    def _invalidateAll(self) -> None:
        self._controlsSurf = None
        self._controlsInputSource = None
        self._controlsScreenSize = None
        self._gameOverSurf = None
        self._gameOverScore = -1
        self._gameOverInputSource = None
        self._levelCompleteSurf = None
        self._levelCompleteScore = -1
        self._levelCompleteInputSource = None

    def resetGameOverCache(self) -> None:
        self._scoreDisplay.reset()
        self._gameOverSurf = None
        self._gameOverScore = -1
        self._gameOverInputSource = None
        self._ecg.reset()
        self._levelCompleteSurf = None
        self._levelCompleteScore = -1
        self._levelCompleteInputSource = None

    def drawScore(self, screen: Surface, score: int, dt: float) -> None:
        x = self._s(30) - self._s(10)
        y = self._s(25) - self._s(10)
        self._scoreDisplay.draw(screen, x, y, score, dt, self.scoreFont)

    def drawControls(self, screen: Surface) -> None:
        from entities.input.manager import InputSource

        curSource = self.inputManager.lastInputSource
        if (self._controlsSurf is not None
                and self._controlsInputSource == curSource
                and self._controlsScreenSize == self.screenSize):
            ctrlX = self._s(30)
            ctrlY = self.screenSize[1] - self._s(55)
            screen.blit(self._controlsSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))
            return

        self._controlsInputSource = curSource
        self._controlsScreenSize = self.screenSize

        iconSize = self._s(36)
        if curSource == InputSource.JOYSTICK:
            hints = self._joystickHints(iconSize)
        else:
            hints = self._keyboardHints(iconSize)

        self._controlsSurf = buildControlsPanel(hints, self.smallFont, self.scale)

        ctrlX = self._s(30)
        ctrlY = self.screenSize[1] - self._s(55)
        screen.blit(self._controlsSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))

    def _keyboardHints(self, iconSize: int) -> list[ControlHint]:
        jumpIcon = keyBindings.getKeyIcon(keyBindings.jump, iconSize)
        if self.bDoubleJump and not self.bSlideEnabled:
            return [ControlHint(jumpIcon, keyBindings.getKeyName(keyBindings.jump), hudDoubleJump)]
        slideIcon = keyBindings.getKeyIcon(keyBindings.slide, iconSize)
        return [
            ControlHint(jumpIcon, keyBindings.getKeyName(keyBindings.jump), hudJump),
            ControlHint(slideIcon, keyBindings.getKeyName(keyBindings.slide), hudSlide),
        ]

    def _joystickHints(self, iconSize: int) -> list[ControlHint]:
        from entities.input.joybindings import JoyBindings
        from entities.input.manager import GameAction

        jb = JoyBindings()
        jumpBtn = jb.getButtonForAction(GameAction.JUMP)
        jumpIcon = self.joyIcons.renderButtonIcon(jumpBtn, (iconSize, iconSize)) if jumpBtn is not None else None
        if self.bDoubleJump and not self.bSlideEnabled:
            return [ControlHint(jumpIcon, "?", hudDoubleJump)]
        slideBtn = jb.getButtonForAction(GameAction.SLIDE)
        slideIcon = self.joyIcons.renderButtonIcon(slideBtn, (iconSize, iconSize)) if slideBtn is not None else None
        return [
            ControlHint(jumpIcon, "?", hudJump),
            ControlHint(slideIcon, "?", hudSlide),
        ]

    def drawGameOver(self, screen: Surface, score: int) -> None:
        from entities.input.manager import InputSource, GameAction
        from entities.input.joybindings import JoyBindings

        curSource = self.inputManager.lastInputSource
        bNeedRebuild = (self._gameOverSurf is None
                        or self._gameOverScore != score
                        or self._gameOverInputSource != curSource)

        if bNeedRebuild:
            self._gameOverScore = score
            self._gameOverInputSource = curSource
            self._ecg.reset()

            w, h = self.screenSize
            self._gameOverSurf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf = self._gameOverSurf
            surf.fill((0, 0, 0, 180))

            cx, cy = w // 2, h // 2

            panelW, panelH = self._s(640), self._s(460)
            cr = self._s(18)
            panel = _gradientRect(panelW, panelH, (22, 24, 32), (10, 12, 18), 240, cr)
            pygame.draw.rect(panel, (160, 30, 30, 180), (0, 0, panelW, panelH), self._s(2), border_radius=cr)

            topAccentW = panelW - self._s(60)
            if topAccentW > 0:
                topAccent = _gradientRect(topAccentW, self._s(3), (200, 40, 40), (100, 15, 15), 200, 1)
                panel.blit(topAccent, ((panelW - topAccentW) // 2, 0))

            hlW = panelW - self._s(30)
            if hlW > 0:
                hl = pygame.Surface((hlW, 1), pygame.SRCALPHA)
                hl.fill((255, 255, 255, 12))
                panel.blit(hl, (self._s(15), self._s(4)))

            panelX, panelY = cx - panelW // 2, cy - panelH // 2 - self._s(40)
            surf.blit(panel, (panelX, panelY))

            titleY = panelY + self._s(45)
            drawGlowTitle(surf, gameOver, self.font, cx, titleY,
                          (255, 55, 55), (160, 0, 0), (40, 0, 0),
                          self._s(12), peakAlpha=50, shadowOffset=self._s(3), bDiagonal=True)
            titleSurf = self.font.render(gameOver, True, (255, 55, 55))

            divY = titleY + titleSurf.get_height() // 2 + self._s(22)
            divW = panelW - self._s(80)
            if divW > 0:
                divSurf = pygame.Surface((divW, self._s(1)), pygame.SRCALPHA)
                halfW = divW // 2
                for px in range(divW):
                    dist = abs(px - halfW)
                    a = max(0, int(40 * (1 - dist / halfW)))
                    divSurf.set_at((px, 0), (255, 60, 60, a))
                surf.blit(divSurf, (cx - divW // 2, divY))

            scoreText = f"Score Final: {score}"
            scoreSurf = self.scoreFont.render(scoreText, True, (220, 230, 255))
            scoreY = divY + self._s(35)

            pillW = scoreSurf.get_width() + self._s(50)
            pillH = scoreSurf.get_height() + self._s(20)
            pillCr = pillH // 2
            pill = _gradientRect(pillW, pillH, (30, 28, 18), (18, 16, 10), 160, pillCr)
            pygame.draw.rect(pill, (180, 150, 0, 80), (0, 0, pillW, pillH), 1, border_radius=pillCr)
            surf.blit(pill, (cx - pillW // 2, scoreY - self._s(10)))

            scoreShadow = self.scoreFont.render(scoreText, True, (30, 35, 50))
            surf.blit(scoreShadow, scoreSurf.get_rect(center=(cx + self._s(2), scoreY + pillH // 2 - self._s(10) + self._s(2))))
            surf.blit(scoreSurf, scoreSurf.get_rect(center=(cx, scoreY + pillH // 2 - self._s(10))))

            restartKeyName = keyBindings.getKeyName(keyBindings.restart)
            if curSource == InputSource.JOYSTICK:
                restartBtn = JoyBindings().getButtonForAction(GameAction.RESTART)
                if restartBtn is not None:
                    restartText = gameRestartButton.format(button=self.joyIcons.getButtonName(restartBtn))
                else:
                    restartText = gameRestartKey.format(key=restartKeyName)
                menuBtn = JoyBindings().getButtonForAction(GameAction.MENU_BACK)
                if menuBtn is not None:
                    menuText = gameOverMenuButton.format(button=self.joyIcons.getButtonName(menuBtn))
                else:
                    menuText = gameOverMenuKey
            else:
                restartText = gameRestartKey.format(key=restartKeyName)
                menuText = gameOverMenuKey

            actionsY = scoreY + pillH + self._s(20)
            restartSurf = self.smallFont.render(restartText, True, (240, 240, 245))
            restartRect = restartSurf.get_rect(center=(cx, actionsY))
            restartShadow = self.smallFont.render(restartText, True, (0, 0, 0))
            surf.blit(restartShadow, restartSurf.get_rect(center=(cx + 1, actionsY + 1)))
            surf.blit(restartSurf, restartRect)

            menuSurf = self.smallFont.render(menuText, True, (130, 132, 150))
            menuRect = menuSurf.get_rect(center=(cx, actionsY + self._s(40)))
            surf.blit(menuSurf, menuRect)

        screen.blit(self._gameOverSurf, (0, 0))  # type: ignore[arg-type]

        w, h = self.screenSize
        cx, cy = w // 2, h // 2
        panelW = self._s(640)
        panelH = self._s(460)
        panelY = cy - panelH // 2 - self._s(40)
        ecgY = panelY + panelH + self._s(15)
        ecgW = self._s(1000)
        ecgH = self._s(180)
        ecgX = cx - ecgW // 2
        self._ecg.draw(screen, ecgX, ecgY, ecgW, ecgH)

    def drawHitCounter(self, screen: Surface, hitCount: int, maxHits: int) -> None:
        x = self.screenSize[0] - self._s(195) - self._s(10)
        y = self._s(25) - self._s(10)
        self._hitCounter.draw(screen, x, y, hitCount, maxHits)

    def drawLevelComplete(self, screen: Surface, score: int) -> None:
        from entities.input.manager import InputSource, GameAction
        from entities.input.joybindings import JoyBindings

        curSource = self.inputManager.lastInputSource
        if (self._levelCompleteSurf is not None
                and self._levelCompleteScore == score
                and self._levelCompleteInputSource == curSource):
            screen.blit(self._levelCompleteSurf, (0, 0))
            return

        self._levelCompleteScore = score
        self._levelCompleteInputSource = curSource
        w, h = self.screenSize
        self._levelCompleteSurf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf = self._levelCompleteSurf
        surf.fill((0, 0, 0, 180))

        cx, cy = w // 2, h // 2
        green = (50, 220, 80)
        darkGreen = (20, 100, 40)

        panelW, panelH = self._s(620), self._s(380)
        cr = self._s(15)
        panel = _gradientRect(panelW, panelH, (25, 27, 35), (12, 14, 20), 240, cr)
        pygame.draw.rect(panel, (*darkGreen, 200), (0, 0, panelW, panelH), self._s(2), border_radius=cr)
        hlW = panelW - self._s(30)
        if hlW > 0:
            hl = pygame.Surface((hlW, 1), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 15))
            panel.blit(hl, (self._s(15), 1))
        surf.blit(panel, (cx - panelW // 2, cy - panelH // 2))

        titleY = cy - self._s(100)
        drawGlowTitle(surf, levelComplete, self.font, cx, titleY,
                      green, darkGreen, (0, 50, 20),
                      self._s(15), shadowOffset=self._s(4))

        scoreText = f"Score Final: {score}"
        scoreSurf = self.scoreFont.render(scoreText, True, gold)
        scoreRect = scoreSurf.get_rect(center=(cx, cy))
        scoreShadow = self.scoreFont.render(scoreText, True, (100, 80, 0))
        surf.blit(scoreShadow, scoreSurf.get_rect(center=(cx + self._s(2), cy + self._s(2))))
        surf.blit(scoreSurf, scoreRect)

        restartKeyName = keyBindings.getKeyName(keyBindings.restart)
        if curSource == InputSource.JOYSTICK:
            restartBtn = JoyBindings().getButtonForAction(GameAction.RESTART)
            if restartBtn is not None:
                restartText = gameRestartButton.format(button=self.joyIcons.getButtonName(restartBtn))
            else:
                restartText = levelCompleteRestart.format(key=restartKeyName)
            menuBtn = JoyBindings().getButtonForAction(GameAction.MENU_BACK)
            if menuBtn is not None:
                menuText = gameOverMenuButton.format(button=self.joyIcons.getButtonName(menuBtn))
            else:
                menuText = gameOverMenuKey
        else:
            restartText = levelCompleteRestart.format(key=restartKeyName)
            menuText = gameOverMenuKey

        restartSurf = self.smallFont.render(restartText, True, white)
        restartRect = restartSurf.get_rect(center=(cx, cy + self._s(70)))
        surf.blit(restartSurf, restartRect)

        menuSurf = self.smallFont.render(menuText, True, (160, 162, 175))
        menuRect = menuSurf.get_rect(center=(cx, cy + self._s(110)))
        surf.blit(menuSurf, menuRect)

        screen.blit(self._levelCompleteSurf, (0, 0))

    def draw(self, screen: Surface, score: int, bGameOver: bool, dt: float, hitCount: int = 0, maxHits: int = 3, bLevelComplete: bool = False) -> None:
        self.drawScore(screen, score, dt)
        if self.bShowHitCounter:
            self.drawHitCounter(screen, hitCount, maxHits)
        self.drawControls(screen)
        if bLevelComplete:
            self.drawLevelComplete(screen, score)
        elif bGameOver:
            self.drawGameOver(screen, score)
