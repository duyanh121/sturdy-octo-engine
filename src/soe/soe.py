import argparse
from pathlib import Path
from .fuzzing_loop import fuzzing_loop
import logging, sys
import pickle
import soe._global as _global

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s/%(levelname)s]: %(message)s',
    # Send output to a file and the console (sys.stderr is default for console)
    handlers=[
        logging.FileHandler("runtime.log"), 
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('soe')

def main():
    parser = argparse.ArgumentParser(
        prog="soe",
        description="sturdy-octo-engine command line tool"
    )
    parser.add_argument(
        "path",
        help="Path of codebase"
    )
    # TODO: add argumment to read from existing global state files

    args = parser.parse_args()
    try:
        fuzzing_loop(Path(args.path))
    except Exception as e:
        logger.critical(f"An error has occurred: {e}")
        sys.exit(1)
    finally:
        # Save global state on exit
        with open("result/function_list.pkl", "wb") as f:
            pickle.dump(_global.get_function_list(), f)
            logger.info("Saved function list to function_list.pkl...")
        with open("result/type_list.pkl", "wb") as f:
            pickle.dump(_global.get_type_list(), f)
            logger.info("Saved type list to type_list.pkl")
        
        logger.info("Exiting")
        


if __name__ == "__main__":
    main()
