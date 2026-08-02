/**
 * Ephemeral toasts for key outcomes (product outcomes matrices).
 * Minimal host — parent owns message state.
 */
import { useEffect } from "react";

export type ToastKind = "ok" | "err";

export type ToastMessage = {
  id: number;
  text: string;
  kind: ToastKind;
};

export function ToastHost({
  toast,
  onDismiss,
  ms = 3200,
}: {
  toast: ToastMessage | null;
  onDismiss: () => void;
  ms?: number;
}) {
  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(onDismiss, ms);
    return () => window.clearTimeout(t);
  }, [toast, onDismiss, ms]);

  if (!toast) return null;
  return (
    <div className="toast-host" aria-live="polite">
      <div className={`toast ${toast.kind}`} role="status">
        {toast.text}
      </div>
    </div>
  );
}
