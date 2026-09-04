"""
Définitions d'événements génériques, indépendantes de Qt (spec section 3/29).

Réservé aux phases futures : servira à faire transiter les événements
gestuels (GESTURE_DETECTED, GESTURE_RELEASED, ...) entre les couches
Gesture Engine / Gesture Mapping sans dépendre de PySide6, pour rester
testable unitairement (spec section 25).

Non utilisé en Phase 1 (caméra uniquement).
"""
