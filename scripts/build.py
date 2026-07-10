import subprocess
import argparse
import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent


def safe_remove_file(path: Path):
    """Delete a file if it exists."""
    if path.exists() and path.is_file():
        print(f">>> Removing file: {path}")
        path.unlink()


def safe_rmtree(path: Path):
    """Delete a directory if it exists."""
    if path.exists() and path.is_dir():
        print(f">>> Removing: {path}")
        shutil.rmtree(path)


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

    # ----------------------------------------------------
    # CLEAN BUILD FOLDERS & FILES
    # ----------------------------------------------------
    safe_rmtree(ROOT / "build")
    safe_rmtree(ROOT / "dist")
    safe_rmtree(ROOT / ".pyarmor")
    safe_remove_file(ROOT / "wwm" / "constants.py")

    # ----------------------------------------------------
    # BUILD STEPS
    # ----------------------------------------------------
    run(f"python scripts/build_copy_files.py")
    run(f"python scripts/build_pem.py")
    run(f"python scripts/build_signature.py --id {args.id}")
    run(f"python scripts/build_constants.py --days {args.days}")
    run(f"pyarmor-7 pack --clean -O dist -e \" --onefile\" wwm\\main.py")


if __name__ == "__main__":
    main()
