/**
 * Theme preference — light/dark, localStorage, reduced-motion aware wipe.
 * Product: docs/product/10-settings-github-theme.md
 */

export type Theme = "light" | "dark";

const KEY = "resumeai_theme";

export function getStoredTheme(): Theme | null {
  try {
    const v = localStorage.getItem(KEY);
    if (v === "light" || v === "dark") return v;
  } catch {
    /* private mode */
  }
  return null;
}

export function defaultTheme(): Theme {
  return getStoredTheme() ?? "light";
}

export function setStoredTheme(theme: Theme): void {
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* ignore */
  }
}

export function toggleTheme(current: Theme): Theme {
  return current === "light" ? "dark" : "light";
}

/** When true, skip diagonal wipe and flip tokens instantly. */
export function prefersReducedMotion(
  mq: { matches: boolean } | null = null,
): boolean {
  if (mq) return mq.matches;
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function applyThemeToDocument(theme: Theme, root: HTMLElement = document.documentElement): void {
  root.dataset.theme = theme;
  root.style.colorScheme = theme;
}
