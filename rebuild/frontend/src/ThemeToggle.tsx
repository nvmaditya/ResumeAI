/**
 * Light/Dark control + optional diagonal wipe (product 10-settings-github-theme).
 */
import { useCallback, useEffect, useState } from "react";
import {
  applyThemeToDocument,
  defaultTheme,
  prefersReducedMotion,
  setStoredTheme,
  toggleTheme,
  type Theme,
} from "./theme";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useState<Theme>(() => defaultTheme());
  const [wiping, setWiping] = useState(false);

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  const onToggle = useCallback(() => {
    if (wiping) return;
    const next = toggleTheme(theme);
    // Product: token flip same tick (editor/chrome); wipe is cosmetic only
    setStoredTheme(next);
    setTheme(next);
    applyThemeToDocument(next);
    if (prefersReducedMotion()) return;
    setWiping(true);
    window.setTimeout(() => setWiping(false), 520);
  }, [theme, wiping]);

  return (
    <>
      <button
        type="button"
        className={`theme-toggle secondary compact ${className}`.trim()}
        onClick={onToggle}
        disabled={wiping}
        aria-label={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
        title={theme === "light" ? "Dark" : "Light"}
      >
        {theme === "light" ? "Dark" : "Light"}
      </button>
      {wiping && (
        <div
          className="theme-wipe"
          aria-hidden
          data-to={theme === "light" ? "dark" : "light"}
        />
      )}
    </>
  );
}

/** Call once on boot so first paint matches stored preference. */
export function bootTheme(): void {
  applyThemeToDocument(defaultTheme());
}
