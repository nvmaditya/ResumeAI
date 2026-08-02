import { describe, expect, it } from "vitest";
import { chromeFromResume, workspaceModeForTrack } from "./workspaceMode";

describe("workspaceModeForTrack", () => {
  it("structured is FORM_PATH: form only, no Lint, no Source", () => {
    const c = workspaceModeForTrack("structured");
    expect(c.mode).toBe("FORM_PATH");
    expect(c.showFormTab).toBe(true);
    expect(c.showSourceEditor).toBe(false);
    expect(c.showLint).toBe(false);
  });

  it("latex is LATEX_ONLY: source + Lint, no Form", () => {
    const c = workspaceModeForTrack("latex");
    expect(c.mode).toBe("LATEX_ONLY");
    expect(c.showFormTab).toBe(false);
    expect(c.showSourceEditor).toBe(true);
    expect(c.showLint).toBe(true);
  });

  it("chromeFromResume follows track only", () => {
    const c = chromeFromResume({ track: "latex" });
    expect(c.showFormTab).toBe(false);
    expect(c.showSourceEditor).toBe(true);
  });
});
