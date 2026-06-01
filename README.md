# Sight-Singing Deck

Code-generated Anki deck experiments for beginner sight singing.

The project started as a 10-card MVP that validates the full pipeline:

- Python generates structured melody card data.
- VexFlow renders notation inside Anki cards.
- Shared media assets provide playback and rendering helpers.
- `genanki` packages the result into `.apkg` files.

Current work also includes fixed-audio curriculum planning, rhythm curriculum notes, and a transcription minigame/debug harness.

## Key Files

- [`MVP_PLAN.md`](MVP_PLAN.md): original 10-card pipeline plan
- [`sight_singing_deck_plan.md`](sight_singing_deck_plan.md): broader deck plan
- [`FIXED_AUDIO_CURRICULUM.md`](FIXED_AUDIO_CURRICULUM.md): fixed-audio curriculum notes
- [`RHYTHM_CURRICULUM.md`](RHYTHM_CURRICULUM.md): rhythm-card curriculum notes
- [`TRANSCRIPTION_MINIGAME_DESIGN.md`](TRANSCRIPTION_MINIGAME_DESIGN.md): transcription interaction design
- [`scripts/build_deck.py`](scripts/build_deck.py): main APKG builder
- [`tests/transcription-harness.spec.js`](tests/transcription-harness.spec.js): Playwright smoke test for the transcription harness

## Python Setup

```sh
uv sync --extra deck --extra dev
```

Build the main deck:

```sh
.venv/bin/python scripts/build_deck.py
```

Generated APKG files are written under `out/`.

## Transcription Debug Harness

Install JavaScript debug dependencies through Socket Firewall:

```sh
sfw npm install
```

Run the debug server from the repository root:

```sh
npm run debug:server
```

Run the Playwright transcription check:

```sh
npm run test:transcription
```

## Notes

- `node_modules/`, `test-results/`, `out/`, rendered audio, and local render caches are intentionally ignored.
- The project uses `uv`'s `exclude-newer = "7 days"` policy and an npm `.npmrc` minimum release-age policy for dependency safety.
