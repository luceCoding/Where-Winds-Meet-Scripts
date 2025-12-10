import subprocess
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, **kwargs):
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=ROOT, **kwargs)
    if result.returncode != 0:
        print(f"\nERROR: Command failed: {cmd}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--days", type=int, default=1)
    args = parser.parse_args()

    run(f"python scripts/build_copy_files.py")
    run(f"python scripts/build_pem.py")
    run(f"python scripts/build_signature.py --id {args.id}")
    run(f"python scripts/build_constants.py --days {args.days}")
    run(f"pyarmor-7 pack -O dist -e \" --onefile\" wwm\\bots\\material_farm\\start_material_farm.py")


if __name__ == "__main__":
    main()
