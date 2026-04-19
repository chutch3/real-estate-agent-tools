import React, { useState, useEffect, useRef } from "react";
import { Trash2, ExternalLink, Plus } from "lucide-react";

const NUMERIC_FIELDS = [
  "sale_price",
  "mortgage_payoff",
  "listing_commission_pct",
  "buyers_agent_commission_pct",
  "seller_concessions",
  "annual_tax_amount",
];

function fmt(value) {
  if (value == null) return "—";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function ScenarioCard({ scenario, onUpdate, onDelete, readOnly = false }) {
  const [fields, setFields] = useState({
    name: scenario.name ?? "",
    sale_price: scenario.sale_price ?? "",
    mortgage_payoff: scenario.mortgage_payoff ?? "",
    listing_commission_pct: scenario.listing_commission_pct ?? "",
    buyers_agent_commission_pct: scenario.buyers_agent_commission_pct ?? "",
    seller_concessions: scenario.seller_concessions ?? "",
    annual_tax_amount: scenario.annual_tax_amount ?? "",
    closing_date: scenario.closing_date ?? "",
  });
  const [costItems, setCostItems] = useState(
    (scenario.closing_cost_items ?? []).map((item) => ({
      label: item.label,
      amount: String(item.amount),
    })),
  );
  const [confirmDelete, setConfirmDelete] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    return () => clearTimeout(debounceRef.current);
  }, []);

  const scheduleUpdate = (fieldUpdates) => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(
      () => onUpdate(scenario.id, fieldUpdates),
      600,
    );
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    const parsed = NUMERIC_FIELDS.includes(name)
      ? value === ""
        ? null
        : parseFloat(value)
      : value;
    setFields((prev) => ({ ...prev, [name]: value }));
    scheduleUpdate({ [name]: parsed });
  };

  const flushCostItems = (items) => {
    scheduleUpdate({
      closing_cost_items: items.map((item) => ({
        label: item.label,
        amount: item.amount === "" ? 0 : parseFloat(item.amount),
      })),
    });
  };

  const handleCostItemChange = (index, field, value) => {
    const updated = costItems.map((item, i) =>
      i === index ? { ...item, [field]: value } : item,
    );
    setCostItems(updated);
    flushCostItems(updated);
  };

  const handleAddCostItem = () => {
    const updated = [...costItems, { label: "", amount: "" }];
    setCostItems(updated);
    flushCostItems(updated);
  };

  const handleRemoveCostItem = (index) => {
    const updated = costItems.filter((_, i) => i !== index);
    setCostItems(updated);
    flushCostItems(updated);
  };

  const handleDeleteClick = () => {
    if (confirmDelete) {
      onDelete(scenario.id);
    } else {
      setConfirmDelete(true);
    }
  };

  const inputClass =
    "w-full px-3 py-1.5 border border-linen-300 rounded bg-white font-sans text-sm text-ink-900 focus:outline-none focus:border-bronze-400 transition-colors";
  const labelClass = "block font-sans text-xs text-ink-400 mb-1";

  return (
    <div
      data-testid="scenario-card"
      className="flex-shrink-0 w-72 bg-white rounded-lg border border-linen-200 shadow-sm flex flex-col"
    >
      {/* Name header */}
      <div className="px-4 pt-4 pb-3 border-b border-linen-100">
        {readOnly ? (
          <p className="font-serif text-lg text-ink-900">{scenario.name}</p>
        ) : (
          <input
            name="name"
            value={fields.name}
            onChange={handleChange}
            aria-label="Scenario name"
            className="w-full font-serif text-lg text-ink-900 bg-transparent border-none focus:outline-none focus:ring-0 p-0"
            placeholder="Scenario name"
          />
        )}
      </div>

      {/* Inputs */}
      <div className="px-4 py-4 space-y-3 flex-1">
        <div>
          <p className={labelClass}>Sale Price</p>
          {readOnly ? (
            <p className="font-sans text-sm text-ink-900">
              ${fmt(scenario.sale_price)}
            </p>
          ) : (
            <input
              id={`sale_price-${scenario.id}`}
              aria-label="Sale Price"
              name="sale_price"
              type="number"
              value={fields.sale_price}
              onChange={handleChange}
              className={inputClass}
              placeholder="350000"
            />
          )}
        </div>

        <div>
          <p className={labelClass}>Mortgage Payoff</p>
          {readOnly ? (
            <p className="font-sans text-sm text-ink-900">
              ${fmt(scenario.mortgage_payoff)}
            </p>
          ) : (
            <input
              id={`mortgage_payoff-${scenario.id}`}
              aria-label="Mortgage Payoff"
              name="mortgage_payoff"
              type="number"
              value={fields.mortgage_payoff}
              onChange={handleChange}
              className={inputClass}
              placeholder="0"
            />
          )}
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <p className={labelClass}>Listing Commission %</p>
            {readOnly ? (
              <p className="font-sans text-sm text-ink-900">
                {fmt(scenario.listing_commission_pct)}%
              </p>
            ) : (
              <input
                id={`listing_commission_pct-${scenario.id}`}
                aria-label="Listing Commission %"
                name="listing_commission_pct"
                type="number"
                step="0.1"
                value={fields.listing_commission_pct}
                onChange={handleChange}
                className={inputClass}
                placeholder="3.0"
              />
            )}
          </div>
          <div className="flex-1">
            <p className={labelClass}>{"Buyer's Agent Commission %"}</p>
            {readOnly ? (
              <p className="font-sans text-sm text-ink-900">
                {fmt(scenario.buyers_agent_commission_pct)}%
              </p>
            ) : (
              <input
                id={`buyers_agent_commission_pct-${scenario.id}`}
                aria-label="Buyer's Agent Commission %"
                name="buyers_agent_commission_pct"
                type="number"
                step="0.1"
                value={fields.buyers_agent_commission_pct}
                onChange={handleChange}
                className={inputClass}
                placeholder="3.0"
              />
            )}
          </div>
        </div>

        <div>
          <p className={labelClass}>Seller Concessions</p>
          {readOnly ? (
            <p className="font-sans text-sm text-ink-900">
              ${fmt(scenario.seller_concessions)}
            </p>
          ) : (
            <input
              id={`seller_concessions-${scenario.id}`}
              aria-label="Seller Concessions"
              name="seller_concessions"
              type="number"
              value={fields.seller_concessions}
              onChange={handleChange}
              className={inputClass}
              placeholder="0"
            />
          )}
        </div>

        <div>
          <p className={labelClass}>Closing Date</p>
          {readOnly ? (
            <p className="font-sans text-sm text-ink-900">
              {scenario.closing_date || "—"}
            </p>
          ) : (
            <input
              id={`closing_date-${scenario.id}`}
              aria-label="Closing Date"
              name="closing_date"
              type="date"
              value={fields.closing_date}
              onChange={handleChange}
              className={inputClass}
            />
          )}
        </div>

        <div>
          <p className={labelClass}>Prior Year Annual Tax</p>
          {readOnly ? (
            <p className="font-sans text-sm text-ink-900">
              ${fmt(scenario.annual_tax_amount)}
            </p>
          ) : (
            <input
              id={`annual_tax_amount-${scenario.id}`}
              aria-label="Annual Tax Amount"
              name="annual_tax_amount"
              type="number"
              value={fields.annual_tax_amount}
              onChange={handleChange}
              className={inputClass}
              placeholder="0"
            />
          )}
          {scenario.tax_lookup_url && !readOnly && (
            <a
              href={scenario.tax_lookup_url}
              target="_blank"
              rel="noreferrer"
              aria-label="Look up tax on DLGF"
              className="inline-flex items-center gap-1 font-sans text-xs text-bronze-500 hover:text-bronze-700 mt-1"
            >
              <ExternalLink size={10} strokeWidth={1.5} />
              Look up tax
            </a>
          )}
          {scenario.tax_guidance && (
            <p
              data-testid="tax-guidance"
              className="font-sans text-xs text-ink-400 mt-1.5 leading-snug"
            >
              {scenario.tax_guidance}
            </p>
          )}
        </div>

        {/* Closing cost items */}
        <div>
          <p className={labelClass}>Additional Closing Costs</p>
          {readOnly ? (
            costItems.length > 0 ? (
              <ul className="space-y-1">
                {costItems.map((item, index) => (
                  <li
                    key={index}
                    className="flex justify-between font-sans text-sm text-ink-700"
                  >
                    <span>{item.label || "—"}</span>
                    <span>${fmt(parseFloat(item.amount) || 0)}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="font-sans text-sm text-ink-300">None</p>
            )
          ) : (
            <>
              {costItems.map((item, index) => (
                <div key={index} className="flex items-center gap-1.5 mb-1.5">
                  <input
                    type="text"
                    value={item.label}
                    onChange={(e) =>
                      handleCostItemChange(index, "label", e.target.value)
                    }
                    placeholder="Item description"
                    aria-label={`Closing cost item ${index + 1} description`}
                    className={`${inputClass} flex-1`}
                  />
                  <input
                    type="number"
                    value={item.amount}
                    onChange={(e) =>
                      handleCostItemChange(index, "amount", e.target.value)
                    }
                    placeholder="0"
                    aria-label={`Closing cost item ${index + 1} amount`}
                    className={`${inputClass} w-24`}
                  />
                  <button
                    onClick={() => handleRemoveCostItem(index)}
                    aria-label={`Remove ${item.label || `item ${index + 1}`}`}
                    className="text-ink-300 hover:text-red-500 transition-colors focus:outline-none flex-shrink-0"
                  >
                    ×
                  </button>
                </div>
              ))}
              <button
                onClick={handleAddCostItem}
                aria-label="Add item"
                className="flex items-center gap-1 font-sans text-xs text-bronze-500 hover:text-bronze-700 mt-1 transition-colors focus:outline-none"
              >
                <Plus size={10} strokeWidth={2.5} />
                Add item
              </button>
            </>
          )}
        </div>
      </div>

      {/* Computed totals */}
      <div className="px-4 py-4 bg-linen-50 border-t border-linen-100 space-y-2">
        <p className="font-sans text-xs uppercase tracking-widest text-ink-400 mb-2">
          Computed
        </p>

        <div className="flex justify-between font-sans text-sm text-ink-700">
          <span>Commission</span>
          <span>${fmt(scenario.total_commission)}</span>
        </div>

        <div className="font-sans text-sm text-ink-700">
          <div className="flex justify-between">
            <span>Tax Proration</span>
            <span>${fmt(scenario.prorated_tax)}</span>
          </div>
          {scenario.tax_proration_breakdown?.formula && (
            <p className="text-xs text-ink-400 mt-0.5 leading-snug">
              {scenario.tax_proration_breakdown.formula}
            </p>
          )}
          {scenario.tax_proration_breakdown?.method_note && (
            <p className="text-xs text-ink-300 mt-0.5 leading-snug italic">
              {scenario.tax_proration_breakdown.method_note}
            </p>
          )}
        </div>

        <div className="flex justify-between font-sans text-sm text-ink-700">
          <span>Closing Costs</span>
          <span>${fmt(scenario.total_closing_costs)}</span>
        </div>

        <div className="flex justify-between font-sans text-sm text-ink-700">
          <span>Total Deductions</span>
          <span>${fmt(scenario.total_deductions)}</span>
        </div>

        <div className="pt-2 border-t border-linen-200">
          <p className="font-sans text-xs uppercase tracking-widest text-ink-400 mb-1">
            Net Proceeds
          </p>
          <p
            data-testid="net-proceeds"
            className="font-serif text-2xl text-ink-900"
          >
            ${fmt(scenario.net_proceeds)}
          </p>
        </div>
      </div>

      {/* Delete */}
      {!readOnly && (
        <div className="px-4 py-3 border-t border-linen-100 flex justify-end">
          <button
            onClick={handleDeleteClick}
            aria-label={confirmDelete ? "Confirm delete" : "Delete scenario"}
            className={`flex items-center gap-1.5 font-sans text-xs transition-colors focus:outline-none ${
              confirmDelete
                ? "text-red-600 hover:text-red-800"
                : "text-ink-300 hover:text-red-500"
            }`}
          >
            <Trash2 size={12} strokeWidth={1.5} />
            {confirmDelete ? "Confirm delete" : "Delete scenario"}
          </button>
        </div>
      )}
    </div>
  );
}

export default ScenarioCard;
