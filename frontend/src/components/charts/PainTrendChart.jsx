import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function PainTrendChart({ data = [] }) {
  if (!data.length) return <div className="rounded-xl bg-white p-4 text-sm text-gray-500">Log symptoms to see trends</div>;
  return (
    <div className="h-64 rounded-xl bg-white p-3">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
          <Tooltip />
          <ReferenceLine y={5} stroke="#FDBA74" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="pain_score" stroke="#0D9488" strokeWidth={3} dot={{ r: 4, fill: "#F97316" }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
