import argparse
from pathlib import Path
import logging, sys
import pickle
from soe.function_list.function_list import generate_function_list
from soe.fuzzer import fuzz
import soe._global as _global

logger = logging.getLogger('soe')

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="soe",
        description="sturdy-octo-engine command line tool"
    )
    parser.add_argument(
        "path",
        help="path of codebase"
    )
    parser.add_argument(
        "-f", "--function-list",
        help="provide an existing function list file (.pkl)"
    )
    parser.add_argument(
        "-t", "--type-list",
        help="provide an existing type list file (.pkl)"
    )
    parser.add_argument(
        "-o", "--output",
        help="specify output directory",
        default="output"
    )
    parser.add_argument(
        "--no-output",
        action="store_true",
        help="disable file output",
    )
    parser.add_argument(
        "--no-fuzz",
        action="store_true",
        help="disable fuzzing"
    )

    args = parser.parse_args()
    soe(args)


def init_logger(level=logging.INFO, output_dir=Path("output"), no_output=False) -> None:
    if no_output:
        logging.basicConfig(
            level=level,
            format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
            handlers=[logging.NullHandler()]
        )
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
        handlers=[
            logging.FileHandler(output_dir / "runtime.log", mode="w"), 
            logging.StreamHandler(sys.stdout)
        ]
)
        

def soe(args) -> None:
    # Initialize logger
    output_dir = Path(args.output)
    init_logger(output_dir=output_dir, no_output=args.no_output)


    # Validate repository path
    fuzz_dir = Path(args.path)
    if not fuzz_dir.exists():
        logger.critical(f"Repository path does not exist: {fuzz_dir}")
        raise FileNotFoundError(f"Repository path {fuzz_dir} does not exist.")
    if not fuzz_dir.is_dir():
        logger.critical(f"Provided path is not a directory: {fuzz_dir}")
        raise NotADirectoryError(f"Provided path {fuzz_dir} must be a directory.")


    # Initialize global state
    _global.init_global()
    # Load existing function list if provided
    if args.function_list:
        with open(args.function_list, "rb") as f:
            function_list = pickle.load(f)
            _global.set_function_list(function_list)
            logger.info(f"Loaded function list from {args.function_list}")
    else:
        logger.info(f"Generating new function list for ${args.path}")
        function_list = generate_function_list(args.path)
        _global.set_function_list(function_list)
    # Load existing type list if provided
    if args.type_list:
        with open(args.type_list, "rb") as f:
            type_list = pickle.load(f)
            _global.set_type_list(type_list)
            logger.info(f"Loaded type list from {args.type_list}")


    if not args.no_fuzz:
        try:
            fuzz(fuzz_dir)
        except Exception as e:
            logger.critical(f"An error has occurred: {e}")


    if not args.no_output:
        # Save global state on exit
        with open(output_dir / "function_list.pkl", "wb") as f:
            pickle.dump(_global.get_function_list(), f)
            logger.info(f"Saved function list to {output_dir / 'function_list.pkl'}")
        with open(output_dir / "type_list.pkl", "wb") as f:
            pickle.dump(_global.get_type_list(), f)
            logger.info(f"Saved type list to {output_dir / 'type_list.pkl'}")


if __name__ == "__main__":
    main()
