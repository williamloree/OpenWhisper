# OpenWhisper

Application Windows de transcription vocale locale avec Whisper AI.

## Fonctionnalites

- **Hotkey global** : `Ctrl + Espace` (toggle enregistrement/transcription)
- **Transcription locale** : Utilise Whisper AI (aucune donnee envoyee sur internet)
- **Injection automatique** : Le texte s'insere directement ou se trouve votre curseur
- **Indicateur sonore** : Son au debut de l'enregistrement et de la transcription
- **Ultra leger** : Icone dans la barre des taches, pas d'interface

## Structure du projet

```text
OpenWhisper/
├── src/                         # Code source
│   ├── app.py                   # Application principale
│   ├── config.py                # Configuration
│   ├── audio_recorder.py        # Enregistrement audio
│   ├── transcriber.py           # Transcription Whisper
│   ├── text_injector.py         # Injection du texte
│   └── sounds.py                # Indicateurs sonores
├── assets/
│   └── open.wav                 # Son d'indication
├── scripts/
│   ├── build.py                 # Script de build
│   └── pyi_rth_rocm.py          # Runtime hook PyInstaller
├── main.py                      # Point d'entree
├── requirements.txt
├── LICENSE
└── README.md
```

## Installation

```bash
# Cloner le repo
git clone https://github.com/votre-username/OpenWhisper.git
cd OpenWhisper

# Creer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate

# Installer les dependances
pip install -r requirements.txt

# Lancer l'application
python main.py
```

## Build

```bash
python scripts/build.py
```

L'executable sera genere dans `dist/OpenWhisper.exe`.

## Release (CI/CD)

Le projet utilise GitHub Actions pour automatiser les releases.

**Creer une nouvelle release :**

```bash
# Creer et pousser un tag de version
git tag v1.0.0
git push origin v1.0.0
```

L'exe sera automatiquement build et disponible sur la page [Releases](../../releases).

**Mettre a jour un tag existant :**

```bash
# Supprimer le tag local et distant
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Recreer et pousser le tag
git tag v1.0.0
git push origin v1.0.0
```

## Utilisation

1. Lancez `OpenWhisper.exe` (mode administrateur recommande)
2. Icone rouge dans la barre des taches
3. **`Ctrl + Espace`** → enregistrement (son + icone verte)
4. **`Ctrl + Espace`** → transcription + injection (son)

## Configuration

Modifiez `src/config.py` :

```python
WHISPER_MODEL = "base"      # tiny, base, small, medium, large
LANGUAGE = "fr"             # Code langue ISO
HOTKEY = "ctrl+space"       # Raccourci clavier
```

## Licence

MIT License - voir [LICENSE](LICENSE)
