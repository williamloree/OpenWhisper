"""Configuration globale de l'application"""

# Modèle Whisper à utiliser (tiny, base, small, medium, large-v3)
# tiny = ultra rapide, précision moyenne
# base = bon compromis vitesse/précision
WHISPER_MODEL = "medium"

# Langue de transcription (fr, en, etc.)
LANGUAGE = "fr"

# Device pour faster-whisper ("cpu", "cuda", "auto")
DEVICE = "cpu"

# Compute type pour faster-whisper
COMPUTE_TYPE = "int8"  # int8 pour CPU, float16 pour GPU

# Paramètres audio
SAMPLE_RATE = 16000  # Hz (requis par Whisper)
CHANNELS = 1  # Mono

# Hotkey
HOTKEY = "ctrl+space"

# Durée minimale d'enregistrement (secondes)
MIN_RECORDING_DURATION = 0.3
