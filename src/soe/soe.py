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
        "-f", "--function-list-file",
        help="provide an existing function list file (.pkl)",
        default=""
    )
    parser.add_argument(
        "-t", "--type-list-file",
        help="provide an existing type list file (.pkl)",
        default=""
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
        "--no-log",
        action="store_true",
        help="disable log output",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="disable state output",
    )
    parser.add_argument(
        "--no-fuzz",
        action="store_true",
        help="disable fuzzing"
    )

    args = parser.parse_args()
    soe(
        fuzz_dir=Path(args.path),
        function_list_file=Path(args.function_list_file),
        type_list_file=Path(args.type_list_file),
        output_dir=Path(args.output),
        no_log=args.no_log,
        no_save=args.no_save,
        no_fuzz=args.no_fuzz
    )


def init_logger(level=logging.INFO, no_log=False) -> None:
    if no_log:
        logging.basicConfig(
            level=level,
            format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
            handlers=[logging.NullHandler()]
        )
        return

    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
        handlers=[
            logging.FileHandler("runtime.log", mode="w"), 
            logging.StreamHandler(sys.stdout)
        ]
    )
        

def soe(
        fuzz_dir: Path, 
        function_list_file: Path = Path(), 
        type_list_file: Path = Path(), 
        output_dir: Path = Path("output"), 
        no_log = False,
        no_save = False,
        no_fuzz = False
    ) -> None:
    # Initialize logger
    init_logger(no_log=no_log)
    logger.info(f"Starting sturdy-octo-engine on {fuzz_dir}")


    # Validate repository path
    if not fuzz_dir.exists():
        logger.critical(f"Repository path does not exist: {fuzz_dir}")
        raise FileNotFoundError(f"Repository path {fuzz_dir} does not exist.")
    if not fuzz_dir.is_dir():
        logger.critical(f"Provided path is not a directory: {fuzz_dir}")
        raise NotADirectoryError(f"Provided path {fuzz_dir} must be a directory.")


    # Initialize global state
    _global.init_global()
    # Load existing function list if provided
    if function_list_file.is_file():
        try:
            with open(function_list_file, "rb") as f:
                function_list = pickle.load(f)
                _global.set_function_list(function_list)
                logger.info(f"Loaded function list from {function_list_file}")
        except Exception as e:
            logger.warning(f"Failed to load function list from {function_list_file}: {e}")
            logger.warning(f"Defaulting to generating new function list")
            function_list = generate_function_list(fuzz_dir)
            _global.set_function_list(function_list)
    else:
        logger.info(f"Generating new function list")
        function_list = generate_function_list(fuzz_dir)
        _global.set_function_list(function_list)
    # Load existing type list if provided
    if type_list_file.is_file():
        try:
            with open(type_list_file, "rb") as f:
                type_list = pickle.load(f)
                _global.set_type_list(type_list)
                logger.info(f"Loaded type list from {type_list_file}")
        except Exception as e:
            logger.warning(f"Failed to load type list from {type_list_file}: {e}")
            logger.warning("Defaulting to empty type list")


    if not no_fuzz:
        try:
            logger.info("Starting fuzzing")
            fuzz(fuzz_dir)
        except Exception as e:
            logger.critical(f"An error has occurred: {e}")


    if not no_save:
        # Save global state on exit
        with open(output_dir / "function_list.pkl", "wb") as f:
            pickle.dump(_global.get_function_list(), f)
            logger.info(f"Saved function list to {output_dir / 'function_list.pkl'}")
        with open(output_dir / "type_list.pkl", "wb") as f:
            pickle.dump(_global.get_type_list(), f)
            logger.info(f"Saved type list to {output_dir / 'type_list.pkl'}")

    logger.info("Exiting sturdy-octo-engine")


if __name__ == "__main__":
    main()
