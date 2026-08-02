import { describe, expect, it, beforeEach, vi } from "vitest";
import {
  applyThemeToDocument,
  defaultTheme,
  getStoredTheme,
  prefersReducedMotion,
  setStoredTheme,
  toggleTheme,
} from "./theme";

const mem: Record<string, string> = {};
const mockStorage = {
  getItem: (k: string) => (k in mem ? mem[k] : null),
  setItem: (k: string, v: string) => {
    mem[k] = String(v);
  },
  removeItem: (k: string) => {
    delete mem[k];
  },
  clear: () => {
    for (const k of Object.keys(mem)) delete mem[k];
  },
  key: (_i: number) => null as string | null,
  get length() {
    return Object.keys(mem).length;
  },
};

describe("theme (Phase 9 hard rules)", () => {
  beforeEach(() => {
    mockStorage.clear();
    vi.stubGlobal("localStorage", mockStorage);
  });

  it("defaults to light when nothing stored", () => {
    expect(defaultTheme()).toBe("light");
    expect(getStoredTheme()).toBeNull();
  });

  it("persists and restores theme from localStorage", () => {
    setStoredTheme("dark");
    expect(getStoredTheme()).toBe("dark");
    expect(defaultTheme()).toBe("dark");
  });

  it("toggleTheme flips light ↔ dark", () => {
    expect(toggleTheme("light")).toBe("dark");
    expect(toggleTheme("dark")).toBe("light");
  });

  it("prefersReducedMotion reads media query", () => {
    expect(prefersReducedMotion({ matches: true })).toBe(true);
    expect(prefersReducedMotion({ matches: false })).toBe(false);
  });

  it("applyThemeToDocument sets data-theme and color-scheme", () => {
    const el = {
      dataset: {} as Record<string, string>,
      style: { colorScheme: "" },
    };
    applyThemeToDocument("dark", el as unknown as HTMLElement);
    expect(el.dataset.theme).toBe("dark");
    expect(el.style.colorScheme).toBe("dark");
  });

  it("toggle then apply is synchronous (no artificial delay in pure helpers)", () => {
    const next = toggleTheme("light");
    expect(next).toBe("dark");
    setStoredTheme(next);
    expect(getStoredTheme()).toBe("dark");
    const el = {
      dataset: {} as Record<string, string>,
      style: { colorScheme: "" },
    };
    applyThemeToDocument(next, el as unknown as HTMLElement);
    expect(el.dataset.theme).toBe("dark");
  });
});
