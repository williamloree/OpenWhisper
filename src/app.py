"""Classe principale de l'application OpenWhisper (cross-platform)"""
import keyboard
import time
import sys
import os
import threading
import platform
import pystray
from PIL import Image, ImageDraw
from src.audio_recorder import AudioRecorder
from src.transcriber import Transcriber
from src.text_injector import TextInjector
from src.config import HOTKEY, MIN_RECORDING_DURATION
from src import sounds

IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'


class OpenWhisperApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.injector = TextInjector()
        self.is_running = True
        self.is_recording = False
        self.record_start_time = None
        self._toggle_cooldown = 0

    # ── Icone ──────────────────────────────────────────

    def _create_icon_image(self, recording=False):
        """Cercle vert si enregistrement en cours, rouge sinon"""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        dc = ImageDraw.Draw(img)
        color = (0, 200, 0) if recording else (220, 50, 50)
        dc.ellipse([8, 8, 56, 56], fill=color)
        return img

    def create_tray_icon(self):
        self.icon = pystray.Icon(
            "open_whisper",
            self._create_icon_image(False),
            "OpenWhisper",
            pystray.Menu(self._menu_items),
        )

    def _menu_items(self):
        """Menu dynamique - regenere a chaque ouverture"""
        status = "[REC] Enregistrement en cours..." if self.is_recording else "[OFF] En attente"
        startup_suffix = " *" if self._is_startup_enabled() else ""
        yield pystray.MenuItem(status, None, enabled=False)
        yield pystray.MenuItem(f"Hotkey : {HOTKEY}", None, enabled=False)
        if IS_WINDOWS:
            yield pystray.MenuItem(f"Demarrer au demarrage{startup_suffix}", self._toggle_startup)
        yield pystray.MenuItem("Quitter", self.quit_app)

    # ── Demarrage automatique ───────────────────────────

    def _get_exe_path(self):
        if getattr(sys, "frozen", False):
            return os.path.abspath(sys.executable)
        return os.path.abspath(sys.argv[0])

    def _is_startup_enabled(self):
        if not IS_WINDOWS:
            return False
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            )
            winreg.QueryValueEx(key, "OpenWhisper")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _toggle_startup(self, icon, item):
        if not IS_WINDOWS:
            return
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        if self._is_startup_enabled():
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, access=winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "OpenWhisper")
            winreg.CloseKey(key)
            print("Demarrage automatique : desactive")
        else:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, access=winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "OpenWhisper", 0, winreg.REG_SZ, f'"{self._get_exe_path()}"')
            winreg.CloseKey(key)
            print("Demarrage automatique : active")

    # ── Presse-papier (cross-platform) ─────────────────

    def _copy_to_clipboard(self, text):
        """Copie le texte dans le presse-papier"""
        try:
            if IS_WINDOWS:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                user32 = ctypes.windll.user32
                user32.OpenClipboard(0)
                user32.EmptyClipboard()
                hMem = kernel32.GlobalAlloc(0x0042, len(text.encode('utf-16-le')) + 2)
                pMem = kernel32.GlobalLock(hMem)
                ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(pMem), text)
                kernel32.GlobalUnlock(hMem)
                user32.SetClipboardData(13, hMem)
                user32.CloseClipboard()
            elif IS_MACOS:
                import subprocess
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
            else:  # Linux
                import subprocess
                # Essayer xclip ou xsel
                for cmd in [['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard', '--input']]:
                    try:
                        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                        process.communicate(text.encode('utf-8'))
                        return
                    except FileNotFoundError:
                        continue
        except Exception as e:
            print(f"[!] Erreur clipboard: {e}")

    # ── Controle enregistrement (toggle) ────────────────

    def toggle_recording(self):
        """Appui unique = demarrer OU arreter"""
        now = time.time()
        if now - self._toggle_cooldown < 0.3:
            return
        self._toggle_cooldown = now

        if self.is_recording:
            self._stop_and_transcribe()
        else:
            self._start_recording()

    def _start_recording(self):
        self.is_recording = True
        self.record_start_time = time.time()
        if not self.recorder.start():
            self.is_recording = False
            return
        self.icon.icon = self._create_icon_image(True)
        sounds.play_start_recording()
        print("[REC] Enregistrement demarre...")

    def _stop_and_transcribe(self):
        duration = time.time() - self.record_start_time
        audio_data = self.recorder.stop()
        self.is_recording = False
        self.icon.icon = self._create_icon_image(False)

        if duration < MIN_RECORDING_DURATION:
            print(f"[!] Enregistrement trop court ({duration:.2f}s)")
            return

        print("[STOP] Enregistrement arrete")

        if audio_data is not None and len(audio_data) > 0:
            sounds.play_start_transcription()
            print("[...] Transcription en cours...")
            text = self.transcriber.transcribe(audio_data)
            if text:
                print(f"[OK] Transcrit: {text}")
                self._copy_to_clipboard(text)
                self.injector.inject(text)
                sounds.play_done()
                print("[OK] Texte copie et injecte")
            else:
                print("[!] Aucun texte detecte")
        else:
            print("[!] Pas d'audio enregistre")

    # ── Cycle de vie ────────────────────────────────────

    def quit_app(self, icon=None, item=None):
        self.is_running = False
        if self.recorder.is_recording():
            self.recorder.stop()
        self.icon.stop()
        sys.exit(0)

    def run(self):
        print("=" * 50)
        print("  OpenWhisper - Demarre")
        print(f"  Hotkey : {HOTKEY}  (mode toggle)")
        print(f"  Plateforme : {platform.system()}")
        print("  1er appui  -> demarrer l'enregistrement")
        print("  2eme appui -> arreter + transcrire")
        print("=" * 50)

        keyboard.add_hotkey(HOTKEY, self.toggle_recording)

        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nArret de l'application...")
            self.quit_app()
