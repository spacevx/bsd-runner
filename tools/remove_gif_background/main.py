from PIL import Image, ImageSequence
from collections import deque
import sys

blackTh: int = 15
alphaTh: int = 40

dirs4: list[tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]
dirs8: list[tuple[int, int]] = dirs4 + [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def isBlack(r: int, g: int, b: int, th: int) -> bool:
    return r <= th and g <= th and b <= th

def floodFill(frame: Image.Image, th: int) -> Image.Image:
    frame = frame.convert('RGBA')
    w, h = frame.size
    px = frame.load()
    visited: set[tuple[int, int]] = set()
    transparent: set[tuple[int, int]] = set()

    starts: list[tuple[int, int]] = [(x, 0) for x in range(w)] + [(x, h-1) for x in range(w)]
    starts += [(0, y) for y in range(h)] + [(w-1, y) for y in range(h)]

    q: deque[tuple[int, int]] = deque()
    for p in starts:
        r, g, b = px[p][0], px[p][1], px[p][2]
        if p not in visited and isBlack(r, g, b, th):
            q.append(p)
            visited.add(p)

    while q:
        x, y = q.popleft()
        r, g, b = px[x, y][0], px[x, y][1], px[x, y][2]
        if isBlack(r, g, b, th):
            transparent.add((x, y))
            for dx, dy in dirs8:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                    nr, ng, nb = px[nx, ny][0], px[nx, ny][1], px[nx, ny][2]
                    if isBlack(nr, ng, nb, alphaTh):
                        visited.add((nx, ny))
                        q.append((nx, ny))

    for x, y in transparent:
        px[x, y] = (0, 0, 0, 0)

    antialias(frame, transparent, th)
    return frame


def antialias(frame: Image.Image, transparent: set[tuple[int, int]], th: int) -> None:
    w, h = frame.size
    px = frame.load()

    edges: list[tuple[int, int]] = []
    for x, y in transparent:
        for dx, dy in dirs4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in transparent:
                r, g, b, a = px[nx, ny]
                if a > 0 and not isBlack(r, g, b, th):
                    edges.append((nx, ny))

    for x, y in edges:
        r, g, b, a = px[x, y]
        transN = total = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    total += 1
                    if (nx, ny) in transparent:
                        transN += 1

        if total > 0 and transN > 0:
            blend = transN / total
            px[x, y] = (r, g, b, max(0, int(a * (1 - blend * 0.3))))


def removeBg(inp: str, out: str, th: int = blackTh) -> None:
    img = Image.open(inp)
    frames: list[Image.Image] = [floodFill(f.copy(), th) for f in ImageSequence.Iterator(img)]

    frames[0].save(
        out, save_all=True, append_images=frames[1:], optimize=False,
        duration=img.info.get('duration', 100), loop=img.info.get('loop', 0),
        transparency=0, disposal=2
    )
    print(f"GIF traite: {inp} ({len(frames)} frames)")


def main() -> None:
    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else inp[:-4] + '_transparent.gif'
    th = int(sys.argv[3]) if len(sys.argv) >= 4 else blackTh
    removeBg(inp, out, th)


if __name__ == "__main__":
    main()
