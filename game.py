import pygame
from pygame import Surface
from pygame.event import Event
from pygame.time import Clock
from pygame.font import Font

from settings import WIDTH, HEIGHT, FPS, TITLE, DARK_GRAY, WHITE, GameState
from screens import MainMenu
from strings import (
    GAME_TITLE, GAME_SUBTITLE,
    OPTIONS_TITLE, OPTIONS_SUBTITLE,
    INSTRUCTION_ESC
)


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen: Surface = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock: Clock = pygame.time.Clock()

        self.running: bool = True
        self.state: GameState = GameState.MENU

        self.menu: MainMenu = MainMenu(self.set_state)

        self.font: Font = pygame.font.Font(None, 48)
        self.small_font: Font = pygame.font.Font(None, 32)

    def set_state(self, new_state: GameState) -> None:
        self.state = new_state
        if self.state == GameState.QUIT:
            self.running = False

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.state == GameState.MENU:
                self.menu.handle_event(event)

            elif self.state in (GameState.GAME, GameState.OPTIONS):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.set_state(GameState.MENU)

    def update(self) -> None:
        if self.state == GameState.MENU:
            self.menu.update()

    def draw(self) -> None:
        if self.state == GameState.MENU:
            self.menu.draw(self.screen)

        elif self.state == GameState.GAME:
            self._draw_placeholder(GAME_TITLE, GAME_SUBTITLE)

        elif self.state == GameState.OPTIONS:
            self._draw_placeholder(OPTIONS_TITLE, OPTIONS_SUBTITLE)

        pygame.display.flip()

    def _draw_placeholder(self, title: str, subtitle: str) -> None:
        self.screen.fill(DARK_GRAY)

        title_surface: Surface = self.font.render(title, True, WHITE)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(title_surface, title_rect)

        subtitle_surface: Surface = self.small_font.render(subtitle, True, WHITE)
        subtitle_rect = subtitle_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        self.screen.blit(subtitle_surface, subtitle_rect)

        esc_surface: Surface = self.small_font.render(INSTRUCTION_ESC, True, (150, 150, 150))
        esc_rect = esc_surface.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        self.screen.blit(esc_surface, esc_rect)

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
