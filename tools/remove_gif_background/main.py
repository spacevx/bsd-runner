# Our player frames had a black background, every website asked me to paid
# Based on a gist i saw on github

from PIL import Image, ImageSequence
import sys

def remove_black_background(input_path, output_path, threshold=30):
    img = Image.open(input_path)

    frames = []

    for frame in ImageSequence.Iterator(img):
        frame = frame.convert('RGBA')

        datas = frame.getdata()

        new_data = []

        for item in datas:
            if item[0] <= threshold and item[1] <= threshold and item[2] <= threshold:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        frame.putdata(new_data)
        frames.append(frame)

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

    msg = str.format("Le GIF %s est maintenant terminé (nbr de frames: %s", input_path, len(frames))
    print(msg)

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    input_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        if input_path.lower().endswith('.gif'):
            output_path = input_path[:-4] + '_transparent.gif'
        else:
            output_path = input_path + '_transparent.gif'

    threshold = 30
    if len(sys.argv) >= 4:
        try:
            threshold = int(sys.argv[3])
        except ValueError:
            print("Impossible")

    try:
        remove_black_background(input_path, output_path, threshold)
    except FileNotFoundError:
        print(f"Le fichier '{input_path}' n'existe pas")
        sys.exit(1)
    except Exception as e:
        sys.exit(1)


if __name__ == "__main__":
    main()