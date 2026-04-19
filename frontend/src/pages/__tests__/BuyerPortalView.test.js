import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import BuyerPortalView from "../BuyerPortalView";
import apiClient from "../../apiClient";

jest.mock("../../apiClient", () => ({
  getConsumerProperty: jest.fn(),
  getConsumerDocuments: jest.fn(),
}));

const mockSession = {
  representation_id: "rep-1",
  role: "buyers_agent",
  property_address: "456 Oak Ave, Indianapolis, IN 46201",
};

const mockProperty = {
  address_line1: "456 Oak Ave",
  city: "Indianapolis",
  state: "IN",
  zip_code: "46201",
  bedrooms: 4,
  bathrooms: 2.5,
  square_footage: 2200,
  year_built: 2003,
  role: "buyers_agent",
  agent_name: "Bob Jones",
  agent_email: "bob@example.com",
};

describe("BuyerPortalView", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("calls apiClient.getConsumerProperty on mount", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<BuyerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(apiClient.getConsumerProperty).toHaveBeenCalledTimes(1);
    });
  });

  it("calls apiClient.getConsumerDocuments on mount", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<BuyerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(apiClient.getConsumerDocuments).toHaveBeenCalledTimes(1);
    });
  });

  it("displays agent name", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<BuyerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(screen.getByText("Bob Jones")).toBeInTheDocument();
    });
  });

  it("displays property address from session", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerDocuments.mockResolvedValue({ documents: [] });

    render(<BuyerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(
        screen.getByText("456 Oak Ave, Indianapolis, IN 46201"),
      ).toBeInTheDocument();
    });
  });

  it("renders visible documents", async () => {
    apiClient.getConsumerProperty.mockResolvedValue(mockProperty);
    apiClient.getConsumerDocuments.mockResolvedValue({
      documents: [{ id: "doc-1", filename: "inspection.pdf" }],
    });

    render(<BuyerPortalView session={mockSession} />);

    await waitFor(() => {
      expect(screen.getByText("inspection.pdf")).toBeInTheDocument();
    });
  });
});
