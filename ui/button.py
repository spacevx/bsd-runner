from typing import Callable

import pygame
from pygame import Surface, Rect
from pygame.event import Event
from pygame.font import Font

from settings import RED, RED_BRIGHT, GOLD, WHITE, Color


class Button(pygame.sprite.Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        callback: Callable[[], None] | None = None
    ) -> None:
        super().__init__()
        self.width: int = width
        self.height: int = height
        self.text: str = text
        self.callback: Callable[[], None] | None = callback
        self.hovered: bool = False

        self.color_normal: Color = RED
        self.color_hover: Color = RED_BRIGHT
        self.border_color: Color = GOLD
        self.text_color: Color = WHITE

        self.image: Surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect: Rect = self.image.get_rect(center=(x, y))

        self.font: Font = pygame.font.Font(None, 36)

        self._render()

    def _render(self) -> None:
        self.image.fill((0, 0, 0, 0))

        color: Color = self.color_hover if self.hovered else self.color_normal
        border_width: int = 3 if self.hovered else 0

        pygame.draw.rect(
            self.image,
            color,
            (0, 0, self.width, self.height),
            border_radius=8
        )

        if self.hovered:
            pygame.draw.rect(
                self.image,
                self.border_color,
                (0, 0, self.width, self.height),
                width=border_width,
                border_radius=8
            )

        text_surface: Surface = self.font.render(self.text, True, self.text_color)
        text_rect: Rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.image.blit(text_surface, text_rect)

    def update(self) -> None:
        mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        was_hovered: bool = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)

        if was_hovered != self.hovered:
            self._render()

    def handle_event(self, event: Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.callback:
                self.callback()
                return True
        return False
