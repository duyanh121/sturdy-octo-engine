import argparse
from pathlib import Path
from .fuzzing_loop import fuzzing_loop
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
    # Send output to a file and the console (sys.stderr is default for console)
    handlers=[
        logging.FileHandler("runtime.log"), 
        logging.StreamHandler(sys.stdout)
    ]
)

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
