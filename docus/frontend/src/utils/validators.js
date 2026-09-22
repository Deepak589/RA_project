export function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export function validateRegister({ name, email, password, confirmPassword }) {
  const errors = {};
  if (!name || name.trim().length < 2) errors.name = "Name must be at least 2 characters";
  if (!isEmail(email || "")) errors.email = "Enter a valid email";
  if (!password || password.length < 8) errors.password = "Password must be at least 8 characters";
  if (password !== confirmPassword) errors.confirmPassword = "Passwords must match";
  return errors;
}
