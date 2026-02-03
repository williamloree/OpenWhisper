"""Transcription audio avec faster-whisper (lazy loading)"""
from src.config import WHISPER_MODEL, LANGUAGE, DEVICE, COMPUTE_TYPE
import numpy as np


class Transcriber:
    def __init__(self):
        self.model = None  # Lazy loading: charge a la premiere utilisation

    def _load_model(self):
        """Charge le modele Whisper (appele une seule fois)"""
        if self.model is None:
            from faster_whisper import WhisperModel
            print(f"Chargement du modele Whisper '{WHISPER_MODEL}'...")
            self.model = WhisperModel(
                WHISPER_MODEL,
                device=DEVICE,
                compute_type=COMPUTE_TYPE
            )
            print("Modele charge")

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcrit l'audio en texte"""
        if audio_data is None or len(audio_data) == 0:
            return ""

        # Charger le modele si pas encore fait
        self._load_model()

        # faster-whisper attend un array numpy float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Transcription
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

        # Recuperation du texte
        text = " ".join([segment.text for segment in segments])
        return text.strip()
