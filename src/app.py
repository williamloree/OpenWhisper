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
        self.is_transcribing = False
        self.record_start_time = None
        self._toggle_cooldown = 0
        self._spinner_frame = 0
        self._spinner_thread = None
        self._logo_base = self._load_logo()

    # ── Asset path (dev + exe) ──────────────────────────

    @staticmethod
    def _get_asset_path(filename):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, filename)
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)

    # ── Logo ────────────────────────────────────────────

    def _load_logo(self):
        """Charge le logo depuis assets/logo.png"""
        logo_path = self._get_asset_path(os.path.join("img", "logo.png"))
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).convert("RGBA").resize((64, 64), Image.LANCZOS)
                print(f"[Logo] Charge depuis: {logo_path}")
                return img
            except Exception as e:
                print(f"[Logo] Erreur chargement: {e}")
        return None

    # ── Icone ──────────────────────────────────────────

    def _create_icon_image(self, state="idle"):
        """
        Cree l'icone tray selon l'etat :
          idle          -> logo + point rouge (bas droite)
          recording     -> logo + point vert  (bas droite)
          transcribing  -> logo + arc spinner (jaune) + point jaune
        """
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

        if self._logo_base:
            img.paste(self._logo_base, (0, 0), self._logo_base)
        else:
            dc = ImageDraw.Draw(img)
            dc.ellipse([4, 4, 60, 60], fill=(50, 50, 50))

        dc = ImageDraw.Draw(img)

        if state == "recording":
            dc.ellipse([46, 46, 60, 60], fill=(0, 200, 0), outline=(0, 150, 0))
        elif state == "transcribing":
            angle = (self._spinner_frame * 30) % 360
            dc.arc([2, 2, 62, 62], angle, angle + 100, fill=(50, 180, 255), width=5)
            dc.ellipse([46, 46, 60, 60], fill=(255, 180, 0), outline=(200, 140, 0))
        else:  # idle
            dc.ellipse([46, 46, 60, 60], fill=(220, 50, 50), outline=(170, 30, 30))

        return img

    def create_tray_icon(self):
        self.icon = pystray.Icon(
            "open_whisper",
            self._create_icon_image("idle"),
            "OpenWhisper",
            pystray.Menu(self._menu_items),
        )

    def _menu_items(self):
        """Menu dynamique - regenere a chaque ouverture"""
        if self.is_recording:
            status = "[REC] Enregistrement en cours..."
        elif self.is_transcribing:
            status = "[...] Transcription en cours..."
        else:
            status = "[OFF] En attente"
        startup_suffix = " *" if self._is_startup_enabled() else ""
        yield pystray.MenuItem(status, None, enabled=False)
        yield pystray.MenuItem(f"Hotkey : {HOTKEY}", None, enabled=False)
        if IS_WINDOWS:
            yield pystray.MenuItem(f"Demarrer au demarrage{startup_suffix}", self._toggle_startup)
        yield pystray.MenuItem("Quitter", self.quit_app)

    # ── Spinner (animation pendant transcription) ───────

    def _start_spinner(self):
        self._spinner_frame = 0
        self._spinner_thread = threading.Thread(target=self._spinner_loop, daemon=True)
        self._spinner_thread.start()

    def _stop_spinner(self):
        self.is_transcribing = False
        if self._spinner_thread and self._spinner_thread.is_alive():
            self._spinner_thread.join(timeout=0.2)
        self._spinner_thread = None

    def _spinner_loop(self):
        while self.is_transcribing:
            self._spinner_frame += 1
            self.icon.icon = self._create_icon_image("transcribing")
            time.sleep(0.1)

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
                kernel32.GlobalAlloc.restype = ctypes.c_void_p
                kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
                kernel32.GlobalLock.restype = ctypes.c_void_p
                kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
                user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
                encoded = text.encode('utf-16-le') + b'\x00\x00'
                user32.OpenClipboard(0)
                user32.EmptyClipboard()
                hMem = kernel32.GlobalAlloc(0x0042, len(encoded))
                pMem = kernel32.GlobalLock(hMem)
                ctypes.memmove(pMem, encoded, len(encoded))
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
        self.icon.icon = self._create_icon_image("recording")
        sounds.play_start_recording()
        print("[REC] Enregistrement demarre...")

    def _stop_and_transcribe(self):
        duration = time.time() - self.record_start_time
        audio_data = self.recorder.stop()
        self.is_recording = False

        if duration < MIN_RECORDING_DURATION:
            self.icon.icon = self._create_icon_image("idle")
            print(f"[!] Enregistrement trop court ({duration:.2f}s)")
            return

        print("[STOP] Enregistrement arrete")

        if audio_data is not None and len(audio_data) > 0:
            # Demarrer l'animation spinner
            self.is_transcribing = True
            self._start_spinner()
            sounds.play_stop_recording()
            print("[...] Transcription en cours...")

            text = self.transcriber.transcribe(audio_data)

            # Arreter le spinner et revenir a idle
            self._stop_spinner()
            self.icon.icon = self._create_icon_image("idle")

            if text:
                print(f"[OK] Transcrit: {text}")
                self._copy_to_clipboard(text)
                self.injector.inject(text)
                sounds.play_done()
                print("[OK] Texte copie et injecte")
            else:
                print("[!] Aucun texte detecte")
        else:
            self.icon.icon = self._create_icon_image("idle")
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
