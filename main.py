import flags
from game import Game


def main() -> None:
    flags.parse()

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
