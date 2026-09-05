# Deku Gesture Control

Application de bureau Windows pour contrôler l'ordinateur (souris, clavier)
à l'aide de gestes de la main détectés par webcam.

**Confidentialité :** tout le traitement se fait localement. Aucune image
ni vidéo n'est jamais envoyée vers un serveur distant.

## État actuel : Phases 1 à 4

- **Phase 1** — structure du projet, `CameraManager`, affichage webcam, FPS,
  bouton Démarrer/Arrêter.
- **Phase 2** — `HandTracker` (MediaPipe HandLandmarker), affichage des 21
  landmarks de la main sur le flux vidéo.
- **Phase 3** — `hand_geometry` (distance, angle, doigts tendus, pinch),
  `GestureEngine` avec machine à états anti-faux-positifs pour le geste
  PINCH (confirmation multi-frames, durée minimale, cooldown).
- **Phase 4** — `CursorController` : l'index pilote réellement le curseur
  système (calibration de zone active, sensibilité, lissage exponentiel,
  zone morte).
- **Phase 5** — le geste PINCH pilote désormais de vraies actions souris :
  clic gauche (pinch bref), double-clic (deux pinch rapides), glisser-déposer
  (pinch maintenu + déplacement). Le geste "deux doigts" (index + majeur
  tendus) déclenche le clic droit.

⚠️ **À savoir avant de lancer l'app** : dès que la caméra est démarrée et
qu'une main est détectée, le **curseur bouge réellement** et les **clics
sont réellement envoyés au système**, pilotés par tes gestes. Cliquez sur
**ARRÊTER** (ou fermez la fenêtre) pour reprendre le contrôle normal de la
souris.

📶 **Premier lancement** : `HandTracker` télécharge automatiquement le
modèle `hand_landmarker.task` (~10 Mo) depuis les serveurs Google au
premier démarrage de la caméra — une connexion Internet est donc
nécessaire une seule fois. Le modèle est ensuite mis en cache dans
`assets/models/` et plus jamais retéléchargé. En cas d'échec (pas de
réseau), un message d'erreur clair s'affiche dans l'interface avec le lien
de téléchargement manuel.

Le mapping gestes -> actions, les clics, le scroll, les profils et la page
de paramètres arriveront dans les phases suivantes (voir plus bas).

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
| 2 ✅ | MediaPipe, HandTracker, affichage des landmarks |
| 3 ✅ | Géométrie de la main, détection du pinch, machine à états |
| 4 ✅ | Contrôle du curseur (calibration, lissage) |
| 5 ✅ | Clic gauche/droit, double-clic, drag & drop |
| 6 | Scroll, swipe, raccourcis clavier |
| 7 | Interface PySide6 complète |
| 8 | Profils, paramètres, mapping personnalisable, mode debug |
| 9 | Tests unitaires |
| 10 | Optimisation et packaging Windows (PyInstaller → `DekuGestureControl.exe`) |

## Prochaine étape

Une fois les Phases 1 à 5 validées sur ta machine (clic, double-clic et
drag & drop fiables, sans faux déclenchement), passer à la Phase 6 :
scroll (mouvement vertical de la main), gestes de swipe
(navigation) et raccourcis clavier configurables.
