import { BarChart3, Home, PlusCircle, User, Utensils } from "lucide-react";
import clsx from "clsx";
import { NavLink, useNavigate } from "react-router-dom";

const items = [
  { label: "Home", icon: Home, to: "/dashboard" },
  { label: "Meals", icon: Utensils, to: "/meals/log" },
  { label: "Insights", icon: BarChart3, to: "/analytics" },
  { label: "Profile", icon: User, to: "/profile" },
];

export default function BottomNav() {
  const navigate = useNavigate();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-gray-100 bg-white px-3 pb-2 pt-1 shadow-sm">
      <div className="mx-auto grid max-w-md grid-cols-5 items-end gap-1">
        {items.slice(0, 2).map((item) => (
          <NavItem key={item.to} item={item} />
        ))}
        <button
          type="button"
          onClick={() => navigate("/symptoms/log")}
          className="flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl text-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
        >
          <PlusCircle className="h-8 w-8" />
          <span className="text-[11px] font-medium">Log</span>
        </button>
        {items.slice(2).map((item) => (
          <NavItem key={item.to} item={item} />
        ))}
      </div>
    </nav>
  );
}

function NavItem({ item }) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        clsx(
          "flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500",
          isActive ? "text-teal-700" : "text-gray-500",
        )
      }
    >
      <Icon className="h-5 w-5" />
      <span className="text-[11px] font-medium">{item.label}</span>
    </NavLink>
  );
}
