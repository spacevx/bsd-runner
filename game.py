import asyncio
import pygame
from pygame import Surface
from pygame.event import Event
from pygame.time import Clock

from settings import (
    width, height, minWidth, minHeight, fps, title,
    GameState, displayFlags, ScreenSize
)
from screens import MainMenu, GameScreen, OptionsScreen, LevelSelectScreen
from discord import DiscordRPC
from levels import level1Config, levelConfigs
from paths import assetsPath
import config
import settings


class Game:
    def __init__(self) -> None:
        pygame.init()
        config.load()
        pygame.display.set_mode((width, height), 0)
        self.screen: Surface = pygame.display.set_mode((width, height), displayFlags)
        pygame.display.set_caption(title)
        iconPath = assetsPath / "logo" / "logo_32.ico"
        pygame.display.set_icon(pygame.image.load(iconPath))
        self.clock: Clock = pygame.time.Clock()

        self.screenSize: ScreenSize = (width, height)
        self.bFullscreen: bool = False
        self.windowedSize: ScreenSize = (width, height)
        self.bRunning: bool = True
        self.state: GameState = GameState.MENU
        self.currentLevel: int = 1

        self.menu: MainMenu = MainMenu(self.setState)
        self.levelSelect: LevelSelectScreen = LevelSelectScreen(
            self.screenSize, self.setState, self.startLevel
        )
        self.gameScreen: GameScreen = GameScreen(self.setState, level1Config)
        self.optionsScreen: OptionsScreen = OptionsScreen((width, height), self.setState)

        self.discordRpc: DiscordRPC = DiscordRPC()
        self.rpcUpdateTimer: float = 0.0
        self.rpcUpdateInterval: float = 5.0

        from entities.input.manager import InputManager
        self.inputManager: InputManager = InputManager()

    def startLevel(self, levelId: int) -> None:
        self.currentLevel = levelId
        cfg = levelConfigs.get(levelId, level1Config)
        self.gameScreen = GameScreen(self.setState, cfg)
        self.gameScreen.onResize(self.screenSize)
        self.setState(GameState.GAME)

    def setState(self, newState: GameState) -> None:
        if newState == GameState.GAME and self.state != GameState.GAME:
            self.gameScreen.reset()
        self.state = newState
        if self.state == GameState.QUIT:
            self.bRunning = False

    def _toggleFullscreen(self) -> None:
        result: int = pygame.display.toggle_fullscreen()

        if result:
            self.bFullscreen = not self.bFullscreen
            info = pygame.display.Info()
            if self.bFullscreen:
                self.windowedSize = self.screenSize
                self.screenSize = (info.current_w, info.current_h)
            else:
                self.screenSize = self.windowedSize
        else:
            self.bFullscreen = not self.bFullscreen
            if self.bFullscreen:
                self.windowedSize = self.screenSize
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                info = pygame.display.Info()
                self.screenSize = (info.current_w, info.current_h)
            else:
                self.screenSize = self.windowedSize
                self.screen = pygame.display.set_mode(self.screenSize, displayFlags)

        self.menu.onResize(self.screenSize)
        self.levelSelect.onResize(self.screenSize)
        self.gameScreen.onResize(self.screenSize)
        self.optionsScreen.onResize(self.screenSize)

    def _handleResize(self, event: Event) -> None:
        w: int = max(event.w, minWidth)
        h: int = max(event.h, minHeight)
        self.screenSize = (w, h)
        self.screen = pygame.display.set_mode(self.screenSize, displayFlags)
        self.menu.onResize(self.screenSize)
        self.levelSelect.onResize(self.screenSize)
        self.gameScreen.onResize(self.screenSize)
        self.optionsScreen.onResize(self.screenSize)

    def handleEvents(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                self.inputManager.handleJoyDeviceAdded(event)
                continue
            elif event.type == pygame.JOYDEVICEREMOVED:
                self.inputManager.handleJoyDeviceRemoved(event)
                continue

            inputEvent = self.inputManager.processEvent(event)

            if event.type == pygame.QUIT:
                self.bRunning = False

            elif event.type == pygame.VIDEORESIZE:
                self._handleResize(event)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self._toggleFullscreen()
                elif event.key == pygame.K_ESCAPE and self.bFullscreen:
                    self._toggleFullscreen()

            if self.state == GameState.MENU:
                self.menu.handleEvent(event, inputEvent)

            elif self.state == GameState.LEVEL_SELECT:
                self.levelSelect.handleEvent(event, inputEvent)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.bFullscreen:
                    self.setState(GameState.MENU)

            elif self.state == GameState.GAME:
                self.gameScreen.handleEvent(event, inputEvent)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.bFullscreen:
                    self.setState(GameState.MENU)

            elif self.state == GameState.OPTIONS:
                self.optionsScreen.handleEvent(event, inputEvent)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.bFullscreen:
                    self.setState(GameState.MENU)

    def update(self, dt: float) -> None:
        if self.state == GameState.MENU:
            self.menu.update(dt)
        elif self.state == GameState.LEVEL_SELECT:
            self.levelSelect.update(dt)
        elif self.state == GameState.GAME:
            self.gameScreen.update(dt)
            if self.gameScreen.bLevelComplete and not settings.bIsLevelCompleted(self.currentLevel):
                settings.completeLevel(self.currentLevel)
                config.save()
        elif self.state == GameState.OPTIONS:
            self.optionsScreen.update(dt)

    def draw(self) -> None:
        if self.state == GameState.MENU:
            self.menu.draw(self.screen)
        elif self.state == GameState.LEVEL_SELECT:
            self.levelSelect.draw(self.screen)
        elif self.state == GameState.GAME:
            self.gameScreen.draw(self.screen)
        elif self.state == GameState.OPTIONS:
            self.optionsScreen.draw(self.screen)

        pygame.display.flip()

    async def _updateDiscordRpc(self, dt: float) -> None:
        self.rpcUpdateTimer += dt
        if self.rpcUpdateTimer < self.rpcUpdateInterval:
            return
        self.rpcUpdateTimer = 0.0

        if self.state in (GameState.MENU, GameState.OPTIONS, GameState.LEVEL_SELECT):
            await self.discordRpc.updateMenu()
        elif self.state == GameState.GAME:
            if self.gameScreen.bGameOver:
                await self.discordRpc.updateGameOver(self.gameScreen.score)
            else:
                await self.discordRpc.updatePlaying(self.gameScreen.score)

    async def run(self) -> None:
        await self.discordRpc.connect()
        try:
            while self.bRunning:
                dt: float = self.clock.tick(fps) / 1000.0
                self.handleEvents()
                self.update(dt)
                await self._updateDiscordRpc(dt)
                self.draw()
                await asyncio.sleep(0)
        finally:
            config.save()
            await self.discordRpc.close()
            pygame.quit()
