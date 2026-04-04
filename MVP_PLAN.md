# Sight-Singing Deck — MVP Implementation Plan

## Goal

Build a **10-card test deck** that validates the full end-to-end pipeline:

- Python generates structured card data
- VexFlow renders notation dynamically on the Anki card
- Web Audio API synthesizes playback in the browser/webview
- `genanki` packages everything into an `.apkg`
- The deck imports and works in Anki desktop

If this works, the entire curriculum design from the full plan can be built on top of it incrementally. If it doesn't, we learn what breaks before investing in the generator.

---

## Scope: what the MVP includes

| Dimension        | MVP value                                |
|------------------|------------------------------------------|
| Cards            | 10                                       |
| Stage            | Stage 1 only (neighbor patterns)         |
| Clef             | Treble only                              |
| Key/mode         | C major only                             |
| Notes per melody | 4 quarter notes in 4/4                   |
| Intervals        | Unisons and seconds only                 |
| Start degree     | 1, 3, or 5                               |
| End degree       | 1, 3, or 5                               |
| Melody source    | Hardcoded list (no generator needed yet) |
| Audio            | Web Audio API sine/triangle oscillator   |
| Notation         | VexFlow 5 rendered in-card               |
| Playback buttons | Cadence, First Note, Tonic, Full Melody  |
| Card front       | Staff + support buttons                  |
| Card back        | Staff + scale degrees + note names + replay |

## Scope: what the MVP does NOT include

- Melody generator / quality rules / sampling
- A natural minor
- Bass clef
- Stages 2–9
- Autoplay
- Tone.js (raw Web Audio is enough for sine tones)
- Any CI, tests, or packaging beyond the build script

---

## The 10 MVP melodies

All in C major, treble clef, 4 quarter notes, Stage 1 constraints (adjacent intervals ≤ 2nd, start/end on 1, 3, or 5).

| #  | Notes            | Degrees | Start→End | Character              |
|----|------------------|---------|-----------|------------------------|
| 1  | C4 D4 C4 C4      | 1 2 1 1 | 1→1       | Upper neighbor return   |
| 2  | C4 D4 D4 C4      | 1 2 2 1 | 1→1       | Up-plateau-back         |
| 3  | C4 D4 E4 E4      | 1 2 3 3 | 1→3       | Ascending to 3          |
| 4  | C4 C4 D4 E4      | 1 1 2 3 | 1→3       | Delayed ascent          |
| 5  | E4 D4 C4 C4      | 3 2 1 1 | 3→1       | Descending to 1         |
| 6  | E4 D4 D4 C4      | 3 2 2 1 | 3→1       | Descent with plateau    |
| 7  | E4 F4 E4 E4      | 3 4 3 3 | 3→3       | Upper neighbor around 3 |
| 8  | E4 F4 G4 G4      | 3 4 5 5 | 3→5       | Ascending to 5          |
| 9  | G4 F4 E4 E4      | 5 4 3 3 | 5→3       | Descending from 5       |
| 10 | G4 A4 G4 G4      | 5 6 5 5 | 5→5       | Upper neighbor around 5 |

These are deliberately simple and pedagogically reasonable. They cover all feasible start→end pairs for Stage 1 with 4-note melodies.

---

## Project structure

```
sight-singing-deck/
├── pyproject.toml
├── .gitignore
├── sight_singing_deck_plan.md      (existing)
├── MVP_PLAN.md                     (this file)
├── scripts/
│   └── build_deck.py               # Main build script
├── src/
│   └── sight_singing/
│       ├── __init__.py
│       ├── melodies.py             # The 10 hardcoded melodies as data
│       ├── card_data.py            # Melody → card field serialization
│       └── anki_model.py           # Note type, templates, CSS, model def
└── assets/
    ├── vexflow.js                  # VexFlow 5 standalone bundle (downloaded)
    ├── renderer.js                 # Our code: parse JSON → draw staff
    └── player.js                   # Our code: Web Audio playback
```

---

## Implementation steps

### Step 1 — Project scaffolding

- `git init`
- Create `pyproject.toml` with `genanki` dependency (following the `chinese-dynasties` pattern: uv, exclude-newer, ruff)
- Create `.gitignore` (`.venv/`, `out/`, `*.apkg`, `__pycache__/`)
- Create directory structure
- `uv venv && uv pip install -e ".[deck]"`

### Step 2 — Download VexFlow bundle

Download the VexFlow 5 standalone build into `assets/vexflow.js`. This file ships inside the `.apkg` as a shared media asset so every card can reference it.

The file is ~400–500 KB. It only needs to be downloaded once and committed (or fetched at build time).

### Step 3 — Write `renderer.js`

A small script (~80–120 lines) that:

1. Reads a JSON payload from a `<div id="melody-data">` element on the card.
2. Creates a VexFlow `Renderer` attached to a `<div id="notation">`.
3. Draws a single-staff system: treble clef, key signature (C major = none), time signature (4/4), 4 quarter notes.
4. Optionally shows scale degrees below the staff (on the back side, controlled by a flag in the JSON or a CSS class on the card).

Design note: the renderer should be defensive — if VexFlow fails to load or the data is malformed, the card should still show the raw note names as a fallback rather than a blank card.

### Step 4 — Write `player.js`

A small script (~100–150 lines) that:

1. Creates an `AudioContext` on first user interaction (required by browser autoplay policies).
2. Maps note names (e.g. `"C4"`) to frequencies.
3. Exposes functions callable from button `onclick` handlers:
   - `playNote(noteName, durationSec)` — play a single note
   - `playSequence(notes, tempo)` — play a sequence of notes at a given tempo
   - `playCadence(key)` — play a I–IV–V–I cadence in the given key
4. Uses a simple triangle-wave oscillator with an ADSR envelope for a clean, piano-ish tone.

No external audio library needed. The Web Audio API is sufficient for single-voice sine/triangle synthesis.

### Step 5 — Write `melodies.py`

A Python module containing the 10 melodies as a list of dictionaries:

```python
MELODIES = [
    {
        "id": "mvp_01",
        "notes": ["C4", "D4", "C4", "C4"],
        "degrees": [1, 2, 1, 1],
        "description": "Upper neighbor return",
    },
    # ... 9 more
]
```

Each entry is minimal. The rest of the card metadata (clef, key, mode, time signature, stage, support info) is identical for all 10 MVP cards and will be added at serialization time.

### Step 6 — Write `card_data.py`

Converts each melody dict into a full card-field payload:

```python
def melody_to_card_fields(melody: dict) -> dict:
    return {
        "MelodyJSON": json.dumps({
            "clef": "treble",
            "key": "C",
            "mode": "major",
            "timeSig": "4/4",
            "notes": melody["notes"],
            "durations": ["q", "q", "q", "q"],
            "degrees": melody["degrees"],
            "supports": {
                "tonic": "C4",
                "firstNote": melody["notes"][0],
                "cadenceKey": "C",
            },
        }),
        "StageID": "stage1",
        "MelodyID": melody["id"],
    }
```

The `MelodyJSON` field is the single source of truth that the JS on the card reads.

### Step 7 — Write `anki_model.py`

Defines the Anki note type using `genanki.Model`:

**Fields:**
- `MelodyJSON` — the JSON payload
- `StageID` — for tagging/filtering
- `MelodyID` — unique identifier

**Front template:**
```html
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div id="notation"></div>
<div class="controls">
  <button onclick="playCadence()">Cadence</button>
  <button onclick="playFirstNote()">First Note</button>
  <button onclick="playTonic()">Tonic</button>
</div>
<div class="prompt">Sing this melody.</div>
<script src="_vexflow.js"></script>
<script src="_renderer.js"></script>
<script src="_player.js"></script>
```

**Back template:**
```html
{{FrontSide}}
<hr id="answer">
<div id="answer-info"></div>
<div class="controls">
  <button onclick="playMelody()">Play Melody</button>
</div>
```

The back reuses the front (standard Anki pattern), then appends the answer section. The renderer checks for the presence of `#answer-info` to decide whether to show scale degrees.

**CSS:** Clean, minimal styling. Dark-on-light, large staff, clearly tappable buttons.

### Step 8 — Write `build_deck.py`

The main build script:

1. Import melodies from `melodies.py`
2. Convert each to card fields via `card_data.py`
3. Create the `genanki.Model` via `anki_model.py`
4. Create a `genanki.Deck`
5. Add 10 `genanki.Note` instances
6. Create a `genanki.Package` with media files: `_vexflow.js`, `_renderer.js`, `_player.js`
7. Write `out/sight-singing-mvp.apkg`

Run with: `python scripts/build_deck.py`

### Step 9 — Build and manual test

1. Run the build script
2. Import `out/sight-singing-mvp.apkg` into Anki desktop
3. Verify:
   - [ ] Staff renders correctly with VexFlow
   - [ ] Clef and time signature display
   - [ ] Notes appear in correct positions
   - [ ] "Cadence" button plays I–IV–V–I
   - [ ] "First Note" button plays the first note
   - [ ] "Tonic" button plays C4
   - [ ] Back side shows scale degrees
   - [ ] "Play Melody" button plays all 4 notes in sequence
   - [ ] No JS errors in the console (Anki → Debug Console)

---

## Key risks and mitigations

### Risk 1: VexFlow doesn't work inside Anki's webview

**Mitigation:** VexFlow renders to SVG or Canvas. Anki's Qt WebEngine supports both. If VexFlow 5 has issues, fall back to VexFlow 4.x, which has years of proven browser compatibility. Worst case, generate static SVGs at build time and embed them (this defeats the dynamic rendering goal but still produces a working deck).

### Risk 2: Web Audio API blocked or unavailable

**Mitigation:** Web Audio API requires user interaction to start an `AudioContext`. All playback is behind manual buttons, which satisfies this requirement. If Anki's webview restricts Web Audio entirely, fall back to embedding small pre-generated MP3/OGG files as media assets (increases deck size but guarantees playback).

### Risk 3: Anki strips `<script>` tags or blocks external JS

**Mitigation:** Anki does allow `<script src="...">` for media files prefixed with `_` (underscore). This is the standard convention for shared assets in Anki packages. The underscore prefix prevents Anki's media check from flagging the files as unused.

### Risk 4: AnkiMobile / AnkiDroid compatibility

**Out of scope for MVP.** The MVP targets Anki desktop only. Mobile testing comes after the desktop pipeline is validated.

---

## What comes after the MVP

Once the 10-card deck works on Anki desktop:

1. **Melody generator** — replace the hardcoded list with a generator that respects stage constraints
2. **Quality rules** — filter out bad melodies
3. **More stages** — add Stages 2–9
4. **A natural minor** — add the second mode
5. **Bass clef** — mirror the curriculum
6. **Better audio** — richer timbre, possibly sampled piano
7. **Autoplay logic** — per-stage default support behavior
8. **Mobile testing** — AnkiDroid and AnkiMobile
9. **Full deck build** — sampled deck with all stages, both clefs, both modes

---

## Dependencies

| Package   | Purpose                        | Install                            |
|-----------|--------------------------------|------------------------------------|
| `genanki` | Build .apkg Anki deck packages | `sfw uv pip install genanki`       |
| `ruff`    | Linter/formatter (dev)         | `sfw uv pip install ruff`          |

No other Python dependencies needed for the MVP. VexFlow is a JS asset, not a Python package.

---

## Estimated effort

| Step                       | Estimate    |
|----------------------------|-------------|
| Project scaffolding        | 5 min       |
| Download VexFlow           | 2 min       |
| `renderer.js`              | 30–45 min   |
| `player.js`                | 20–30 min   |
| `melodies.py`              | 5 min       |
| `card_data.py`             | 10 min      |
| `anki_model.py`            | 20–30 min   |
| `build_deck.py`            | 10–15 min   |
| Build + test + debug cycle | 30–60 min   |
| **Total**                  | **~2.5–3 h** |

Most of the time will go into `renderer.js`, `player.js`, and the test/debug cycle. The Python side is straightforward.
