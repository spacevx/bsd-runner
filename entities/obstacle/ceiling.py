import pygame
from pygame import Surface

from settings import Color


class Ceiling:
    defaultHeight: int = 60

    def __init__(self, screenWidth: int, screenHeight: int) -> None:
        self.width = screenWidth
        self.height = self.defaultHeight
        self.image = self._createSurface(screenWidth)
        self.rect = self.image.get_rect(topleft=(0, 0))

    def _createSurface(self, width: int) -> Surface:
        surface = pygame.Surface((width, self.height), pygame.SRCALPHA)

        beamColor: Color = (50, 45, 40)
        darkBeam: Color = (30, 28, 25)
        highlight: Color = (70, 65, 60)

        pygame.draw.rect(surface, beamColor, (0, 0, width, self.height))
        pygame.draw.rect(surface, darkBeam, (0, self.height - 8, width, 8))
        pygame.draw.line(surface, highlight, (0, 5), (width, 5), 2)

        rafterSpacing = 200
        for x in range(0, width + rafterSpacing, rafterSpacing):
            pygame.draw.rect(surface, darkBeam, (x - 15, 0, 30, self.height))
            pygame.draw.line(surface, highlight, (x - 14, 0), (x - 14, self.height - 10), 1)

        return surface

    def onResize(self, newWidth: int) -> None:
        self.width = newWidth
        self.image = self._createSurface(newWidth)
        self.rect = self.image.get_rect(topleft=(0, 0))

    def draw(self, screen: Surface) -> None:
        screen.blit(self.image, self.rect)
