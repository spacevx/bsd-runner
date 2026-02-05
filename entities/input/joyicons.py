from typing import Final
from enum import Enum, auto

import pygame
from pygame import Surface


class ControllerType(Enum):
    XBOX = auto()
    PLAYSTATION = auto()
    GENERIC = auto()


class JoyIcons:
    ICON_SIZE: Final[tuple[int, int]] = (32, 32)

    XBOX_NAMES: Final[dict[int, str]] = {
        0: "A", 1: "B", 2: "X", 3: "Y",
        4: "LB", 5: "RB", 6: "Back", 7: "Start",
        8: "LS", 9: "RS", 10: "LT", 11: "RT"
    }

    PS_NAMES: Final[dict[int, str]] = {
        0: "✕", 1: "○", 2: "□", 3: "△",
        4: "L1", 5: "R1", 6: "Select", 7: "Start",
        8: "L3", 9: "R3", 10: "L2", 11: "R2"
    }

    _instance: "JoyIcons | None" = None

    def __new__(cls) -> "JoyIcons":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.controllerType: ControllerType = ControllerType.GENERIC
        self.iconCache: dict[tuple[ControllerType, int, tuple[int, int]], Surface] = {}

    # Couldn't find proper name of joystick name on pygame.joystick docs, so i just put all of the name knowned
    def detectControllerType(self, joystickName: str) -> ControllerType:
        nameLower = joystickName.lower()
        if "xbox" in nameLower or "xinput" in nameLower:
            return ControllerType.XBOX
        elif "playstation" in nameLower or "ps4" in nameLower or "ps5" in nameLower or "dualshock" in nameLower or "dualsense" in nameLower:
            return ControllerType.PLAYSTATION
        return ControllerType.GENERIC

    def getButtonName(self, button: int, controllerType: ControllerType | None = None) -> str:
        from entities.input.manager import InputManager

        if controllerType is None:
            joy = InputManager().getActiveJoystick()
            if joy:
                self.controllerType = self.detectControllerType(joy.get_name())
            controllerType = self.controllerType

        if controllerType == ControllerType.XBOX:
            return self.XBOX_NAMES.get(button, f"B{button}")
        elif controllerType == ControllerType.PLAYSTATION:
            return self.PS_NAMES.get(button, f"B{button}")
        return f"Button {button}"

    def renderButtonIcon(self, button: int, size: tuple[int, int] | None = None) -> Surface:
        sz = size or self.ICON_SIZE
        cacheKey = (self.controllerType, button, sz)

        if cacheKey in self.iconCache:
            return self.iconCache[cacheKey]

        surf = Surface(sz, pygame.SRCALPHA)
        surf.fill((60, 60, 60))
        pygame.draw.rect(surf, (100, 100, 100), surf.get_rect(), 2, border_radius=4)

        fontSize = max(10, sz[1] - 8)
        font = pygame.font.Font(None, fontSize)
        name = self.getButtonName(button)
        text = font.render(name, True, (255, 255, 255))
        textRect = text.get_rect(center=(sz[0] // 2, sz[1] // 2))
        surf.blit(text, textRect)

        self.iconCache[cacheKey] = surf
        return surf

    def setControllerType(self, cType: ControllerType) -> None:
        self.controllerType = cType
        self.iconCache.clear()
