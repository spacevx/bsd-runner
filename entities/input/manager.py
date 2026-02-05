from enum import Enum, auto
from dataclasses import dataclass
from typing import Final

import pygame


class InputSource(Enum):
    KEYBOARD = auto()
    JOYSTICK = auto()


class GameAction(Enum):
    JUMP = auto()
    SLIDE = auto()
    RESTART = auto()
    MENU_UP = auto()
    MENU_DOWN = auto()
    MENU_LEFT = auto()
    MENU_RIGHT = auto()
    MENU_CONFIRM = auto()
    MENU_BACK = auto()
    PAUSE = auto()


@dataclass(slots=True)
class InputEvent:
    action: GameAction
    source: InputSource
    bPressed: bool
    rawValue: float = 1.0


class InputManager:
    DEADZONE: Final[float] = 0.3
    AXIS_THRESHOLD: Final[float] = 0.5

    _instance: "InputManager | None" = None

    def __new__(cls) -> "InputManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        self.activeJoystickId: int | None = None
        self.bJoystickConnected: bool = False
        self.lastInputSource: InputSource = InputSource.KEYBOARD

        self._axisStates: dict[int, dict[int, int]] = {}
        self._hatStates: dict[int, dict[int, tuple[int, int]]] = {}

        pygame.joystick.init()
        self._scanJoysticks()

    def _scanJoysticks(self) -> None:
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            instanceId = joy.get_instance_id()
            self.joysticks[instanceId] = joy
            self._axisStates[instanceId] = {}
            self._hatStates[instanceId] = {}
            if self.activeJoystickId is None:
                self.activeJoystickId = instanceId
        self.bJoystickConnected = len(self.joysticks) > 0

    def handleJoyDeviceAdded(self, event: pygame.event.Event) -> None:
        joy = pygame.joystick.Joystick(event.device_index)
        joy.init()
        instanceId = joy.get_instance_id()
        self.joysticks[instanceId] = joy
        self._axisStates[instanceId] = {}
        self._hatStates[instanceId] = {}
        if self.activeJoystickId is None:
            self.activeJoystickId = instanceId
        self.bJoystickConnected = True

    def handleJoyDeviceRemoved(self, event: pygame.event.Event) -> None:
        instanceId = event.instance_id
        if instanceId in self.joysticks:
            del self.joysticks[instanceId]
            del self._axisStates[instanceId]
            del self._hatStates[instanceId]
        if self.activeJoystickId == instanceId:
            self.activeJoystickId = next(iter(self.joysticks.keys()), None)
        self.bJoystickConnected = len(self.joysticks) > 0

    def processEvent(self, event: pygame.event.Event) -> InputEvent | None:
        from .joybindings import JoyBindings
        from keybindings import KeyBindings

        if event.type == pygame.KEYDOWN:
            self.lastInputSource = InputSource.KEYBOARD
            action = KeyBindings().getActionForKey(event.key)
            if action:
                return InputEvent(action, InputSource.KEYBOARD, True)

        elif event.type == pygame.KEYUP:
            action = KeyBindings().getActionForKey(event.key)
            if action:
                return InputEvent(action, InputSource.KEYBOARD, False)

        elif event.type == pygame.JOYBUTTONDOWN:
            if event.instance_id != self.activeJoystickId:
                return None
            self.lastInputSource = InputSource.JOYSTICK
            action = JoyBindings().getActionForButton(event.button)
            if action:
                inputEvent = InputEvent(action, InputSource.JOYSTICK, True)
                return inputEvent

        elif event.type == pygame.JOYBUTTONUP:
            if event.instance_id != self.activeJoystickId:
                return None
            action = JoyBindings().getActionForButton(event.button)
            if action:
                return InputEvent(action, InputSource.JOYSTICK, False)

        elif event.type == pygame.JOYAXISMOTION:
            if event.instance_id != self.activeJoystickId:
                return None
            return self._processAxisEvent(event)

        elif event.type == pygame.JOYHATMOTION:
            if event.instance_id != self.activeJoystickId:
                return None
            return self._processHatEvent(event)

        return None

    def _processAxisEvent(self, event: pygame.event.Event) -> InputEvent | None:
        joyId = event.instance_id
        axis = event.axis
        value = event.value

        if abs(value) < self.DEADZONE:
            newState = 0
        elif value < -self.AXIS_THRESHOLD:
            newState = -1
        elif value > self.AXIS_THRESHOLD:
            newState = 1
        else:
            newState = 0

        oldState = self._axisStates[joyId].get(axis, 0)
        self._axisStates[joyId][axis] = newState

        if newState == oldState:
            return None

        self.lastInputSource = InputSource.JOYSTICK

        if axis == 0:
            if newState == -1:
                return InputEvent(GameAction.MENU_LEFT, InputSource.JOYSTICK, True)
            elif newState == 1:
                return InputEvent(GameAction.MENU_RIGHT, InputSource.JOYSTICK, True)
        elif axis == 1:
            if newState == -1:
                return InputEvent(GameAction.MENU_UP, InputSource.JOYSTICK, True)
            elif newState == 1:
                return InputEvent(GameAction.MENU_DOWN, InputSource.JOYSTICK, True)

        return None

    def _processHatEvent(self, event: pygame.event.Event) -> InputEvent | None:
        joyId = event.instance_id
        hat = event.hat
        x, y = event.value

        oldState = self._hatStates[joyId].get(hat, (0, 0))
        self._hatStates[joyId][hat] = (x, y)

        if (x, y) == oldState:
            return None

        self.lastInputSource = InputSource.JOYSTICK

        if y == 1 and oldState[1] != 1:
            return InputEvent(GameAction.MENU_UP, InputSource.JOYSTICK, True)
        elif y == -1 and oldState[1] != -1:
            return InputEvent(GameAction.MENU_DOWN, InputSource.JOYSTICK, True)
        elif x == -1 and oldState[0] != -1:
            return InputEvent(GameAction.MENU_LEFT, InputSource.JOYSTICK, True)
        elif x == 1 and oldState[0] != 1:
            return InputEvent(GameAction.MENU_RIGHT, InputSource.JOYSTICK, True)

        return None

    def getActiveJoystick(self) -> pygame.joystick.JoystickType | None:
        if self.activeJoystickId is not None:
            return self.joysticks.get(self.activeJoystickId)
        return None

    def getJoystickName(self) -> str:
        joy = self.getActiveJoystick()
        return joy.get_name() if joy else "No Controller"

    def setActiveJoystick(self, instanceId: int) -> None:
        if instanceId in self.joysticks:
            self.activeJoystickId = instanceId
