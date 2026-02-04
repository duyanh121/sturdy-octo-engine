import argparse
from pathlib import Path
import logging, sys
import pickle
from soe import fuzzer
from soe.function_list.function_list import generate_function_list
from soe.fuzzer import simple_fuzzer, blackbox_fuzzer
import soe._global as _global
from soe.runner.environment import RunnerEnvironment

logger = logging.getLogger('soe')

fuzzer_options = {
    "simple": simple_fuzzer,
    "blackbox": blackbox_fuzzer
}

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
        "-fl", "--function-list-file",
        help="provide an existing function list file (.pkl)",
        default=""
    )
    parser.add_argument(
        "-tl", "--type-list-file",
        help="provide an existing type list file (.pkl)",
        default=""
    )
    parser.add_argument(
        "-o", "--output",
        help="specify output directory",
        default="output"
    )
    parser.add_argument(
        "-f", "--fuzzer",
        help="specify fuzzer",
        default="simple"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="verbose",
    )
    parser.add_argument(
        "-e", "--environment",
        action="store_true",
        help="set up environment only",
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
    if args.environment:
        with RunnerEnvironment(Path(args.path)) as runner:
            modules = runner.list_modules()
            print(modules)
    else:
        soe(
            fuzz_dir=Path(args.path),
            function_list_file=Path(args.function_list_file),
            type_list_file=Path(args.type_list_file),
            output_dir=Path(args.output),
            fuzzer=args.fuzzer,
            verbose=args.verbose,
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
        fuzzer: str = "simple",
        verbose = False,
        no_log = False,
        no_save = False,
        no_fuzz = False
    ) -> None:
    # Initialize logger
    init_logger(level=logging.DEBUG if verbose else logging.INFO, no_log=no_log)
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
    _global.set_dir_path(fuzz_dir)
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
            if fuzzer not in fuzzer_options:
                raise KeyError(f"Fuzzer '{fuzzer}' not found. ")
            fuzz = fuzzer_options[fuzzer]
            fuzz(fuzz_dir)
        except KeyError as e:
            logger.critical(e)
            raise
        except Exception as e:
            logger.critical(f"An error has occurred: {e}")
            raise


    # if not no_save:
    if False:
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

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
