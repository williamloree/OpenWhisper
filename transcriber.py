"""Transcription audio avec faster-whisper"""
from faster_whisper import WhisperModel
from config import WHISPER_MODEL, LANGUAGE, DEVICE, COMPUTE_TYPE, SAMPLE_RATE
import numpy as np


class Transcriber:
    def __init__(self):
        print(f"Chargement du modèle Whisper '{WHISPER_MODEL}'...")
        self.model = WhisperModel(
            WHISPER_MODEL,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        print("Modèle chargé ✓")
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcrit l'audio en texte
        
        Args:
            audio_data: Array numpy float32 mono à 16kHz
            
        Returns:
            Texte transcrit
        """
        if audio_data is None or len(audio_data) == 0:
            return ""
        
        # faster-whisper attend un array numpy float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Transcription
        segments, info = self.model.transcribe(
            audio_data,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,  # Filtre de détection de voix
            vad_parameters={
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
            }
        )
        
        # Récupération du texte
        text = " ".join([segment.text for segment in segments])
        return text.strip()
