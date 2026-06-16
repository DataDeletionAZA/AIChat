import shutil
import sys
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent.absolute()
REPO_ROOT = SCRIPT_DIR.parent
ASSETS_DIR = SCRIPT_DIR / "assets"

COMMON_FILES = [
    "AIChat.dll",
    "api_v2_ex.py",
    "Voice_MainScenario_27_016.wav",
    "README.html",
]

PACKAGES = {
    "AIChatMod-Windows.zip": "BepInEx_win_x64",
    "AIChatMod-macOS.zip": "BepInEx_macos_x64",
    "AIChatMod-Linux.zip": "BepInEx_linux_x64",
}


def add_file(zip_file, source_path, archive_path):
    if source_path.exists():
        zip_file.write(source_path, archive_path)


def add_directory(zip_file, source_dir):
    for path in source_dir.rglob("*"):
        if path.is_file():
            zip_file.write(path, path.relative_to(source_dir))


def build_package(output_name, bepinex_dir_name):
    bepinex_dir = ASSETS_DIR / bepinex_dir_name
    if not bepinex_dir.exists():
        raise FileNotFoundError(f"缺少 {bepinex_dir}")

    output_path = REPO_ROOT / output_name
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        add_directory(zip_file, bepinex_dir)
        for file_name in COMMON_FILES:
            add_file(zip_file, ASSETS_DIR / file_name, file_name)

    print(f"已生成 {output_path}")


def main():
    missing_files = [
        str(ASSETS_DIR / file_name)
        for file_name in COMMON_FILES
        if not (ASSETS_DIR / file_name).exists()
    ]
    if missing_files:
        print("缺少以下打包文件：")
        print("\n".join(missing_files))
        return 1

    for output_name, bepinex_dir_name in PACKAGES.items():
        build_package(output_name, bepinex_dir_name)

    windows_zip = REPO_ROOT / "AIChatMod-Windows.zip"
    legacy_zip = REPO_ROOT / "AIChatMod.zip"
    if legacy_zip.exists():
        legacy_zip.unlink()
    shutil.copy2(windows_zip, legacy_zip)
    print(f"已生成兼容旧下载名 {legacy_zip}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
