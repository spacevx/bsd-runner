from typing import Any, Final
from enum import Enum, auto
import time
import sys

from strings import rpcGameName, rpcInMenu, rpcPlaying, rpcGameOver


_BROWSER_ENV: Final[bool] = sys.platform == "emscripten"

AioPresence: Any = None
DiscordNotFound: Any = Exception
PipeClosed: Any = Exception
_PYPRESENCE_AVAILABLE: bool = False

if not _BROWSER_ENV:
    try:
        from pypresence import AioPresence as _AioPresence, DiscordNotFound as _DiscordNotFound, PipeClosed as _PipeClosed  # type: ignore[import-not-found]
        AioPresence = _AioPresence
        DiscordNotFound = _DiscordNotFound
        PipeClosed = _PipeClosed
        _PYPRESENCE_AVAILABLE = True
    except ImportError:
        pass


clientId: Final[str] = "1468228058472386624"

class PresenceState(Enum):
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class DiscordRPC:
    def __init__(self) -> None:
        self.rpc: Any = None
        self.bConnected: bool = False
        self.currentState: PresenceState | None = None
        self.currentScore: int = 0
        self.startTime: int = 0

    async def connect(self) -> None:
        if not _PYPRESENCE_AVAILABLE or AioPresence is None:
            self.bConnected = False
            return
        try:
            self.rpc = AioPresence(clientId)
            await self.rpc.connect()
            self.bConnected = True
            self.startTime = int(time.time())
        except (DiscordNotFound, PipeClosed, ConnectionRefusedError, FileNotFoundError):
            self.bConnected = False
        except Exception:
            self.bConnected = False

    async def updateMenu(self) -> None:
        if not self.bConnected or self.rpc is None:
            return
        if self.currentState == PresenceState.MENU:
            return
        self.currentState = PresenceState.MENU
        try:
            await self.rpc.update(
                state=rpcInMenu,
                large_image="game_logo",
                large_text=rpcGameName,
                start=self.startTime
            )
        except (PipeClosed, ConnectionRefusedError, BrokenPipeError, RuntimeError):
            self.bConnected = False

    async def updatePlaying(self, score: int) -> None:
        if not self.bConnected or self.rpc is None:
            return
        if self.currentState == PresenceState.PLAYING and self.currentScore == score:
            return
        self.currentState = PresenceState.PLAYING
        self.currentScore = score
        try:
            await self.rpc.update(
                state=rpcPlaying.format(score=score),
                large_image="game_logo",
                large_text=rpcGameName,
                start=self.startTime
            )
        except (PipeClosed, ConnectionRefusedError, BrokenPipeError, RuntimeError):
            self.bConnected = False

    async def updateGameOver(self, finalScore: int) -> None:
        if not self.bConnected or self.rpc is None:
            return
        if self.currentState == PresenceState.GAME_OVER and self.currentScore == finalScore:
            return
        self.currentState = PresenceState.GAME_OVER
        self.currentScore = finalScore
        try:
            await self.rpc.update(
                state=rpcGameOver.format(score=finalScore),
                large_image="game_logo",
                large_text=rpcGameName,
                start=self.startTime
            )
        except (PipeClosed, ConnectionRefusedError, BrokenPipeError, RuntimeError):
            self.bConnected = False

    async def close(self) -> None:
        if self.rpc is not None:
            try:
                await self.rpc.clear()
            except (PipeClosed, ConnectionRefusedError, BrokenPipeError, Exception):
                pass
            try:
                self.rpc.close()
            except (PipeClosed, ConnectionRefusedError, BrokenPipeError, Exception):
                pass
        self.bConnected = False
        self.rpc = None
