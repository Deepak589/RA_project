import Slider from "../ui/Slider.jsx";

export default function SymptomSlider({ label, value, onChange }) {
  const text = value <= 2 ? "No pain" : value <= 4 ? "Mild" : value <= 6 ? "Moderate" : value <= 8 ? "Significant" : "Severe";
  return <Slider label={label} value={value} onChange={onChange} valueLabel={`${value} ${text}`} />;
}
