from typing import Final
from dataclasses import dataclass
from pathlib import Path
import json

from .manager import GameAction


@dataclass
class JoyBinding:
    button: int | None = None
    axis: int | None = None
    axisDirection: int = 1
    trigger: int | None = None


class JoyBindings:
    CONFIG_FILE: Final[str] = "joybindings.json"

    DEFAULT_BINDINGS: Final[dict[GameAction, JoyBinding]] = {
        GameAction.JUMP: JoyBinding(button=0),
        GameAction.SLIDE: JoyBinding(button=1),
        GameAction.RESTART: JoyBinding(button=2),
        GameAction.PAUSE: JoyBinding(button=7),
    }

    _instance: "JoyBindings | None" = None

    def __new__(cls) -> "JoyBindings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.bindings: dict[GameAction, JoyBinding] = dict(self.DEFAULT_BINDINGS)
        self._buttonToAction: dict[int, GameAction] = {}
        self._rebuildLookup()
        self._loadConfig()

    def _rebuildLookup(self) -> None:
        self._buttonToAction.clear()
        gameplayActions = {GameAction.JUMP, GameAction.SLIDE, GameAction.RESTART, GameAction.PAUSE}

        for action, binding in self.bindings.items():
            if binding.button is not None:
                existing = self._buttonToAction.get(binding.button)
                if existing is None or (action in gameplayActions and existing not in gameplayActions):
                    self._buttonToAction[binding.button] = action

    def _loadConfig(self) -> None:
        configPath = Path(self.CONFIG_FILE)
        if not configPath.exists():
            return
        try:
            with open(configPath, 'r') as f:
                data = json.load(f)
            for actionName, bindingData in data.items():
                action = GameAction[actionName]
                self.bindings[action] = JoyBinding(
                    button=bindingData.get('button'),
                    axis=bindingData.get('axis'),
                    axisDirection=bindingData.get('axisDirection', 1),
                    trigger=bindingData.get('trigger')
                )
            self._rebuildLookup()
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            pass

    def saveConfig(self) -> None:
        data = {}
        for action, binding in self.bindings.items():
            data[action.name] = {
                'button': binding.button,
                'axis': binding.axis,
                'axisDirection': binding.axisDirection,
                'trigger': binding.trigger
            }
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def getActionForButton(self, button: int) -> GameAction | None:
        return self._buttonToAction.get(button)

    def setBinding(self, action: GameAction, binding: JoyBinding) -> None:
        self.bindings[action] = binding
        self._rebuildLookup()

    def getBinding(self, action: GameAction) -> JoyBinding | None:
        return self.bindings.get(action)

    def getButtonForAction(self, action: GameAction) -> int | None:
        binding = self.bindings.get(action)
        return binding.button if binding else None

    def resetToDefaults(self) -> None:
        self.bindings = dict(self.DEFAULT_BINDINGS)
        self._rebuildLookup()
