from typing import Final
from enum import Enum, auto
import time

from pypresence import Presence, DiscordNotFound, PipeClosed

from strings import rpcGameName, rpcInMenu, rpcPlaying, rpcGameOver


clientId: Final[str] = "1468228058472386624"

class PresenceState(Enum):
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class DiscordRPC:
    def __init__(self) -> None:
        self.rpc: Presence | None = None
        self.bConnected: bool = False
        self.currentState: PresenceState | None = None
        self.currentScore: int = 0
        self.startTime: int = 0
        self._connect()

    def _connect(self) -> None:
        if clientId == "YOUR_CLIENT_ID_HERE":
            return
        try:
            self.rpc = Presence(clientId)
            self.rpc.connect()
            self.bConnected = True
            self.startTime = int(time.time())
        except (DiscordNotFound, PipeClosed, ConnectionRefusedError, FileNotFoundError):
            self.bConnected = False

    def updateMenu(self) -> None:
        if not self.bConnected or self.rpc is None:
            return
        if self.currentState == PresenceState.MENU:
            return
        self.currentState = PresenceState.MENU
        try:
            self.rpc.update(
                state=rpcInMenu,
                large_image="game_logo",
                large_text=rpcGameName,
                start=self.startTime
            )
        except (PipeClosed, ConnectionRefusedError, BrokenPipeError):
            self.bConnected = False

    def updatePlaying(self, score: int) -> None:
        if not self.bConnected or self.rpc is None:
            return
        if self.currentState == PresenceState.PLAYING and self.currentScore == score:
            return
        self.currentState = PresenceState.PLAYING
        self.currentScore = score
        try:
            self.rpc.update(
                state=rpcPlaying.format(score=score),
                large_image="game_logo",
                large_text=rpcGameName,
                start=self.startTime
            )
        except (PipeClosed, ConnectionRefusedError, BrokenPipeError):
            self.bConnected = False

    def updateGameOver(self, finalScore: int) -> None:
        if not self.bConnected or self.rpc is None:
            return
        if self.currentState == PresenceState.GAME_OVER and self.currentScore == finalScore:
            return
        self.currentState = PresenceState.GAME_OVER
        self.currentScore = finalScore
        try:
            self.rpc.update(
                state=rpcGameOver.format(score=finalScore),
                large_image="game_logo",
                large_text=rpcGameName,
                start=self.startTime
            )
        except (PipeClosed, ConnectionRefusedError, BrokenPipeError):
            self.bConnected = False

    def close(self) -> None:
        if self.bConnected and self.rpc is not None:
            try:
                self.rpc.close()
            except (PipeClosed, ConnectionRefusedError, BrokenPipeError):
                pass
        self.bConnected = False
