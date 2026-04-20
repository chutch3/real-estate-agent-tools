import React, { useState } from "react";
import { useParams } from "react-router-dom";
import apiClient from "../apiClient";
import SellerPortalView from "./SellerPortalView";
import BuyerPortalView from "./BuyerPortalView";

function ConsumerPortal() {
  const { portalToken } = useParams();
  const [code, setCode] = useState("");
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await apiClient.createConsumerSession(portalToken, code);
      setSession(result);
    } catch {
      setError("Invalid access code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (session) {
    if (session.role === "listing_agent") {
      return <SellerPortalView session={session} />;
    }
    return <BuyerPortalView session={session} />;
  }

  return (
    <div className="min-h-screen bg-linen-50 flex items-center justify-center px-6">
      <div className="max-w-md w-full space-y-6">
        <p className="font-serif text-2xl text-ink-900 text-center">
          Client Portal
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="access-code"
              className="block font-sans text-sm text-ink-600 mb-1"
            >
              Access Code
            </label>
            <input
              id="access-code"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full border border-ink-200 rounded px-3 py-2 font-mono text-sm"
              placeholder="Enter your access code"
            />
          </div>
          {error && <p className="font-sans text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-bronze-500 text-white font-sans text-sm py-2 rounded disabled:opacity-50"
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  );
}

export default ConsumerPortal;
