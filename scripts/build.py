"""
build.py - Genere OpenWhisper.exe

Utilisation (depuis la racine du projet) :
    python scripts/build.py
"""
import subprocess
import sys
import os
import site

# Se placer a la racine du projet
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT_DIR)


def fix_ctranslate2():
    """ctranslate2 cherche des dossiers ROCm qui n'existent pas sans GPU AMD"""
    for sp in site.getsitepackages():
        for name in ("_rocm_sdk_core", "_rocm_sdk_libraries_custom"):
            os.makedirs(os.path.join(sp, name, "bin"), exist_ok=True)


def create_ico():
    """Genere icon.ico (cercle rouge avec point blanc au centre)"""
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    dc = ImageDraw.Draw(img)
    dc.ellipse([16, 16, 240, 240], fill=(220, 50, 50))
    dc.ellipse([96, 96, 160, 160], fill=(255, 255, 255))
    img.save("icon.ico")
    print("  [OK] icon.ico cree")


def main():
    print("=" * 50)
    print("  Build : OpenWhisper.exe")
    print("=" * 50)

    # 1. PyInstaller
    print("\n[1/4] Installation de PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])

    # 2. Fix ctranslate2 avant l'analyse
    print("\n[2/4] Fix ctranslate2 (dossiers ROCm)...")
    fix_ctranslate2()

    # 3. Icone
    print("\n[3/4] Generation de l'icone...")
    create_ico()

    # 4. PyInstaller
    print("\n[4/4] Build PyInstaller...\n")

    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--onefile",
        "--noconsole",
        "--name", "OpenWhisper",
        "--icon", "icon.ico",
        "--paths", ".",
        "--add-data", "assets/open.wav;.",
        "--runtime-hook", "scripts/pyi_rth_rocm.py",
        "--hidden-import", "pystray._impl.comtypes",
        "--hidden-import", "comtypes",
        "--hidden-import", "comtypes.client",
        "--hidden-import", "comtypes.server",
        "--collect-all", "ctranslate2",
        "--collect-all", "sounddevice",
        "--collect-all", "_sounddevice_data",
        "--collect-all", "faster_whisper",
        "--collect-all", "pystray",
        "--collect-all", "comtypes",
        "--collect-all", "keyboard",
    ])

    # 5. Resultat
    exe = os.path.abspath(os.path.join("dist", "OpenWhisper.exe"))
    print("\n" + "=" * 50)
    print("  [OK] Build termine !")
    print(f"  -> {exe}")
    print("=" * 50)


if __name__ == "__main__":
    main()
