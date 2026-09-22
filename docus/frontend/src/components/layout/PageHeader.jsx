import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function PageHeader({ title, action, back = false }) {
  const navigate = useNavigate();
  return (
    <header className="sticky top-0 z-20 flex min-h-16 items-center justify-between gap-3 border-b border-gray-100 bg-gray-50/95 px-4 backdrop-blur">
      <div className="flex items-center gap-2">
        {back && (
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="flex min-h-11 min-w-11 items-center justify-center rounded-full text-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
        )}
        <h1 className="text-lg font-semibold text-gray-800">{title}</h1>
      </div>
      {action}
    </header>
  );
}
