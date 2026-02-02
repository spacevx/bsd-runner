import pygame
from settings import RED, RED_BRIGHT, GOLD, WHITE


class Button(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height, text, callback=None):
        super().__init__()
        self.width = width
        self.height = height
        self.text = text
        self.callback = callback
        self.hovered = False

        self.color_normal = RED
        self.color_hover = RED_BRIGHT
        self.border_color = GOLD
        self.text_color = WHITE

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

        self.font = pygame.font.Font(None, 36)

        self._render()

    def _render(self):
        self.image.fill((0, 0, 0, 0))

        color = self.color_hover if self.hovered else self.color_normal
        border_width = 3 if self.hovered else 0

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

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.image.blit(text_surface, text_rect)

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)

        if was_hovered != self.hovered:
            self._render()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.callback:
                self.callback()
                return True
        return False
