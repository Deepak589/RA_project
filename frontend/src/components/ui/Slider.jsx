export default function Slider({ label, min = 0, max = 10, step = 1, value, onChange, showValue = true, valueLabel }) {
  return (
    <div>
      <div className="mb-2 flex items-end justify-between gap-3">
        <label className="text-base font-medium text-gray-700">{label}</label>
        {showValue && <div className="text-3xl font-semibold text-teal-700">{valueLabel || value}</div>}
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="h-3 w-full accent-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
      />
    </div>
  );
}
