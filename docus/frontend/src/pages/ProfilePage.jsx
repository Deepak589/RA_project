import { useState } from "react";
import AppLayout from "../components/layout/AppLayout.jsx";
import DietPreferences from "../components/DietPreferences.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import Input from "../components/ui/Input.jsx";
import { changePassword } from "../api/auth";
import { useAuth } from "../hooks/useAuth.js";
import { useProfile } from "../hooks/useProfile.js";

const goalOptions = ["reduce_inflammation", "increase_energy", "maintain_weight", "better_sleep", "balanced_meals"];

export default function ProfilePage() {
  const { logout } = useAuth();
  const { profile, updatePreferences, addMedication, removeMedication } = useProfile();
  const data = profile.data;
  const prefs = data?.preferences;
  const [med, setMed] = useState({ medication_name: "", dosage: "" });
  const [passwords, setPasswords] = useState({ current: "", next: "" });

  async function savePrefs(nextPrefs) {
    await updatePreferences.mutateAsync(nextPrefs);
  }

  async function addMed() {
    if (!med.medication_name.trim()) return;
    await addMedication.mutateAsync(med);
    setMed({ medication_name: "", dosage: "" });
  }

  return (
    <AppLayout title="Profile">
      <Card>
        <h2 className="text-xl font-semibold text-gray-800">{data?.user?.full_name}</h2>
        <p className="text-sm text-gray-500">{data?.user?.email}</p>
      </Card>
      <Card className="space-y-3">
        <h2 className="font-semibold">Dietary preferences</h2>
        <DietPreferences value={prefs?.dietary_flags_jsonb || []} onChange={(value) => savePrefs({ dietary_flags: value })} />
        <Input label="Allergies, comma separated" defaultValue={(prefs?.allergies_jsonb || []).join(", ")} onBlur={(e) => savePrefs({ allergies: e.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} />
        <Button
          variant={(prefs?.goal_flags_jsonb || []).includes("budget_friendly") ? "primary" : "secondary"}
          onClick={() => savePrefs({ budget_friendly: !(prefs?.goal_flags_jsonb || []).includes("budget_friendly") })}
        >
          Budget friendly meals
        </Button>
        <div className="flex flex-wrap gap-2">
          {goalOptions.map((goal) => <Button key={goal} size="sm" variant={(prefs?.goal_flags_jsonb || []).includes(goal) ? "primary" : "secondary"} onClick={() => {
            const current = prefs?.goal_flags_jsonb || [];
            savePrefs({ goals: current.includes(goal) ? current.filter((item) => item !== goal) : [...current, goal] });
          }}>{goal.replaceAll("_", " ")}</Button>)}
        </div>
      </Card>
      <Card className="space-y-3">
        <h2 className="font-semibold">Medications</h2>
        {(data?.medications || []).map((item) => <div key={item.id} className="flex items-center justify-between gap-2"><span>{item.medication_name} {item.schedule_note}</span><Button size="sm" variant="ghost" onClick={() => removeMedication.mutate(item.id)}>Remove</Button></div>)}
        <Input label="Medication name" value={med.medication_name} onChange={(e) => setMed({ ...med, medication_name: e.target.value })} />
        <Input label="Dosage" value={med.dosage} onChange={(e) => setMed({ ...med, dosage: e.target.value })} />
        <Button variant="secondary" onClick={addMed}>Add medication</Button>
        <p className="text-sm text-gray-500">Medication details help us suggest more suitable meals. Always follow your doctor's guidance. [VERIFY WITH CLINICIAN]</p>
      </Card>
      <Card className="space-y-3">
        <h2 className="font-semibold">Account</h2>
        <Input label="Current password" type="password" value={passwords.current} onChange={(e) => setPasswords({ ...passwords, current: e.target.value })} />
        <Input label="New password" type="password" value={passwords.next} onChange={(e) => setPasswords({ ...passwords, next: e.target.value })} />
        <Button variant="secondary" onClick={() => changePassword(passwords.current, passwords.next)}>Change password</Button>
        <Button variant="danger" onClick={logout}>Log out</Button>
      </Card>
    </AppLayout>
  );
}
