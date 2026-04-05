import React from 'react';

const LAYER_GRADIENTS = {
  'crime-violent': 'linear-gradient(to right, #F8F5F0, #B85450, #8B2E2B)',
  'crime-property': 'linear-gradient(to right, #F8F5F0, #B89A78, #3E3B37)',
};

const DEFAULT_GRADIENT = 'linear-gradient(to right, #F8F5F0, #92400e, #1c1917)';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatDate(dateStr) {
  const [year, month] = dateStr.split('-').map(Number);
  return `${MONTHS[month - 1]} ${year}`;
}

function formatCount(count) {
  return new Intl.NumberFormat('en-US').format(count);
}

function CrimeLayerLegend({ groups, isActive, panelOpen = false }) {
  const activeCategories = groups
    .flatMap((g) => g.categories)
    .filter((c) => isActive(c.id));

  if (activeCategories.length === 0) return null;

  return (
    <div
      className="absolute bottom-6 bg-linen-50/90 backdrop-blur-sm border border-linen-200 rounded-lg px-3 py-2 animate-fade-up flex flex-col gap-3"
      style={{ right: panelOpen ? '336px' : '16px' }}
      role="img"
      aria-label="Crime density scale from low to high"
    >
      {activeCategories.map((category) => (
        <div key={category.id}>
          <p className="font-sans text-xs font-semibold text-ink-700">{category.label}</p>
          <p className="font-sans text-xs text-ink-400">{`${formatDate(category.date_from)} – ${formatDate(category.date_to)}`}</p>
          <p className="font-sans text-xs text-ink-400 mb-1">{`${formatCount(category.record_count)} incidents`}</p>
          <div className="flex items-center gap-2">
            <span className="font-sans text-xs text-ink-400">Low</span>
            <div
              className="h-2 w-24 rounded-full"
              style={{ background: LAYER_GRADIENTS[category.id] ?? DEFAULT_GRADIENT }}
              aria-hidden="true"
            />
            <span className="font-sans text-xs text-ink-400">High</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default CrimeLayerLegend;
