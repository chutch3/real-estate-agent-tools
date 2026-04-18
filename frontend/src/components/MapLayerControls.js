import React from "react";
import { ShieldAlert, Home, Layers } from "lucide-react";

const LAYER_ICONS = {
  "crime-violent": ShieldAlert,
  "crime-property": Home,
};

function MapLayerControls({ groups, isActive, onToggle }) {
  const categories = groups.flatMap((g) => g.categories);

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10">
      <div className="flex gap-1 p-1 bg-linen-50/90 backdrop-blur-sm border border-linen-200 rounded-full shadow-lg">
        {categories.map((category) => {
          const Icon = LAYER_ICONS[category.id] ?? Layers;
          const active = isActive(category.id);
          const available = category.available === true;
          return (
            <button
              key={category.id}
              aria-label={category.label}
              aria-pressed={active}
              disabled={!available}
              title={available ? undefined : category.unavailable_reason}
              onClick={available ? () => onToggle(category.id) : undefined}
              className={`flex flex-col items-center gap-1 px-5 py-2 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-300 ${
                !available
                  ? "text-ink-200 cursor-not-allowed"
                  : active
                    ? "bg-bronze-500 text-white"
                    : "text-ink-400 hover:text-ink-700"
              }`}
            >
              <Icon size={18} strokeWidth={1.75} />
              <span
                className={`font-sans text-xs ${active ? "font-semibold" : "font-normal"}`}
              >
                {category.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default MapLayerControls;
