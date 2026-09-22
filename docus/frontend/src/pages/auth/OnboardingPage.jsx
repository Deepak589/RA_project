import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DietPreferences from "../../components/DietPreferences.jsx";
import AppLayout from "../../components/layout/AppLayout.jsx";
import Button from "../../components/ui/Button.jsx";
import Card from "../../components/ui/Card.jsx";
import Input from "../../components/ui/Input.jsx";
import { useProfile } from "../../hooks/useProfile.js";

const allergies = ["nuts", "dairy", "gluten", "eggs", "shellfish", "soy"];
const goals = ["reduce_inflammation", "increase_energy", "maintain_weight", "better_sleep", "balanced_meals"];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { updatePreferences, addMedication } = useProfile();
  const [step, setStep] = useState(1);
  const [prefs, setPrefs] = useState({ dietary_flags: ["no_preference"], allergies: [], goals: [], budget_friendly: false });
  const [medications, setMedications] = useState([{ medication_name: "", dosage: "" }]);

  async function finish() {
    await updatePreferences.mutateAsync({
      dietary_flags: prefs.dietary_flags,
      allergies: prefs.allergies,
      goals: prefs.goals,
      budget_friendly: prefs.budget_friendly,
    });
    for (const med of medications.filter((item) => item.medication_name.trim())) {
      await addMedication.mutateAsync(med);
    }
    navigate("/dashboard", { replace: true });
  }

  return (
    <AppLayout title="Onboarding" back>
      <div className="h-2 rounded-full bg-gray-100">
        <div className={`h-2 rounded-full bg-teal-600 ${["w-1/4", "w-2/4", "w-3/4", "w-full"][step - 1]}`} />
      </div>
      <p className="text-sm text-gray-500">Step {step}/4</p>
      {step === 1 && (
        <Card className="space-y-3">
          <Input label="Height (cm)" type="number" />
          <Input label="Weight (kg)" type="number" />
          <Input label="Age" type="number" />
          <Input label="How long have you had RA? (years)" type="number" />
        </Card>
      )}
      {step === 2 && (
        <Card className="space-y-4">
          <DietPreferences value={prefs.dietary_flags} onChange={(value) => setPrefs({ ...prefs, dietary_flags: value })} />
          <Toggle label="Budget friendly meals" active={prefs.budget_friendly} onClick={() => setPrefs({ ...prefs, budget_friendly: !prefs.budget_friendly })} />
          <ChipGroup label="Food allergies" items={allergies} selected={prefs.allergies} onChange={(value) => setPrefs({ ...prefs, allergies: value })} />
        </Card>
      )}
      {step === 3 && (
        <Card>
          <ChipGroup label="Pick up to 3 goals" items={goals} selected={prefs.goals} onChange={(value) => setPrefs({ ...prefs, goals: value.slice(0, 3) })} />
        </Card>
      )}
      {step === 4 && (
        <Card className="space-y-3">
          <p className="text-sm text-gray-600">Medication information helps us suggest more suitable meals. Always follow your doctor's advice. [VERIFY WITH CLINICIAN]</p>
          {medications.map((med, index) => (
            <div className="grid gap-2" key={index}>
              <Input label="Medication name" value={med.medication_name} onChange={(e) => setMedications((items) => items.map((item, i) => (i === index ? { ...item, medication_name: e.target.value } : item)))} />
              <Input label="Dosage" value={med.dosage} onChange={(e) => setMedications((items) => items.map((item, i) => (i === index ? { ...item, dosage: e.target.value } : item)))} />
            </div>
          ))}
          <Button variant="secondary" onClick={() => setMedications([...medications, { medication_name: "", dosage: "" }])}>Add another</Button>
        </Card>
      )}
      <div className="grid grid-cols-2 gap-2">
        <Button variant="secondary" disabled={step === 1} onClick={() => setStep(step - 1)}>Back</Button>
        {step < 4 ? <Button onClick={() => setStep(step + 1)}>Next</Button> : <Button onClick={finish}>Complete</Button>}
      </div>
    </AppLayout>
  );
}

function Toggle({ label, active, onClick }) {
  return <Button variant={active ? "primary" : "secondary"} className="w-full" onClick={onClick}>{label}: {active ? "Yes" : "No"}</Button>;
}

function ChipGroup({ label, items, selected, onChange }) {
  function toggle(item) {
    onChange(selected.includes(item) ? selected.filter((value) => value !== item) : [...selected, item]);
  }
  return (
    <div>
      <p className="mb-2 font-medium text-gray-700">{label}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => <Button key={item} size="sm" variant={selected.includes(item) ? "primary" : "secondary"} onClick={() => toggle(item)}>{item.replaceAll("_", " ")}</Button>)}
      </div>
    </div>
  );
}
