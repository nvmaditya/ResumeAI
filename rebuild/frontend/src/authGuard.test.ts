/**
 * Drives shipped authGuard helpers — invalid session must land on login
 * without re-entering home (product 01-auth outcomes matrix).
 */
import { describe, expect, it } from "vitest";
import {
  afterUnauthorizedSession,
  pathToRoute,
  resolveClientRoute,
  routeAfterUnauthorized,
} from "./authGuard";

describe("pathToRoute", () => {
  it("maps auth, home, and detail paths", () => {
    expect(pathToRoute("/login")).toBe("login");
    expect(pathToRoute("/register")).toBe("register");
    expect(pathToRoute("/")).toBe("resumes");
    expect(pathToRoute("/resumes")).toBe("resumes");
    expect(pathToRoute("/resumes/abc-123")).toBe("resume_detail");
  });
});

describe("resolveClientRoute", () => {
  it("sends unauthenticated users from home to login", () => {
    const d = resolveClientRoute({ pathname: "/", hasSession: false });
    expect(d.pathname).toBe("/login");
    expect(d.reason).toBe("need_login");
  });

  it("sends authenticated users from login/register to home", () => {
    expect(resolveClientRoute({ pathname: "/login", hasSession: true }).pathname).toBe(
      "/",
    );
    expect(
      resolveClientRoute({ pathname: "/register", hasSession: true }).pathname,
    ).toBe("/");
  });

  it("keeps unauthenticated user on login (no bounce home)", () => {
    const d = resolveClientRoute({ pathname: "/login", hasSession: false });
    expect(d.pathname).toBe("/login");
    expect(d.reason).toBe("stay");
  });

  it("keeps authenticated user on home", () => {
    const d = resolveClientRoute({ pathname: "/", hasSession: true });
    expect(d.pathname).toBe("/");
    expect(d.reason).toBe("stay");
  });
});

describe("routeAfterUnauthorized", () => {
  it("clears session and lands on login without re-entering home", () => {
    const cleared = afterUnauthorizedSession();
    expect(cleared.hasSession).toBe(false);
    expect(cleared.pathname).toBe("/login");
    expect(cleared.clearStorage).toBe(true);

    // Simulate the bounce bug: if hasSession stayed true after 401, login→home.
    // After proper clear, resolveClientRoute must stay on login.
    const stuckAuthedBug = resolveClientRoute({
      pathname: "/login",
      hasSession: true,
    });
    expect(stuckAuthedBug.pathname).toBe("/"); // documents the bug condition

    const fixed = routeAfterUnauthorized("/");
    expect(fixed.pathname).toBe("/login");
    expect(fixed.reason).toBe("stay");

    // Second pass: still no session on login → never re-enter home
    const second = resolveClientRoute({
      pathname: fixed.pathname,
      hasSession: false,
    });
    expect(second.pathname).toBe("/login");
    expect(pathToRoute(second.pathname)).toBe("login");
  });
});
