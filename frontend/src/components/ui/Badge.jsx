import clsx from "clsx";

export default function Badge({ label, variant = "grey" }) {
  const variants = {
    blue: "bg-sky-50 text-sky-700",
    green: "bg-green-50 text-green-700",
    orange: "bg-orange-50 text-orange-800",
    grey: "bg-gray-100 text-gray-600",
    red: "bg-red-50 text-red-700",
    teal: "bg-teal-50 text-teal-700",
  };
  return <span className={clsx("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", variants[variant])}>{label}</span>;
}
