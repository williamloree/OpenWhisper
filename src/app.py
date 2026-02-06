"""Classe principale de l'application OpenWhisper (cross-platform)"""
import keyboard
import time
import sys
import os
import threading
import platform
import webbrowser
import pystray
from PIL import Image, ImageDraw, ImageEnhance
from src.audio_recorder import AudioRecorder
from src.transcriber import Transcriber
from src.text_injector import TextInjector
from src.config import MIN_RECORDING_DURATION
from src.settings import Settings
from src.version import VERSION, GITHUB_REPO
from src.updater import UpdateChecker
from src.ui.settings_window import SettingsWindow
from src.ui.recording_overlay import RecordingOverlay
from src import sounds

IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'


class OpenWhisperApp:
    def __init__(self):
        # Settings persistants
        self.settings = Settings()

        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(self.settings)
        self.injector = TextInjector()
        self.is_running = True
        self.is_recording = False
        self.is_transcribing = False
        self.is_model_loading = True
        self.record_start_time = None
        self._toggle_cooldown = 0
        self._spinner_frame = 0
        self._spinner_thread = None
        self._loading_thread = None
        self._logo_base = self._load_logo()
        self._logo_gray = self._create_gray_logo()

        # Update checker
        self.update_checker = UpdateChecker(VERSION, GITHUB_REPO)
        self.update_available = False
        self.latest_version = None
        self.download_url = None

        # UI components
        self.settings_window = SettingsWindow(self.settings, self._on_settings_saved)
        # Toujours centrer l'overlay au demarrage (ignorer position sauvegardee)
        self.recording_overlay = RecordingOverlay(None)

        # Hotkey actuel (pour re-enregistrement)
        self._current_hotkey = self.settings.hotkey

    # ── Asset path (dev + exe) ──────────────────────────

    @staticmethod
    def _get_asset_path(filename):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, filename)
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)

    # ── Logo ────────────────────────────────────────────

    def _load_logo(self):
        """Charge le logo depuis assets/img/logo.png"""
        logo_path = self._get_asset_path(os.path.join("img", "logo.png"))
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).convert("RGBA").resize((64, 64), Image.LANCZOS)
                print(f"[Logo] Charge depuis: {logo_path}")
                return img
            except Exception as e:
                print(f"[Logo] Erreur chargement: {e}")
        return None

    def _create_gray_logo(self):
        """Cree une version grisee du logo pour l'etat loading"""
        if self._logo_base:
            gray = self._logo_base.convert("LA").convert("RGBA")
            enhancer = ImageEnhance.Brightness(gray)
            return enhancer.enhance(0.5)
        return None

    # ── Icone ──────────────────────────────────────────

    def _create_icon_image(self, state="idle"):
        """
        Cree l'icone tray selon l'etat :
          loading       -> logo grise + arc spinner orange
          idle          -> logo + point rouge (bas droite)
          recording     -> logo + point vert  (bas droite)
          transcribing  -> logo + arc spinner bleu + point jaune
          error         -> logo grise + croix rouge
        """
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))

        if state == "loading":
            if self._logo_gray:
                img.paste(self._logo_gray, (0, 0), self._logo_gray)
            else:
                dc = ImageDraw.Draw(img)
                dc.ellipse([4, 4, 60, 60], fill=(80, 80, 80))
            dc = ImageDraw.Draw(img)
            angle = (self._spinner_frame * 30) % 360
            dc.arc([2, 2, 62, 62], angle, angle + 100, fill=(255, 140, 0), width=5)
        elif state == "error":
            if self._logo_gray:
                img.paste(self._logo_gray, (0, 0), self._logo_gray)
            else:
                dc = ImageDraw.Draw(img)
                dc.ellipse([4, 4, 60, 60], fill=(80, 80, 80))
            dc = ImageDraw.Draw(img)
            dc.line([44, 44, 60, 60], fill=(255, 50, 50), width=4)
            dc.line([60, 44, 44, 60], fill=(255, 50, 50), width=4)
        else:
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
            self._create_icon_image("loading"),
            "OpenWhisper",
            pystray.Menu(self._menu_items),
        )

    def _menu_items(self):
        """Menu dynamique - regenere a chaque ouverture"""
        if self.is_model_loading:
            status = "[...] Chargement du modele Whisper..."
        elif self.transcriber.has_error():
            status = "[ERR] Erreur chargement modele"
        elif self.is_recording:
            status = "[REC] Enregistrement en cours..."
        elif self.is_transcribing:
            status = "[...] Transcription en cours..."
        else:
            status = "[OK] Pret"

        startup_suffix = " *" if self._is_startup_enabled() else ""
        hotkey = self.settings.hotkey

        yield pystray.MenuItem(status, None, enabled=False)
        yield pystray.MenuItem(f"Hotkey : {hotkey}", None, enabled=False)
        yield pystray.Menu.SEPARATOR

        # Mise a jour disponible
        if self.update_available and self.latest_version:
            yield pystray.MenuItem(
                f"Mise a jour disponible: v{self.latest_version}",
                self._open_download_page
            )
            yield pystray.Menu.SEPARATOR

        # Parametres (desactive temporairement)
        yield pystray.MenuItem("Parametres...", self._open_settings)

        # if IS_WINDOWS:
        #     yield pystray.MenuItem(f"Demarrer au demarrage{startup_suffix}", self._toggle_startup)

        yield pystray.Menu.SEPARATOR
        yield pystray.MenuItem("Quitter", self.quit_app)

    # ── Loading animation (pendant chargement modele) ───

    def _start_loading_animation(self):
        self._spinner_frame = 0
        self._loading_thread = threading.Thread(target=self._loading_loop, daemon=True)
        self._loading_thread.start()

    def _stop_loading_animation(self):
        self.is_model_loading = False
        self._loading_thread = None
        self.icon.icon = self._create_icon_image("idle")

    def _loading_loop(self):
        while self.is_model_loading and self.is_running:
            self._spinner_frame += 1
            self.icon.icon = self._create_icon_image("loading")
            time.sleep(0.1)
            # Verifier si le modele est charge
            if self.transcriber.is_ready():
                self.is_model_loading = False
                if self.transcriber.has_error():
                    self.icon.icon = self._create_icon_image("error")
                    print(f"[ERREUR] Chargement modele echoue: {self.transcriber.get_error()}")
                else:
                    self.icon.icon = self._create_icon_image("idle")
                    print("[OK] Modele pret - Hotkey active")
                break
        self._loading_thread = None

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

    # ── Parametres et mises a jour ────────────────────

    def _open_settings(self, icon=None, item=None):
        """Ouvre la fenetre de parametres"""
        if self.is_recording:
            print("[!] Impossible d'ouvrir les parametres pendant l'enregistrement")
            return

        # Attendre que l'overlay soit completement ferme
        if self.recording_overlay.is_visible:
            print("[!] Attente fermeture overlay...")
            self.recording_overlay.hide()

        # Attendre un peu pour que le thread tkinter de l'overlay soit nettoye
        time.sleep(0.2)

        self.settings_window.show()

    def _open_download_page(self, icon=None, item=None):
        """Ouvre la page de telechargement dans le navigateur"""
        if self.download_url:
            webbrowser.open(self.download_url)

    def _on_settings_saved(self, model_changed: bool, hotkey_changed: bool):
        """Callback appele apres sauvegarde des parametres"""
        print("[Settings] Parametres sauvegardes")

        # Re-enregistrer le hotkey si change
        if hotkey_changed:
            try:
                keyboard.remove_hotkey(self._current_hotkey)
            except Exception:
                pass
            self._current_hotkey = self.settings.hotkey
            keyboard.add_hotkey(self._current_hotkey, self.toggle_recording)
            print(f"[Settings] Hotkey change: {self._current_hotkey}")

        # Recharger le modele si necessaire
        if model_changed:
            print("[Settings] Rechargement du modele...")
            self.is_model_loading = True
            self.icon.icon = self._create_icon_image("loading")
            self.transcriber = Transcriber(self.settings)
            self._start_loading_animation()

    def _on_update_checked(self, has_update: bool, version: str, url: str):
        """Callback appele apres verification des mises a jour"""
        self.update_available = has_update
        self.latest_version = version
        self.download_url = url
        if has_update:
            print(f"[Update] Nouvelle version disponible: v{version}")

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
        # Bloquer si le modele n'est pas charge
        if self.is_model_loading:
            print("[!] Modele en cours de chargement, veuillez patienter...")
            return

        # Bloquer si le modele est en erreur
        if self.transcriber.has_error():
            print(f"[!] Modele non disponible: {self.transcriber.get_error()}")
            return

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

        # Callback pour la waveform
        def on_audio(samples):
            if self.recording_overlay.is_visible:
                self.recording_overlay.update_waveform(samples)

        if not self.recorder.start(on_audio_callback=on_audio):
            self.is_recording = False
            return

        self.icon.icon = self._create_icon_image("recording")

        # Afficher l'overlay
        self.recording_overlay.show()

        sounds.play_start_recording()
        print("[REC] Enregistrement demarre...")

    def _stop_and_transcribe(self):
        duration = time.time() - self.record_start_time
        audio_data = self.recorder.stop()
        self.is_recording = False

        # Cacher l'overlay et sauvegarder la position
        overlay_pos = self.recording_overlay.hide()
        if overlay_pos:
            self.settings.set("overlay_position", overlay_pos)
            self.settings.save()

        if duration < MIN_RECORDING_DURATION:
            self.icon.icon = self._create_icon_image("idle")
            print(f"[!] Enregistrement trop court ({duration:.2f}s)")
            return

        print("[STOP] Enregistrement arrete")

        if audio_data is not None and len(audio_data) > 0:
            self.is_transcribing = True
            self._start_spinner()
            sounds.play_stop_recording()
            print("[...] Transcription en cours...")

            text = self.transcriber.transcribe(audio_data)

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
        self.is_model_loading = False
        if self.recorder.is_recording():
            self.recorder.stop()
        self.icon.stop()
        sys.exit(0)

    def run(self):
        hotkey = self.settings.hotkey
        print("=" * 50)
        print(f"  OpenWhisper v{VERSION} - Demarre")
        print(f"  Hotkey : {hotkey}  (mode toggle)")
        print(f"  Plateforme : {platform.system()}")
        print("  1er appui  -> demarrer l'enregistrement")
        print("  2eme appui -> arreter + transcrire")
        print("=" * 50)
        print("[...] Chargement du modele Whisper...")

        keyboard.add_hotkey(hotkey, self.toggle_recording)

        # Verifier les mises a jour en arriere-plan
        self.update_checker.check_async(self._on_update_checked)

        # Demarrer l'animation de chargement
        self._start_loading_animation()

        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nArret de l'application...")
            self.quit_app()
