import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ConsumerPortal from "../ConsumerPortal";
import apiClient from "../../apiClient";

jest.mock("../../apiClient", () => ({
  createConsumerSession: jest.fn(),
}));

jest.mock(
  "../SellerPortalView",
  () =>
    function MockSellerPortalView({ session }) {
      return <div data-testid="seller-portal-view">{session.role}</div>;
    },
);

jest.mock(
  "../BuyerPortalView",
  () =>
    function MockBuyerPortalView({ session }) {
      return <div data-testid="buyer-portal-view">{session.role}</div>;
    },
);

function renderWithToken(token = "test-token") {
  return render(
    <MemoryRouter initialEntries={[`/client/${token}`]}>
      <Routes>
        <Route path="/client/:token" element={<ConsumerPortal />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ConsumerPortal", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("calls apiClient.createConsumerSession with the token from the URL", async () => {
    apiClient.createConsumerSession.mockResolvedValue({
      representation_id: "rep-1",
      role: "listing_agent",
      property_address: "123 Main St",
    });

    renderWithToken("abc-token");

    await waitFor(() => {
      expect(apiClient.createConsumerSession).toHaveBeenCalledWith("abc-token");
    });
  });

  it("renders SellerPortalView for listing_agent role", async () => {
    apiClient.createConsumerSession.mockResolvedValue({
      representation_id: "rep-1",
      role: "listing_agent",
      property_address: "123 Main St",
    });

    renderWithToken("abc-token");

    await waitFor(() => {
      expect(screen.getByTestId("seller-portal-view")).toBeInTheDocument();
    });
  });

  it("renders BuyerPortalView for buyers_agent role", async () => {
    apiClient.createConsumerSession.mockResolvedValue({
      representation_id: "rep-1",
      role: "buyers_agent",
      property_address: "456 Oak Ave",
    });

    renderWithToken("abc-token");

    await waitFor(() => {
      expect(screen.getByTestId("buyer-portal-view")).toBeInTheDocument();
    });
  });

  it("shows error state when session creation fails", async () => {
    apiClient.createConsumerSession.mockRejectedValue(new Error("invalid"));

    renderWithToken("bad-token");

    await waitFor(() => {
      expect(screen.getByText("Link Unavailable")).toBeInTheDocument();
    });
  });

  it("shows loading spinner before session resolves", () => {
    apiClient.createConsumerSession.mockReturnValue(new Promise(() => {}));

    renderWithToken("slow-token");

    expect(screen.queryByTestId("seller-portal-view")).not.toBeInTheDocument();
    expect(screen.queryByTestId("buyer-portal-view")).not.toBeInTheDocument();
    expect(screen.queryByText("Link Unavailable")).not.toBeInTheDocument();
  });
});
