# OpenWhisper

Application Windows de transcription vocale locale avec Whisper AI.

## Fonctionnalites

- **Hotkey global** : `Ctrl + Espace` (toggle enregistrement/transcription)
- **Transcription locale** : Utilise Whisper AI (aucune donnee envoyee sur internet)
- **Injection automatique** : Le texte s'insere directement ou se trouve votre curseur
- **Copie automatique** : Le texte est copie dans le presse-papier
- **Indicateurs sonores** : Son au debut et a la fin de la transcription
- **Ultra leger** : Icone dans la barre des taches, pas d'interface

## Telechargement

1. Allez sur la page [Releases](../../releases)
2. Telechargez `OpenWhisper.exe`
3. Lancez l'application (mode administrateur recommande)

## Utilisation

1. **Lancez** `OpenWhisper.exe`
2. Une **icone rouge** apparait dans la barre des taches
3. **`Ctrl + Espace`** pour demarrer l'enregistrement (son + icone verte)
4. **`Ctrl + Espace`** pour arreter et transcrire (son de fin)
5. Le texte est **injecte** a la position du curseur et **copie** dans le presse-papier

**Menu** (clic droit sur l'icone) :

- Voir le statut (enregistrement en cours ou en attente)
- Activer/desactiver le demarrage automatique avec Windows
- Quitter l'application

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

### Lancer l'application

**PowerShell :**

```powershell
.\venv\Scripts\activate
python main.py
```

**Git Bash / Terminal :**

```bash
./venv/Scripts/python.exe main.py
```

### Build

```bash
python scripts/build.py
```

L'executable sera genere dans `dist/OpenWhisper.exe`.

### Release (CI/CD)

Le projet utilise GitHub Actions pour automatiser les releases.

**Creer une nouvelle release :**

```bash
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
│   ├── build.py                 # Script de build
│   └── pyi_rth_rocm.py          # Runtime hook PyInstaller
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
