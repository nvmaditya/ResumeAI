/**
 * Settings drawer — GitHub username + cache refresh.
 * Theme toggle lives on app shell (product 10).
 */
import { useCallback, useEffect, useState } from "react";
import * as api from "./api";
import type { UserSettings } from "./api";
import { ToastHost, type ToastMessage } from "./toast";

export function SettingsDrawer({
  open,
  onClose,
  onSessionInvalid,
  onLogout,
}: {
  open: boolean;
  onClose: () => void;
  onSessionInvalid: () => void;
  onLogout: () => void;
}) {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [username, setUsername] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  function showToast(text: string, kind: "ok" | "err" = "ok") {
    setToast({ id: Date.now(), text, kind });
  }

  const load = useCallback(async () => {
    try {
      const s = await api.getSettings();
      setSettings(s);
      setUsername(s.github_username || "");
      setError(null);
    } catch {
      onSessionInvalid();
    }
  }, [onSessionInvalid]);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  async function onSave() {
    setBusy(true);
    setStatus(null);
    setError(null);
    try {
      const s = await api.saveSettings({ github_username: username.trim() });
      setSettings(s);
      setStatus("GitHub username saved");
      showToast("GitHub username saved", "ok");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Save failed";
      setError(msg);
      showToast(msg, "err");
    } finally {
      setBusy(false);
    }
  }

  async function onUpdateCache() {
    setBusy(true);
    setStatus(null);
    setError(null);
    try {
      if (username.trim() && username.trim() !== (settings?.github_username || "")) {
        await api.saveSettings({ github_username: username.trim() });
      }
      const s = await api.updateGithubCache();
      setSettings(s);
      setUsername(s.github_username || username);
      const msg = s.cache_status || "GitHub cache updated";
      setStatus(msg);
      showToast(msg, "ok");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Update failed";
      setError(msg);
      showToast(msg, "err");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="settings-overlay" role="presentation" onClick={onClose}>
      <aside
        className="settings-drawer"
        role="dialog"
        aria-label="Settings"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="settings-head">
          <h2>Settings</h2>
          <button type="button" className="secondary compact" onClick={onClose}>
            ✕
          </button>
        </div>

        <section className="settings-block">
          <h3>Account</h3>
          <p className="muted small">
            {settings?.email || "—"}
          </p>
          <p className="muted small">
            Contact links live on each resume form, not here.
          </p>
        </section>

        <section className="settings-block">
          <h3>GitHub (for scoring)</h3>
          <label>
            GitHub username
            <input
              value={username}
              placeholder="octocat"
              autoComplete="off"
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <div className="settings-actions">
            <button
              type="button"
              className="secondary compact"
              disabled={busy}
              onClick={() => void onSave()}
            >
              Save username
            </button>
            <button
              type="button"
              className="secondary compact"
              disabled={busy || !username.trim()}
              onClick={() => void onUpdateCache()}
            >
              Update GitHub data
            </button>
          </div>
          <p
            className={
              settings?.github_cache ? "ok small" : "muted small"
            }
          >
            {settings?.cache_status ||
              "No GitHub cache yet — Update GitHub data in Settings."}
          </p>
        </section>

        {status && <p className="ok small">{status}</p>}
        {error && (
          <p className="err small" role="alert">
            {error}
          </p>
        )}

        <section className="settings-block">
          <button type="button" className="secondary danger" onClick={onLogout}>
            Log out
          </button>
        </section>
      </aside>
      <ToastHost toast={toast} onDismiss={() => setToast(null)} />
    </div>
  );
}
