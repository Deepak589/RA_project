import clsx from "clsx";

export default function Card({ children, className, onClick, padding = "p-4" }) {
  const Component = onClick ? "button" : "div";
  return (
    <Component
      onClick={onClick}
      className={clsx(
        "w-full rounded-xl border border-gray-100 bg-white text-left shadow-sm",
        onClick && "focus:outline-none focus:ring-2 focus:ring-teal-500",
        padding,
        className,
      )}
    >
      {children}
    </Component>
  );
}
