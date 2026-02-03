"""
Application de transcription vocale par hotkey
Ctrl+Space pour enregistrer et transcrire
"""
import keyboard
import time
import sys
from audio_recorder import AudioRecorder
from transcriber import Transcriber
from text_injector import TextInjector
from config import HOTKEY, MIN_RECORDING_DURATION
import pystray
from PIL import Image, ImageDraw
import threading


class VoiceToTextApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.injector = TextInjector()
        self.is_running = True
        self.record_start_time = None
        
    def create_tray_icon(self):
        """Crée une icône system tray minimaliste"""
        # Icône simple (cercle rouge)
        image = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(image)
        dc.ellipse([16, 16, 48, 48], fill='red')
        
        menu = pystray.Menu(
            pystray.MenuItem("Voice to Text - Actif", lambda: None, enabled=False),
            pystray.MenuItem(f"Hotkey: {HOTKEY}", lambda: None, enabled=False),
            pystray.MenuItem("Quitter", self.quit_app)
        )
        
        self.icon = pystray.Icon("voice_to_text", image, "Voice to Text", menu)
    
    def quit_app(self):
        """Quitte l'application proprement"""
        self.is_running = False
        self.icon.stop()
        sys.exit(0)
    
    def on_hotkey_press(self):
        """Callback quand le hotkey est pressé"""
        if not self.recorder.is_recording():
            print("🎤 Enregistrement démarré...")
            self.record_start_time = time.time()
            self.recorder.start()
    
    def on_hotkey_release(self):
        """Callback quand le hotkey est relâché"""
        if self.recorder.is_recording():
            # Vérification durée minimale
            duration = time.time() - self.record_start_time
            if duration < MIN_RECORDING_DURATION:
                print(f"⚠️  Enregistrement trop court ({duration:.2f}s)")
                self.recorder.stop()
                return
            
            print("⏹️  Enregistrement arrêté")
            audio_data = self.recorder.stop()
            
            if audio_data is not None and len(audio_data) > 0:
                print("🔄 Transcription en cours...")
                text = self.transcriber.transcribe(audio_data)
                
                if text:
                    print(f"✓ Transcrit: {text}")
                    self.injector.inject(text)
                    print("✓ Texte injecté")
                else:
                    print("⚠️  Aucun texte détecté")
            else:
                print("⚠️  Pas d'audio enregistré")
    
    def run(self):
        """Boucle principale de l'application"""
        print("=" * 50)
        print("🎙️  Voice to Text - Démarré")
        print(f"Hotkey: {HOTKEY}")
        print("Maintenez le raccourci pour enregistrer")
        print("Relâchez pour transcrire et injecter")
        print("=" * 50)
        
        # Enregistrement du hotkey avec callbacks séparés
        keyboard.on_press_key(
            HOTKEY.split('+')[-1],
            lambda _: self.on_hotkey_press() if keyboard.is_pressed('ctrl') else None
        )
        keyboard.on_release_key(
            HOTKEY.split('+')[-1],
            lambda _: self.on_hotkey_release()
        )
        
        # Lancement du tray icon dans un thread séparé
        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()
        
        # Boucle principale
        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n👋 Arrêt de l'application...")
            self.quit_app()


if __name__ == "__main__":
    app = VoiceToTextApp()
    app.create_tray_icon()
    app.run()
