import { Flame } from "lucide-react";

export default function FlareBanner({ mode }) {
  if (!["flare_only", "mixed"].includes(mode)) return null;
  return (
    <div className="rounded-xl border border-orange-100 bg-orange-50 p-4 text-orange-800">
      <div className="flex gap-3">
        <Flame className="h-5 w-5 shrink-0" />
        <p className="text-sm leading-6">You reported pain today. Showing gentle, easy-to-prepare meals.</p>
      </div>
    </div>
  );
}
