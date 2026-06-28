import { ReactNode } from "react";
import { AlertTriangle, ShieldQuestion } from "lucide-react";
import { Modal } from "./Modal";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "default" | "danger";
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open, title, message, confirmLabel = "Confirm", cancelLabel = "Cancel",
  tone = "default", loading = false, onConfirm, onCancel,
}: ConfirmDialogProps) {
  const isDanger = tone === "danger";
  return (
    <Modal open={open} onClose={onCancel} size="sm">
      <div className="flex gap-4">
        <div
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
            isDanger ? "bg-rose-100 text-rose-600" : "bg-brand-100 text-brand-700"
          )}
        >
          {isDanger ? <AlertTriangle className="h-5 w-5" /> : <ShieldQuestion className="h-5 w-5" />}
        </div>
        <div className="flex-1">
          <h3 className="font-display text-lg font-semibold text-ink-900">{title}</h3>
          <div className="mt-1.5 text-sm leading-relaxed text-ink-600">{message}</div>
        </div>
      </div>
      <div className="mt-6 flex items-center justify-end gap-3">
        <Button variant="secondary" onClick={onCancel} disabled={loading}>{cancelLabel}</Button>
        <Button
          variant={isDanger ? "danger" : "primary"}
          onClick={onConfirm}
          loading={loading}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
