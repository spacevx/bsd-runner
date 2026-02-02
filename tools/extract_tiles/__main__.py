from pathlib import Path
import sys
import pygame

tileSize: int = 64
groundRatio: float = 0.85
ceilingHeight: int = 60

root: Path = Path(__file__).parent.parent.parent
bgPath: Path = root / "screens" / "background.png"
tilesDir: Path = root / "assets" / "tiles"


def initPygame() -> pygame.Surface:
    pygame.init()
    pygame.display.set_mode((1, 1))
    return pygame.image.load(str(bgPath)).convert()


def extractGround(bg: pygame.Surface) -> None:
    w, h = bg.get_size()
    groundY = int(h * groundRatio)
    groundH = h - groundY
    out = tilesDir / "ground"
    out.mkdir(parents=True, exist_ok=True)

    for i in range(w // tileSize):
        x = i * tileSize
        rect = pygame.Rect(x, groundY, tileSize, min(tileSize, groundH))
        tile = bg.subsurface(rect).copy()
        pygame.image.save(tile, str(out / f"mat_{i:02d}.png"))
        print(f"Extracted ground tile {i}")

    print(f"Done: {w // tileSize} ground tiles saved to {out}")


def extractCeiling(bg: pygame.Surface) -> None:
    w, _ = bg.get_size()
    out = tilesDir / "ceiling"
    out.mkdir(parents=True, exist_ok=True)

    for i in range(w // tileSize):
        x = i * tileSize
        rect = pygame.Rect(x, 0, tileSize, ceilingHeight)
        tile = bg.subsurface(rect).copy()
        pygame.image.save(tile, str(out / f"ceiling_{i:02d}.png"))
        print(f"Extracted ceiling tile {i}")

    print(f"Done: {w // tileSize} ceiling tiles saved to {out}")


def main(mode: str) -> None:
    bg = initPygame()

    match mode:
        case "ground":
            extractGround(bg)
        case "ceiling":
            extractCeiling(bg)
        case "all":
            extractGround(bg)
            extractCeiling(bg)
        case _:
            sys.exit(1)

    pygame.quit()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    main(mode)
