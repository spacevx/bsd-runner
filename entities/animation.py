import re
from pathlib import Path

import pygame
from pygame import Surface
from pygame.sprite import Sprite


class AnimationFrame:
    def __init__(self, surface: Surface, delay: float) -> None:
        self.surface: Surface = surface
        self.delay: float = delay


class AnimatedSprite(Sprite):
    def __init__(self, x: int, y: int, frames: list[AnimationFrame]) -> None:
        super().__init__()
        self.frames: list[AnimationFrame] = frames
        self.frame_idx: int = 0
        self.anim_timer: float = 0.0
        self.image: Surface = self.frames[0].surface
        self.rect: pygame.Rect = self.image.get_rect(midbottom=(x, y))

    def _get_frame(self) -> Surface:
        return self.frames[self.frame_idx].surface

    def update_animation(self, dt: float) -> bool:
        self.anim_timer += dt
        if self.anim_timer >= self.frames[self.frame_idx].delay:
            self.anim_timer = 0.0
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            return True
        return False


# Pattern is the regex for searching specific frame files (see assets/player/frames)
def load_frames(path: Path, pattern: str = r"frame_(\d+)_delay-([\d.]+)s\.gif", scale: float = 1.0, fallback: Surface | None = None) -> list[AnimationFrame]:
    if not path.exists():
        if fallback:
            return [AnimationFrame(fallback, 0.05)]
        raise FileNotFoundError(f"Frames path not found: {path}")

    ## instead of checking the regex x times in the loop we're doing it once, thanks to re.compile
    regex = re.compile(pattern)
    frames: list[AnimationFrame] = []

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

    if not frames:
        if fallback:
            return [AnimationFrame(fallback, 0.05)]
        raise ValueError(f"No valid frames found in: {path}")

    return frames
