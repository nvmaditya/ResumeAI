/**
 * Pure client auth/routing decisions.
 * Tested without React — App must call these so invalid session cannot bounce.
 */

export type Route = "login" | "register" | "resumes" | "resume_detail";

export function pathToRoute(pathname: string): Route {
  const p = pathname.replace(/\/+$/, "") || "/";
  if (p === "/register") return "register";
  if (p === "/login") return "login";
  if (/^\/resumes\/[^/]+$/.test(p)) return "resume_detail";
  return "resumes";
}

export function parseResumeId(pathname: string): string | null {
  const p = pathname.replace(/\/+$/, "") || "/";
  const m = p.match(/^\/resumes\/([^/]+)$/);
  return m ? decodeURIComponent(m[1]) : null;
}

export type RouteDecision = {
  pathname: string;
  reason: "stay" | "need_login" | "already_authed";
};

/**
 * Where the client should be given current path + whether a session token exists.
 * After unauthorized/clear: hasSession=false → login page must STAY (not bounce home).
 */
export function resolveClientRoute(input: {
  pathname: string;
  hasSession: boolean;
}): RouteDecision {
  const route = pathToRoute(input.pathname);
  if (!input.hasSession && (route === "resumes" || route === "resume_detail")) {
    return { pathname: "/login", reason: "need_login" };
  }
  if (input.hasSession && (route === "login" || route === "register")) {
    return { pathname: "/", reason: "already_authed" };
  }
  const path = input.pathname.replace(/\/+$/, "") || "/";
  return { pathname: path === "" ? "/" : path, reason: "stay" };
}

/** Result of handling 401 / invalid server session on a protected call. */
export function afterUnauthorizedSession(): {
  hasSession: boolean;
  pathname: string;
  clearStorage: true;
} {
  return { hasSession: false, pathname: "/login", clearStorage: true };
}

/**
 * Full post-401 pipeline: clear session flag then resolve route so UI cannot
 * re-enter home while storage is empty but React state still thought authed.
 */
export function routeAfterUnauthorized(_currentPathname?: string): RouteDecision {
  const cleared = afterUnauthorizedSession();
  return resolveClientRoute({
    pathname: cleared.pathname,
    hasSession: cleared.hasSession,
  });
}
