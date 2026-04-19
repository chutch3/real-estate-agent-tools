import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import apiClient from "../apiClient";
import SellerPortalView from "./SellerPortalView";
import BuyerPortalView from "./BuyerPortalView";

function ConsumerPortal() {
  const { token } = useParams();
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiClient
      .createConsumerSession(token)
      .then(setSession)
      .catch(() => setError(true));
  }, [token]);

  if (error) {
    return (
      <div className="min-h-screen bg-linen-50 flex items-center justify-center px-6">
        <div className="max-w-md w-full text-center space-y-4">
          <p className="font-serif text-2xl text-ink-900">Link Unavailable</p>
          <p className="font-sans text-sm text-ink-400">
            This link has expired or is no longer valid.
          </p>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-linen-50 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-bronze-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (session.role === "listing_agent") {
    return <SellerPortalView session={session} />;
  }
  return <BuyerPortalView session={session} />;
}

export default ConsumerPortal;
