import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch {
      setError("Invalid email or password");
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-linen-100">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm"
      >
        <h1 className="font-sans text-xl font-semibold text-ink-900 mb-6">
          Sign in
        </h1>

        <div className="mb-4">
          <label
            htmlFor="email"
            className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-1.5"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2.5 border border-linen-300 rounded-md bg-white font-sans text-sm text-ink-900 placeholder-ink-300 focus:outline-none focus:border-bronze-400 transition-colors"
          />
        </div>

        <div className="mb-6">
          <label
            htmlFor="password"
            className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-1.5"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-2.5 border border-linen-300 rounded-md bg-white font-sans text-sm text-ink-900 placeholder-ink-300 focus:outline-none focus:border-bronze-400 transition-colors"
          />
        </div>

        {error && (
          <p className="mb-4 font-sans text-sm text-red-600">{error}</p>
        )}

        <button
          type="submit"
          className="w-full py-2.5 bg-bronze-500 text-white font-sans text-sm font-medium rounded-md hover:bg-bronze-600 transition-colors"
        >
          Sign in
        </button>
      </form>
    </div>
  );
}

export default LoginPage;
