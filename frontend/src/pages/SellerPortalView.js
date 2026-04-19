import React, { useEffect, useState } from "react";
import { FileText, Mail } from "lucide-react";
import apiClient from "../apiClient";
import ScenarioCard from "../components/ScenarioCard";

function SellerPortalView({ session }) {
  const [property, setProperty] = useState(null);
  const [netSheet, setNetSheet] = useState(null);
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    apiClient.getConsumerProperty().then(setProperty);
    apiClient.getConsumerNetSheet().then(setNetSheet);
    apiClient
      .getConsumerDocuments()
      .then((d) => setDocuments(d?.documents ?? []));
  }, []);

  if (!property) {
    return (
      <div className="min-h-screen bg-linen-50 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-bronze-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-linen-50">
      <div className="max-w-xl mx-auto px-6 py-10 space-y-8">
        {/* Agent branding */}
        <div className="text-center space-y-1">
          <p className="font-sans text-xs uppercase tracking-widest text-bronze-500">
            Your Listing Agent
          </p>
          {property.agent_name && (
            <p className="font-serif text-xl text-ink-900">
              {property.agent_name}
            </p>
          )}
          {property.agent_email && (
            <a
              href={`mailto:${property.agent_email}`}
              className="font-sans text-sm text-bronze-500 hover:underline flex items-center justify-center gap-1"
            >
              <Mail size={13} />
              {property.agent_email}
            </a>
          )}
        </div>

        {/* Property details */}
        <div className="bg-white rounded-xl border border-linen-200 p-6 space-y-4">
          <p className="font-sans text-xs uppercase tracking-widest text-ink-400">
            Your Property
          </p>
          <p className="font-serif text-2xl leading-snug text-ink-900">
            {session.property_address || property.address_line1}
          </p>
          <div className="grid grid-cols-2 gap-4 pt-2">
            {property.bedrooms != null && (
              <div>
                <p className="font-sans text-xs text-ink-400">Bedrooms</p>
                <p className="font-sans text-sm font-medium text-ink-900">
                  {property.bedrooms}
                </p>
              </div>
            )}
            {property.bathrooms != null && (
              <div>
                <p className="font-sans text-xs text-ink-400">Bathrooms</p>
                <p className="font-sans text-sm font-medium text-ink-900">
                  {property.bathrooms}
                </p>
              </div>
            )}
            {property.square_footage != null && (
              <div>
                <p className="font-sans text-xs text-ink-400">Sq Ft</p>
                <p className="font-sans text-sm font-medium text-ink-900">
                  {property.square_footage.toLocaleString()}
                </p>
              </div>
            )}
            {property.year_built != null && (
              <div>
                <p className="font-sans text-xs text-ink-400">Year Built</p>
                <p className="font-sans text-sm font-medium text-ink-900">
                  {property.year_built}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Net sheet */}
        {netSheet && netSheet.scenarios && netSheet.scenarios.length > 0 && (
          <div className="space-y-4">
            <p className="font-sans text-xs uppercase tracking-widest text-ink-400">
              Net Sheet
            </p>
            <div className="flex gap-5 overflow-x-auto pb-2">
              {netSheet.scenarios.map((s) => (
                <ScenarioCard
                  key={s.id}
                  scenario={s}
                  onUpdate={() => {}}
                  onDelete={() => {}}
                  readOnly
                />
              ))}
            </div>
          </div>
        )}

        {/* Documents */}
        {documents.length > 0 && (
          <div className="bg-white rounded-xl border border-linen-200 p-6 space-y-3">
            <p className="font-sans text-xs uppercase tracking-widest text-ink-400">
              Documents
            </p>
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li key={doc.id}>
                  <a
                    href={`${apiClient.baseURL}/documents/${doc.id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 font-sans text-sm text-bronze-500 hover:underline"
                  >
                    <FileText size={13} strokeWidth={1.5} />
                    {doc.filename}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default SellerPortalView;
