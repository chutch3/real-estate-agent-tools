import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
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
    <MemoryRouter initialEntries={[`/portal/${token}`]}>
      <Routes>
        <Route path="/portal/:portalToken" element={<ConsumerPortal />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ConsumerPortal", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows a code entry form on initial load", () => {
    renderWithToken("abc-token");

    expect(
      screen.getByRole("textbox", { name: /access code/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /continue/i }),
    ).toBeInTheDocument();
  });

  it("calls createConsumerSession with portal token and entered code on submit", async () => {
    apiClient.createConsumerSession.mockResolvedValue({
      representation_id: "rep-1",
      role: "listing_agent",
      property_address: "123 Main St",
    });

    renderWithToken("abc-token");

    fireEvent.change(screen.getByRole("textbox", { name: /access code/i }), {
      target: { value: "ABCD1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(apiClient.createConsumerSession).toHaveBeenCalledWith(
        "abc-token",
        "ABCD1234",
      );
    });
  });

  it("renders SellerPortalView after valid code for listing_agent role", async () => {
    apiClient.createConsumerSession.mockResolvedValue({
      representation_id: "rep-1",
      role: "listing_agent",
      property_address: "123 Main St",
    });

    renderWithToken("abc-token");

    fireEvent.change(screen.getByRole("textbox", { name: /access code/i }), {
      target: { value: "ABCD1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(screen.getByTestId("seller-portal-view")).toBeInTheDocument();
    });
  });

  it("renders BuyerPortalView after valid code for buyers_agent role", async () => {
    apiClient.createConsumerSession.mockResolvedValue({
      representation_id: "rep-1",
      role: "buyers_agent",
      property_address: "456 Oak Ave",
    });

    renderWithToken("abc-token");

    fireEvent.change(screen.getByRole("textbox", { name: /access code/i }), {
      target: { value: "ABCD1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(screen.getByTestId("buyer-portal-view")).toBeInTheDocument();
    });
  });

  it("shows error message when code is invalid", async () => {
    apiClient.createConsumerSession.mockRejectedValue(
      new Error("unauthorized"),
    );

    renderWithToken("abc-token");

    fireEvent.change(screen.getByRole("textbox", { name: /access code/i }), {
      target: { value: "WRONGCOD" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid access code/i)).toBeInTheDocument();
    });
  });

  it("shows spinner while session request is in flight", async () => {
    apiClient.createConsumerSession.mockReturnValue(new Promise(() => {}));

    renderWithToken("abc-token");

    fireEvent.change(screen.getByRole("textbox", { name: /access code/i }), {
      target: { value: "ABCD1234" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
  });
});
