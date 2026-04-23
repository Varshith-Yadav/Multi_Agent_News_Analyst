import { FormEvent, useMemo, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { isAuthenticated, loginUser, signupUser } from "@/lib/api";

type AuthMode = "login" | "signup";

const Auth = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const heading = useMemo(
    () => (mode === "login" ? "Sign in to NeuralNews" : "Create your NeuralNews account"),
    [mode],
  );

  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const cleanUsername = username.trim().toLowerCase();
    if (cleanUsername.length < 3) {
      setError("Username must be at least 3 characters.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (mode === "signup" && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (mode === "login") {
        await loginUser({ username: cleanUsername, password });
      } else {
        await signupUser({ username: cleanUsername, password });
      }
      navigate("/", { replace: true });
    } catch (submitError) {
      const message =
        submitError instanceof Error ? submitError.message : "Authentication failed.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6 py-10">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl shadow-black/25">
        <h1 className="text-2xl font-semibold text-foreground">{heading}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {mode === "login"
            ? "Use your account to access analysis dashboard."
            : "Sign up and start running multi-agent analysis."}
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-muted-foreground">
              Username
            </label>
            <input
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none ring-primary transition focus:ring-2"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="analyst"
              required
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-muted-foreground">
              Password
            </label>
            <input
              type="password"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none ring-primary transition focus:ring-2"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 8 characters"
              required
              disabled={isSubmitting}
            />
          </div>

          {mode === "signup" && (
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted-foreground">
                Confirm Password
              </label>
              <input
                type="password"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground outline-none ring-primary transition focus:ring-2"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Repeat password"
                required
                disabled={isSubmitting}
              />
            </div>
          )}

          {error && (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Please wait..."
              : mode === "login"
                ? "Sign In"
                : "Create Account"}
          </button>
        </form>

        <div className="mt-4 text-center text-sm text-muted-foreground">
          {mode === "login" ? "Need an account?" : "Already have an account?"}{" "}
          <button
            type="button"
            className="text-primary underline"
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
            disabled={isSubmitting}
          >
            {mode === "login" ? "Sign up" : "Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;
