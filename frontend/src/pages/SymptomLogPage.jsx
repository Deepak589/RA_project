import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import AppLayout from "../components/layout/AppLayout.jsx";
import SymptomSlider from "../components/logs/SymptomSlider.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import EscalationBanner from "../components/ui/EscalationBanner.jsx";
import Input from "../components/ui/Input.jsx";
import { useSymptoms } from "../hooks/useLogs.js";

const stiffnessOptions = [["None", 0], ["<30min", 20], ["30-60min", 45], ["1-2hrs", 90], ["2hrs+", 130]];
const flares = ["none", "mild", "moderate", "severe"];
const ESCALATION_MESSAGE = "You logged symptoms that may need medical attention. This app cannot assess urgent health problems or tell you how to treat a flare. If this pain or flare is severe, unusual for you, getting worse, or you are worried about your safety, please contact your clinician, urgent care, or local emergency services as appropriate.";

export default function SymptomLogPage() {
  const queryClient = useQueryClient();
  const { today, save } = useSymptoms();
  const [form, setForm] = useState({ pain_score: 2, fatigue_score: 2, stiffness_score: 0, stiffness_minutes: 0, swelling_score: 0, flare_level: "none", note: "" });
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (today.data) {
      setForm((current) => ({ ...current, ...today.data }));
    }
  }, [today.data]);

  useEffect(() => {
    if (!successMessage) return undefined;
    const timeoutId = window.setTimeout(() => setSuccessMessage(""), 3000);
    return () => window.clearTimeout(timeoutId);
  }, [successMessage]);

  const showEscalation = Number(form.pain_score) >= 8 || ["moderate", "severe"].includes(form.flare_level);

  async function submit() {
    await save.mutateAsync({ hasExistingLog: Boolean(today.data), payload: form });
    await queryClient.invalidateQueries({ queryKey: ["dashboard", "weekly"] });
    setSuccessMessage(today.data ? "Symptoms updated." : "Symptoms logged.");
  }

  return (
    <AppLayout title="Symptoms" back>
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-gray-800">{today.data ? "Update today's symptoms" : "Log symptoms"}</h2>
        <p className="text-sm text-gray-500">
          {today.data ? "Your earlier log for today has been loaded. Adjust any values and save." : "Track how you're feeling today."}
        </p>
      </div>
      <Card className="space-y-5">
        <SymptomSlider label="Pain score" value={Number(form.pain_score)} onChange={(value) => setForm({ ...form, pain_score: value })} />
        <SymptomSlider label="Fatigue level" value={Number(form.fatigue_score)} onChange={(value) => setForm({ ...form, fatigue_score: value })} />
        <div>
          <p className="mb-2 font-medium text-gray-700">How long was morning stiffness?</p>
          <div className="grid grid-cols-2 gap-2">
            {stiffnessOptions.map(([label, value]) => <Button key={label} variant={form.stiffness_minutes === value ? "primary" : "secondary"} onClick={() => setForm({ ...form, stiffness_minutes: value })}>{label}</Button>)}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Button variant={form.swelling_score > 0 ? "primary" : "secondary"} onClick={() => setForm({ ...form, swelling_score: 5 })}>Swelling: YES</Button>
          <Button variant={form.swelling_score === 0 ? "primary" : "secondary"} onClick={() => setForm({ ...form, swelling_score: 0 })}>Swelling: NO</Button>
        </div>
        <div>
          <p className="mb-2 font-medium text-gray-700">Overall flare level</p>
          <div className="grid grid-cols-2 gap-2">
            {flares.map((flare) => <Button key={flare} variant={form.flare_level === flare ? "primary" : "secondary"} onClick={() => setForm({ ...form, flare_level: flare })}>{flare}</Button>)}
          </div>
        </div>
        <Input label="Any notes? Optional" value={form.note || ""} onChange={(e) => setForm({ ...form, note: e.target.value })} />
      </Card>
      <EscalationBanner message={showEscalation ? ESCALATION_MESSAGE : ""} />
      {successMessage ? <p className="text-sm font-medium text-teal-700">✓ {successMessage}</p> : null}
      <Button className="w-full min-h-14" loading={save.isPending} onClick={submit}>{today.data ? "Update symptoms" : "Save symptoms"}</Button>
    </AppLayout>
  );
}
