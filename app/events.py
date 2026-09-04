"""
Réservé aux phases futures : bus de signaux Qt (QObject + Signal) utilisé
pour découpler les couches Gesture Engine / UI une fois les gestes
implémentés (spec section 24 : communication propre et thread-safe entre
threads).

Non utilisé en Phase 1. La communication caméra -> UI passe pour l'instant
directement par les signaux de CameraWorker (voir ui/main_window.py).
"""
