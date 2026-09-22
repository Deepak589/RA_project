import clsx from "clsx";

export default function Select({ label, options = [], error, className, ...props }) {
  return (
    <label className="block">
      {label && <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>}
      <select
        className={clsx(
          "min-h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-base outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500",
          error && "border-red-300",
          className,
        )}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value ?? option} value={option.value ?? option}>
            {option.label ?? option}
          </option>
        ))}
      </select>
      {error && <span className="mt-1 block text-sm text-red-600">{error}</span>}
    </label>
  );
}
