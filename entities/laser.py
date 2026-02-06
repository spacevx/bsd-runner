import pygame
from pygame import Surface


class LaserBeam:
    duration: float = 0.18

    def __init__(self, startX: int, startY: int, endX: int, endY: int) -> None:
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.timer = self.duration
        self.bActive = True

    def update(self, dt: float) -> None:
        self.timer -= dt
        if self.timer <= 0:
            self.bActive = False

    def draw(self, screen: Surface) -> None:
        if not self.bActive:
            return
        t = self.timer / self.duration
        alpha = int(255 * t)

        outerGlow = (255, 30, 0, min(40, alpha // 4))
        midGlow = (255, 60, 20, min(80, alpha // 3))
        innerGlow = (255, 100, 50, min(120, alpha // 2))
        coreColor = (255, 200, 180, alpha)

        start = (self.startX, self.startY)
        end = (self.endX, self.endY)

        pygame.draw.line(screen, outerGlow, start, end, 25)
        pygame.draw.line(screen, midGlow, start, end, 18)
        pygame.draw.line(screen, innerGlow, start, end, 12)
        pygame.draw.line(screen, coreColor, start, end, 6)
