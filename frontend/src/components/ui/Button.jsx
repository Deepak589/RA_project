import clsx from "clsx";
import Spinner from "./Spinner.jsx";

export default function Button({ variant = "primary", size = "md", loading = false, disabled = false, className, children, ...props }) {
  const variants = {
    primary: "bg-teal-600 text-white hover:bg-teal-700 border border-teal-600",
    secondary: "bg-white text-teal-700 border border-teal-200 hover:bg-teal-50",
    dashed: "bg-white text-teal-700 border border-dashed border-teal-300 hover:bg-teal-50",
    danger: "bg-red-50 text-red-700 border border-red-100 hover:bg-red-100",
    ghost: "bg-transparent text-teal-700 border border-transparent hover:bg-teal-50",
  };
  const sizes = { sm: "min-h-11 px-3 text-sm", md: "min-h-11 px-4", lg: "min-h-12 px-5 text-lg" };
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        sizes[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  );
}
