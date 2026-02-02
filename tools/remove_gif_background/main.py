# Our player frames had a black background, every website asked me to paid
# Based on a gist i saw on github

from PIL import Image, ImageSequence
from typing import Final
from collections import deque
import sys


BLACK_THRESHOLD: Final[int] = 15
ALPHA_GRADIENT_THRESHOLD: Final[int] = 40


def is_black_pixel(r: int, g: int, b: int, threshold: int) -> bool:
    return r <= threshold and g <= threshold and b <= threshold


def flood_fill_transparency(frame: Image.Image, threshold: int) -> Image.Image:
    frame = frame.convert('RGBA')
    width, height = frame.size
    pixels = frame.load()
    visited: set[tuple[int, int]] = set()
    to_make_transparent: set[tuple[int, int]] = set()

    start_points: list[tuple[int, int]] = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
    ]

    for x in range(width):
        start_points.append((x, 0))
        start_points.append((x, height - 1))
    for y in range(height):
        start_points.append((0, y))
        start_points.append((width - 1, y))

    queue: deque[tuple[int, int]] = deque()

    for point in start_points:
        if point not in visited:
            r, g, b, a = pixels[point[0], point[1]]
            if is_black_pixel(r, g, b, threshold):
                queue.append(point)
                visited.add(point)

    directions: list[tuple[int, int]] = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    while queue:
        x, y = queue.popleft()
        r, g, b, a = pixels[x, y]

        if is_black_pixel(r, g, b, threshold):
            to_make_transparent.add((x, y))

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    nr, ng, nb, na = pixels[nx, ny]
                    if is_black_pixel(nr, ng, nb, ALPHA_GRADIENT_THRESHOLD):
                        visited.add((nx, ny))
                        queue.append((nx, ny))

    for x, y in to_make_transparent:
        pixels[x, y] = (0, 0, 0, 0)

    apply_edge_antialiasing(frame, to_make_transparent, threshold)

    return frame


def apply_edge_antialiasing(
    frame: Image.Image,
    transparent_pixels: set[tuple[int, int]],
    threshold: int
) -> None:
    width, height = frame.size
    pixels = frame.load()
    edge_pixels: list[tuple[int, int]] = []

    directions: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for x, y in transparent_pixels:
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in transparent_pixels:
                    r, g, b, a = pixels[nx, ny]
                    if a > 0 and not is_black_pixel(r, g, b, threshold):
                        edge_pixels.append((nx, ny))

    for x, y in edge_pixels:
        r, g, b, a = pixels[x, y]
        transparent_neighbors = 0
        total_neighbors = 0

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    total_neighbors += 1
                    if (nx, ny) in transparent_pixels:
                        transparent_neighbors += 1

        if total_neighbors > 0 and transparent_neighbors > 0:
            blend_factor = transparent_neighbors / total_neighbors
            new_alpha = int(a * (1 - blend_factor * 0.3))
            pixels[x, y] = (r, g, b, max(0, new_alpha))


def remove_black_background(input_path: str, output_path: str, threshold: int = BLACK_THRESHOLD) -> None:
    img: Image.Image = Image.open(input_path)
    frames: list[Image.Image] = []

    for frame in ImageSequence.Iterator(img):
        processed_frame = flood_fill_transparency(frame.copy(), threshold)
        frames.append(processed_frame)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        optimize=False,
        duration=img.info.get('duration', 100),
        loop=img.info.get('loop', 0),
        transparency=0,
        disposal=2
    )

    print(f"GIF traite: {input_path} ({len(frames)} frames)")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(1)

    input_path: str = sys.argv[1]
    output_path: str

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        if input_path.lower().endswith('.gif'):
            output_path = input_path[:-4] + '_transparent.gif'
        else:
            output_path = input_path + '_transparent.gif'

    threshold: int = BLACK_THRESHOLD
    if len(sys.argv) >= 4:
        try:
            threshold = int(sys.argv[3])
        except ValueError:
            print(f"Threshold invalide, utilisation de {BLACK_THRESHOLD}")

    try:
        remove_black_background(input_path, output_path, threshold)
    except FileNotFoundError:
        print(f"Fichier introuvable: {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
