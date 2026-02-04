import asyncio
import os
import pygame
from pygame import Surface
from pygame.event import Event
from pygame.time import Clock
from pygame.font import Font

from settings import (
    width, height, minWidth, minHeight, fps, title,
    darkGray, white, GameState, displayFlags, ScreenSize
)
from screens import MainMenu, GameScreen
from strings import optionsTitle, optionsSubtitle, instructionEsc
from discord import DiscordRPC


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_mode((width, height), 0)
        self.screen: Surface = pygame.display.set_mode((width, height), displayFlags)
        pygame.display.set_caption(title)
        self.clock: Clock = pygame.time.Clock()

        self.screenSize: ScreenSize = (width, height)
        self.bFullscreen: bool = False
        self.windowedSize: ScreenSize = (width, height)
        self.bRunning: bool = True
        self.state: GameState = GameState.MENU

        self.menu: MainMenu = MainMenu(self.setState)
        self.gameScreen: GameScreen = GameScreen(self.setState)

        self.font: Font = pygame.font.Font(None, 48)
        self.smallFont: Font = pygame.font.Font(None, 32)

        self.discordRpc: DiscordRPC = DiscordRPC()
        self.rpcUpdateTimer: float = 0.0
        self.rpcUpdateInterval: float = 5.0

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
        self.gameScreen.onResize(self.screenSize)

    def _handleResize(self, event: Event) -> None:
        w: int = max(event.w, minWidth)
        h: int = max(event.h, minHeight)
        self.screenSize = (w, h)
        self.screen = pygame.display.set_mode(self.screenSize, displayFlags)
        self.menu.onResize(self.screenSize)
        self.gameScreen.onResize(self.screenSize)

    def handleEvents(self) -> None:
        for event in pygame.event.get():
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
                self.menu.handleEvent(event)

            elif self.state == GameState.GAME:
                self.gameScreen.handleEvent(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.bFullscreen:
                    self.setState(GameState.MENU)

            elif self.state == GameState.OPTIONS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.bFullscreen:
                    self.setState(GameState.MENU)

    def update(self, dt: float) -> None:
        if self.state == GameState.MENU:
            self.menu.update(dt)
        elif self.state == GameState.GAME:
            self.gameScreen.update(dt)

    def draw(self) -> None:
        if self.state == GameState.MENU:
            self.menu.draw(self.screen)

        elif self.state == GameState.GAME:
            self.gameScreen.draw(self.screen)

        elif self.state == GameState.OPTIONS:
            self._drawPlaceholder(optionsTitle, optionsSubtitle)

        pygame.display.flip()

    def _drawPlaceholder(self, titleText: str, subtitle: str) -> None:
        w, h = self.screenSize

        self.screen.fill(darkGray)

        titleSurf: Surface = self.font.render(titleText, True, white)
        titleRect = titleSurf.get_rect(center=(w // 2, h // 2 - 30))
        self.screen.blit(titleSurf, titleRect)

        subSurf: Surface = self.smallFont.render(subtitle, True, white)
        subRect = subSurf.get_rect(center=(w // 2, h // 2 + 20))
        self.screen.blit(subSurf, subRect)

        escSurf: Surface = self.smallFont.render(instructionEsc, True, (150, 150, 150))
        escRect = escSurf.get_rect(center=(w // 2, h - 50))
        self.screen.blit(escSurf, escRect)

    async def _updateDiscordRpc(self, dt: float) -> None:
        self.rpcUpdateTimer += dt
        if self.rpcUpdateTimer < self.rpcUpdateInterval:
            return
        self.rpcUpdateTimer = 0.0

        if self.state == GameState.MENU or self.state == GameState.OPTIONS:
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
            await self.discordRpc.close()
            pygame.quit()
