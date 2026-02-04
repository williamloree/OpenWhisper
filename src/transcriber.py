"""Transcription audio avec faster-whisper (chargement au demarrage)"""
from src.config import WHISPER_MODEL, LANGUAGE, DEVICE, COMPUTE_TYPE
import numpy as np
import threading


class Transcriber:
    def __init__(self):
        self.model = None
        self._ready = threading.Event()
        self._error = None
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        # Fix SSL certificates for PyInstaller bundle
        try:
            import ssl
            import certifi
            ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
        except Exception:
            pass

        try:
            from faster_whisper import WhisperModel
            print(f"[Whisper] Chargement du modele '{WHISPER_MODEL}'...")
            self.model = WhisperModel(
                WHISPER_MODEL,
                device=DEVICE,
                compute_type=COMPUTE_TYPE
            )
            print("[Whisper] Modele charge")
        except Exception as e:
            import traceback
            self._error = str(e)
            print(f"[Whisper] ERREUR chargement: {e}")
            print(f"[Whisper] Traceback:\n{traceback.format_exc()}")
        finally:
            self._ready.set()

    def is_ready(self) -> bool:
        """Retourne True si le modele est charge (ou en erreur)"""
        return self._ready.is_set()

    def has_error(self) -> bool:
        """Retourne True si le chargement a echoue"""
        return self._error is not None

    def get_error(self) -> str:
        """Retourne le message d'erreur"""
        return self._error

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcrit l'audio en texte"""
        if audio_data is None or len(audio_data) == 0:
            return ""

        if not self._ready.is_set():
            print("[Whisper] En attente du chargement du modele...")
        self._ready.wait()

        if self.model is None:
            print(f"[Whisper] Modele non disponible: {self._error}")
            return ""

        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        segments, info = self.model.transcribe(
            audio_data,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
            }
        )

        text = " ".join([segment.text for segment in segments])
        return text.strip()
