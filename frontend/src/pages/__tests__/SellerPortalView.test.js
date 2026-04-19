import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import SellerPortalView from "../SellerPortalView";
import apiClient from "../../apiClient";

jest.mock("../../apiClient", () => ({
  getConsumerProperty: jest.fn(),
  getConsumerNetSheet: jest.fn(),
  getConsumerDocuments: jest.fn(),
}));

const mockSession = {
  representation_id: "rep-1",
  role: "listing_agent",
  property_address: "123 Main St, Louisville, KY 40202",
};

const mockProperty = {
  address_line1: "123 Main St",
  city: "Louisville",
  state: "KY",
  zip_code: "40202",
  bedrooms: 3,
  bathrooms: 2,
  square_footage: 1800,
  year_built: 1995,
  role: "listing_agent",
  agent_name: "Jane Smith",
  agent_email: "jane@example.com",
};

describe("SellerPortalView", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("calls apiClient.getConsumerProperty on mount", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerNetSheet.mockResolvedValue(null);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<SellerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(apiClient.getConsumerProperty).toHaveBeenCalledTimes(1);
    });
  });

  it("calls apiClient.getConsumerNetSheet on mount", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerNetSheet.mockResolvedValue(null);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<SellerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(apiClient.getConsumerNetSheet).toHaveBeenCalledTimes(1);
    });
  });

  it("calls apiClient.getConsumerDocuments on mount", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerNetSheet.mockResolvedValue(null);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<SellerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(apiClient.getConsumerDocuments).toHaveBeenCalledTimes(1);
    });
  });

  it("displays agent name", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerNetSheet.mockResolvedValue(null);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<SellerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    });
  });

  it("displays property address from session", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerNetSheet.mockResolvedValue(null);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<SellerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(
        screen.getByText("123 Main St, Louisville, KY 40202"),
      ).toBeInTheDocument();
    });
  });

  it("renders full scenario details as read-only when net sheet is present", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerNetSheet.mockResolvedValue({
      scenarios: [
        {
          id: "s-1",
          name: "Base Case",
          sale_price: 350000,
          mortgage_payoff: 200000,
          listing_commission_pct: 3.0,
          buyers_agent_commission_pct: 3.0,
          seller_concessions: 5000,
          annual_tax_amount: 3600,
          closing_date: "2026-06-01",
          closing_cost_items: [],
          total_commission: 21000,
          prorated_tax: 900,
          total_closing_costs: 0,
          total_deductions: 27700,
          net_proceeds: 122300,
        },
      ],
    });
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<SellerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(screen.getByText("$200,000.00")).toBeInTheDocument();
      expect(screen.getByTestId("net-proceeds")).toBeInTheDocument();
    });
    expect(screen.queryByRole("spinbutton", { name: "Sale Price" })).toBeNull();
  });

  it("renders visible documents", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerNetSheet.mockResolvedValue(null);
    apiClient.getConsumerDocuments.mockResolvedValue({
      documents: [{ id: "doc-1", filename: "disclosure.pdf" }],
    });

    render(<SellerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(screen.getByText("disclosure.pdf")).toBeInTheDocument();
    });
  });
});
