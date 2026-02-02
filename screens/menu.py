import pygame
import math
from settings import WIDTH, HEIGHT, DARK_GRAY, DARK_GRAY_LIGHT, GOLD, RED, WHITE, GameState
from ui import Button
from strings import (
    MENU_TITLE, MENU_SUBTITLE,
    BTN_START, BTN_OPTIONS, BTN_QUIT
)


class MainMenu:
    def __init__(self, set_state_callback):
        self.set_state = set_state_callback

        self.background = self._create_background()

        self.buttons = pygame.sprite.Group()

        button_y_start = 350
        button_spacing = 70
        button_width = 320
        button_height = 50

        start_btn = Button(
            WIDTH // 2, button_y_start,
            button_width, button_height,
            BTN_START,
            lambda: self.set_state(GameState.GAME)
        )

        options_btn = Button(
            WIDTH // 2, button_y_start + button_spacing,
            button_width, button_height,
            BTN_OPTIONS,
            lambda: self.set_state(GameState.OPTIONS)
        )

        quit_btn = Button(
            WIDTH // 2, button_y_start + button_spacing * 2,
            button_width, button_height,
            BTN_QUIT,
            lambda: self.set_state(GameState.QUIT)
        )

        self.buttons.add(start_btn, options_btn, quit_btn)

        self.title_font = pygame.font.Font(None, 120)
        self.subtitle_font = pygame.font.Font(None, 36)

    def _create_background(self):
        surface = pygame.Surface((WIDTH, HEIGHT))

        for y in range(HEIGHT):
            factor = 1 - abs(y - HEIGHT // 2) / (HEIGHT // 2) * 0.3
            color = (
                int(DARK_GRAY[0] * factor),
                int(DARK_GRAY[1] * factor),
                int(DARK_GRAY[2] * factor)
            )
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))

        self._draw_spotlight(surface)
        self._draw_octagon(surface)
        self._draw_cage_fence(surface)

        return surface

    def _draw_spotlight(self, surface):
        center_x = WIDTH // 2
        for y in range(HEIGHT // 2):
            radius = int(y * 0.8)
            alpha = max(0, 30 - y // 10)
            if alpha > 0 and radius > 0:
                spotlight = pygame.Surface((radius * 2, 2), pygame.SRCALPHA)
                spotlight.fill((255, 255, 255, alpha))
                surface.blit(spotlight, (center_x - radius, y))

    def _draw_octagon(self, surface):
        center_x = WIDTH // 2
        center_y = HEIGHT // 2 + 50
        radius = 200

        points = []
        for i in range(8):
            angle = math.pi / 8 + i * math.pi / 4  # 22.5 degrees
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))

        octagon_color = (60, 60, 70)
        pygame.draw.polygon(surface, octagon_color, points, 3)

        inner_points = []
        inner_radius = radius - 20
        for i in range(8):
            angle = math.pi / 8 + i * math.pi / 4
            x = center_x + inner_radius * math.cos(angle)
            y = center_y + inner_radius * math.sin(angle)
            inner_points.append((x, y))

        pygame.draw.polygon(surface, (50, 50, 60), inner_points, 2)

    def _draw_cage_fence(self, surface):
        fence_color = (45, 45, 55)

        # Left edge
        for y in range(0, HEIGHT, 20):
            for x in range(0, 40, 20):
                pygame.draw.line(surface, fence_color, (x, y), (x + 10, y + 10), 1)
                pygame.draw.line(surface, fence_color, (x + 10, y + 10), (x, y + 20), 1)

        for y in range(0, HEIGHT, 20):
            for x in range(WIDTH - 40, WIDTH, 20):
                pygame.draw.line(surface, fence_color, (x, y), (x + 10, y + 10), 1)
                pygame.draw.line(surface, fence_color, (x + 10, y + 10), (x, y + 20), 1)

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)

    def update(self):
        self.buttons.update()

    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        shadow_surface = self.title_font.render(MENU_TITLE, True, RED)
        shadow_rect = shadow_surface.get_rect(center=(WIDTH // 2 + 4, 120 + 4))
        screen.blit(shadow_surface, shadow_rect)

        title_surface = self.title_font.render(MENU_TITLE, True, GOLD)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, 120))
        screen.blit(title_surface, title_rect)

        subtitle_surface = self.subtitle_font.render(MENU_SUBTITLE, True, WHITE)
        subtitle_rect = subtitle_surface.get_rect(center=(WIDTH // 2, 180))
        screen.blit(subtitle_surface, subtitle_rect)

        self.buttons.draw(screen)
