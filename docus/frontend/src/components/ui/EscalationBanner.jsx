import { AlertTriangle } from "lucide-react";

export default function EscalationBanner({ message }) {
  if (!message) return null;
  return (
    <div className="rounded-xl border border-orange-100 bg-orange-50 p-4 text-orange-800">
      <div className="flex gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
        <div>
          <h2 className="font-semibold">Symptoms may need attention</h2>
          <p className="mt-1 text-sm leading-6">{message}</p>
        </div>
      </div>
    </div>
  );
}
