# Deku Gesture Control

Application de bureau Windows pour contrôler l'ordinateur (souris, clavier)
à l'aide de gestes de la main détectés par webcam.

**Confidentialité :** tout le traitement se fait localement. Aucune image
ni vidéo n'est jamais envoyée vers un serveur distant.

## État actuel : Phase 1 — Caméra

Cette version contient uniquement :

- la structure complète du projet ;
- le `CameraManager` (détection, ouverture/fermeture, lecture de frames,
  gestion des erreurs) ;
- une interface PySide6 affichant le flux webcam, le FPS et un bouton
  Démarrer/Arrêter.

La reconnaissance de gestes, le contrôle du curseur, le mapping
configurable, etc. arriveront dans les phases suivantes (voir plus bas).

## Installation

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

## Lancer l'application

```bash
python main.py
```

## Structure du projet

```
deku-gesture-control/
├── main.py
├── requirements.txt
├── app/            # bootstrap Qt (application.py, events.py)
├── camera/         # CameraManager, CameraSettings — implémenté
├── vision/         # hand tracking MediaPipe — Phase 2
├── gestures/       # moteur de gestes, machine à états — Phase 3+
├── input/          # contrôle souris/clavier/système — Phase 4+
├── cursor/         # mapping écran, lissage, calibration — Phase 4
├── config/         # settings.json, gestures.json, profiles.json
├── ui/             # main_window.py — implémenté ; autres pages à venir
├── core/           # logger, constants, events
└── tests/          # tests unitaires — Phase 9
```

## Feuille de route

| Phase | Contenu |
|---|---|
| 1 ✅ | Structure, CameraManager, affichage webcam |
| 2 | MediaPipe, HandTracker, affichage des landmarks |
| 3 | Géométrie de la main, détection du pinch, machine à états |
| 4 | Contrôle du curseur (calibration, lissage) |
| 5 | Clic gauche/droit, double-clic, drag & drop |
| 6 | Scroll, swipe, raccourcis clavier |
| 7 | Interface PySide6 complète |
| 8 | Profils, paramètres, mapping personnalisable, mode debug |
| 9 | Tests unitaires |
| 10 | Optimisation et packaging Windows (PyInstaller → `DekuGestureControl.exe`) |

## Prochaine étape

Une fois la Phase 1 validée (webcam détectée, flux affiché, FPS correct),
passer à la Phase 2 : intégration de MediaPipe pour le hand tracking.
