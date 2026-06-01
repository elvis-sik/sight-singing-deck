import { test, expect } from "@playwright/test";

test("empty bar starts as one whole interval and zones follow selected duration", async ({
  page,
}) => {
  await page.goto("/debug/transcription-harness.html");

  const eighthButton = page.locator("#transcribe-duration-8");
  const quarterButton = page.locator("#transcribe-duration-q");
  const wholeButton = page.locator("#transcribe-duration-w");

  await expect(wholeButton).toHaveClass(/ss-tool-active/);
  await expect(page.locator(".ss-transcribe-gap")).toHaveCount(1);
  await expect(page.locator(".ss-transcribe-gap-label")).toHaveText(["w"]);
  await expect(page.locator(".ss-transcribe-hit")).toHaveCount(1);

  await eighthButton.click();

  await expect(eighthButton).toHaveClass(/ss-tool-active/);
  await expect(wholeButton).not.toHaveClass(/ss-tool-active/);
  await expect(page.locator(".ss-transcribe-hit")).toHaveCount(8);
  await expect(page.locator(".ss-transcribe-hit-valid")).toHaveCount(8);

  await page
    .locator('.ss-transcribe-hit[data-start-unit="0"]')
    .click({ position: { x: 10, y: 60 } });

  await expect(page.locator(".ss-transcribe-note-8")).toHaveCount(1);

  await quarterButton.click();

  await expect(quarterButton).toHaveClass(/ss-tool-active/);
  await expect(page.locator(".ss-transcribe-gap-label")).toHaveText(["8", "q", "h"]);
  await expect(page.locator(".ss-transcribe-hit")).toHaveCount(4);
  await expect(page.locator(".ss-transcribe-hit-valid")).toHaveCount(3);
  await expect(page.locator(".ss-transcribe-hit-invalid")).toHaveCount(1);
});

test("rest mode uses selected duration", async ({ page }) => {
  await page.goto("/debug/transcription-harness.html");

  await page.locator("#transcribe-tool-rest").click();
  await page.locator("#transcribe-duration-8").click();
  await page.locator('.ss-transcribe-hit[data-start-unit="0"]').click();

  await expect(page.locator(".ss-transcribe-rest-8")).toHaveCount(1);
  await expect(page.locator(".ss-transcribe-duration-tag")).toHaveText("8");
});
