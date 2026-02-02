import pygame
from pygame import Surface
from pygame.event import Event
from pygame.time import Clock
from pygame.font import Font

from settings import (
    WIDTH, HEIGHT, MIN_WIDTH, MIN_HEIGHT, FPS, TITLE,
    DARK_GRAY, WHITE, GameState, DISPLAY_FLAGS, ScreenSize
)
from screens import MainMenu, GameScreen
from strings import OPTIONS_TITLE, OPTIONS_SUBTITLE, INSTRUCTION_ESC


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen: Surface = pygame.display.set_mode((WIDTH, HEIGHT), DISPLAY_FLAGS)
        pygame.display.set_caption(TITLE)
        self.clock: Clock = pygame.time.Clock()

        self.screen_size: ScreenSize = (WIDTH, HEIGHT)
        self.fullscreen: bool = False
        self.windowed_size: ScreenSize = (WIDTH, HEIGHT)
        self.running: bool = True
        self.state: GameState = GameState.MENU

        self.menu: MainMenu = MainMenu(self.set_state)
        self.game_screen: GameScreen = GameScreen(self.set_state)

        self.font: Font = pygame.font.Font(None, 48)
        self.small_font: Font = pygame.font.Font(None, 32)

    def set_state(self, new_state: GameState) -> None:
        if new_state == GameState.GAME and self.state != GameState.GAME:
            self.game_screen.reset()
        self.state = new_state
        if self.state == GameState.QUIT:
            self.running = False

    def _toggle_fullscreen(self) -> None:
        result: int = pygame.display.toggle_fullscreen()

        if result:
            self.fullscreen = not self.fullscreen
            info = pygame.display.Info()
            if self.fullscreen:
                self.windowed_size = self.screen_size
                self.screen_size = (info.current_w, info.current_h)
            else:
                self.screen_size = self.windowed_size
        else:
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self.windowed_size = self.screen_size
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                info = pygame.display.Info()
                self.screen_size = (info.current_w, info.current_h)
            else:
                self.screen_size = self.windowed_size
                self.screen = pygame.display.set_mode(self.screen_size, DISPLAY_FLAGS)

        self.menu.on_resize(self.screen_size)
        self.game_screen.on_resize(self.screen_size)

    def _handle_resize(self, event: Event) -> None:
        w: int = max(event.w, MIN_WIDTH)
        h: int = max(event.h, MIN_HEIGHT)
        self.screen_size = (w, h)
        self.screen = pygame.display.set_mode(self.screen_size, DISPLAY_FLAGS)
        self.menu.on_resize(self.screen_size)
        self.game_screen.on_resize(self.screen_size)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE and self.fullscreen:
                    self._toggle_fullscreen()

            if self.state == GameState.MENU:
                self.menu.handle_event(event)

            elif self.state == GameState.GAME:
                self.game_screen.handle_event(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.fullscreen:
                    self.set_state(GameState.MENU)

            elif self.state == GameState.OPTIONS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.fullscreen:
                    self.set_state(GameState.MENU)

    def update(self, dt: float) -> None:
        if self.state == GameState.MENU:
            self.menu.update(dt)
        elif self.state == GameState.GAME:
            self.game_screen.update(dt)

    def draw(self) -> None:
        if self.state == GameState.MENU:
            self.menu.draw(self.screen)

        elif self.state == GameState.GAME:
            self.game_screen.draw(self.screen)

        elif self.state == GameState.OPTIONS:
            self._draw_placeholder(OPTIONS_TITLE, OPTIONS_SUBTITLE)

        pygame.display.flip()

    def _draw_placeholder(self, title: str, subtitle: str) -> None:
        w, h = self.screen_size

        self.screen.fill(DARK_GRAY)

        title_surf: Surface = self.font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(center=(w // 2, h // 2 - 30))
        self.screen.blit(title_surf, title_rect)

        sub_surf: Surface = self.small_font.render(subtitle, True, WHITE)
        sub_rect = sub_surf.get_rect(center=(w // 2, h // 2 + 20))
        self.screen.blit(sub_surf, sub_rect)

        esc_surf: Surface = self.small_font.render(INSTRUCTION_ESC, True, (150, 150, 150))
        esc_rect = esc_surf.get_rect(center=(w // 2, h - 50))
        self.screen.blit(esc_surf, esc_rect)

    def run(self) -> None:
        while self.running:
            dt: float = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
