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


def convert_logo():
    """Convertit assets/img/logo.svg en assets/logo.png via cairosvg"""
    svg_path = os.path.join("assets", "img", "logo.svg")
    png_path = os.path.join("assets", "img", "logo.png")

    if os.path.exists(png_path):
        print("  [OK] logo.png existe deja")
        return True

    if not os.path.exists(svg_path):
        print("  [!] logo.svg non trouve")
        return False

    try:
        import cairosvg
        cairosvg.svg2png(
            url=os.path.abspath(svg_path),
            write_to=png_path,
            output_width=256,
            output_height=256
        )
        print("  [OK] logo.png genere avec cairosvg")
        return True
    except ImportError:
        print("  [!] cairosvg non installe")
        print("      -> pip install cairosvg")
        print("      -> ou convertissez logo.svg en logo.png manuellement")
        print("         et placez le fichier dans assets/")
    except Exception as e:
        print(f"  [!] Erreur cairosvg: {e}")

    return False


def create_ico():
    """Genere icon.ico depuis logo.png (ou fallback programmatique)"""
    from PIL import Image, ImageDraw

    logo_path = os.path.join("assets", "img", "logo.png")

    if os.path.exists(logo_path):
        base = Image.open(logo_path).convert("RGBA")
    else:
        # Fallback : cercle rouge avec point blanc
        base = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        dc = ImageDraw.Draw(base)
        dc.ellipse([16, 16, 240, 240], fill=(220, 50, 50))
        dc.ellipse([96, 96, 160, 160], fill=(255, 255, 255))
        print("  [!] logo.png absent, icone par defaut utilisee")

    base.save("icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("  [OK] icon.ico cree")


def main():
    print("=" * 50)
    print("  Build : OpenWhisper.exe")
    print("=" * 50)

    # 1. PyInstaller
    print("\n[1/5] Installation de PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])

    # 2. Fix ctranslate2 avant l'analyse
    print("\n[2/5] Fix ctranslate2 (dossiers ROCm)...")
    fix_ctranslate2()

    # 3. Conversion logo SVG -> PNG
    print("\n[3/5] Conversion du logo...")
    convert_logo()

    # 4. Icone .ico
    print("\n[4/5] Generation de l'icone...")
    create_ico()

    # 5. PyInstaller
    print("\n[5/5] Build PyInstaller...\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--onefile",
        "--noconsole",
        "--name", "OpenWhisper",
        "--icon", "icon.ico",
        "--paths", ".",
        "--add-data", "assets/on.wav;.",
        "--add-data", "assets/off.wav;.",
        "--add-data", "assets/finish.wav;.",
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
    ]

    # Inclure logo.png dans le package si disponible
    if os.path.exists(os.path.join("assets", "img", "logo.png")):
        cmd.extend(["--add-data", "assets/img/logo.png;img/"])

    subprocess.check_call(cmd)

    # 6. Resultat
    exe = os.path.abspath(os.path.join("dist", "OpenWhisper.exe"))
    print("\n" + "=" * 50)
    print("  [OK] Build termine !")
    print(f"  -> {exe}")
    print("=" * 50)


if __name__ == "__main__":
    main()
