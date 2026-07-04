# Known Issues

## AnkiDroid: a harmless "Card Content Error: Failed to load '…'" message

**What you see:** On Android (AnkiDroid), a small message may briefly appear at
the bottom of the screen when a card loads:

> Card Content Error: Failed to load '…'

**It is harmless. You can ignore it.** The card still displays correctly, the
notation renders, and audio plays normally. It does **not** mean anything on
the card failed to load.

**Why it happens:** This message comes from **AnkiDroid itself**, not from this
deck. It is a known, long-standing false positive in AnkiDroid's reviewer,
triggered by AnkiDroid's own internal JavaScript bridge — see AnkiDroid issues
[#16510](https://github.com/ankidroid/Anki-Android/issues/16510) and
[#10033](https://github.com/ankidroid/Anki-Android/issues/10033). It appears
"despite everything working fine," it is intermittent, and it never happens on
Anki Desktop or AnkiMobile (iOS).

**How we confirmed it is not this deck's fault:** As of note type
`v24`, these cards contain **no external JavaScript files at all** — the
notation engine (a slim, Bravura-only VexFlow build) and all card scripts are
embedded directly in the card templates. Every resource the card references
loads successfully (verified over Chrome DevTools against a real AnkiDroid
build). The message still appears even with zero external resources, which is
only possible if the source is AnkiDroid's own code. There is no reliable
card-side fix; it is up to the AnkiDroid team.

## Platform support

Cards render and play audio offline on **Anki Desktop**, **AnkiMobile (iOS)**,
and **AnkiDroid (Android)**. No internet connection is required — the notation
engine and audio are bundled in the deck.
