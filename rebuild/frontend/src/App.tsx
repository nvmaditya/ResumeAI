/**
 * Phase 1–2: auth + resume list/create (structure first).
 * Traps: only the two product create CTAs (no template picker).
 */
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import * as api from "./api";
import type { ResumeListItem } from "./api";
import {
  parseResumeId,
  pathToRoute,
  resolveClientRoute,
  routeAfterUnauthorized,
} from "./authGuard";
import { clearToken, getToken } from "./session";
import { SettingsDrawer } from "./SettingsDrawer";
import { ThemeToggle } from "./ThemeToggle";
import { ToastHost, type ToastMessage } from "./toast";
import { Workspace } from "./Workspace";
import "./index.css";

function navigate(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export default function App() {
  const [path, setPath] = useState(() => window.location.pathname);
  const route = useMemo(() => pathToRoute(path), [path]);
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  useEffect(() => {
    const decision = resolveClientRoute({
      pathname: path,
      hasSession: Boolean(token),
    });
    if (pathToRoute(path) !== pathToRoute(decision.pathname)) {
      navigate(decision.pathname);
      setPath(decision.pathname);
    }
  }, [path, token]);

  // ?settings=1 opens drawer once then cleans URL
  useEffect(() => {
    if (!token) return;
    const sp = new URLSearchParams(window.location.search);
    if (sp.get("settings") === "1") {
      setSettingsOpen(true);
      const url = new URL(window.location.href);
      url.searchParams.delete("settings");
      window.history.replaceState({}, "", url.pathname + url.search);
    }
  }, [token, path]);

  async function onAuthSuccess() {
    setTokenState(getToken());
    navigate("/");
    setPath("/");
  }

  const endSessionToLogin = useCallback(() => {
    clearToken();
    setTokenState(null);
    setSettingsOpen(false);
    const next = routeAfterUnauthorized(path);
    navigate(next.pathname);
    setPath(next.pathname);
  }, [path]);

  async function onLogout() {
    await api.logout();
    endSessionToLogin();
  }

  function go(to: string) {
    navigate(to);
    setPath(to);
  }

  const settingsDrawer = token ? (
    <SettingsDrawer
      open={settingsOpen}
      onClose={() => setSettingsOpen(false)}
      onSessionInvalid={endSessionToLogin}
      onLogout={() => void onLogout()}
    />
  ) : null;

  if (route === "register") {
    return (
      <AuthScreen
        mode="register"
        onSuccess={onAuthSuccess}
        onSwitch={() => go("/login")}
      />
    );
  }

  if (route === "login" || !token) {
    return (
      <AuthScreen
        mode="login"
        onSuccess={onAuthSuccess}
        onSwitch={() => go("/register")}
      />
    );
  }

  if (route === "resume_detail") {
    const id = parseResumeId(path);
    if (!id) {
      go("/");
      return null;
    }
    return (
      <>
        <Workspace
          id={id}
          onBack={() => go("/")}
          onSessionInvalid={endSessionToLogin}
          onDeleted={() => go("/")}
          onOpenSettings={() => setSettingsOpen(true)}
        />
        {settingsDrawer}
      </>
    );
  }

  return (
    <>
      <ResumesHome
        onLogout={onLogout}
        onSessionInvalid={endSessionToLogin}
        onOpen={(id) => go(`/resumes/${id}`)}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      {settingsDrawer}
    </>
  );
}

function AuthScreen({
  mode,
  onSuccess,
  onSwitch,
}: {
  mode: "login" | "register";
  onSuccess: () => void;
  onSwitch: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register" && password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register(email.trim(), password);
      } else {
        await api.login(email.trim(), password);
      }
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell auth">
      <header className="row auth-head">
        <div>
          <h1>ResumeAI</h1>
          <p className="muted">{mode === "register" ? "Create account" : "Sign in"}</p>
        </div>
        <ThemeToggle />
      </header>
      <form onSubmit={onSubmit} className="card">
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password {mode === "register" ? "(≥ 8)" : ""}
          <input
            type="password"
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            required
            minLength={mode === "register" ? 8 : 1}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && (
          <p className="err" role="alert">
            {error}
          </p>
        )}
        <button type="submit" disabled={busy}>
          {busy
            ? mode === "register"
              ? "Creating…"
              : "Signing in…"
            : mode === "register"
              ? "Create account"
              : "Continue"}
        </button>
      </form>
      <p className="muted footer-link">
        {mode === "register" ? (
          <>
            Already have an account?{" "}
            <button type="button" className="link" onClick={onSwitch}>
              Log in
            </button>
          </>
        ) : (
          <>
            Need an account?{" "}
            <button type="button" className="link" onClick={onSwitch}>
              Create one
            </button>
          </>
        )}
      </p>
    </main>
  );
}

function ResumesHome({
  onLogout,
  onSessionInvalid,
  onOpen,
  onOpenSettings,
}: {
  onLogout: () => void;
  onSessionInvalid: () => void;
  onOpen: (id: string) => void;
  onOpenSettings?: () => void;
}) {
  const [items, setItems] = useState<ResumeListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [busyCreate, setBusyCreate] = useState<"ai" | "latex" | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  function showToast(text: string, kind: "ok" | "err" = "ok") {
    setToast({ id: Date.now(), text, kind });
  }

  const load = useCallback(async () => {
    try {
      const list = await api.listResumes({
        q: q.trim() || undefined,
        tags: selectedTags.length ? selectedTags : undefined,
      });
      setItems(list);
      setError(null);
    } catch {
      setError("Session expired");
      onSessionInvalid();
    }
  }, [onSessionInvalid, q, selectedTags]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate(kind: "ai" | "latex") {
    setBusyCreate(kind);
    setStatus(null);
    setError(null);
    try {
      const created = await api.createResume(kind);
      const msg =
        kind === "ai"
          ? "Created resume — fill the form, then Compile for PDF."
          : "Created LaTeX resume.";
      setStatus(msg);
      showToast(msg, "ok");
      onOpen(created.id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Create failed";
      setError(msg);
      showToast(msg, "err");
    } finally {
      setBusyCreate(null);
    }
  }

  async function onDelete(id: string, title: string) {
    if (!window.confirm(`Delete “${title}”? This cannot be undone.`)) return;
    try {
      await api.deleteResume(id);
      setStatus("Deleted.");
      showToast("Deleted.", "ok");
      await load();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      setError(msg);
      showToast(msg, "err");
    }
  }

  function addTagFilter() {
    const t = tagInput.trim().toLowerCase();
    if (!t) return;
    if (!selectedTags.includes(t)) setSelectedTags([...selectedTags, t]);
    setTagInput("");
  }

  function clearFilters() {
    setQ("");
    setSelectedTags([]);
  }

  const allTags = useMemo(() => {
    const s = new Set<string>();
    (items || []).forEach((r) => r.tags.forEach((t) => s.add(t)));
    return [...s].sort();
  }, [items]);

  return (
    <main className="shell wide">
      <header className="row">
        <div>
          <h1>Your resumes</h1>
          <p className="muted">
            {items === null
              ? "Loading…"
              : items.length === 0 && !q && selectedTags.length === 0
                ? "No resumes yet"
                : `${items?.length ?? 0} shown`}
          </p>
        </div>
        <div className="header-actions">
          <ThemeToggle />
          <button
            type="button"
            className="secondary compact"
            onClick={() => onOpenSettings?.()}
          >
            Settings
          </button>
          <button type="button" className="secondary" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>

      <div className="cta-row">
        <button
          type="button"
          disabled={busyCreate !== null}
          onClick={() => void onCreate("ai")}
        >
          {busyCreate === "ai" ? "Creating…" : "New resume"}
        </button>
        <button
          type="button"
          className="secondary"
          disabled={busyCreate !== null}
          onClick={() => void onCreate("latex")}
        >
          {busyCreate === "latex" ? "Creating…" : "New LaTeX"}
        </button>
      </div>

      <div className="filters card">
        <label>
          Search
          <input
            type="search"
            placeholder="Title, track, or tag text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
        <div className="tag-row">
          <input
            type="text"
            placeholder="Add tag filter"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addTagFilter();
              }
            }}
          />
          <button type="button" className="secondary" onClick={addTagFilter}>
            Add tag
          </button>
          {(q || selectedTags.length > 0) && (
            <button type="button" className="link" onClick={clearFilters}>
              Clear filters
            </button>
          )}
        </div>
        {selectedTags.length > 0 && (
          <p className="chips">
            {selectedTags.map((t) => (
              <button
                key={t}
                type="button"
                className="chip"
                onClick={() =>
                  setSelectedTags(selectedTags.filter((x) => x !== t))
                }
              >
                {t} ×
              </button>
            ))}
          </p>
        )}
        {allTags.length > 0 && (
          <p className="muted small">
            Tags in results: {allTags.join(", ")}
          </p>
        )}
      </div>

      {status && <p className="ok">{status}</p>}
      {error && (
        <p className="err" role="alert">
          {error}
        </p>
      )}
      <ToastHost toast={toast} onDismiss={() => setToast(null)} />

      {items && items.length === 0 && (q || selectedTags.length > 0) && (
        <p className="muted">
          No resumes match…{" "}
          <button type="button" className="link" onClick={clearFilters}>
            Clear filters
          </button>
        </p>
      )}

      {items && items.length === 0 && !q && selectedTags.length === 0 && (
        <div className="card empty">
          <p>Create your first resume with one of the buttons above.</p>
          <p className="muted small">
            Exactly two create paths: <strong>New resume</strong> (form) and{" "}
            <strong>New LaTeX</strong>. No template picker.
          </p>
        </div>
      )}

      {items && items.length > 0 && (
        <ul className="resume-list">
          {items.map((r) => (
            <li key={r.id} className="resume-row">
              <button
                type="button"
                className="link title"
                onClick={() => onOpen(r.id)}
              >
                {r.title}
              </button>
              <span className="track-chip">{r.track}</span>
              <span className="muted small tags">
                {r.tags.length ? r.tags.join(", ") : "—"}
              </span>
              <button
                type="button"
                className="secondary danger"
                onClick={() => void onDelete(r.id, r.title)}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
