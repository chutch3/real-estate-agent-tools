import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PropertyDetailPanel from "../PropertyDetailPanel";
import apiClient from "../../apiClient";

jest.mock("../../apiClient", () => ({
  updateDocumentVisibility: jest.fn(),
  createMagicLink: jest.fn(),
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
});
