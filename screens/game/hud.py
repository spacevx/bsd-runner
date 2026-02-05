import pygame
from pygame import Surface
from pygame.font import Font

from keybindings import keyBindings
from settings import ScreenSize, white, gold
from strings import gameOver, gameRestartKey, gameRestartButton, hudJump, hudSlide


class HUD:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: ScreenSize) -> None:
        self.screenSize = screenSize
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)
        self._createFonts()

        from entities.input.manager import InputManager
        from entities.input.joyicons import JoyIcons
        self.inputManager = InputManager()
        self.joyIcons = JoyIcons()

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _createFonts(self) -> None:
        self.font: Font = pygame.font.Font(None, self._s(96))
        self.smallFont: Font = pygame.font.Font(None, self._s(42))
        self.scoreFont: Font = pygame.font.Font(None, self._s(64))

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self._createFonts()

    def _drawTextWithShadow(self, screen: Surface, text: str, font: Font,
                            color: tuple[int, int, int], pos: tuple[int, int],
                            shadowOffset: int = 2) -> None:
        shadow = font.render(text, True, (0, 0, 0))
        surf = font.render(text, True, color)
        screen.blit(shadow, (pos[0] + shadowOffset, pos[1] + shadowOffset))
        screen.blit(surf, pos)

    def drawScore(self, screen: Surface, score: int) -> None:
        scoreX, scoreY = self._s(30), self._s(25)
        scoreText = f"Score: {score}"

        boxW = self._s(280)
        boxH = self._s(60)
        boxSurf = pygame.Surface((boxW, boxH), pygame.SRCALPHA)
        pygame.draw.rect(boxSurf, (0, 0, 0, 120), (0, 0, boxW, boxH), border_radius=self._s(8))
        pygame.draw.rect(boxSurf, (255, 255, 255, 40), (0, 0, boxW, boxH), self._s(2), border_radius=self._s(8))
        screen.blit(boxSurf, (scoreX - self._s(10), scoreY - self._s(10)))

        self._drawTextWithShadow(screen, scoreText, self.scoreFont, white, (scoreX, scoreY), self._s(3))

    def drawControls(self, screen: Surface) -> None:
        from entities.input.manager import InputSource
        from entities.input.joybindings import JoyBindings
        from entities.input.manager import GameAction

        if self.inputManager.lastInputSource == InputSource.JOYSTICK:
            self._drawJoystickHints(screen)
            return

        iconSize = self._s(36)
        ctrlX = self._s(30)
        ctrlY = self.screenSize[1] - self._s(55)

        jumpIcon = keyBindings.getKeyIcon(keyBindings.jump, iconSize)
        slideIcon = keyBindings.getKeyIcon(keyBindings.slide, iconSize)

        jumpLabel = self.smallFont.render(hudJump, True, white)
        slideLabel = self.smallFont.render(hudSlide, True, white)
        separator = self.smallFont.render("|", True, (150, 150, 150))

        totalW = iconSize + self._s(8) + jumpLabel.get_width() + self._s(20)
        totalW += separator.get_width() + self._s(20)
        totalW += iconSize + self._s(8) + slideLabel.get_width()
        boxH = iconSize + self._s(10)

        bgSurf = pygame.Surface((totalW + self._s(20), boxH), pygame.SRCALPHA)
        pygame.draw.rect(bgSurf, (0, 0, 0, 100), bgSurf.get_rect(), border_radius=self._s(5))
        screen.blit(bgSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))

        x = ctrlX
        centerY = ctrlY + boxH // 2 - self._s(5)

        if jumpIcon:
            screen.blit(jumpIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render(keyBindings.getKeyName(keyBindings.jump), True, white)
            screen.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        screen.blit(jumpLabel, (x, centerY - jumpLabel.get_height() // 2))
        x += jumpLabel.get_width() + self._s(20)

        screen.blit(separator, (x, centerY - separator.get_height() // 2))
        x += separator.get_width() + self._s(20)

        if slideIcon:
            screen.blit(slideIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render(keyBindings.getKeyName(keyBindings.slide), True, white)
            screen.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        screen.blit(slideLabel, (x, centerY - slideLabel.get_height() // 2))

    def _drawJoystickHints(self, screen: Surface) -> None:
        from entities.input.joybindings import JoyBindings
        from entities.input.manager import GameAction

        jb = JoyBindings()
        iconSize = self._s(36)
        ctrlX = self._s(30)
        ctrlY = self.screenSize[1] - self._s(55)

        jumpBtn = jb.getButtonForAction(GameAction.JUMP)
        slideBtn = jb.getButtonForAction(GameAction.SLIDE)

        jumpLabel = self.smallFont.render(hudJump, True, white)
        slideLabel = self.smallFont.render(hudSlide, True, white)
        separator = self.smallFont.render("|", True, (150, 150, 150))

        totalW = iconSize + self._s(8) + jumpLabel.get_width() + self._s(20)
        totalW += separator.get_width() + self._s(20)
        totalW += iconSize + self._s(8) + slideLabel.get_width()
        boxH = iconSize + self._s(10)

        bgSurf = pygame.Surface((totalW + self._s(20), boxH), pygame.SRCALPHA)
        pygame.draw.rect(bgSurf, (0, 0, 0, 100), bgSurf.get_rect(), border_radius=self._s(5))
        screen.blit(bgSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))

        x = ctrlX
        centerY = ctrlY + boxH // 2 - self._s(5)

        if jumpBtn is not None:
            jumpIcon = self.joyIcons.renderButtonIcon(jumpBtn, (iconSize, iconSize))
            screen.blit(jumpIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render("?", True, white)
            screen.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        screen.blit(jumpLabel, (x, centerY - jumpLabel.get_height() // 2))
        x += jumpLabel.get_width() + self._s(20)

        screen.blit(separator, (x, centerY - separator.get_height() // 2))
        x += separator.get_width() + self._s(20)

        if slideBtn is not None:
            slideIcon = self.joyIcons.renderButtonIcon(slideBtn, (iconSize, iconSize))
            screen.blit(slideIcon, (x, centerY - iconSize // 2))
            x += iconSize + self._s(8)
        else:
            fallback = self.smallFont.render("?", True, white)
            screen.blit(fallback, (x, centerY - fallback.get_height() // 2))
            x += fallback.get_width() + self._s(8)

        screen.blit(slideLabel, (x, centerY - slideLabel.get_height() // 2))

    def drawGameOver(self, screen: Surface, score: int) -> None:
        w, h = self.screenSize
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        cx, cy = w // 2, h // 2

        panelW, panelH = self._s(600), self._s(350)
        panel = pygame.Surface((panelW, panelH), pygame.SRCALPHA)
        pygame.draw.rect(panel, (30, 30, 35, 240), (0, 0, panelW, panelH), border_radius=self._s(15))
        pygame.draw.rect(panel, (139, 0, 0, 200), (0, 0, panelW, panelH), self._s(4), border_radius=self._s(15))
        screen.blit(panel, (cx - panelW // 2, cy - panelH // 2))

        titleSurf = self.font.render(gameOver, True, (255, 50, 50))
        titleRect = titleSurf.get_rect(center=(cx, cy - self._s(80)))

        for offset in range(self._s(15), 0, -3):
            glow = self.font.render(gameOver, True, (139, 0, 0))
            glow.set_alpha(int(40 * (1 - offset / self._s(15))))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow, titleSurf.get_rect(center=(cx + dx, cy - self._s(80) + dy)))

        shadow = self.font.render(gameOver, True, (50, 0, 0))
        screen.blit(shadow, titleSurf.get_rect(center=(cx + self._s(4), cy - self._s(76))))
        screen.blit(titleSurf, titleRect)

        scoreText = f"Score Final: {score}"
        scoreSurf = self.scoreFont.render(scoreText, True, gold)
        scoreRect = scoreSurf.get_rect(center=(cx, cy + self._s(10)))

        scoreShadow = self.scoreFont.render(scoreText, True, (100, 80, 0))
        screen.blit(scoreShadow, scoreSurf.get_rect(center=(cx + self._s(2), cy + self._s(12))))
        screen.blit(scoreSurf, scoreRect)

        from entities.input.manager import InputSource, GameAction
        from entities.input.joybindings import JoyBindings

        if self.inputManager.lastInputSource == InputSource.JOYSTICK:
            restartBtn = JoyBindings().getButtonForAction(GameAction.RESTART)
            if restartBtn is not None:
                btnName = self.joyIcons.getButtonName(restartBtn)
                restartText = gameRestartButton.format(button=btnName)
            else:
                restartText = gameRestartKey
        else:
            restartText = gameRestartKey

        restartSurf = self.smallFont.render(restartText, True, white)
        restartRect = restartSurf.get_rect(center=(cx, cy + self._s(90)))
        screen.blit(restartSurf, restartRect)

    def drawHitCounter(self, screen: Surface, hitCount: int, maxHits: int) -> None:
        x = self.screenSize[0] - self._s(200)
        y = self._s(25)
        boxW = self._s(180)
        boxH = self._s(60)
        boxSurf = pygame.Surface((boxW, boxH), pygame.SRCALPHA)
        pygame.draw.rect(boxSurf, (0, 0, 0, 120), (0, 0, boxW, boxH), border_radius=self._s(8))
        pygame.draw.rect(boxSurf, (255, 255, 255, 40), (0, 0, boxW, boxH), self._s(2), border_radius=self._s(8))
        screen.blit(boxSurf, (x - self._s(10), y - self._s(10)))

        heartSize = self._s(32)
        spacing = self._s(45)
        startX = x + self._s(10)
        for i in range(maxHits):
            heartX = startX + i * spacing
            heartY = y + self._s(5)
            if i < hitCount:
                color = (80, 80, 80)
            else:
                color = (220, 50, 50)
            pygame.draw.polygon(screen, color, [
                (heartX + heartSize // 2, heartY + heartSize),
                (heartX, heartY + heartSize // 3),
                (heartX + heartSize // 4, heartY),
                (heartX + heartSize // 2, heartY + heartSize // 4),
                (heartX + heartSize * 3 // 4, heartY),
                (heartX + heartSize, heartY + heartSize // 3),
            ])

    def draw(self, screen: Surface, score: int, bGameOver: bool, hitCount: int = 0, maxHits: int = 3) -> None:
        self.drawScore(screen, score)
        self.drawHitCounter(screen, hitCount, maxHits)
        self.drawControls(screen)
        if bGameOver:
            self.drawGameOver(screen, score)
