import os
import sys
import zipfile
import urllib.request
import subprocess
import ssl
import shutil
from pathlib import Path

UNITY_VERSION = "2021.3.33"
BEPINEX_VERSION = "5.4.23.4"

SCRIPT_DIR = Path(__file__).parent.absolute()
UNITY_DEPS_DIR = SCRIPT_DIR / "mokgamedir/Chill With You_Data/Managed"
BEPINEX_DISTRIBUTIONS = {
    "BepInEx_win_x64": f"https://github.com/BepInEx/BepInEx/releases/download/v{BEPINEX_VERSION}/BepInEx_win_x64_{BEPINEX_VERSION}.zip",
    "BepInEx_macos_x64": f"https://github.com/BepInEx/BepInEx/releases/download/v{BEPINEX_VERSION}/BepInEx_macos_x64_{BEPINEX_VERSION}.zip",
    "BepInEx_linux_x64": f"https://github.com/BepInEx/BepInEx/releases/download/v{BEPINEX_VERSION}/BepInEx_linux_x64_{BEPINEX_VERSION}.zip",
}
BEPINEX_DIRS = {
    name: SCRIPT_DIR / "assets" / name
    for name in BEPINEX_DISTRIBUTIONS
}

if sys.platform == "win32":
    NUGET_PATH = Path(os.environ["USERPROFILE"]) / ".nuget" / "packages" / "unityengine.modules" / UNITY_VERSION / "lib" / "net45"
else:
    NUGET_PATH = Path(os.environ["HOME"]) / ".nuget" / "packages" / "unityengine.modules" / UNITY_VERSION / "lib" / "net45"

UNITY_DLL_LIST = [
    "UnityEngine.dll",
    "UnityEngine.CoreModule.dll",
    "UnityEngine.AnimationModule.dll",
    "UnityEngine.AudioModule.dll",
    "UnityEngine.IMGUIModule.dll",
    "UnityEngine.InputLegacyModule.dll",
    "UnityEngine.TextRenderingModule.dll",
    "UnityEngine.UIModule.dll",
    "UnityEngine.UnityWebRequestModule.dll",
    "UnityEngine.UnityWebRequestAudioModule.dll",
    "UnityEngine.ImageConversionModule.dll"
]

BEPINEX_DLL_LIST = [
    "0Harmony.dll",
    "BepInEx.dll",
]

def check_files_exist(folder_path, file_list):
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        return False

    existing_files = {file.name for file in folder.iterdir() if file.is_file()}

    for file_name in file_list:
        if file_name not in existing_files:
            return False

    return True

def download_bepinex(distribution_name):
    if distribution_name not in BEPINEX_DISTRIBUTIONS:
        print(f"未知 BepInEx 发行包: {distribution_name}")
        return 1

    bepinex_dir = BEPINEX_DIRS[distribution_name]
    bepinex_url = BEPINEX_DISTRIBUTIONS[distribution_name]
    bepinex_dir.mkdir(parents=True, exist_ok=True)

    temp_file = bepinex_dir / "bepinex.zip"
    try:
        print(f"正在下载 {distribution_name} v{BEPINEX_VERSION}...")
        print(f"下载地址: {bepinex_url}")
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(bepinex_url, context=ssl_context) as response, open(temp_file, 'wb') as out_file:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                block_size = 8192
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    out_file.write(buffer)

                    if total_size > 0:
                        percent = min(100, int(downloaded / total_size * 100))
                        sys.stdout.write(f"\r进度: [{percent:3d}%] {downloaded//1024}KB/{total_size//1024}KB")
                        sys.stdout.flush()
            sys.stdout.write("\n")

        except Exception as e:
            raise Exception(f"\n下载失败: {str(e)}")
        
        print("\n正在解压 BepInEx...")
        try:
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                zip_ref.testzip()
                zip_ref.extractall(bepinex_dir)
        except Exception as e:
            raise Exception(f"\n解压失败: {str(e)}")

        print(f"{distribution_name} v{BEPINEX_VERSION} 下载并解压完成")
        print(f"路径: {bepinex_dir}")
        return 0

    except Exception as e:
        print(str(e))
        return 1

    finally:
        if temp_file.exists(): temp_file.unlink()

def download_unity_dlls():
    UNITY_DEPS_DIR.mkdir(parents=True, exist_ok=True)

    temp_dir = Path("unity-deps-temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        try:
            subprocess.run(
                ["dotnet", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
                encoding='utf-8',
                shell=sys.platform == "win32"
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("未找到 dotnet 命令，请安装 .NET SDK（https://dotnet.microsoft.com/download）")

        csproj_path = temp_dir / "UnityDeps.csproj"
        csproj_content = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>netstandard2.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="UnityEngine.Modules" Version="{UNITY_VERSION}" />
  </ItemGroup>
</Project>'''
        with open(csproj_path, 'w', encoding='utf-8') as f:
            f.write(csproj_content)

        print(f"正在从 NuGet 下载 UnityEngine.Modules {UNITY_VERSION}...")
        try:
            subprocess.run(
                ["dotnet", "restore"],
                cwd=temp_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                shell=sys.platform == "win32"
            )
        except subprocess.CalledProcessError as e:
            raise Exception(f"dotnet restore 失败: {e.stderr}")

        if not NUGET_PATH.exists():
            raise Exception(f"NuGet 包路径不存在: {NUGET_PATH}")

        print(f"正在复制 Unity DLL 到 {UNITY_DEPS_DIR}...")
        for dll_name in UNITY_DLL_LIST:
            src_dll = NUGET_PATH / dll_name
            dst_dll = UNITY_DEPS_DIR / dll_name
            if not src_dll.exists():
                print(f"未找到 DLL: {src_dll}，跳过")
                continue
            shutil.copy2(src_dll, dst_dll)
            print(f"复制成功: {dll_name}")

        print(f"\nUnityEngine DLL 下载复制完成！")
        return 0

    except Exception as e:
        print(str(e))
        return 1

    finally:
        if temp_dir.exists(): shutil.rmtree(temp_dir)

if __name__ == "__main__":
    for distribution_name, bepinex_dir in BEPINEX_DIRS.items():
        if not check_files_exist(bepinex_dir / "BepInEx/core", BEPINEX_DLL_LIST):
            print(f"===== 开始下载 {distribution_name} =====")
            ret = download_bepinex(distribution_name)
            if ret != 0:
                print(f"{distribution_name} 下载失败")
                sys.exit(ret)
        else:
            print(f"{distribution_name} OK")

    if not check_files_exist(UNITY_DEPS_DIR, UNITY_DLL_LIST):
        print("\n===== 开始下载 UnityEngine DLL =====")
        ret = download_unity_dlls()
        if ret != 0:
            print("UnityEngine DLL 下载失败")
            sys.exit(ret)
    else:
        print(f"UnityEngine DLL OK")

    print("All Deps OK.")
    sys.exit(0)
