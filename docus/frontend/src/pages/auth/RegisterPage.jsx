import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../../components/ui/Button.jsx";
import Card from "../../components/ui/Card.jsx";
import Input from "../../components/ui/Input.jsx";
import { useAuth } from "../../hooks/useAuth.js";
import { validateRegister } from "../../utils/validators.js";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [generalError, setGeneralError] = useState("");
  const [loading, setLoading] = useState(false);

  function updateField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => {
      if (!current[name]) return current;
      const next = { ...current };
      delete next[name];
      return next;
    });
    setGeneralError("");
  }

  async function submit(event) {
    event.preventDefault();
    const nextErrors = validateRegister(form);
    setFieldErrors(nextErrors);
    setGeneralError("");
    if (Object.keys(nextErrors).length) return;
    setLoading(true);
    try {
      await register(form.email, form.password, form.name);
      navigate("/onboarding", { replace: true });
    } catch (error) {
      const detail = error?.response?.data?.detail;
      const code = detail?.code;
      if (code === "EMAIL_ALREADY_EXISTS") {
        setFieldErrors((current) => ({ ...current, email: "An account with this email already exists." }));
      } else if (code === "PASSWORD_TOO_SHORT") {
        setFieldErrors((current) => ({ ...current, password: detail.message }));
      } else {
        setGeneralError("We couldn't create your account right now. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="max-w-md space-y-5">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">Create your account</h1>
          <p className="mt-1 text-gray-500">Set up your RA nutrition guide.</p>
        </div>
        <form className="space-y-4" onSubmit={submit}>
          <Input label="Full name" value={form.name} error={fieldErrors.name} onChange={(e) => updateField("name", e.target.value)} />
          <Input label="Email" type="email" value={form.email} error={fieldErrors.email} onChange={(e) => updateField("email", e.target.value)} />
          <Input label="Password" type="password" value={form.password} error={fieldErrors.password} onChange={(e) => updateField("password", e.target.value)} />
          <Input
            label="Confirm password"
            type="password"
            value={form.confirmPassword}
            error={fieldErrors.confirmPassword}
            onChange={(e) => updateField("confirmPassword", e.target.value)}
          />
          {generalError ? <p className="text-sm text-red-600">{generalError}</p> : null}
          <Button className="w-full" size="lg" loading={loading}>Register</Button>
        </form>
        <p className="text-center text-sm text-gray-500">
          Already have an account? <Link className="font-medium text-teal-700" to="/login">Log in</Link>
        </p>
      </Card>
    </main>
  );
}
