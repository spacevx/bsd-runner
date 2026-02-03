from argparse import ArgumentParser

bDisableChaser: bool = False


def parse(args: list[str] | None = None) -> None:
    global bDisableChaser
    parser = ArgumentParser()
    parser.add_argument("--disableChaser", action="store_true")
    parsed = parser.parse_args(args)
    bDisableChaser = parsed.disableChaser