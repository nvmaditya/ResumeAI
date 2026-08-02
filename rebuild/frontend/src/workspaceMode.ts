/**
 * Pure workspace mode from track (form-path pivot).
 * FORM_PATH: form only — no Source, no Lint.
 * LATEX_ONLY: source + Lint.
 */

export type WorkspaceMode = "FORM_PATH" | "LATEX_ONLY";

export type WorkspaceChrome = {
  mode: WorkspaceMode;
  showFormTab: boolean;
  showSourceEditor: boolean;
  showLint: boolean;
};

export function workspaceModeForTrack(track: string): WorkspaceChrome {
  const t = (track || "").trim().toLowerCase();
  if (t === "latex") {
    return {
      mode: "LATEX_ONLY",
      showFormTab: false,
      showSourceEditor: true,
      showLint: true,
    };
  }
  return {
    mode: "FORM_PATH",
    showFormTab: true,
    showSourceEditor: false,
    showLint: false,
  };
}

export function chromeFromResume(r: { track: string }): WorkspaceChrome {
  return workspaceModeForTrack(r.track);
}
