"""Transcription audio avec faster-whisper (chargement au demarrage)"""
from src.config import WHISPER_MODEL, LANGUAGE, DEVICE, COMPUTE_TYPE
import numpy as np
import threading


class Transcriber:
    def __init__(self, settings=None):
        self.model = None
        self._ready = threading.Event()
        self._error = None
        self._settings = settings

        # Utiliser les settings si fournis, sinon les defaults de config
        if settings:
            self._model_name = settings.whisper_model
            self._language = settings.language
            self._device = settings.device
            self._compute_type = settings.compute_type
        else:
            self._model_name = WHISPER_MODEL
            self._language = LANGUAGE
            self._device = DEVICE
            self._compute_type = COMPUTE_TYPE

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
            print(f"[Whisper] Chargement du modele '{self._model_name}'...")
            self.model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type
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

        # Utiliser la langue des settings si disponible
        language = self._language

        segments, info = self.model.transcribe(
            audio_data,
            language=language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
            }
        )

        text = " ".join([segment.text for segment in segments])
        return text.strip()
