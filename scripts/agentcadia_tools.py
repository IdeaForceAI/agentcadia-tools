#!/usr/bin/env python3
import argparse
import json
import pathlib
import runpy
import sys


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"upload", "download", "eval"}:
        print(
            "Usage: python3 scripts/agentcadia_tools.py <upload|download|eval> [args...]",
            file=sys.stderr,
        )
        sys.exit(2)

    command = sys.argv[1]
    script_dir = pathlib.Path(__file__).resolve().parent
    if command == 'upload':
        target = script_dir / 'upload_agentcadia.py'
    elif command == 'download':
        target = script_dir / 'download_agentcadia.py'
    else:
        target = script_dir / 'eval_agentcadia.py'
    sys.argv = [str(target), *sys.argv[2:]]
    runpy.run_path(str(target), run_name='__main__')


if __name__ == "__main__":
    main()
