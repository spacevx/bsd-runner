import pygame
from pygame import Surface
from pygame.font import Font

from settings import ScreenSize, white, gold
from strings import gameOver, gameRestart


class HUD:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: ScreenSize) -> None:
        self.screenSize = screenSize
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)
        self._createFonts()

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
        controlsText = "ESPACE: Sauter | BAS: Glisser"
        ctrlX = self._s(30)
        ctrlY = self.screenSize[1] - self._s(50)

        ctrlSurf = self.smallFont.render(controlsText, True, white)
        ctrlW, ctrlH = ctrlSurf.get_size()

        bgSurf = pygame.Surface((ctrlW + self._s(20), ctrlH + self._s(10)), pygame.SRCALPHA)
        pygame.draw.rect(bgSurf, (0, 0, 0, 100), bgSurf.get_rect(), border_radius=self._s(5))
        screen.blit(bgSurf, (ctrlX - self._s(10), ctrlY - self._s(5)))

        self._drawTextWithShadow(screen, controlsText, self.smallFont, white, (ctrlX, ctrlY), self._s(2))

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

        restartSurf = self.smallFont.render(gameRestart, True, white)
        restartRect = restartSurf.get_rect(center=(cx, cy + self._s(90)))
        screen.blit(restartSurf, restartRect)

    def draw(self, screen: Surface, score: int, bGameOver: bool) -> None:
        self.drawScore(screen, score)
        self.drawControls(screen)
        if bGameOver:
            self.drawGameOver(screen, score)
