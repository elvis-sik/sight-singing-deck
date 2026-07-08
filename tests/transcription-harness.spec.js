import { test, expect } from "@playwright/test";

async function debugState(page) {
  return page.evaluate(() => window.SightSingingTranscriptionDebug.getState());
}

async function tapStaff(page, unit, pitch) {
  const point = await page.evaluate(
    ([u, p]) => window.SightSingingTranscriptionDebug.clientPoint(u, p),
    [unit, pitch]
  );
  expect(point).not.toBeNull();
  await page.mouse.move(point.x, point.y);
  await page.mouse.down();
  await page.mouse.up();
}

test.beforeEach(async ({ page }) => {
  await page.goto("/debug/transcription-harness.html");
  await page.waitForSelector(".ss-editor-overlay");
});

test("starts with quarter notes selected and places a note by tapping", async ({
  page,
}) => {
  await expect(page.locator("#transcribe-duration-q")).toHaveClass(
    /ss-tool-active/
  );
  await expect(page.locator("#transcribe-tool-note")).toHaveClass(
    /ss-tool-active/
  );

  await tapStaff(page, 0, "E4");

  const state = await debugState(page);
  expect(state.events).toEqual([
    { kind: "note", pitch: "E4", duration: "q", startUnit: 0 },
  ]);
  await expect(page.locator("#transcribe-status")).toContainText(
    "1 of 4 beats"
  );

  // The engraved score must draw the note at the aimed pitch, not just
  // store it: compare the rendered notehead's y with the pitch reference.
  const rendered = await page.evaluate(() => {
    const dbg = window.SightSingingTranscriptionDebug;
    const heads = Array.from(
      document.querySelectorAll(".ss-editor-score svg .vf-notehead")
    ).map((n) => {
      const r = n.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    });
    const placed = heads.reduce((a, b) => (a && a.x < b.x ? a : b), null);
    return { noteheadY: placed && placed.y, expectedY: dbg.clientPoint(0, "E4").y };
  });
  expect(Math.abs(rendered.noteheadY - rendered.expectedY)).toBeLessThan(3);

  const firstBeatWidth = await page
    .locator(".ss-beat-fill")
    .first()
    .evaluate((el) => el.style.width);
  expect(firstBeatWidth).toBe("100%");
});

test("rest mode places rests using the selected duration", async ({ page }) => {
  await page.locator("#transcribe-duration-8").click();
  await page.locator("#transcribe-tool-rest").click();

  await tapStaff(page, 0, null);

  const state = await debugState(page);
  expect(state.mode).toBe("rest");
  expect(state.events).toEqual([
    { kind: "rest", pitch: null, duration: "8", startUnit: 0 },
  ]);
});

test("erase removes an event and undo restores it", async ({ page }) => {
  await tapStaff(page, 0, "E4");
  await tapStaff(page, 2, "D4");
  expect((await debugState(page)).events).toHaveLength(2);

  await page.locator("#transcribe-tool-erase").click();
  await tapStaff(page, 0, "E4");
  expect((await debugState(page)).events).toHaveLength(1);

  await page.locator("#transcribe-undo").click();
  expect((await debugState(page)).events).toHaveLength(2);
});

test("clicking an occupied slot overwrites without the eraser", async ({
  page,
}) => {
  await tapStaff(page, 0, "E4");
  await tapStaff(page, 0, "G4");
  expect((await debugState(page)).events).toEqual([
    { kind: "note", pitch: "G4", duration: "q", startUnit: 0 },
  ]);

  // A half note painted over units 0-3 replaces everything it overlaps.
  await tapStaff(page, 2, "D4");
  await page.locator("#transcribe-duration-h").click();
  await tapStaff(page, 0, "C4");
  expect((await debugState(page)).events).toEqual([
    { kind: "note", pitch: "C4", duration: "h", startUnit: 0 },
  ]);
});

test("ghost span width is constant per duration and replaced notes dim", async ({
  page,
}) => {
  const hoverAt = async (unit, pitch) => {
    const point = await page.evaluate(
      ([u, p]) => window.SightSingingTranscriptionDebug.clientPoint(u, p),
      [unit, pitch]
    );
    await page.mouse.move(point.x, point.y);
  };
  const spanWidth = () =>
    page
      .locator('[data-ss="ghost-span"]')
      .evaluate((el) => el.getBoundingClientRect().width);

  await page.locator("#transcribe-duration-8").click();
  await hoverAt(0, "G4");
  const widthAtStart = await spanWidth();
  await hoverAt(6, "G4");
  const widthNearEnd = await spanWidth();
  expect(Math.abs(widthAtStart - widthNearEnd)).toBeLessThan(1);

  // Place a quarter, then hover a replacement over it: same eighth span
  // width as before, and the existing note's glyph dims.
  await page.locator("#transcribe-duration-q").click();
  await tapStaff(page, 0, "E4");
  await page.locator("#transcribe-duration-8").click();
  await hoverAt(0, "B4");
  const widthOverOccupied = await spanWidth();
  expect(Math.abs(widthOverOccupied - widthAtStart)).toBeLessThan(1);
  await expect(page.locator(".ss-editor-score .ss-doomed")).toHaveCount(1);

  // Moving to a free slot restores the note.
  await hoverAt(4, "B4");
  await expect(page.locator(".ss-editor-score .ss-doomed")).toHaveCount(0);
});

test("block selection flips right at the visible edge of the highlight box", async ({
  page,
}) => {
  await page.locator("#transcribe-duration-q").click();

  // Aim at the first quarter tile and read the highlight box geometry.
  const start = await page.evaluate(() =>
    window.SightSingingTranscriptionDebug.clientPoint(0, "G4")
  );
  await page.mouse.move(start.x, start.y);
  const box = await page
    .locator('[data-ss="ghost-span"]')
    .evaluate((el) => {
      const r = el.getBoundingClientRect();
      return { left: r.left, right: r.right };
    });

  // Placing a note reports which block was selected; undo to stay clean.
  const placedStartUnit = async (clientX) => {
    await page.mouse.move(clientX, start.y);
    await page.mouse.down();
    await page.mouse.up();
    const startUnit = await page.evaluate(
      () => window.SightSingingTranscriptionDebug.getState().events[0].startUnit
    );
    await page.locator("#transcribe-undo").click();
    return startUnit;
  };

  // Just inside the right edge → still the first block (unit 0).
  expect(await placedStartUnit(box.right - 3)).toBe(0);
  // A few pixels past the visible edge → next block (unit 2).
  expect(await placedStartUnit(box.right + 4)).toBe(2);
});

test("commit uses the last move position, not button-event coordinates", async ({
  page,
}) => {
  // Simulate Anki's Qt webview, where pointerdown/up carry wrong Y coords.
  const events = await page.evaluate(() => {
    const overlay = document.querySelector(".ss-editor-overlay");
    const dbg = window.SightSingingTranscriptionDebug;
    const fire = (type, x, y) =>
      overlay.dispatchEvent(
        new PointerEvent(type, {
          bubbles: true,
          pointerId: 1,
          isPrimary: true,
          clientX: x,
          clientY: y,
        })
      );
    const p = dbg.clientPoint(0, "G4");
    fire("pointermove", p.x, p.y);
    fire("pointerdown", p.x, 9999);
    fire("pointerup", p.x, 9999);
    return dbg.getState().events;
  });
  expect(events).toEqual([
    { kind: "note", pitch: "G4", duration: "q", startUnit: 0 },
  ]);
});

test("full bar reports completion and clear resets it", async ({ page }) => {
  await page.locator("#transcribe-duration-w").click();
  await tapStaff(page, 0, "G4");

  await expect(page.locator("#transcribe-status")).toContainText(
    "All 4 beats filled"
  );

  await page.locator("#transcribe-reset").click();
  expect((await debugState(page)).events).toHaveLength(0);
});

test("multi-bar melody (6 quarters) sizes the grid and accepts notes past bar 1", async ({
  page,
}) => {
  await page.goto("/debug/transcription-harness-multibar.html");
  await page.waitForSelector(".ss-editor-overlay");

  // A 6-quarter phrase is 1.5 bars → the editor lays out 6 beats (not "out of
  // scope"), so the beat bar has 6 cells, not the single-bar 4.
  await expect(page.locator("#transcribe-beatbar .ss-beat")).toHaveCount(6);

  // Place all six, including the two in bar 2 (units 8 and 10).
  const target = [
    [0, "G4"],
    [2, "F4"],
    [4, "G4"],
    [6, "A4"],
    [8, "B4"],
    [10, "C5"],
  ];
  for (const [unit, pitch] of target) {
    await tapStaff(page, unit, pitch);
  }

  const state = await debugState(page);
  expect(state.events).toEqual(
    target.map(([unit, pitch]) => ({
      kind: "note",
      pitch,
      duration: "q",
      startUnit: unit,
    }))
  );
  await expect(page.locator("#transcribe-status")).toContainText(
    "All 6 beats filled"
  );
});

test("bass clef + low range: places notes below the old treble window", async ({
  page,
}) => {
  await page.goto("/debug/transcription-harness-bass.html");
  await page.waitForSelector(".ss-editor-overlay");

  // Bass-clef melody G3-A3-B3-C4 — all below the editor's old fixed C4–C5 treble
  // window. Real mouse events must hit the overlay at these pitches' positions
  // (the vertical-layout regression this guards: low notes fell off the canvas).
  const target = [
    [0, "G3"],
    [2, "A3"],
    [4, "B3"],
    [6, "C4"],
  ];
  for (const [unit, pitch] of target) {
    await tapStaff(page, unit, pitch);
  }
  const state = await debugState(page);
  expect(state.events).toEqual(
    target.map(([unit, pitch]) => ({
      kind: "note",
      pitch,
      duration: "q",
      startUnit: unit,
    }))
  );
});

test("review page compares the saved answer with the target", async ({
  page,
}) => {
  await page.goto("/debug/review-harness.html");
  await page.waitForSelector("#transcribe-result svg");

  await expect(page.locator("#transcribe-result")).toContainText(
    "2 of 3 events match"
  );

  const colors = await page.evaluate(() => {
    const styles = window.getComputedStyle(document.body);
    return {
      good: styles.getPropertyValue("--ss-good").trim(),
      bad: styles.getPropertyValue("--ss-bad").trim(),
    };
  });

  const counts = await page.evaluate(
    ([good, bad]) => ({
      greens: document
        .getElementById("transcribe-user")
        .querySelectorAll('[fill="' + good + '"]').length,
      reds: document
        .getElementById("transcribe-user")
        .querySelectorAll('[fill="' + bad + '"]').length,
      targetSvgs: document
        .getElementById("transcribe-target")
        .querySelectorAll("svg").length,
    }),
    [colors.good, colors.bad]
  );

  expect(counts.greens).toBeGreaterThan(0);
  expect(counts.reds).toBeGreaterThan(0);
  expect(counts.targetSvgs).toBe(1);
});

test("rhythm dictation grades by sounded rhythm (rest spelling + pitch agnostic)", async ({
  page,
}) => {
  // Target: quarter, HALF REST, quarter (B4). Seeded answer spells the half rest
  // as two quarter rests and puts the notes on G4. Exact-match would fail both;
  // the sounded grader must call it perfect.
  await page.goto("/debug/review-harness-rhythm.html");
  await page.waitForSelector("#transcribe-target svg");

  await expect(page.locator("#transcribe-result")).toContainText(
    "Perfect — the rhythm matches"
  );
  const parsedMode = await page.evaluate(
    () => window.SightSingingParseData().gradeMode
  );
  expect(parsedMode).toBe("rhythm");
});
