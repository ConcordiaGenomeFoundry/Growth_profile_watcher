import os
import sys
import watcher
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Watch a file and run a command when it changes.")
    parser.add_argument("path", nargs="?", help="Enter path to the CSV file to watch (e.g., ./GP_20250930_111331_OD.csv)")
    # parser.add_argument("--cmd", help="Command to execute when the file changes")
    parser.add_argument("--process", help="Momentum Process to call when the threshold is met")
    args = parser.parse_args()

    path_arg = args.path or input(" --- Enter path to the CSV file to watch (e.g., C://GP_20250930_111331_OD.csv): ").strip()
    if not path_arg:
        print("\n[GP Watcher] Error: no file path provided", file=sys.stderr)
        return 2

    process_arg = args.process or input(" --- Enter the momentum process to call when the threshold is met: ").strip()
    if not process_arg:
        print("\n[GP Watcher] Error: no process name provided", file=sys.stderr)
        return 2

    target_path = Path(os.path.expanduser(path_arg))
    if target_path.is_dir():
        print("\n[GP Watcher] Error: path must be a file", file=sys.stderr)
        return 2

    parent_dir = target_path.resolve().parent
    if not parent_dir.exists():
        print(f"\n[GP Watcher] Error: directory does not exist: {parent_dir}", file=sys.stderr)
        return 2

    # target_path = ("/Users/flavia/PycharmProjects/growth_profile_watcher/sample/GP_20171118_012019_OD.csv")
    print(f"\n[GP Watcher] Watching: {target_path}")
    watcher.start_watching(target_path, process_arg)


if __name__ == "__main__":
    raise SystemExit(main())

