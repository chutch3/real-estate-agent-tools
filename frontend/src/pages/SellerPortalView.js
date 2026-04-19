import React, { useEffect, useState } from "react";
import { FileText, Phone, Mail } from "lucide-react";

const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";

function SellerPortalView({ session }) {
  const [property, setProperty] = useState(null);
  const [netSheet, setNetSheet] = useState(null);
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/consumer/property`, { credentials: "include" })
      .then((r) => r.json())
      .then(setProperty);
    fetch(`${API_BASE}/consumer/net-sheet`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then(setNetSheet);
    fetch(`${API_BASE}/consumer/documents`, { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setDocuments(d.documents ?? []));
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
          <div className="bg-white rounded-xl border border-linen-200 p-6 space-y-4">
            <p className="font-sans text-xs uppercase tracking-widest text-ink-400">
              Net Sheet
            </p>
            {netSheet.scenarios.map((s) => (
              <div
                key={s.id}
                className="border-t border-linen-100 pt-4 space-y-2"
              >
                <p className="font-sans text-sm font-medium text-ink-900">
                  {s.name}
                </p>
                <div className="flex justify-between font-sans text-sm">
                  <span className="text-ink-400">Sale Price</span>
                  <span className="text-ink-900">
                    ${s.sale_price.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between font-sans text-sm">
                  <span className="text-ink-400">Net Proceeds</span>
                  <span className="font-medium text-ink-900">
                    ${s.net_proceeds.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
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
                    href={`${API_BASE}/documents/${doc.id}`}
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
