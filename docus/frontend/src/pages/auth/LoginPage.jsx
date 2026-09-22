import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../../components/ui/Button.jsx";
import Card from "../../components/ui/Card.jsx";
import Input from "../../components/ui/Input.jsx";
import { useAuth } from "../../hooks/useAuth.js";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(form.email, form.password);
      navigate(user?.preferences ? "/dashboard" : "/onboarding", { replace: true });
    } catch {
      setError("Incorrect email or password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Card className="max-w-md space-y-5">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">RA Nutrition Guide</h1>
          <p className="mt-1 text-gray-500">Your daily food and wellness companion</p>
        </div>
        <form className="space-y-4" onSubmit={submit}>
          <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <div className="relative">
            <Input label="Password" type={showPassword ? "text" : "password"} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            <button type="button" className="absolute right-3 top-8 min-h-11 text-gray-500" onClick={() => setShowPassword((value) => !value)} aria-label="Toggle password visibility">
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button className="w-full" size="lg" loading={loading}>Login</Button>
        </form>
        <p className="text-center text-sm text-gray-500">
          New here? <Link className="font-medium text-teal-700" to="/register">Create an account</Link>
        </p>
      </Card>
    </main>
  );
}
