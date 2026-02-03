# PyInstaller runtime hook: cree les dossiers ROCm vides requis par ctranslate2
import os
import sys

if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
    for name in ("_rocm_sdk_core", "_rocm_sdk_libraries_custom"):
        os.makedirs(os.path.join(base, name, "bin"), exist_ok=True)
