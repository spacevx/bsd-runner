import pygame
from pygame import Surface
from pygame.font import Font

from keybindings import keyBindings
from settings import ScreenSize, white, gold
from strings import (
    gameOver, gameRestartKey, gameRestartButton, hudJump, hudSlide, hudDoubleJump,
    levelComplete, levelCompleteRestart, gameOverMenuKey, gameOverMenuButton
)
from screens.ui import _gradientRect, tablerIcon


class HUD:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: ScreenSize, bDoubleJump: bool = False,
                 bSlideEnabled: bool = True, bFallingCages: bool = True) -> None:
        self.screenSize = screenSize
        self.bDoubleJump = bDoubleJump
        self.bSlideEnabled = bSlideEnabled
        self.bFallingCages = bFallingCages
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)
        self._createFonts()

        from entities.input.manager import InputManager
        from entities.input.joyicons import JoyIcons
        self.inputManager = InputManager()
        self.joyIcons = JoyIcons()

        self.displayScore: float = 0.0

        self._cachedScoreVal: int = -1
        self._cachedScoreSurf: Surface | None = None
        self._cachedScoreBoxSurf: Surface | None = None

        self._controlsSurf: Surface | None = None
        self._controlsInputSource: object = None
        self._controlsScreenSize: ScreenSize | None = None

        self._cachedHits: int = -1
        self._cachedMaxHits: int = -1
        self._cachedHitSurf: Surface | None = None

        self._gameOverSurf: Surface | None = None
        self._gameOverScore: int = -1
        self._gameOverInputSource: object = None

        self._levelCompleteSurf: Surface | None = None
        self._levelCompleteScore: int = -1
        self._levelCompleteInputSource: object = None

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _glassPanel(self, w: int, h: int) -> Surface:
        cr = self._s(12)
        panel = _gradientRect(w, h, (20, 22, 30), (12, 14, 20), 200, cr)
        pygame.draw.rect(panel, (45, 48, 60), (0, 0, w, h), 1, border_radius=cr)
        return panel

    def _drawHeart(self, surf: Surface, cx: int, cy: int, size: int,
                   color: str) -> None:
        from pytablericons import FilledIcon  # type: ignore[import-untyped]
        icon = tablerIcon(FilledIcon.HEART, size, color)
        surf.blit(icon, (cx - size // 2, cy - size // 2))

    def _createFonts(self) -> None:
        self.font: Font = pygame.font.Font(None, self._s(96))
        self.smallFont: Font = pygame.font.Font(None, self._s(42))
        self.scoreFont: Font = pygame.font.Font(None, self._s(64))

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self._createFonts()
        self._invalidateAll()

    def _invalidateAll(self) -> None:
        self._cachedScoreVal = -1
        self._cachedScoreSurf = None
        self._cachedScoreBoxSurf = None
        self._controlsSurf = None
        self._controlsInputSource = None
        self._controlsScreenSize = None
        self._cachedHits = -1
        self._cachedMaxHits = -1
        self._cachedHitSurf = None
        self._gameOverSurf = None
        self._gameOverScore = -1
        self._gameOverInputSource = None
        self._levelCompleteSurf = None
        self._levelCompleteScore = -1
        self._levelCompleteInputSource = None

    def resetGameOverCache(self) -> None:
        self.displayScore = 0.0
        self._gameOverSurf = None
        self._gameOverScore = -1
        self._gameOverInputSource = None
        self._levelCompleteSurf = None
        self._levelCompleteScore = -1
        self._levelCompleteInputSource = None

    def _drawTextWithShadow(self, screen: Surface, text: str, font: Font,
                            color: tuple[int, int, int], pos: tuple[int, int],
                            shadowOffset: int = 2) -> None:
        shadow = font.render(text, True, (0, 0, 0))
        surf = font.render(text, True, color)
        screen.blit(shadow, (pos[0] + shadowOffset, pos[1] + shadowOffset))
        screen.blit(surf, pos)

    def _drawTextWithShadowOnSurf(self, target: Surface, text: str, font: Font,
                                  color: tuple[int, int, int], pos: tuple[int, int],
                                  shadowOffset: int = 2) -> None:
        shadow = font.render(text, True, (0, 0, 0))
        surf = font.render(text, True, color)
        target.blit(shadow, (pos[0] + shadowOffset, pos[1] + shadowOffset))
        target.blit(surf, pos)

    def drawScore(self, screen: Surface, score: int, dt: float) -> None:
        scoreX, scoreY = self._s(30), self._s(25)

        if self._cachedScoreBoxSurf is None:
            boxW = self._s(260)
            boxH = self._s(56)
            self._cachedScoreBoxSurf = self._glassPanel(boxW, boxH)

        screen.blit(self._cachedScoreBoxSurf, (scoreX - self._s(10), scoreY - self._s(10)))

        t = min(1.0, 1.0 - 0.04 ** dt)
        self.displayScore = pygame.math.lerp(self.displayScore, float(score), t)
        if abs(self.displayScore - score) < 1.0:
            self.displayScore = float(score)
        shown = int(self.displayScore)

        if shown != self._cachedScoreVal:
            self._cachedScoreVal = shown
            scoreText = f"Score: {shown}"
            boxW = self._cachedScoreBoxSurf.get_width()
            boxH = self._cachedScoreBoxSurf.get_height()
            self._cachedScoreSurf = pygame.Surface((boxW, boxH), pygame.SRCALPHA)
            self._drawTextWithShadowOnSurf(self._cachedScoreSurf, scoreText, self.scoreFont, (240, 240, 245), (self._s(10), self._s(10)), self._s(2))

        if self._cachedScoreSurf:
            screen.blit(self._cachedScoreSurf, (scoreX - self._s(10), scoreY - self._s(10)))

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

        if curSource == InputSource.JOYSTICK:
            self._buildJoystickControlsSurf()
        else:
            self._buildKeyboardControlsSurf()

        ctrlX = self._s(30)
        ctrlY = self.screenSize[1] - self._s(55)
        if self._controlsSurf:
            screen.blit(self._controlsSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))

    def _buildKeyboardControlsSurf(self) -> None:
        iconSize = self._s(36)
        textColor = (240, 240, 245)

        jumpIcon = keyBindings.getKeyIcon(keyBindings.jump, iconSize)

        if self.bDoubleJump and not self.bSlideEnabled:
            jumpLabel = self.smallFont.render(hudDoubleJump, True, textColor)
            totalW = iconSize + self._s(8) + jumpLabel.get_width()
            boxH = iconSize + self._s(10)
            bgSurf = self._glassPanel(totalW + self._s(20), boxH)
            x = self._s(10)
            centerY = boxH // 2
            if jumpIcon:
                bgSurf.blit(jumpIcon, (x, centerY - iconSize // 2))
                x += iconSize + self._s(8)
            else:
                fallback = self.smallFont.render(keyBindings.getKeyName(keyBindings.jump), True, textColor)
                bgSurf.blit(fallback, (x, centerY - fallback.get_height() // 2))
                x += fallback.get_width() + self._s(8)
            bgSurf.blit(jumpLabel, (x, centerY - jumpLabel.get_height() // 2))
            self._controlsSurf = bgSurf
            return

        slideIcon = keyBindings.getKeyIcon(keyBindings.slide, iconSize)

        jumpLabel = self.smallFont.render(hudJump, True, textColor)
        slideLabel = self.smallFont.render(hudSlide, True, textColor)
        separator = self.smallFont.render("|", True, (80, 82, 95))

        totalW = iconSize + self._s(8) + jumpLabel.get_width() + self._s(20)
        totalW += separator.get_width() + self._s(20)
        totalW += iconSize + self._s(8) + slideLabel.get_width()
        boxH = iconSize + self._s(10)

        bgSurf = self._glassPanel(totalW + self._s(20), boxH)

        x = self._s(10)
        centerY = boxH // 2

        if jumpIcon:
            bgSurf.blit(jumpIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render(keyBindings.getKeyName(keyBindings.jump), True, textColor)
            bgSurf.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        bgSurf.blit(jumpLabel, (x, centerY - jumpLabel.get_height() // 2))
        x += jumpLabel.get_width() + self._s(20)

        bgSurf.blit(separator, (x, centerY - separator.get_height() // 2))
        x += separator.get_width() + self._s(20)

        if slideIcon:
            bgSurf.blit(slideIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render(keyBindings.getKeyName(keyBindings.slide), True, textColor)
            bgSurf.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        bgSurf.blit(slideLabel, (x, centerY - slideLabel.get_height() // 2))

        self._controlsSurf = bgSurf

    def _buildJoystickControlsSurf(self) -> None:
        from entities.input.joybindings import JoyBindings
        from entities.input.manager import GameAction

        jb = JoyBindings()
        iconSize = self._s(36)
        textColor = (240, 240, 245)

        jumpBtn = jb.getButtonForAction(GameAction.JUMP)

        if self.bDoubleJump and not self.bSlideEnabled:
            jumpLabel = self.smallFont.render(hudDoubleJump, True, textColor)
            totalW = iconSize + self._s(8) + jumpLabel.get_width()
            boxH = iconSize + self._s(10)
            bgSurf = self._glassPanel(totalW + self._s(20), boxH)
            x = self._s(10)
            centerY = boxH // 2
            if jumpBtn is not None:
                jumpIcon = self.joyIcons.renderButtonIcon(jumpBtn, (iconSize, iconSize))
                bgSurf.blit(jumpIcon, (x, centerY - iconSize // 2))
                x += iconSize + self._s(8)
            else:
                fallback = self.smallFont.render("?", True, textColor)
                bgSurf.blit(fallback, (x, centerY - fallback.get_height() // 2))
                x += fallback.get_width() + self._s(8)
            bgSurf.blit(jumpLabel, (x, centerY - jumpLabel.get_height() // 2))
            self._controlsSurf = bgSurf
            return

        slideBtn = jb.getButtonForAction(GameAction.SLIDE)

        jumpLabel = self.smallFont.render(hudJump, True, textColor)
        slideLabel = self.smallFont.render(hudSlide, True, textColor)
        separator = self.smallFont.render("|", True, (80, 82, 95))

        totalW = iconSize + self._s(8) + jumpLabel.get_width() + self._s(20)
        totalW += separator.get_width() + self._s(20)
        totalW += iconSize + self._s(8) + slideLabel.get_width()
        boxH = iconSize + self._s(10)

        bgSurf = self._glassPanel(totalW + self._s(20), boxH)

        x = self._s(10)
        centerY = boxH // 2

        if jumpBtn is not None:
            jumpIcon = self.joyIcons.renderButtonIcon(jumpBtn, (iconSize, iconSize))
            bgSurf.blit(jumpIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render("?", True, textColor)
            bgSurf.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        bgSurf.blit(jumpLabel, (x, centerY - jumpLabel.get_height() // 2))
        x += jumpLabel.get_width() + self._s(20)

        bgSurf.blit(separator, (x, centerY - separator.get_height() // 2))
        x += separator.get_width() + self._s(20)

        if slideBtn is not None:
            slideIcon = self.joyIcons.renderButtonIcon(slideBtn, (iconSize, iconSize))
            bgSurf.blit(slideIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render("?", True, textColor)
            bgSurf.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        bgSurf.blit(slideLabel, (x, centerY - slideLabel.get_height() // 2))

        self._controlsSurf = bgSurf

    def drawGameOver(self, screen: Surface, score: int) -> None:
        from entities.input.manager import InputSource, GameAction
        from entities.input.joybindings import JoyBindings
        from pytablericons import OutlineIcon

        curSource = self.inputManager.lastInputSource
        if (self._gameOverSurf is not None
                and self._gameOverScore == score
                and self._gameOverInputSource == curSource):
            screen.blit(self._gameOverSurf, (0, 0))
            return

        self._gameOverScore = score
        self._gameOverInputSource = curSource

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

        panelX, panelY = cx - panelW // 2, cy - panelH // 2
        surf.blit(panel, (panelX, panelY))

        iconSize = self._s(72)
        iconY = panelY + self._s(35)
        iconSurf = tablerIcon(OutlineIcon.SKULL, iconSize, '#FF3232', 1.8)

        glowSize = iconSize + self._s(40)
        iconGlow = pygame.Surface((glowSize, glowSize), pygame.SRCALPHA)
        pygame.draw.circle(iconGlow, (180, 20, 20, 25), (glowSize // 2, glowSize // 2), glowSize // 2)
        surf.blit(iconGlow, (cx - glowSize // 2, iconY + iconSize // 2 - glowSize // 2))
        surf.blit(iconSurf, (cx - iconSize // 2, iconY))

        titleY = iconY + iconSize + self._s(30)
        titleSurf = self.font.render(gameOver, True, (255, 55, 55))
        titleRect = titleSurf.get_rect(center=(cx, titleY))

        maxGlow = self._s(12)
        for offset in range(maxGlow, 0, -2):
            glow = self.font.render(gameOver, True, (160, 0, 0))
            glow.set_alpha(int(50 * (1 - offset / maxGlow)))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset),
                           (-offset // 2, -offset // 2), (offset // 2, -offset // 2),
                           (-offset // 2, offset // 2), (offset // 2, offset // 2)]:
                surf.blit(glow, titleSurf.get_rect(center=(cx + dx, titleY + dy)))

        shadow = self.font.render(gameOver, True, (40, 0, 0))
        surf.blit(shadow, titleSurf.get_rect(center=(cx + self._s(3), titleY + self._s(3))))
        surf.blit(titleSurf, titleRect)

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

        screen.blit(self._gameOverSurf, (0, 0))

    def drawHitCounter(self, screen: Surface, hitCount: int, maxHits: int) -> None:
        if hitCount == self._cachedHits and maxHits == self._cachedMaxHits and self._cachedHitSurf is not None:
            x = self.screenSize[0] - self._s(195)
            y = self._s(25)
            screen.blit(self._cachedHitSurf, (x - self._s(10), y - self._s(10)))
            return

        self._cachedHits = hitCount
        self._cachedMaxHits = maxHits

        boxW = self._s(170)
        boxH = self._s(56)
        hitSurf = self._glassPanel(boxW, boxH)

        heartSize = self._s(28)
        spacing = self._s(42)
        totalHeartsW = (maxHits - 1) * spacing + heartSize
        startX = (boxW - totalHeartsW) // 2 + heartSize // 2
        centerY = boxH // 2

        for i in range(maxHits):
            cx = startX + i * spacing
            color = '#32343F' if i < hitCount else '#DC3232'
            self._drawHeart(hitSurf, cx, centerY, heartSize, color)

        self._cachedHitSurf = hitSurf

        x = self.screenSize[0] - self._s(195)
        y = self._s(25)
        screen.blit(self._cachedHitSurf, (x - self._s(10), y - self._s(10)))

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
        titleSurf = self.font.render(levelComplete, True, green)
        titleRect = titleSurf.get_rect(center=(cx, titleY))

        for offset in range(self._s(15), 0, -2):
            glow = self.font.render(levelComplete, True, darkGreen)
            glow.set_alpha(int(60 * (1 - offset / self._s(15))))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                surf.blit(glow, titleSurf.get_rect(center=(cx + dx, titleY + dy)))

        shadow = self.font.render(levelComplete, True, (0, 50, 20))
        surf.blit(shadow, titleSurf.get_rect(center=(cx + self._s(4), titleY + self._s(4))))
        surf.blit(titleSurf, titleRect)

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
        if self.bFallingCages:
            self.drawHitCounter(screen, hitCount, maxHits)
        self.drawControls(screen)
        if bLevelComplete:
            self.drawLevelComplete(screen, score)
        elif bGameOver:
            self.drawGameOver(screen, score)
