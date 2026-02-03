# 🎙️ Voice to Text - Transcription vocale instantanée

Application Windows légère pour transcrire votre voix en texte via un simple raccourci clavier.

## ⚡ Fonctionnalités

- **Hotkey global** : `Ctrl + Espace` (maintenez pour enregistrer, relâchez pour transcrire)
- **Transcription locale** : Utilise Whisper AI (aucune donnée envoyée sur internet)
- **Injection automatique** : Le texte s'insère directement où se trouve votre curseur
- **Ultra léger** : Pas d'interface, juste une icône dans la barre des tâches
- **Support français** : Optimisé pour le français (modifiable pour d'autres langues)

## 📦 Contenu du package

```
voice-to-text/
├── main.py                      # Point d'entrée de l'application
├── audio_recorder.py            # Gestion de l'enregistrement audio
├── transcriber.py               # Transcription avec Whisper
├── text_injector.py             # Injection du texte
├── config.py                    # Configuration (modèle, langue, hotkey)
├── requirements.txt             # Dépendances Python
├── lancer_voice_to_text.bat     # Script de lancement rapide
├── INSTALLATION.md              # Guide d'installation détaillé
└── README.md                    # Ce fichier
```

## 🚀 Installation rapide

1. **Installer Python 3.9+** (cochez "Add Python to PATH")
2. **Extraire le ZIP** dans un dossier
3. **Ouvrir PowerShell** dans ce dossier (Shift + clic droit)
4. **Créer l'environnement virtuel** :
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
5. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```
6. **Lancer l'application** :
   ```bash
   python main.py
   ```

**📖 Pour le guide complet**, consultez `INSTALLATION.md`

## 🎯 Utilisation

1. Lancez l'application (icône rouge dans la barre des tâches)
2. Placez votre curseur dans n'importe quel champ de texte
3. **Maintenez `Ctrl + Espace`** et parlez
4. **Relâchez** → Le texte apparaît automatiquement !

## ⚙️ Configuration

Modifiez `config.py` pour personnaliser :

- **Modèle** : `tiny` (rapide) → `base` (défaut) → `small` (précis)
- **Langue** : `fr`, `en`, `es`, `de`, etc.
- **Raccourci** : `ctrl+space`, `ctrl+shift+v`, etc.

## 📊 Performances recommandées

| Configuration | Modèle | Vitesse de transcription |
|---------------|--------|--------------------------|
| PC classique  | `base` | ~2-3 secondes |
| PC puissant   | `small` | ~3-5 secondes |
| Avec GPU      | `medium` | ~2-4 secondes |

## 🔧 Dépannage rapide

- **Erreur "keyboard"** → Lancez PowerShell en Administrateur
- **Pas de son** → Vérifiez votre micro dans Paramètres Windows
- **Texte non inséré** → Vérifiez que le champ est bien actif

## 📄 Licence

Ce projet est fourni tel quel, sans garantie. Utilisation libre pour usage personnel et commercial.

---

**Développé par William - Janvier 2025**
