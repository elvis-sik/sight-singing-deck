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
    "Bar complete"
  );

  await page.locator("#transcribe-reset").click();
  expect((await debugState(page)).events).toHaveLength(0);
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
