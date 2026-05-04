import clsx from "clsx";

export default function Input({ label, error, hint, className, id, ...props }) {
  const inputId = id || props.name || label;
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>}
      <input
        id={inputId}
        className={clsx(
          "min-h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-base text-gray-800 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500",
          error && "border-red-300",
          className,
        )}
        {...props}
      />
      {hint && <span className="mt-1 block text-sm text-gray-500">{hint}</span>}
      {error && <span className="mt-1 block text-sm text-red-600">{error}</span>}
    </label>
  );
}
