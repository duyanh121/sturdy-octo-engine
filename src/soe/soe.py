import argparse
from pathlib import Path
from .fuzzing_loop import fuzzing_loop

def main():
    print("hello")
    parser = argparse.ArgumentParser(
        prog="soe",
        description="sturdy-octo-engine command line tool"
    )
    parser.add_argument(
        "path",
        help="Path of codebase"
    )

    args = parser.parse_args()
    fuzzing_loop(Path(args.path))


if __name__ == "__main__":
    main()
