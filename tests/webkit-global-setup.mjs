import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";

// Regenerate the card HTML fixtures from the live templates before the WebKit
// suite runs, so the injection emulation always tests current output.
export default function globalSetup() {
  const python = existsSync(".venv/bin/python") ? ".venv/bin/python" : "python3";
  execFileSync(python, ["scripts/dump_card_fixtures.py"], { stdio: "inherit" });
}
