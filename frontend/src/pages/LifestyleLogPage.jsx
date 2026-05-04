import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import AppLayout from "../components/layout/AppLayout.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Input from "../components/ui/Input.jsx";
import Slider from "../components/ui/Slider.jsx";
import { useLifestyle } from "../hooks/useLogs.js";

export default function LifestyleLogPage() {
  const queryClient = useQueryClient();
  const { today, save } = useLifestyle();
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({ log_date: new Date().toISOString().slice(0, 10), sleep_hours: 7.5, steps: 5000, water_ml: 1500, stress_level: 3, exercise_type: "", exercise_duration_minutes: 0, medication_taken: true, smoking: false, alcohol: false });

  useEffect(() => { if (today.data) setForm((current) => ({ ...current, ...today.data })); }, [today.data]);

  async function submit() {
    await save.mutateAsync(form);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["dashboard", "today"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] }),
      queryClient.invalidateQueries({ queryKey: ["recommendation"] }),
    ]);
    setSaved(true);
  }

  return (
    <AppLayout title="Lifestyle" back>
      <Card className="space-y-5">
        <Slider label="How did you sleep?" min={0} max={12} step={0.5} value={Number(form.sleep_hours)} onChange={(value) => setForm({ ...form, sleep_hours: value })} valueLabel={`${form.sleep_hours} hours`} />
        <Choice label="Steps today" options={[["<2000", 1000], ["2-5K", 3500], ["5-10K", 7500], ["10K+", 11000]]} value={form.steps} onChange={(steps) => setForm({ ...form, steps })} />
        <Input label="Exercise type" value={form.exercise_type || ""} onChange={(e) => setForm({ ...form, exercise_type: e.target.value })} />
        <Choice label="Duration" options={[["15", 15], ["30", 30], ["45", 45], ["60", 60], ["90+", 90]]} value={form.exercise_duration_minutes} onChange={(exercise_duration_minutes) => setForm({ ...form, exercise_duration_minutes })} />
        <Choice label="Water intake" options={[["<1L", 750], ["1-1.5L", 1250], ["1.5-2L", 1750], ["2L+", 2200]]} value={form.water_ml} onChange={(water_ml) => setForm({ ...form, water_ml })} />
        <Slider label="Stress level" value={Number(form.stress_level)} onChange={(value) => setForm({ ...form, stress_level: value })} />
        <Toggle label="Medication taken" value={form.medication_taken} onChange={(medication_taken) => setForm({ ...form, medication_taken })} />
        <Toggle label="Smoking" value={form.smoking} onChange={(smoking) => setForm({ ...form, smoking })} />
        <Toggle label="Alcohol" value={form.alcohol} onChange={(alcohol) => setForm({ ...form, alcohol })} />
      </Card>
      {saved && <p className="text-center text-sm font-medium text-teal-700">✓ Lifestyle log saved</p>}
      <Button className="w-full min-h-14" loading={save.isPending} onClick={submit}>Save lifestyle log</Button>
    </AppLayout>
  );
}

function Choice({ label, options, value, onChange }) {
  return <div><p className="mb-2 font-medium text-gray-700">{label}</p><div className="grid grid-cols-2 gap-2">{options.map(([labelText, optionValue]) => <Button key={labelText} variant={value === optionValue ? "primary" : "secondary"} onClick={() => onChange(optionValue)}>{labelText}</Button>)}</div></div>;
}

function Toggle({ label, value, onChange }) {
  return <div><p className="mb-2 font-medium text-gray-700">{label}</p><div className="grid grid-cols-2 gap-2"><Button variant={value ? "primary" : "secondary"} onClick={() => onChange(true)}>YES</Button><Button variant={!value ? "primary" : "secondary"} onClick={() => onChange(false)}>NO</Button></div></div>;
}
