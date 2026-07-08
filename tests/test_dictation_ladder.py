"""Objective-coverage assertions for the dictation melodic spine.

The review pass (see DICTATION_CURRICULUM.md rev 3) found that specs must be
*validated against their objectives*, not merely written: the old tendency stage
was titled "ti→do" yet generated zero ti→do resolutions. These tests fail the
build if a dictation stage stops honouring its own promise.

Invariants checked for every generated pitch-only stage:
  * no immediate repeats (repeats carry no pitch info in even rhythm);
  * no melodic interval wider than a perfect 5th (the strand never has a 6th);
  * the stage's own max_step ceiling is respected;
  * each stage actually yields exercises (no silently-empty rung);
and the objective-specific ones:
  * DD8 resolves ti→do in EVERY item (the regression guard);
  * fa→mi is represented somewhere in the strand;
  * the length ramp matches the documented ladder (steps to 6, then reset).
"""

from __future__ import annotations

import unittest

from sight_singing.curriculum.stages import (
    DICTATION_INTERVAL_STAGES,
    DICTATION_MINOR_HARMONIC_STAGES,
    DICTATION_MINOR_STAGES,
    DICTATION_PRIMING_SINGLETONS,
    DICTATION_STAGES,
)
from sight_singing.generate.melody_gen import generate_stage
from sight_singing.theory.scales import diatonic_semitone

PERFECT_FIFTH_SEMITONES = 7


def _semitone_leaps(mel: tuple[int, ...]) -> list[int]:
    return [
        abs(diatonic_semitone(b, "major") - diatonic_semitone(a, "major"))
        for a, b in zip(mel, mel[1:])
    ]


def _has_resolution(mel: tuple[int, ...], from_pos: int, delta: int) -> bool:
    """Does the melody contain scale-position `from_pos` moving by `delta`?"""
    return any((a % 7 == from_pos) and (b - a == delta) for a, b in zip(mel, mel[1:]))


class DictationLadderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.generated = {s.id: generate_stage(s) for s in DICTATION_STAGES}

    def test_every_stage_yields(self) -> None:
        for stage in DICTATION_STAGES:
            with self.subTest(stage=stage.id):
                self.assertGreaterEqual(
                    len(self.generated[stage.id]), 6,
                    f"{stage.id} yielded too few exercises — spec is over-tight",
                )

    def test_no_immediate_repeats(self) -> None:
        # Every pitch-only stage sets min_step >= 1, so no two adjacent notes are
        # equal. Repeats are deferred until the rhythm strand gives them meaning.
        for stage in DICTATION_STAGES:
            for mel in self.generated[stage.id]:
                with self.subTest(stage=stage.id, mel=mel):
                    self.assertTrue(
                        all(a != b for a, b in zip(mel, mel[1:])),
                        f"{stage.id} produced an immediate repeat: {mel}",
                    )

    def test_no_interval_wider_than_a_fifth(self) -> None:
        # max_step <= 4 (a 5th) across the strand => never a 6th.
        for stage in DICTATION_STAGES:
            self.assertLessEqual(stage.max_step, 4, f"{stage.id} allows a 6th+")
            for mel in self.generated[stage.id]:
                with self.subTest(stage=stage.id, mel=mel):
                    self.assertTrue(
                        all(s <= PERFECT_FIFTH_SEMITONES for s in _semitone_leaps(mel)),
                        f"{stage.id} produced a leap wider than a P5: {mel}",
                    )

    def test_max_step_ceiling_respected(self) -> None:
        for stage in DICTATION_STAGES:
            for mel in self.generated[stage.id]:
                with self.subTest(stage=stage.id, mel=mel):
                    self.assertTrue(
                        all(abs(b - a) <= stage.max_step for a, b in zip(mel, mel[1:])),
                        f"{stage.id} exceeded its diatonic ceiling: {mel}",
                    )

    def test_dd8_every_item_resolves_ti_to_do(self) -> None:
        # The regression guard: the leading tone (ti, upper index 6, or ti, below
        # tonic at index -1 == 6 mod 7) must resolve UP by a half-step in EVERY
        # DD8 item. Upper ti -> do' is (6 -> 7); lower ti, -> do is (-1 -> 0).
        dd8 = self.generated["DD8"]
        self.assertTrue(dd8, "DD8 generated nothing")
        for mel in dd8:
            with self.subTest(mel=mel):
                resolves = _has_resolution(mel, 6, +1)
                self.assertTrue(resolves, f"DD8 item has no ti->do resolution: {mel}")

    def test_fa_to_mi_is_represented_in_the_strand(self) -> None:
        # fa->mi (index 3 -> 2) is the other primary tendency; it is trained across
        # the stepwise stages rather than forced into DD8. Assert it actually shows
        # up somewhere so "tendency tones" isn't secretly ti-only.
        found = any(
            _has_resolution(mel, 3, -1)
            for mels in self.generated.values()
            for mel in mels
        )
        self.assertTrue(found, "fa->mi never appears in the dictation strand")

    def test_priming_singletons_are_single_stable_degrees(self) -> None:
        for mel in DICTATION_PRIMING_SINGLETONS:
            with self.subTest(mel=mel):
                self.assertEqual(len(mel), 1, "DP0 echo must be a single degree")
                self.assertIn(mel[0], (0, 2, 4), "DP0 uses the pillars do/mi/so")

    def test_length_ramp_isolates_length_from_leaps(self) -> None:
        # The documented ladder: priming 2,2; steps grow 3,3,4,5,6 with max_step=1;
        # then leaps enter and length RESETS to 4 (DD6 thirds, DD7 4ths/5ths);
        # then length grows again 5,6 (DD8, DD9). The triad rungs (DP1, DD1) are the
        # deliberate exception — triad-tone leaps come first by design.
        by_id = {s.id: s for s in DICTATION_STAGES}
        # Steps-only rungs never exceed a 2nd.
        for sid in ("DP2", "DD2", "DD3", "DD4", "DD5"):
            self.assertEqual(by_id[sid].max_step, 1, f"{sid} should be stepwise")
        # Length reaches 6 on steps (DD5) before any non-triad leap stage.
        self.assertEqual(by_id["DD5"].length, 6)
        # Leaps reset the length to 4.
        self.assertEqual(by_id["DD6"].length, 4)
        self.assertEqual(by_id["DD7"].length, 4)
        # Then it climbs again.
        self.assertEqual(by_id["DD8"].length, 5)
        self.assertEqual(by_id["DD9"].length, 6)


class MinorDictationTest(unittest.TestCase):
    """The natural-minor ladder mirrors the major invariants."""

    def setUp(self) -> None:
        self.generated = {s.id: generate_stage(s) for s in DICTATION_MINOR_STAGES}

    def test_every_stage_yields(self) -> None:
        for stage in DICTATION_MINOR_STAGES:
            with self.subTest(stage=stage.id):
                self.assertGreaterEqual(len(self.generated[stage.id]), 6)

    def test_no_repeats_and_no_interval_past_a_fifth(self) -> None:
        for stage in DICTATION_MINOR_STAGES:
            self.assertLessEqual(stage.max_step, 4, f"{stage.id} allows a 6th+")
            for mel in self.generated[stage.id]:
                with self.subTest(stage=stage.id, mel=mel):
                    self.assertTrue(all(a != b for a, b in zip(mel, mel[1:])))
                    self.assertTrue(
                        all(
                            abs(
                                diatonic_semitone(b, "natural_minor")
                                - diatonic_semitone(a, "natural_minor")
                            )
                            <= PERFECT_FIFTH_SEMITONES
                            for a, b in zip(mel, mel[1:])
                        ),
                        f"{stage.id} leap wider than a P5: {mel}",
                    )

    def test_nd8_every_item_resolves_ti_to_do(self) -> None:
        # Minor's leading tone ti sits at index 1; ti->do is index 1 -> +1.
        for mel in self.generated["ND8"]:
            with self.subTest(mel=mel):
                self.assertTrue(
                    _has_resolution(mel, 1, +1), f"ND8 item has no ti->do: {mel}"
                )

    def test_harmonic_capstone_resolves_si_to_la(self) -> None:
        # ND9h is deferred from the built deck (si = G# needs accidental input),
        # but the spec must still resolve the raised 7 (index 6) up in every item.
        for stage in DICTATION_MINOR_HARMONIC_STAGES:
            for mel in generate_stage(stage):
                with self.subTest(mel=mel):
                    self.assertTrue(_has_resolution(mel, 6, +1))


class IntervalDictationTest(unittest.TestCase):
    def test_each_interval_stage_yields(self) -> None:
        # IVD8 (octave) is inherently small (only do<->do' and ti<->ti' exist in
        # the one-octave-plus pool), so the floor is 4, not 6.
        for stage in DICTATION_INTERVAL_STAGES:
            with self.subTest(stage=stage.id):
                self.assertGreaterEqual(len(generate_stage(stage)), 4)

    def test_tritone_stripped_in_the_realization_mode(self) -> None:
        # The interval stages declare no mode, so generate_stage takes the
        # realization mode. The forbidden tritone (6 semitones) sits at DIFFERENT
        # scale positions in major (fa↔ti) vs la-based minor, so a stage realized
        # in minor must be filtered in minor — not with the major default. This is
        # the guard for the forbid_tritone_leap mode fix.
        fourth = next(s for s in DICTATION_INTERVAL_STAGES if s.id == "IVD4")
        for mode in ("major", "natural_minor", "harmonic_minor"):
            mels = generate_stage(fourth, mode)
            self.assertTrue(mels, f"IVD4 yielded nothing in {mode}")
            for mel in mels:
                leaps = [
                    abs(diatonic_semitone(b, mode) - diatonic_semitone(a, mode))
                    for a, b in zip(mel, mel[1:])
                ]
                with self.subTest(mode=mode, mel=mel):
                    self.assertNotIn(
                        6, leaps, f"IVD4 kept a tritone when realized in {mode}: {mel}"
                    )


if __name__ == "__main__":
    unittest.main()
