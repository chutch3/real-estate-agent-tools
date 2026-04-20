import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PropertyDetailPanel from "../PropertyDetailPanel";
import apiClient from "../../apiClient";

jest.mock("../../apiClient", () => ({
  updateDocumentVisibility: jest.fn(),
  getPortalInfo: jest.fn(),
  generateAccessCode: jest.fn(),
}));

const mockProperty = {
  id: "prop-1",
  representation_id: "rep-1",
  formatted_address: "123 Main St",
  documents: [
    { id: "doc-1", filename: "contract.pdf", consumer_visible: false },
  ],
};

describe("PropertyDetailPanel", () => {
  beforeEach(() => {
    apiClient.getPortalInfo.mockResolvedValue({
      portal_url: "http://localhost:3001/portal/tok-abc",
      has_active_code: false,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("calls onDocumentVisibilityChange with no arguments after toggling visibility", async () => {
    apiClient.updateDocumentVisibility.mockResolvedValue({
      id: "doc-1",
      filename: "contract.pdf",
      consumer_visible: true,
    });
    const onDocumentVisibilityChange = jest.fn();

    render(
      <PropertyDetailPanel
        property={mockProperty}
        onClose={jest.fn()}
        onDocumentVisibilityChange={onDocumentVisibilityChange}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Show contract.pdf to client" }),
    );

    await waitFor(() => {
      expect(onDocumentVisibilityChange).toHaveBeenCalledWith();
    });
  });

  it("calls apiClient.updateDocumentVisibility with the correct arguments", async () => {
    apiClient.updateDocumentVisibility.mockResolvedValue({
      id: "doc-1",
      filename: "contract.pdf",
      consumer_visible: true,
    });

    render(
      <PropertyDetailPanel
        property={mockProperty}
        onClose={jest.fn()}
        onDocumentVisibilityChange={jest.fn()}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Show contract.pdf to client" }),
    );

    await waitFor(() => {
      expect(apiClient.updateDocumentVisibility).toHaveBeenCalledWith(
        "prop-1",
        "doc-1",
        true,
      );
    });
  });

  it("does not call onDocumentVisibilityChange when not provided", async () => {
    apiClient.updateDocumentVisibility.mockResolvedValue({
      id: "doc-1",
      filename: "contract.pdf",
      consumer_visible: true,
    });

    expect(() =>
      render(
        <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} />,
      ),
    ).not.toThrow();

    fireEvent.click(
      screen.getByRole("button", { name: "Show contract.pdf to client" }),
    );

    await waitFor(() => {
      expect(apiClient.updateDocumentVisibility).toHaveBeenCalled();
    });
  });

  it("fetches portal info on mount and shows the portal URL", async () => {
    render(<PropertyDetailPanel property={mockProperty} onClose={jest.fn()} />);

    await waitFor(() => {
      expect(apiClient.getPortalInfo).toHaveBeenCalledWith("rep-1");
      expect(
        screen.getByDisplayValue("http://localhost:3001/portal/tok-abc"),
      ).toBeInTheDocument();
    });
  });

  it("shows generate code button when no active code", async () => {
    render(<PropertyDetailPanel property={mockProperty} onClose={jest.fn()} />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /generate code/i }),
      ).toBeInTheDocument();
    });
  });

  it("shows rotate code button when active code exists", async () => {
    apiClient.getPortalInfo.mockResolvedValue({
      portal_url: "http://localhost:3001/portal/tok-abc",
      has_active_code: true,
    });

    render(<PropertyDetailPanel property={mockProperty} onClose={jest.fn()} />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /rotate code/i }),
      ).toBeInTheDocument();
    });
  });

  it("calls generateAccessCode and displays the returned code", async () => {
    apiClient.generateAccessCode.mockResolvedValue({
      code: "ABCD1234",
      portal_url: "http://localhost:3001/portal/tok-abc",
    });

    render(<PropertyDetailPanel property={mockProperty} onClose={jest.fn()} />);

    await waitFor(() => screen.getByRole("button", { name: /generate code/i }));
    fireEvent.click(screen.getByRole("button", { name: /generate code/i }));

    await waitFor(() => {
      expect(apiClient.generateAccessCode).toHaveBeenCalledWith("rep-1");
      expect(screen.getByText("ABCD1234")).toBeInTheDocument();
    });
  });
});
