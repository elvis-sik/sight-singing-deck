"""Hardcoded Stage-1 MVP melodies (C major, treble, four quarter notes)."""

from __future__ import annotations

MELODIES: list[dict[str, object]] = [
    {
        "id": "mvp_01",
        "notes": ["C4", "D4", "C4", "C4"],
        "degrees": [1, 2, 1, 1],
        "description": "Upper neighbor return",
    },
    {
        "id": "mvp_02",
        "notes": ["C4", "D4", "C4"],
        "durations": ["q", "q", "h"],
        "degrees": [1, 2, 1],
        "description": "Half-note return",
    },
    {
        "id": "mvp_03",
        "notes": ["C4", "D4", "E4", "E4"],
        "degrees": [1, 2, 3, 3],
        "description": "Ascending to 3",
    },
    {
        "id": "mvp_04",
        "notes": ["C4", "D4", "E4", "D4", "C4", "C4"],
        "durations": ["8", "8", "q", "q", "8", "8"],
        "degrees": [1, 2, 3, 2, 1, 1],
        "description": "Eighth-note arch",
    },
    {
        "id": "mvp_05",
        "notes": ["E4", "D4", "C4", "C4"],
        "degrees": [3, 2, 1, 1],
        "description": "Descending to 1",
    },
    {
        "id": "mvp_06",
        "notes": ["E4", "D4", "D4", "C4"],
        "degrees": [3, 2, 2, 1],
        "description": "Descent with plateau",
    },
    {
        "id": "mvp_07",
        "notes": ["E4", "F4", "E4", "E4"],
        "degrees": [3, 4, 3, 3],
        "description": "Upper neighbor around 3",
    },
    {
        "id": "mvp_08",
        "notes": ["E4", "G4", "E4"],
        "durations": ["h", "q", "q"],
        "degrees": [3, 5, 3],
        "description": "Half-note leap return",
    },
    {
        "id": "mvp_09",
        "notes": ["G4", "F4", "E4", "E4"],
        "degrees": [5, 4, 3, 3],
        "description": "Descending from 5",
    },
    {
        "id": "mvp_10",
        "notes": ["G4", "A4", "G4", "E4"],
        "durations": ["8", "8", "h", "q"],
        "degrees": [5, 6, 5, 3],
        "description": "Quick upper neighbor to long 5",
    },
]
