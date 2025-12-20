import argparse
from .download_repo import download_repo, download_all, list_projects

def main():
    parser = argparse.ArgumentParser(
        prog="downloader",
        description="Benchmark downloader command line tool"
    )
    parser.add_argument(
        "-i", "--install",
        help="specify project to download"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="download all projects"
    )

    args = parser.parse_args()
    if args.all:
        print("Downloading all projects...")
        download_all()
    elif args.install:
        download_repo(args.install)
    else:
        print("Available projects:")
        list_projects()


if __name__ == "__main__":
    main()
