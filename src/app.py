"""Classe principale de l'application OpenWhisper"""
import keyboard
import time
import sys
import os
import winreg
import threading
import pystray
from PIL import Image, ImageDraw
from src.audio_recorder import AudioRecorder
from src.transcriber import Transcriber
from src.text_injector import TextInjector
from src.config import HOTKEY, MIN_RECORDING_DURATION
from src import sounds


class OpenWhisperApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.injector = TextInjector()
        self.is_running = True
        self.is_recording = False
        self.record_start_time = None
        self._toggle_cooldown = 0

    # ── Icône ──────────────────────────────────────────

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
        """Menu dynamique — regénéré à chaque ouverture"""
        status = "🟢 Enregistrement en cours..." if self.is_recording else "🔴 En attente"
        startup_suffix = " ✓" if self._is_startup_enabled() else ""
        yield pystray.MenuItem(status, None, enabled=False)
        yield pystray.MenuItem(f"Hotkey : {HOTKEY}", None, enabled=False)
        yield pystray.MenuItem(f"Démarrer au démarrage{startup_suffix}", self._toggle_startup)
        yield pystray.MenuItem("Quitter", self.quit_app)

    # ── Démarrage automatique (registre Windows) ───────

    def _get_exe_path(self):
        if getattr(sys, "frozen", False):
            return os.path.abspath(sys.executable)
        return os.path.abspath(sys.argv[0])

    def _is_startup_enabled(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            )
            winreg.QueryValueEx(key, "OpenWhisper")
            winreg.CloseKey(key)
            return True
        except OSError:
            return False

    def _toggle_startup(self, icon, item):
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        if self._is_startup_enabled():
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, access=winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "OpenWhisper")
            winreg.CloseKey(key)
            print("Démarrage automatique : désactivé")
        else:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, access=winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "OpenWhisper", 0, winreg.REG_SZ, f'"{self._get_exe_path()}"')
            winreg.CloseKey(key)
            print("Démarrage automatique : activé")

    # ── Contrôle enregistrement (toggle) ────────────────

    def toggle_recording(self):
        """Appui unique = démarrer OU arrêter"""
        now = time.time()
        if now - self._toggle_cooldown < 0.3:   # ignore key-repeat
            return
        self._toggle_cooldown = now

        if self.is_recording:
            self._stop_and_transcribe()
        else:
            self._start_recording()

    def _start_recording(self):
        self.is_recording = True
        self.record_start_time = time.time()
        self.recorder.start()
        self.icon.icon = self._create_icon_image(True)
        sounds.play_start_recording()
        print("🎤 Enregistrement démarré...")

    def _stop_and_transcribe(self):
        duration = time.time() - self.record_start_time
        audio_data = self.recorder.stop()
        self.is_recording = False
        self.icon.icon = self._create_icon_image(False)

        if duration < MIN_RECORDING_DURATION:
            print(f"⚠️  Enregistrement trop court ({duration:.2f}s)")
            return

        print("⏹️  Enregistrement arrêté")

        if audio_data is not None and len(audio_data) > 0:
            sounds.play_start_transcription()
            print("🔄 Transcription en cours...")
            text = self.transcriber.transcribe(audio_data)
            if text:
                print(f"✓ Transcrit: {text}")
                self.injector.inject(text)
                sounds.play_done()
                print("✓ Texte injecté")
            else:
                print("⚠️  Aucun texte détecté")
        else:
            print("⚠️  Pas d'audio enregistré")

    # ── Cycle de vie ────────────────────────────────────

    def quit_app(self, icon=None, item=None):
        self.is_running = False
        if self.recorder.is_recording():
            self.recorder.stop()
        self.icon.stop()
        sys.exit(0)

    def run(self):
        print("=" * 50)
        print("🎙️  OpenWhisper - Démarré")
        print(f"Hotkey : {HOTKEY}  (mode toggle)")
        print("  1er appui  → démarrer l'enregistrement")
        print("  2ème appui → arrêter + transcrire")
        print("=" * 50)

        keyboard.add_hotkey(HOTKEY, self.toggle_recording)

        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Arrêt de l'application...")
            self.quit_app()
