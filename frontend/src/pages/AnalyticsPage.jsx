import { useQuery } from "@tanstack/react-query";
import AppLayout from "../components/layout/AppLayout.jsx";
import PainTrendChart from "../components/charts/PainTrendChart.jsx";
import WeeklyAdherenceChart from "../components/charts/WeeklyAdherenceChart.jsx";
import { getWeeklyDashboard } from "../api/dashboard";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import { number } from "../utils/formatters.js";

export default function AnalyticsPage() {
  const { data } = useQuery({
    queryKey: ["dashboard", "weekly"],
    queryFn: getWeeklyDashboard,
    staleTime: 0,
  });
  const trend = data?.pain_trend || data?.symptom_trend || [];
  const loggedDays = data?.meal_logged_days ?? 0;
  const insights = data?.insights || [];

  return (
    <AppLayout title="Insights">
      <div className="flex items-center justify-between">
        <Button variant="ghost">Previous</Button>
        <span className="font-medium text-gray-700">This week</span>
        <Button variant="ghost">Next</Button>
      </div>
      <PainTrendChart data={trend} />
      <div className="grid grid-cols-2 gap-2">
        <Metric label="Avg pain" value={number(data?.avg_pain_score || data?.average_pain || 0, 1)} />
        <Metric label="Meal days" value={loggedDays} />
        <Metric label="Meals logged" value={data?.total_meals_logged ?? 0} />
        <Metric label="Accepted (of decisions made)" value={`${number(data?.recommendation_acceptance_rate || 0)}%`} />
        <Metric label="Flare days" value={data?.flare_days_count || 0} />
      </div>
      <section className="space-y-2">
        <h2 className="font-semibold text-gray-800">Weekly insights</h2>
        {insights.length ? insights.map((item) => <Card key={item}><p className="text-sm text-gray-600">{item}</p></Card>) : <Card><p className="text-sm text-gray-500">No insights yet - keep logging for 7 days to see patterns</p></Card>}
      </section>
      <WeeklyAdherenceChart loggedDays={loggedDays} />
    </AppLayout>
  );
}

function Metric({ label, value }) {
  return <Card><p className="text-sm text-gray-500">{label}</p><p className="text-xl font-semibold text-teal-700">{value}</p></Card>;
}
