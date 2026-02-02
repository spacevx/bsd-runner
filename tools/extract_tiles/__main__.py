from pathlib import Path
import sys
import pygame

TILE_SIZE: int = 64
GROUND_RATIO: float = 0.85
CEILING_HEIGHT: int = 60

ROOT: Path = Path(__file__).parent.parent.parent
BG_PATH: Path = ROOT / "screens" / "background.png"
TILES_DIR: Path = ROOT / "assets" / "tiles"


def init_pygame() -> pygame.Surface:
    pygame.init()
    pygame.display.set_mode((1, 1))
    return pygame.image.load(str(BG_PATH)).convert()


def extract_ground(bg: pygame.Surface) -> None:
    w, h = bg.get_size()
    ground_y = int(h * GROUND_RATIO)
    ground_h = h - ground_y
    out = TILES_DIR / "ground"
    out.mkdir(parents=True, exist_ok=True)

    for i in range(w // TILE_SIZE):
        x = i * TILE_SIZE
        rect = pygame.Rect(x, ground_y, TILE_SIZE, min(TILE_SIZE, ground_h))
        tile = bg.subsurface(rect).copy()
        pygame.image.save(tile, str(out / f"mat_{i:02d}.png"))
        print(f"Extracted ground tile {i}")

    print(f"Done: {w // TILE_SIZE} ground tiles saved to {out}")


def extract_ceiling(bg: pygame.Surface) -> None:
    w, _ = bg.get_size()
    out = TILES_DIR / "ceiling"
    out.mkdir(parents=True, exist_ok=True)

    for i in range(w // TILE_SIZE):
        x = i * TILE_SIZE
        rect = pygame.Rect(x, 0, TILE_SIZE, CEILING_HEIGHT)
        tile = bg.subsurface(rect).copy()
        pygame.image.save(tile, str(out / f"ceiling_{i:02d}.png"))
        print(f"Extracted ceiling tile {i}")

    print(f"Done: {w // TILE_SIZE} ceiling tiles saved to {out}")


def main(mode: str) -> None:
    bg = init_pygame()

    match mode:
        case "ground":
            extract_ground(bg)
        case "ceiling":
            extract_ceiling(bg)
        case "all":
            extract_ground(bg)
            extract_ceiling(bg)
        case _:
            sys.exit(1)

    pygame.quit()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    main(mode)
