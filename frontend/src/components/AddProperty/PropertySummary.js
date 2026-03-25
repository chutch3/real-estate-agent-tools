import React from 'react';
import { FileText } from 'lucide-react';

function Row({ label, value }) {
  if (!value && value !== 0) return null;
  return (
    <div className="flex justify-between py-2 border-b border-linen-100 last:border-0">
      <span className="font-sans text-xs uppercase tracking-widest text-ink-400">{label}</span>
      <span className="font-sans text-sm text-ink-800">{value}</span>
    </div>
  );
}

function SummaryCard({ title, children }) {
  return (
    <div className="rounded-lg border border-linen-200 p-5">
      <h3 className="font-serif text-lg text-ink-800 mb-3">{title}</h3>
      {children}
    </div>
  );
}

function PropertySummary({ propertyData }) {
  const activeFeatures = Object.entries(propertyData.features || {})
    .filter(([, value]) => value === true)
    .map(([key]) => key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '));

  return (
    <div>
      <h2 className="font-serif text-2xl text-ink-900 mb-5">Summary</h2>
      <div className="space-y-4">
        <SummaryCard title="Basic Information">
          <Row label="Address" value={propertyData.formatted_address} />
          <Row label="Property Type" value={propertyData.property_type} />
          <Row label="Bedrooms" value={propertyData.bedrooms} />
          <Row label="Bathrooms" value={propertyData.bathrooms} />
          <Row label="Square Footage" value={propertyData.square_footage} />
          <Row label="Year Built" value={propertyData.year_built} />
        </SummaryCard>

        {activeFeatures.length > 0 && (
          <SummaryCard title="Features">
            <div className="flex flex-wrap gap-2">
              {activeFeatures.map((feature) => (
                <span
                  key={feature}
                  className="font-sans text-xs bg-linen-100 text-ink-700 px-2.5 py-1 rounded-full border border-linen-200"
                >
                  {feature}
                </span>
              ))}
            </div>
          </SummaryCard>
        )}

        <SummaryCard title="Documents">
          {(propertyData.documents || []).length === 0 ? (
            <p className="font-sans text-sm text-ink-300">No documents attached</p>
          ) : (
            <ul className="space-y-2" role="list">
              {(propertyData.documents || []).map((doc) => (
                <li key={doc.id} className="flex items-center gap-2.5">
                  <FileText size={14} className="text-bronze-400 flex-shrink-0" strokeWidth={1.5} />
                  <span className="font-sans text-sm text-ink-700">{doc.filename}</span>
                </li>
              ))}
            </ul>
          )}
        </SummaryCard>
      </div>
    </div>
  );
}

export default PropertySummary;
