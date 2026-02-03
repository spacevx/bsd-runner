import re
from pathlib import Path

import pygame
from pygame import Surface
from pygame.sprite import Sprite

# Code who were basically in entities/player, but in case we need to reuse it for animating other entites (maybe like the chaser?)

class AnimationFrame:
    def __init__(self, surface: Surface, delay: float) -> None:
        self.surface: Surface = surface
        self.delay: float = delay


class AnimatedSprite(Sprite):
    def __init__(self, x: int, y: int, frames: list[AnimationFrame]) -> None:
        super().__init__()
        self.frames: list[AnimationFrame] = frames
        self.frameIdx: int = 0
        self.animTimer: float = 0.0
        self.image: Surface = self.frames[0].surface
        self.rect: pygame.Rect = self.image.get_rect(midbottom=(x, y))

    def _getFrame(self) -> Surface:
        return self.frames[self.frameIdx].surface

    def updateAnimation(self, dt: float) -> bool:
        self.animTimer += dt
        bAdvanced = False
        while self.animTimer >= self.frames[self.frameIdx].delay:
            self.animTimer -= self.frames[self.frameIdx].delay
            self.frameIdx = (self.frameIdx + 1) % len(self.frames)
            bAdvanced = True
        return bAdvanced


# Pattern is the regex for searching specific frame files (see assets/player/frames for example)
def loadFrames(path: Path, pattern: str = r"frame_(\d+)_delay-([\d.]+)s\.gif", scale: float = 1.0) -> list[AnimationFrame]:
    ## instead of checking the regex x times in the loop we're doing it once thanks to re.compile
    regex = re.compile(pattern)
    frames: list[AnimationFrame] = []

    # Don't ask me about this lol
    for file in sorted(path.glob("*.gif")):
        if match := regex.match(file.name):
            delay = float(match.group(2))
            try:
                surf = pygame.image.load(str(file)).convert_alpha()
                if scale != 1.0:
                    w, h = int(surf.get_width() * scale), int(surf.get_height() * scale)
                    surf = pygame.transform.scale(surf, (w, h))
                frames.append(AnimationFrame(surf, delay))
            except pygame.error:
                continue

    return frames
