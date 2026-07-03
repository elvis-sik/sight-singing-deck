import { defineConfig, devices } from "@playwright/test";

// Runs the WebKit-engine checks. WebKit is the same engine AnkiMobile (iOS)
// uses, so this reproduces card-rendering behavior we cannot see in the
// Chromium preview or QtWebEngine (desktop Anki / workbench).
export default defineConfig({
  testDir: "./tests",
  testMatch: /webkit-.*\.spec\.js/,
  globalSetup: "./tests/webkit-global-setup.mjs",
  timeout: 30_000,
  webServer: {
    command: "python3 -m http.server 4173",
    cwd: ".",
    port: 4173,
    reuseExistingServer: true,
  },
  use: {
    baseURL: "http://127.0.0.1:4173",
    ...devices["iPhone 14"],
  },
});
