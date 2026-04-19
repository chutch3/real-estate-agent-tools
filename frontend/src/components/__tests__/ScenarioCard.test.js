import React from "react";
import { render, screen } from "@testing-library/react";
import ScenarioCard from "../ScenarioCard";

const mockScenario = {
  id: "s-1",
  name: "Base Case",
  sale_price: 350000,
  mortgage_payoff: 200000,
  listing_commission_pct: 3.0,
  buyers_agent_commission_pct: 3.0,
  seller_concessions: 5000,
  annual_tax_amount: 3600,
  closing_date: "2026-06-01",
  closing_cost_items: [{ label: "Title Insurance", amount: 800 }],
  total_commission: 21000,
  prorated_tax: 900,
  total_closing_costs: 800,
  total_deductions: 27700,
  net_proceeds: 122300,
};

describe("ScenarioCard", () => {
  it("renders scenario name in read-only mode as text, not an input", () => {
    render(
      <ScenarioCard
        scenario={mockScenario}
        onUpdate={jest.fn()}
        onDelete={jest.fn()}
        readOnly
      />,
    );

    expect(screen.queryByRole("textbox", { name: "Scenario name" })).toBeNull();
    expect(screen.getByText("Base Case")).toBeInTheDocument();
  });

  it("renders sale price as text in read-only mode", () => {
    render(
      <ScenarioCard
        scenario={mockScenario}
        onUpdate={jest.fn()}
        onDelete={jest.fn()}
        readOnly
      />,
    );

    expect(screen.queryByRole("spinbutton", { name: "Sale Price" })).toBeNull();
    expect(screen.getByText("$350,000.00")).toBeInTheDocument();
  });

  it("hides the delete button in read-only mode", () => {
    render(
      <ScenarioCard
        scenario={mockScenario}
        onUpdate={jest.fn()}
        onDelete={jest.fn()}
        readOnly
      />,
    );

    expect(screen.queryByRole("button", { name: /delete/i })).toBeNull();
  });

  it("hides the add item button in read-only mode", () => {
    render(
      <ScenarioCard
        scenario={mockScenario}
        onUpdate={jest.fn()}
        onDelete={jest.fn()}
        readOnly
      />,
    );

    expect(screen.queryByRole("button", { name: "Add item" })).toBeNull();
  });

  it("still shows computed totals in read-only mode", () => {
    render(
      <ScenarioCard
        scenario={mockScenario}
        onUpdate={jest.fn()}
        onDelete={jest.fn()}
        readOnly
      />,
    );

    expect(screen.getByTestId("net-proceeds")).toBeInTheDocument();
  });
});
