import { Navigate, Route, Routes } from "react-router-dom";
import Spinner from "./components/ui/Spinner.jsx";
import { useAuth } from "./hooks/useAuth.js";
import AnalyticsPage from "./pages/AnalyticsPage.jsx";
import CustomMealPage from "./pages/CustomMealPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import LifestyleLogPage from "./pages/LifestyleLogPage.jsx";
import MealLogPage from "./pages/MealLogPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import RecommendationPage from "./pages/RecommendationPage.jsx";
import SymptomLogPage from "./pages/SymptomLogPage.jsx";
import LoginPage from "./pages/auth/LoginPage.jsx";
import OnboardingPage from "./pages/auth/OnboardingPage.jsx";
import RegisterPage from "./pages/auth/RegisterPage.jsx";

export default function App() {
  const { authStatus } = useAuth();
  return (
    <Routes>
      <Route path="/" element={<Navigate to={authStatus === "authenticated" ? "/dashboard" : "/login"} replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/onboarding" element={<PrivateRoute><OnboardingPage /></PrivateRoute>} />
      <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
      <Route path="/recommendations" element={<PrivateRoute><RecommendationPage /></PrivateRoute>} />
      <Route path="/meals/log" element={<PrivateRoute><MealLogPage /></PrivateRoute>} />
      <Route path="/custom-meal" element={<PrivateRoute><CustomMealPage /></PrivateRoute>} />
      <Route path="/meals/custom" element={<PrivateRoute><CustomMealPage /></PrivateRoute>} />
      <Route path="/symptoms/log" element={<PrivateRoute><SymptomLogPage /></PrivateRoute>} />
      <Route path="/lifestyle/log" element={<PrivateRoute><LifestyleLogPage /></PrivateRoute>} />
      <Route path="/analytics" element={<PrivateRoute><AnalyticsPage /></PrivateRoute>} />
      <Route path="/profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
    </Routes>
  );
}

function PrivateRoute({ children }) {
  const { authStatus } = useAuth();
  if (authStatus === "bootstrapping") return <div className="flex min-h-screen items-center justify-center bg-gray-50"><Spinner size="lg" /></div>;
  if (authStatus !== "authenticated") return <Navigate to="/login" replace />;
  return children;
}
