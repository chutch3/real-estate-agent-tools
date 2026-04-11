import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, MapPin, Plus, Loader2 } from "lucide-react";
import ScenarioCard from "../components/ScenarioCard";
import apiClient from "../apiClient";

function NetSheet() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const property = state?.property;

  const [sheet, setSheet] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!property) return;
    apiClient
      .getNetSheet(property.id)
      .then(setSheet)
      .catch(() => setError("Failed to load net sheet."))
      .finally(() => setIsLoading(false));
  }, [property?.id]);

  const handleAddScenario = async () => {
    setError(null);
    const count = sheet?.scenarios?.length ?? 0;
    try {
      const updated = await apiClient.addScenario(property.id, {
        name: `Scenario ${count + 1}`,
      });
      setSheet(updated);
    } catch {
      setError("Failed to add scenario.");
    }
  };

  const handleUpdateScenario = async (scenarioId, updates) => {
    setError(null);
    try {
      const updated = await apiClient.updateScenario(
        property.id,
        scenarioId,
        updates,
      );
      setSheet(updated);
    } catch {
      setError("Failed to save changes.");
    }
  };

  const handleDeleteScenario = async (scenarioId) => {
    setError(null);
    try {
      const updated = await apiClient.deleteScenario(property.id, scenarioId);
      setSheet(updated);
    } catch {
      setError("Failed to delete scenario.");
    }
  };

  const scenarios = sheet?.scenarios ?? [];

  return (
    <main
      data-testid="net-sheet-page"
      className="min-h-screen bg-linen-100 pt-14"
    >
      <div className="max-w-screen-xl mx-auto px-6 py-10">
        {/* Back */}
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

        {/* Heading */}
        <div
          className="mb-8 animate-fade-up"
          style={{ animationFillMode: "both" }}
        >
          <h1 className="font-serif text-4xl text-ink-900 mb-2">Net Sheet</h1>
          {property && (
            <div className="flex items-center gap-2">
              <MapPin size={13} className="text-bronze-400" strokeWidth={1.5} />
              <span className="font-sans text-sm text-ink-400">
                {property.formatted_address}
              </span>
            </div>
          )}
        </div>

        {error && (
          <p className="font-sans text-sm text-red-700 mb-6" role="alert">
            {error}
          </p>
        )}

        {/* Add Scenario */}
        <div className="mb-6">
          <button
            onClick={handleAddScenario}
            disabled={isLoading}
            className="flex items-center gap-2 py-2 px-4 bg-bronze-500 hover:bg-bronze-600 disabled:bg-linen-300 disabled:cursor-not-allowed text-white font-sans text-sm rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-400 focus:ring-offset-1"
          >
            <Plus size={14} strokeWidth={2.5} />
            Add Scenario
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 size={24} className="animate-spin text-bronze-400" />
          </div>
        ) : scenarios.length === 0 ? (
          <div
            data-testid="empty-state"
            className="flex flex-col items-center justify-center py-20 text-ink-300"
          >
            <p className="font-sans text-sm">No scenarios yet.</p>
            <p className="font-sans text-xs text-ink-200 mt-1">
              Add a scenario to start calculating net proceeds.
            </p>
          </div>
        ) : (
          <div className="flex gap-5 overflow-x-auto pb-4">
            {scenarios.map((scenario) => (
              <ScenarioCard
                key={scenario.id}
                scenario={scenario}
                onUpdate={handleUpdateScenario}
                onDelete={handleDeleteScenario}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

export default NetSheet;
