import shutil
from pathlib import Path


def copy_png_tree(src_root, dst_root):
    src_root = Path(src_root)
    dst_root = Path(dst_root)

    for png_file in src_root.rglob("*.png"):
        relative_path = png_file.relative_to(src_root)
        dest_path = dst_root / relative_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png_file, dest_path)
        print(f"Copied: {png_file} -> {dest_path}")


def copy_config(src_root, dst_root):
    src_root = Path(src_root)
    dst_root = Path(dst_root)

    config_src = src_root / "config.yaml"
    if config_src.exists():
        config_dst = dst_root / "config.yaml"
        config_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config_src, config_dst)
        print(f"Copied config.yaml -> {config_dst}")
    else:
        print("config.yaml not found in source root")


copy_png_tree(
    r"wwm",
    r"dist\wwm"
)

copy_config(
    r"wwm/bots/material_farm",
    r"dist"
)
