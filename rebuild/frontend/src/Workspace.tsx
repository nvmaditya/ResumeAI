/**
 * Per-resume workspace shell.
 * FORM_PATH: form only; Compile = form→PDF; no generate CTA; no Lint.
 * LATEX_ONLY: source + Lint; no Form.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import * as api from "./api";
import type {
  Checkpoint,
  Diagnostic,
  JobStatus,
  ResumeDetail,
  ScoreResult,
} from "./api";
import {
  emptyForm,
  normalizeForm,
  type FormSectionKey,
  type ResumeForm,
} from "./emptyForm";
import { ThemeToggle } from "./ThemeToggle";
import { ToastHost, type ToastMessage } from "./toast";
import { chromeFromResume } from "./workspaceMode";

type EditorTab = "form" | "source";

function formatCheckpointTime(iso: string): string {
  try {
    const d = new Date(iso.includes("T") ? iso : iso.replace(" ", "T") + "Z");
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function Workspace({
  id,
  onBack,
  onSessionInvalid,
  onDeleted,
  onOpenSettings,
}: {
  id: string;
  onBack: () => void;
  onSessionInvalid: () => void;
  onDeleted?: () => void;
  onOpenSettings?: () => void;
}) {
  const [doc, setDoc] = useState<ResumeDetail | null>(null);
  const [title, setTitle] = useState("");
  const [tagsText, setTagsText] = useState("");
  const [form, setForm] = useState<ResumeForm>(emptyForm());
  const [latex, setLatex] = useState("");
  const [tab, setTab] = useState<EditorTab>("form");
  const [dirty, setDirty] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [engine, setEngine] = useState<string | null>(null);
  const [compiling, setCompiling] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfBusy, setPdfBusy] = useState(false);
  // PR3: presentation-only UI state — not a backend field
  const [pdfStale, setPdfStale] = useState(false);
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [commitMsg, setCommitMsg] = useState("");
  const [versionBusy, setVersionBusy] = useState(false);
  const [scoreJob, setScoreJob] = useState<JobStatus | null>(null);
  const [scoreResult, setScoreResult] = useState<ScoreResult | null>(null);
  const [scoreBusy, setScoreBusy] = useState(false);
  const [scoreHadComplete, setScoreHadComplete] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);

  function showToast(text: string, kind: "ok" | "err" = "ok") {
    setToast({ id: Date.now(), text, kind });
  }

  const chrome = useMemo(
    () => (doc ? chromeFromResume(doc) : null),
    [doc],
  );

  const loadVersions = useCallback(async () => {
    try {
      const rows = await api.listVersions(id);
      setCheckpoints(rows);
    } catch {
      /* list failure surfaces on next commit attempt */
    }
  }, [id]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.getResume(id);
      setDoc(r);
      setTitle(r.title);
      setTagsText((r.tags || []).join(", "));
      setForm(normalizeForm(r.form));
      setLatex(r.latex_source || "");
      const c = chromeFromResume(r);
      setTab(c.showFormTab ? "form" : "source");
      setDirty(false);
      await loadVersions();
    } catch {
      setError("Could not load resume");
      onSessionInvalid();
    } finally {
      setLoading(false);
    }
  }, [id, onSessionInvalid, loadVersions]);

  useEffect(() => {
    void load();
  }, [load]);

  // LATEX_ONLY: never stay on form tab
  useEffect(() => {
    if (chrome && !chrome.showFormTab && tab === "form") {
      setTab("source");
    }
  }, [chrome, tab]);

  // Revoke blob URL on change/unmount (iframe + blob preview; no pdf.js)
  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

  function markDirty() {
    setDirty(true);
    // If a preview blob already exists, edits invalidate it until next successful compile
    if (pdfUrl) setPdfStale(true);
  }

  async function persistIfNeeded(): Promise<boolean> {
    if (!doc) return false;
    if (!dirty) return true;
    const tags = tagsText
      .split(/[,;]/)
      .map((t) => t.trim())
      .filter(Boolean);
    const body: Parameters<typeof api.patchResume>[1] = {
      title,
      tags,
      form: chrome?.showFormTab ? form : undefined,
      latex_source: latex,
    };
    const saved = await api.patchResume(id, body);
    setDoc(saved);
    setDirty(false);
    return true;
  }

  async function onSave() {
    if (!doc) return;
    setSaving(true);
    setStatus(null);
    setError(null);
    try {
      await persistIfNeeded();
      setStatus("Saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function refreshPdfPreview() {
    setPdfBusy(true);
    try {
      const blob = await api.fetchPdfBlob(id);
      const url = URL.createObjectURL(blob);
      setPdfUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return url;
      });
    } catch {
      // no PDF yet
    } finally {
      setPdfBusy(false);
    }
  }

  async function onCompile() {
    if (!doc) return;
    setCompiling(true);
    setStatus(null);
    setError(null);
    setPdfBusy(true);
    try {
      await persistIfNeeded();
      const result = await api.compileResume(id);
      setEngine(result.engine);
      // Form path: reload so latex_source snapshot (for .tex) is current; stay on form
      const refreshed = await api.getResume(id);
      setDoc(refreshed);
      setForm(normalizeForm(refreshed.form));
      setLatex(refreshed.latex_source || "");
      setDirty(false);
      setPdfStale(false);
      if (chromeFromResume(refreshed).showFormTab) {
        setTab("form");
        setStatus(
          result.engine === "tectonic"
            ? "PDF ready — form still editable"
            : "Preview ready (layout) — form still editable",
        );
      } else {
        setStatus(
          result.engine === "tectonic"
            ? "TeX ready (tectonic)"
            : "Preview ready (layout engine)",
        );
      }
      await refreshPdfPreview();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compile failed");
      setPdfBusy(false);
    } finally {
      setCompiling(false);
    }
  }

  async function onLint() {
    if (!doc || !chrome?.showLint) return;
    try {
      await persistIfNeeded();
      const r = await api.lintResume(id);
      setDiagnostics(r.diagnostics);
      setStatus(
        r.count === 0 ? "No lint issues" : `${r.count} lint issue(s)`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lint failed");
    }
  }

  async function onDownloadPdf() {
    try {
      await persistIfNeeded();
      try {
        await api.downloadFile(id, "pdf");
      } catch {
        await api.compileResume(id);
        await api.downloadFile(id, "pdf");
        await refreshPdfPreview();
      }
      setStatus("PDF download started");
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF download failed");
    }
  }

  async function onDownloadTex() {
    try {
      await persistIfNeeded();
      await api.downloadFile(id, "tex");
      setStatus(".tex download started");
    } catch (err) {
      setError(err instanceof Error ? err.message : ".tex download failed");
    }
  }

  // Debounced auto-preview after source edits (when we already have compiled once)
  useEffect(() => {
    if (!engine || dirty === false) return;
    if (tab === "form" && !latex.trim()) return;
    const t = window.setTimeout(() => {
      void (async () => {
        try {
          await persistIfNeeded();
          await api.compileResume(id);
          await refreshPdfPreview();
        } catch {
          /* ignore auto-preview errors */
        }
      })();
    }, 1200);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- deliberate debounce on latex/form dirty
  }, [latex, dirty, engine, id, tab]);

  async function onDelete() {
    if (!doc) return;
    if (!window.confirm(`Delete “${doc.title}”? This cannot be undone.`)) return;
    try {
      await api.deleteResume(id);
      onDeleted?.();
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function onCheckScore() {
    if (!doc) return;
    setScoreBusy(true);
    setStatus(null);
    setError(null);
    setScoreJob({ job_id: "", status: "queued" });
    try {
      await persistIfNeeded();
      const started = await api.startScore(id);
      setScoreJob(started);
      if (started.status === "complete" && started.result) {
        setScoreResult(started.result);
        setScoreHadComplete(true);
        const msg = `Score ${started.result.overall}/100`;
        setStatus(msg);
        showToast(msg, "ok");
        setScoreBusy(false);
        return;
      }
      const jid = started.job_id || started.id || "";
      const deadline = Date.now() + 45_000;
      let last: JobStatus = started;
      while (Date.now() < deadline) {
        last = await api.getJob(jid);
        setScoreJob(last);
        if (last.status === "complete") {
          setScoreResult(last.result || null);
          setScoreHadComplete(true);
          const msg = last.result
            ? `Score ${last.result.overall}/100`
            : "Score complete";
          setStatus(msg);
          showToast(msg, "ok");
          break;
        }
        if (last.status === "failed") {
          const msg = last.error || "Score failed";
          setError(msg);
          showToast(msg, "err");
          break;
        }
        await new Promise((r) => setTimeout(r, 200));
      }
      if (last.status !== "complete" && last.status !== "failed") {
        const msg = "Score timed out — try again";
        setError(msg);
        showToast(msg, "err");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Score failed";
      setError(msg);
      showToast(msg, "err");
    } finally {
      setScoreBusy(false);
    }
  }

  async function onCommitVersion() {
    if (!doc) return;
    setVersionBusy(true);
    setStatus(null);
    setError(null);
    try {
      // Product: auto-save dirty first so snapshot matches editor
      await persistIfNeeded();
      const result = await api.commitVersion(id, commitMsg.trim() || undefined);
      if (result.unchanged || !result.committed) {
        const msg = result.message || "No changes since last commit";
        setStatus(msg);
        showToast(msg, "ok");
      } else {
        const msg = result.message || "Version saved";
        setStatus(msg);
        showToast(msg, "ok");
        setCommitMsg("");
        await loadVersions();
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Commit failed";
      setError(msg);
      showToast(msg, "err");
    } finally {
      setVersionBusy(false);
    }
  }

  async function onRestoreVersion(cp: Checkpoint) {
    if (!doc) return;
    if (
      !window.confirm(
        `Restore “${cp.message}” (${formatCheckpointTime(cp.created_at)})? Live LaTeX will be replaced.`,
      )
    ) {
      return;
    }
    setVersionBusy(true);
    setStatus(null);
    setError(null);
    try {
      const result = await api.restoreVersion(id, cp.id);
      setDoc(result);
      setTitle(result.title);
      setTagsText((result.tags || []).join(", "));
      setForm(normalizeForm(result.form));
      setLatex(result.latex_source || "");
      // Restore is LaTeX-centric; only switch editor if source path
      setTab(chromeFromResume(result).showSourceEditor ? "source" : "form");
      setDirty(false);
      const msg = result.message || "Restored";
      setStatus(msg);
      showToast(msg, "ok");
      if (result.compile_engine) setEngine(result.compile_engine);
      try {
        await refreshPdfPreview();
      } catch {
        /* quiet recompile optional */
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Restore failed";
      setError(msg);
      showToast(msg, "err");
    } finally {
      setVersionBusy(false);
    }
  }

  async function onDeleteVersion(cp: Checkpoint) {
    if (!doc) return;
    if (
      !window.confirm(
        `Delete checkpoint “${cp.message}”? The resume itself is kept.`,
      )
    ) {
      return;
    }
    setVersionBusy(true);
    setStatus(null);
    setError(null);
    try {
      await api.deleteVersion(id, cp.id);
      setStatus("Checkpoint deleted");
      showToast("Checkpoint deleted", "ok");
      await loadVersions();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Delete checkpoint failed";
      setError(msg);
      showToast(msg, "err");
    } finally {
      setVersionBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="workspace">
        <p className="muted">Loading resume…</p>
      </main>
    );
  }

  if (error && !doc) {
    return (
      <main className="workspace">
        <p className="err">{error}</p>
        <button type="button" className="link" onClick={onBack}>
          ← Resumes
        </button>
      </main>
    );
  }

  if (!doc || !chrome) return null;

  return (
    <main className="workspace">
      {/* Tier 1 — identity */}
      <div className="identity-row">
        <button type="button" className="link" onClick={onBack}>
          ← Resumes
        </button>
        <button
          type="button"
          className="secondary compact"
          onClick={() => onOpenSettings?.()}
        >
          Settings
        </button>
        <ThemeToggle />
        <input
          className="title-input"
          value={title}
          aria-label="Resume title"
          onChange={(e) => {
            setTitle(e.target.value);
            markDirty();
          }}
        />
        <span className="track-chip" title="Track">
          {doc.track}
        </span>
        <span className="engine-chip" title="Compile engine">
          {engine || "—"}
        </span>
        <span className={dirty ? "dirty-chip" : "saved-chip"}>
          {dirty ? "Unsaved" : "Saved"}
        </span>
        <input
          className="tags-input"
          value={tagsText}
          aria-label="Tags"
          placeholder="tags (comma-separated)"
          onChange={(e) => {
            setTagsText(e.target.value);
            markDirty();
          }}
        />
      </div>

      {/* Tier 2 — File | Build | Score | Danger */}
      <div className="toolbar" role="toolbar" aria-label="Workspace actions">
        <div className="toolbar-group" data-group="File">
          <span className="group-label">File</span>
          <button
            type="button"
            className={dirty ? undefined : "secondary"}
            disabled={saving}
            onClick={() => void onSave()}
          >
            {saving ? "Saving…" : "Save"}
          </button>
          <button
            type="button"
            className="secondary"
            disabled={!latex.trim()}
            title={
              latex.trim()
                ? "Download last compile LaTeX snapshot"
                : "Compile first to produce a .tex snapshot"
            }
            onClick={() => void onDownloadTex()}
          >
            .tex
          </button>
        </div>
        <div className="toolbar-group" data-group="Build">
          <span className="group-label">Build</span>
          <button
            type="button"
            className={!dirty && (!pdfUrl || pdfStale) ? undefined : "secondary"}
            disabled={compiling}
            onClick={() => void onCompile()}
          >
            {compiling ? "Compiling…" : "Compile"}
          </button>
          {chrome.showLint && (
            <button
              type="button"
              className="secondary"
              onClick={() => void onLint()}
            >
              Lint
            </button>
          )}
          <button
            type="button"
            className="secondary"
            onClick={() => void onDownloadPdf()}
          >
            PDF
          </button>
        </div>
        <div className="toolbar-group" data-group="Score">
          <span className="group-label">Score</span>
          <button
            type="button"
            className="secondary"
            disabled={scoreBusy}
            onClick={() => void onCheckScore()}
          >
            {scoreBusy
              ? "Scoring…"
              : scoreHadComplete
                ? "Re-check score"
                : "Check score"}
          </button>
        </div>
        <div className="toolbar-group" data-group="Danger">
          <span className="group-label">Danger</span>
          <button type="button" className="secondary danger" onClick={() => void onDelete()}>
            Delete
          </button>
        </div>
      </div>

      {status && <p className="status-line ok">{status}</p>}
      {error && (
        <p className="status-line err" role="alert">
          {error}
        </p>
      )}
      <ToastHost toast={toast} onDismiss={() => setToast(null)} />

      {/* rail · editor · PDF */}
      <div className="workspace-grid">
        <aside className="rail" aria-label="Left rail">
          <section className="versions-panel" aria-label="Versions">
            <h3>Versions</h3>
            <div className="version-commit-row">
              <input
                type="text"
                className="version-message"
                placeholder="checkpoint"
                maxLength={200}
                value={commitMsg}
                disabled={versionBusy}
                aria-label="Commit message"
                onChange={(e) => setCommitMsg(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void onCommitVersion();
                  }
                }}
              />
              <button
                type="button"
                className="secondary compact"
                disabled={versionBusy}
                onClick={() => void onCommitVersion()}
              >
                Commit
              </button>
            </div>
            {checkpoints.length === 0 ? (
              <p className="muted small">No checkpoints yet.</p>
            ) : (
              <ul className="version-list">
                {checkpoints.map((cp) => (
                  <li key={cp.id} className="version-row">
                    <div className="version-meta">
                      <strong className="version-msg">{cp.message}</strong>
                      <span className="muted small version-time">
                        {formatCheckpointTime(cp.created_at)}
                      </span>
                    </div>
                    <div className="version-actions">
                      <button
                        type="button"
                        className="link"
                        disabled={versionBusy}
                        onClick={() => void onRestoreVersion(cp)}
                      >
                        Restore
                      </button>
                      <button
                        type="button"
                        className="link danger"
                        disabled={versionBusy}
                        onClick={() => void onDeleteVersion(cp)}
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
          {chrome.showLint && (
            <section>
              <h3>Diagnostics</h3>
              {diagnostics.length === 0 ? (
                <p className="muted small">Run Lint for issues and fix hints.</p>
              ) : (
                <ul className="diag-list">
                  {diagnostics.map((d, i) => (
                    <li key={i}>
                      <button
                        type="button"
                        className="link diag-item"
                        onClick={() => {
                          if (d.line) {
                            setStatus(`Jump to line ${d.line}`);
                          }
                        }}
                      >
                        <strong>{d.severity}</strong>
                        {d.line != null ? ` L${d.line}: ` : ": "}
                        {d.message}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
          <section className="score-rail" aria-label="ATS score">
            <h3>ATS score</h3>
            <ol className="score-stepper" aria-label="Score job stepper">
              {(
                [
                  ["queued", "Queued"],
                  ["processing", "Processing"],
                  ["complete", "Complete"],
                ] as const
              ).map(([key, label]) => {
                const st = scoreJob?.status;
                const failed = st === "failed";
                const active =
                  st === key ||
                  (key === "complete" && st === "complete") ||
                  (key === "processing" && st === "processing") ||
                  (key === "queued" && (st === "queued" || st === "processing" || st === "complete"));
                const done =
                  (key === "queued" &&
                    (st === "processing" || st === "complete")) ||
                  (key === "processing" && st === "complete") ||
                  (key === "complete" && st === "complete");
                return (
                  <li
                    key={key}
                    className={[
                      "score-step",
                      done ? "done" : "",
                      active && !done ? "active" : "",
                      failed && key === "complete" ? "failed" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    {failed && key === "complete" ? "Failed" : label}
                  </li>
                );
              })}
            </ol>
            {!scoreJob && !scoreResult && (
              <p className="muted small">
                Manual Check score only — never auto after edits.
              </p>
            )}
            {scoreBusy && (
              <p className="muted small">Scoring…</p>
            )}
            {scoreJob?.status === "failed" && (
              <p className="err small">{scoreJob.error || "Score failed"}</p>
            )}
            {scoreResult && (
              <div className="score-result">
                <p className="score-overall">
                  <strong>{scoreResult.overall}</strong>
                  <span className="muted"> /100</span>
                </p>
                <ul className="score-cats">
                  {(scoreResult.categories || []).map((c) => (
                    <li key={c.name}>
                      <strong>
                        {c.name}: {c.score}
                      </strong>
                      <span className="muted small"> — {c.evidence}</span>
                    </li>
                  ))}
                </ul>
                {scoreResult.github_enriched === false && (
                  <p className="muted small">
                    Weak GitHub signal — open Settings → Update GitHub data.
                  </p>
                )}
              </div>
            )}
          </section>
        </aside>

        <section className="editor" aria-label="Editor">
          {chrome.showFormTab ? (
            <div className="editor-tabs">
              <span className="tab active static">Form</span>
            </div>
          ) : (
            <div className="editor-tabs">
              <span className="tab active static">LaTeX source</span>
            </div>
          )}

          {chrome.showFormTab ? (
            <StructuredForm
              form={form}
              onChange={(next) => {
                setForm(next);
                markDirty();
              }}
            />
          ) : (
            <LatexSourceEditor
              value={latex}
              onChange={(next) => {
                setLatex(next);
                markDirty();
              }}
            />
          )}
        </section>

        <aside className="pdf-pane" aria-label="PDF preview">
          <h3>PDF</h3>
          {pdfBusy && <p className="muted small">Updating…</p>}
          {!pdfBusy && !pdfUrl && (
            <p className="muted small">
              Click <strong>Compile</strong> for iframe preview (blob URL; no
              pdf.js).
            </p>
          )}
          {pdfUrl && pdfStale && !pdfBusy && (
            <p className="muted small">Preview may be outdated — Compile to refresh.</p>
          )}
          {pdfUrl && (
            <iframe
              className="pdf-frame"
              title="Resume PDF preview"
              src={pdfUrl}
            />
          )}
        </aside>
      </div>
    </main>
  );
}

/** Dark LaTeX editor: plain soft-wrap monospace (no dual-layer highlight). */
function LatexSourceEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="source-editor-shell">
      <textarea
        className="source-editor"
        aria-label="LaTeX source"
        value={value}
        spellCheck={false}
        wrap="soft"
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

const SECTION_LABELS: Record<FormSectionKey, string> = {
  experience: "Work",
  education: "Education",
  projects: "Projects",
  skills: "Skills",
};

function reorderList<T>(items: T[], from: number, to: number): T[] {
  if (from === to || from < 0 || to < 0 || from >= items.length || to >= items.length) {
    return items;
  }
  const next = items.slice();
  const [row] = next.splice(from, 1);
  next.splice(to, 0, row);
  return next;
}

function MoveButtons({
  index,
  total,
  onMove,
  label,
}: {
  index: number;
  total: number;
  onMove: (from: number, to: number) => void;
  label: string;
}) {
  return (
    <span className="move-btns">
      <button
        type="button"
        className="secondary compact"
        disabled={index <= 0}
        title={`Move ${label} up`}
        aria-label={`Move ${label} up`}
        onClick={() => onMove(index, index - 1)}
      >
        ↑
      </button>
      <button
        type="button"
        className="secondary compact"
        disabled={index >= total - 1}
        title={`Move ${label} down`}
        aria-label={`Move ${label} down`}
        onClick={() => onMove(index, index + 1)}
      >
        ↓
      </button>
    </span>
  );
}

function StructuredForm({
  form,
  onChange,
}: {
  form: ResumeForm;
  onChange: (f: ResumeForm) => void;
}) {
  const b = form.basics;
  const order = form.section_order;

  function setBasics(patch: Partial<ResumeForm["basics"]>) {
    onChange({ ...form, basics: { ...form.basics, ...patch } });
  }

  function moveSection(from: number, to: number) {
    onChange({
      ...form,
      section_order: reorderList(order, from, to),
    });
  }

  function renderBodySection(key: FormSectionKey, index: number) {
    const head = (
      <MoveButtons
        index={index}
        total={order.length}
        onMove={moveSection}
        label={`${SECTION_LABELS[key]} section`}
      />
    );

    if (key === "experience") {
      return (
        <ListSection
          key={key}
          title="Work"
          sectionMove={head}
          items={form.experience}
          onChange={(experience) => onChange({ ...form, experience })}
          blank={() => ({
            company: "",
            position: "",
            dates: "",
            summary: "",
          })}
          render={(item, _i, update) => (
            <div className="field-grid">
              <label>
                Company
                <input
                  value={item.company}
                  onChange={(e) => update({ ...item, company: e.target.value })}
                />
              </label>
              <label>
                Position
                <input
                  value={item.position}
                  onChange={(e) =>
                    update({ ...item, position: e.target.value })
                  }
                />
              </label>
              <label className="span-2">
                Dates
                <input
                  value={item.dates}
                  onChange={(e) => update({ ...item, dates: e.target.value })}
                />
              </label>
              <label className="span-2">
                Summary
                <input
                  value={item.summary}
                  onChange={(e) => update({ ...item, summary: e.target.value })}
                />
              </label>
            </div>
          )}
        />
      );
    }

    if (key === "education") {
      return (
        <ListSection
          key={key}
          title="Education"
          sectionMove={head}
          items={form.education}
          onChange={(education) => onChange({ ...form, education })}
          blank={() => ({
            institution: "",
            area: "",
            degree: "",
            dates: "",
          })}
          render={(item, _i, update) => (
            <div className="field-grid">
              <label>
                Institution
                <input
                  value={item.institution}
                  onChange={(e) =>
                    update({ ...item, institution: e.target.value })
                  }
                />
              </label>
              <label>
                Area
                <input
                  value={item.area}
                  onChange={(e) => update({ ...item, area: e.target.value })}
                />
              </label>
              <label>
                Degree
                <input
                  value={item.degree}
                  onChange={(e) => update({ ...item, degree: e.target.value })}
                />
              </label>
              <label>
                Dates
                <input
                  value={item.dates}
                  onChange={(e) => update({ ...item, dates: e.target.value })}
                />
              </label>
            </div>
          )}
        />
      );
    }

    if (key === "skills") {
      return (
        <ListSection
          key={key}
          title="Skills"
          sectionMove={head}
          items={form.skills}
          onChange={(skills) => onChange({ ...form, skills })}
          blank={() => ({ name: "", keywords: "" })}
          render={(item, _i, update) => (
            <div className="field-grid">
              <label>
                Name
                <input
                  value={item.name}
                  onChange={(e) => update({ ...item, name: e.target.value })}
                />
              </label>
              <label>
                Keywords
                <input
                  value={item.keywords}
                  placeholder="comma-separated"
                  onChange={(e) =>
                    update({ ...item, keywords: e.target.value })
                  }
                />
              </label>
            </div>
          )}
        />
      );
    }

    return (
      <ListSection
        key={key}
        title="Projects"
        sectionMove={head}
        items={form.projects}
        onChange={(projects) => onChange({ ...form, projects })}
        blank={() => ({
          name: "",
          description: "",
          url: "",
          highlights: [],
        })}
        render={(item, _i, update) => (
          <div className="field-grid">
            <label>
              Name
              <input
                value={item.name}
                onChange={(e) => update({ ...item, name: e.target.value })}
              />
            </label>
            <label>
              URL
              <input
                value={item.url}
                onChange={(e) => update({ ...item, url: e.target.value })}
              />
            </label>
            <label className="span-2">
              Description
              <input
                value={item.description}
                onChange={(e) =>
                  update({ ...item, description: e.target.value })
                }
              />
            </label>
            <label className="span-2">
              Highlights (one per line)
              <textarea
                rows={2}
                value={(item.highlights || []).join("\n")}
                onChange={(e) =>
                  update({
                    ...item,
                    highlights: e.target.value.split("\n").filter(Boolean),
                  })
                }
              />
            </label>
          </div>
        )}
      />
    );
  }

  return (
    <div className="structured-form">
      <section className="form-block">
        <div className="list-head">
          <h3>Basics</h3>
        </div>
        <div className="field-grid">
          <label>
            Name
            <input
              value={b.name}
              onChange={(e) => setBasics({ name: e.target.value })}
            />
          </label>
          <label>
            Email
            <input
              value={b.email}
              onChange={(e) => setBasics({ email: e.target.value })}
            />
          </label>
          <label>
            Phone
            <input
              value={b.phone}
              onChange={(e) => setBasics({ phone: e.target.value })}
            />
          </label>
          <label>
            Location
            <input
              value={b.location}
              onChange={(e) => setBasics({ location: e.target.value })}
            />
          </label>
          <label>
            Website / portfolio
            <input
              value={b.website || ""}
              onChange={(e) => setBasics({ website: e.target.value })}
            />
          </label>
          <label>
            LinkedIn
            <input
              value={b.linkedin || ""}
              onChange={(e) => setBasics({ linkedin: e.target.value })}
            />
          </label>
          <label className="span-2">
            GitHub
            <input
              value={b.github || ""}
              onChange={(e) => setBasics({ github: e.target.value })}
            />
          </label>
          <label className="span-2">
            Summary
            <textarea
              rows={3}
              value={b.summary}
              onChange={(e) => setBasics({ summary: e.target.value })}
            />
          </label>
        </div>
      </section>

      <p className="muted small section-hint">
        Use ↑ / ↓ to reorder sections or entries. Section order is used in the
        PDF after Compile.
      </p>

      {order.map((key, index) => renderBodySection(key, index))}
    </div>
  );
}

function ListSection<T>({
  title,
  items,
  onChange,
  blank,
  render,
  sectionMove,
}: {
  title: string;
  items: T[];
  onChange: (items: T[]) => void;
  blank: () => T;
  render: (item: T, index: number, update: (item: T) => void) => ReactNode;
  sectionMove?: ReactNode;
}) {
  function move(from: number, to: number) {
    onChange(reorderList(items, from, to));
  }

  return (
    <section className="list-section form-block">
      <div className="list-head">
        <div className="list-head-left">
          {sectionMove}
          <h3>{title}</h3>
        </div>
        <button
          type="button"
          className="secondary compact"
          onClick={() => onChange([...items, blank()])}
        >
          Add
        </button>
      </div>
      {items.length === 0 && <p className="muted small">None yet.</p>}
      {items.map((item, i) => (
        <div key={i} className="list-item">
          <div className="list-item-toolbar">
            <MoveButtons
              index={i}
              total={items.length}
              onMove={move}
              label={`${title} entry`}
            />
            <button
              type="button"
              className="link"
              onClick={() => onChange(items.filter((_, j) => j !== i))}
            >
              Remove
            </button>
          </div>
          {render(item, i, (next) => {
            const copy = items.slice();
            copy[i] = next;
            onChange(copy);
          })}
        </div>
      ))}
    </section>
  );
}
