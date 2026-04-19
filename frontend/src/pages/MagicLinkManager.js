import React, { useState, useEffect, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, MapPin, Plus, Copy, Trash2, Check } from "lucide-react";
import apiClient from "../apiClient";

function MagicLinkManager() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const property = state?.property;

  const [tokens, setTokens] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [copiedId, setCopiedId] = useState(null);

  const loadTokens = useCallback(async () => {
    try {
      const data = await apiClient.listMagicLinks(property.representation_id);
      setTokens(data.tokens);
    } catch {
      setError("Failed to load links.");
    } finally {
      setIsLoading(false);
    }
  }, [property?.representation_id]);

  useEffect(() => {
    if (property) loadTokens();
  }, [property?.representation_id, loadTokens]);

  const handleCreate = async () => {
    setError("");
    try {
      await apiClient.createMagicLink(property.representation_id);
      await loadTokens();
    } catch {
      setError("Failed to create link.");
    }
  };

  const handleRevoke = async (tokenId) => {
    setError("");
    try {
      await apiClient.revokeMagicLink(property.representation_id, tokenId);
      await loadTokens();
    } catch {
      setError("Failed to revoke link.");
    }
  };

  const handleCopy = (token) => {
    const url = `${window.location.origin}/client/${token.token}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopiedId(token.id);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const portalUrl = (token) =>
    `${window.location.origin}/client/${token.token}`;

  return (
    <main
      data-testid="magic-link-manager-page"
      className="min-h-screen bg-linen-100 pt-14"
    >
      <div className="max-w-2xl mx-auto px-6 py-10">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 font-sans text-sm text-ink-400 hover:text-ink-900 transition-colors mb-8 group"
          aria-label="Go back"
        >
          <ArrowLeft
            size={14}
            className="group-hover:-translate-x-0.5 transition-transform"
          />
          Back
        </button>

        <div
          className="mb-8 animate-fade-up"
          style={{ animationFillMode: "both" }}
        >
          <h1 className="font-serif text-4xl text-ink-900 mb-2">
            Client Portal Links
          </h1>
          {property && (
            <div className="flex items-center gap-2">
              <MapPin size={13} className="text-bronze-400" strokeWidth={1.5} />
              <span className="font-sans text-sm text-ink-400">
                {property.formatted_address}
              </span>
            </div>
          )}
        </div>

        <div className="mb-6">
          <button
            onClick={handleCreate}
            className="flex items-center gap-2 bg-bronze-500 hover:bg-bronze-600 text-white font-sans text-sm font-medium py-3 px-6 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-400 focus:ring-offset-1"
          >
            <Plus size={15} strokeWidth={2} />
            Create Link
          </button>
        </div>

        {error && (
          <p className="font-sans text-sm text-red-700 mb-5" role="alert">
            {error}
          </p>
        )}

        {isLoading ? null : tokens.length === 0 ? (
          <p className="font-sans text-sm text-ink-400">
            No active links. Create one to share the client portal.
          </p>
        ) : (
          <ul className="space-y-4">
            {tokens.map((token) => (
              <li
                key={token.id}
                className="bg-white rounded-lg border border-linen-200 p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="font-sans text-sm text-ink-800 truncate">
                      {portalUrl(token)}
                    </p>
                    <p className="font-sans text-xs text-ink-400 mt-1">
                      {token.last_accessed_at
                        ? `Last accessed ${new Date(token.last_accessed_at).toLocaleDateString()}`
                        : "Never accessed"}
                    </p>
                    <p className="font-sans text-xs text-ink-400">
                      Expires {new Date(token.expires_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleCopy(token)}
                      aria-label="Copy link"
                      className="p-2 text-ink-400 hover:text-bronze-500 transition-colors"
                    >
                      {copiedId === token.id ? (
                        <Check size={15} />
                      ) : (
                        <Copy size={15} />
                      )}
                    </button>
                    <button
                      onClick={() => handleRevoke(token.id)}
                      aria-label="Revoke"
                      className="p-2 text-ink-400 hover:text-red-500 transition-colors"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}

export default MagicLinkManager;
