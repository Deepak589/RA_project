export default function WeeklyAdherenceChart({ loggedDays = 0 }) {
  const percent = Math.min(100, Math.round((loggedDays / 7) * 100));
  const widths = ["w-0", "w-[14%]", "w-[29%]", "w-[43%]", "w-[57%]", "w-[71%]", "w-[86%]", "w-full"];
  return (
    <div className="rounded-xl bg-white p-4">
      <div className="mb-2 flex justify-between text-sm">
        <span className="text-gray-600">You logged meals {loggedDays} out of 7 days</span>
        <span className="font-medium text-teal-700">{percent}%</span>
      </div>
      <div className="h-3 rounded-full bg-gray-100">
        <div className={`h-3 rounded-full bg-teal-600 ${widths[Math.min(7, Math.max(0, loggedDays))]}`} />
      </div>
    </div>
  );
}
