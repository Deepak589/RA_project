import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import AppLayout from "../components/layout/AppLayout.jsx";
import PainTrendChart from "../components/charts/PainTrendChart.jsx";
import WeeklyAdherenceChart from "../components/charts/WeeklyAdherenceChart.jsx";
import { getWeeklyDashboard } from "../api/dashboard";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { number } from "../utils/formatters.js";

function weekLabel(offset) {
  if (offset === 0) return "This week";
  if (offset === -1) return "Last week";
  return `${Math.abs(offset)} weeks ago`;
}

export default function AnalyticsPage() {
  const [weekOffset, setWeekOffset] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "weekly", weekOffset],
    queryFn: () => getWeeklyDashboard(weekOffset),
    staleTime: 0,
  });

  const trend = data?.pain_trend || [];
  const loggedDays = data?.meal_logged_days ?? 0;
  const insights = data?.insights || [];
  const avgPain = data?.avg_pain_score ?? null;
  const acceptance = data?.recommendation_acceptance_rate ?? null;

  return (
    <AppLayout title="Insights">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => setWeekOffset((o) => o - 1)}>← Previous</Button>
        <span className="font-medium text-gray-700">{weekLabel(weekOffset)}</span>
        <Button variant="ghost" disabled={weekOffset === 0} onClick={() => setWeekOffset((o) => o + 1)}>Next →</Button>
      </div>

      {isLoading ? (
        <div className="text-center text-sm text-gray-400 py-8">Loading…</div>
      ) : (
        <>
          <PainTrendChart data={trend} />
          <div className="grid grid-cols-2 gap-2">
            <Metric label="Avg pain" value={avgPain !== null ? number(avgPain, 1) : "—"} />
            <Metric label="Meal days" value={loggedDays} />
            <Metric label="Meals logged" value={data?.total_meals_logged ?? 0} />
            <Metric label="Accepted" value={acceptance !== null ? `${number(acceptance)}%` : "—"} />
            <Metric label="Flare days" value={data?.flare_days_count ?? 0} />
          </div>
          <section className="space-y-2">
            <h2 className="font-semibold text-gray-800">Weekly insights</h2>
            {insights.length
              ? insights.map((item) => <Card key={item}><p className="text-sm text-gray-600">{item}</p></Card>)
              : <Card><p className="text-sm text-gray-500">No data for this week — try navigating to a previous week or keep logging.</p></Card>}
          </section>
          <WeeklyAdherenceChart loggedDays={loggedDays} />
        </>
      )}
    </AppLayout>
  );
}

function Metric({ label, value }) {
  return (
    <Card>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-xl font-semibold text-teal-700">{value}</p>
    </Card>
  );
}
