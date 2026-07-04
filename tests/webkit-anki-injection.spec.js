import { test, expect } from "@playwright/test";

// WebKit == AnkiMobile's engine. These load the real card HTML through an
// Anki-style injection (innerHTML + re-created <script> nodes that load
// async, out of order) to catch rendering that only breaks on iOS.

async function expectStaff(page, url) {
  await page.goto(url);
  await expect(page.locator("#notation svg, .ss-editor-score svg")).toBeVisible({
    timeout: 8000,
  });
  const paths = await page
    .locator("#notation svg path, .ss-editor-score svg path")
    .count();
  expect(paths).toBeGreaterThan(0);
  // The diagnostic must never appear when rendering succeeds.
  await expect(page.locator(".ss-diag")).toHaveCount(0);
}

test("Sing front renders notation despite out-of-order script loads", async ({
  page,
}) => {
  await expectStaff(page, "/debug/anki-inject-emulation.html?card=sing&side=front");
});

test("Sing back renders notation despite out-of-order script loads", async ({
  page,
}) => {
  await expectStaff(page, "/debug/anki-inject-emulation.html?card=sing&side=back");
});

test("Transcribe front renders the staff editor despite load order", async ({
  page,
}) => {
  await expectStaff(
    page,
    "/debug/anki-inject-emulation.html?card=transcribe&side=front"
  );
});

test("Transcribe back renders the comparison despite load order", async ({
  page,
}) => {
  await page.goto("/debug/anki-inject-emulation.html?card=transcribe&side=back");
  // Target notation always renders on the back; user notation only if an
  // answer was saved (none here), so assert the target staff appears.
  await expect(page.locator("#transcribe-target svg")).toBeVisible({
    timeout: 8000,
  });
  expect(await page.locator("#transcribe-target svg path").count()).toBeGreaterThan(0);
  await expect(page.locator(".ss-diag")).toHaveCount(0);
});
