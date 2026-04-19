import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import GeneratePost from "../GeneratePost";
import apiClient from "../../apiClient";

jest.mock("../../apiClient", () => ({
  generatePost: jest.fn(),
  getMe: jest.fn(),
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useLocation: () => ({
    state: {
      property: {
        id: "prop-1",
        formatted_address: "123 Main St",
      },
    },
  }),
  useNavigate: () => jest.fn(),
}));

describe("GeneratePost", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("pre-populates agent name, contact, and company from getMe on mount", async () => {
    apiClient.getMe.mockResolvedValue({
      name: "Jane Smith",
      email: "jane@example.com",
      brokerage: { name: "Acme Realty" },
    });

    render(
      <MemoryRouter>
        <GeneratePost />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByLabelText("Agent Name").value).toBe("Jane Smith");
      expect(screen.getByLabelText("Contact").value).toBe("jane@example.com");
      expect(screen.getByLabelText("Company").value).toBe("Acme Realty");
    });
  });

  it("calls generatePost with property id not address", async () => {
    apiClient.getMe.mockResolvedValue({
      name: "Jane Smith",
      email: "jane@example.com",
    });
    apiClient.generatePost.mockResolvedValue({ post: "Great listing!" });

    render(
      <MemoryRouter>
        <GeneratePost />
      </MemoryRouter>,
    );

    await waitFor(() => screen.getByLabelText("Agent Name"));
    fireEvent.click(screen.getByRole("button", { name: /generate/i }));

    await waitFor(() => {
      expect(apiClient.generatePost).toHaveBeenCalledWith(
        "prop-1",
        expect.objectContaining({ agent_name: "Jane Smith" }),
        null,
      );
    });
  });
});
