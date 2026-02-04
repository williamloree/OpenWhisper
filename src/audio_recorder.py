"""Gestion de l'enregistrement audio"""
import sounddevice as sd
import numpy as np
from src.config import SAMPLE_RATE, CHANNELS


class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []
        self.stream = None
        self.device = self._find_input_device()

    def _find_input_device(self):
        """Trouve un peripherique d'entree valide"""
        try:
            # Essayer le peripherique par defaut
            default = sd.default.device[0]
            if default is not None and default >= 0:
                return default
        except Exception:
            pass

        # Chercher un peripherique d'entree disponible
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    print(f"[Audio] Peripherique trouve: {dev['name']}")
                    return i
        except Exception as e:
            print(f"[Audio] Erreur lors de la recherche: {e}")

        return None

    def start(self):
        """Demarre l'enregistrement audio"""
        if self.device is None:
            print("[!] Aucun peripherique audio trouve")
            return False

        self.recording = True
        self.frames = []

        def callback(indata, frames, time, status):
            if status:
                print(f"[Audio] Status: {status}")
            if self.recording:
                self.frames.append(indata.copy())

        try:
            self.stream = sd.InputStream(
                device=self.device,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                callback=callback,
                dtype='float32'
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"[!] Erreur demarrage audio: {e}")
            self.recording = False
            return False

    def stop(self):
        """Arrete l'enregistrement et retourne l'audio"""
        self.recording = False

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if not self.frames:
            return None

        # Convertir en array numpy
        audio_data = np.concatenate(self.frames, axis=0).flatten()
        return audio_data

    def is_recording(self):
        return self.recording
