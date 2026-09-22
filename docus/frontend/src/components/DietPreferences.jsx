import Button from "./ui/Button.jsx";

const OPTIONS = [
  { key: "no_preference", label: "No preference", description: "I eat everything" },
  { key: "vegetarian", label: "Vegetarian", description: "No meat or fish" },
  { key: "pescatarian", label: "Pescatarian", description: "No meat, fish is fine" },
  { key: "vegan", label: "Vegan", description: "No animal products" },
  { key: "gluten_free", label: "Gluten-free", description: "Avoiding gluten" },
  { key: "dairy_free", label: "Dairy-free", description: "No dairy products" },
  { key: "low_sodium", label: "Low-sodium", description: "Reducing salt intake" },
];

export default function DietPreferences({ value = [], onChange }) {
  function isSelected(key) {
    return key === "no_preference" ? value.length === 0 || value.includes(key) : value.includes(key);
  }

  function toggle(key) {
    if (key === "no_preference") {
      onChange(["no_preference"]);
      return;
    }

    const next = value.filter((item) => item !== "no_preference");
    if (next.includes(key)) {
      const filtered = next.filter((item) => item !== key);
      onChange(filtered);
      return;
    }
    onChange([...next, key]);
  }

  return (
    <div>
      <p className="mb-2 font-medium text-gray-700">Dietary preferences</p>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {OPTIONS.map((option) => (
          <Button
            key={option.key}
            type="button"
            variant={isSelected(option.key) ? "primary" : "secondary"}
            className="min-h-24 flex-col items-start px-4 py-3 text-left"
            onClick={() => toggle(option.key)}
          >
            <span>{option.label}</span>
            <span className="text-sm font-normal opacity-80">{option.description}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}
