# OpenWhisper

Application de transcription vocale locale avec Whisper AI.

**Plateformes supportees** : Windows, Linux, macOS

## Fonctionnalites

- **Hotkey global** : `Ctrl + Espace` (toggle enregistrement/transcription)
- **Transcription locale** : Utilise Whisper AI (aucune donnee envoyee sur internet)
- **Injection automatique** : Le texte s'insere directement ou se trouve votre curseur
- **Copie automatique** : Le texte est copie dans le presse-papier
- **Indicateurs sonores** : Son au debut et a la fin de la transcription
- **Ultra leger** : Icone dans la barre des taches, pas d'interface

## Telechargement

1. Allez sur la page [Releases](../../releases)
2. Telechargez la version correspondant a votre OS :
   - `OpenWhisper-Windows.exe` (Windows)
   - `OpenWhisper-Linux` (Linux)
   - `OpenWhisper-macOS` (macOS)
3. Lancez l'application

## Utilisation

1. **Lancez** l'application
2. Une **icone rouge** apparait dans la barre des taches
3. **`Ctrl + Espace`** pour demarrer l'enregistrement (son + icone verte)
4. **`Ctrl + Espace`** pour arreter et transcrire (son de fin)
5. Le texte est **injecte** a la position du curseur et **copie** dans le presse-papier

**Menu** (clic droit sur l'icone) :

- Voir le statut (enregistrement en cours ou en attente)
- Activer/desactiver le demarrage automatique (Windows uniquement)
- Quitter l'application

**Notes par plateforme :**

- **Windows** : Mode administrateur recommande
- **Linux** : Necessite `xclip` ou `xsel` pour le presse-papier, `paplay`/`aplay` pour les sons
- **macOS** : Fonctionne nativement

---

## Developpement

### Installation

```bash
# Cloner le repo
git clone https://github.com/votre-username/OpenWhisper.git
cd OpenWhisper

# Creer l'environnement virtuel
python -m venv venv

# Installer les dependances
pip install -r requirements.txt
```

**Dependances systeme (Linux) :**

```bash
sudo apt-get install portaudio19-dev xclip
```

**Dependances systeme (macOS) :**

```bash
brew install portaudio
```

### Lancer l'application

**Windows (PowerShell) :**

```powershell
.\venv\Scripts\activate
python main.py
```

**Windows (Git Bash) / Linux / macOS :**

```bash
source venv/bin/activate  # Linux/macOS
# ou: ./venv/Scripts/python.exe main.py  # Windows Git Bash
python main.py
```

### Build

```bash
python scripts/build.py
```

L'executable sera genere dans `dist/`.

### Release (CI/CD)

Le projet utilise GitHub Actions pour automatiser les builds multi-plateformes.

**Creer une nouvelle release :**

```bash
git tag v1.0.0
git push origin v1.0.0
```

Les executables pour Windows, Linux et macOS seront automatiquement generes et disponibles sur la page [Releases](../../releases).

**Mettre a jour un tag existant :**

```bash
# Supprimer le tag local et distant
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Recreer et pousser le tag
git tag v1.0.0
git push origin v1.0.0
```

### Structure du projet

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
│   ├── open.wav                 # Son de debut
│   └── finish.mp3               # Son de fin
├── scripts/
│   ├── build.py                 # Script de build (Windows)
│   └── pyi_rth_rocm.py          # Runtime hook PyInstaller
├── .github/workflows/           # CI/CD GitHub Actions
│   ├── build.yml                # Test de build multi-plateforme
│   └── release.yml              # Build + release multi-plateforme
├── main.py                      # Point d'entree
├── requirements.txt
├── LICENSE
└── README.md
```

### Configuration

Modifiez `src/config.py` :

```python
WHISPER_MODEL = "base"      # tiny, base, small, medium, large
LANGUAGE = "fr"             # Code langue ISO
HOTKEY = "ctrl+space"       # Raccourci clavier
MODEL_UNLOAD_DELAY = 300    # Secondes avant dechargement du modele
```

## Licence

MIT License - voir [LICENSE](LICENSE)
