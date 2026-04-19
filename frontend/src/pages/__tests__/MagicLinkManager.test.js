import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import MagicLinkManager from "../MagicLinkManager";
import apiClient from "../../apiClient";

jest.mock("../../apiClient", () => ({
  listMagicLinks: jest.fn(),
  createMagicLink: jest.fn(),
  revokeMagicLink: jest.fn(),
}));

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useLocation: () => ({
    state: {
      property: {
        id: "prop-1",
        representation_id: "rep-1",
        formatted_address: "123 Main St, Louisville, KY",
      },
    },
  }),
  useNavigate: () => jest.fn(),
}));

const mockToken = {
  id: "tok-1",
  token: "abc123",
  expires_at: "2026-05-19T00:00:00Z",
  last_accessed_at: null,
};

describe("MagicLinkManager", () => {
  afterEach(() => jest.clearAllMocks());

  it("shows the property address", async () => {
    apiClient.listMagicLinks.mockResolvedValue({ tokens: [] });

    render(
      <MemoryRouter>
        <MagicLinkManager />
      </MemoryRouter>,
    );

    expect(
      await screen.findByText("123 Main St, Louisville, KY"),
    ).toBeInTheDocument();
  });

  it("lists existing magic links on mount", async () => {
    apiClient.listMagicLinks.mockResolvedValue({ tokens: [mockToken] });

    render(
      <MemoryRouter>
        <MagicLinkManager />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/localhost\/client\/abc123/)).toBeInTheDocument();
    });
    expect(apiClient.listMagicLinks).toHaveBeenCalledWith("rep-1");
  });

  it("shows never accessed when last_accessed_at is null", async () => {
    apiClient.listMagicLinks.mockResolvedValue({ tokens: [mockToken] });

    render(
      <MemoryRouter>
        <MagicLinkManager />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Never accessed")).toBeInTheDocument();
  });

  it("shows empty state when no links exist", async () => {
    apiClient.listMagicLinks.mockResolvedValue({ tokens: [] });

    render(
      <MemoryRouter>
        <MagicLinkManager />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/no active links/i)).toBeInTheDocument();
  });

  it("creates a link and refreshes the list", async () => {
    apiClient.listMagicLinks
      .mockResolvedValueOnce({ tokens: [] })
      .mockResolvedValueOnce({ tokens: [mockToken] });
    apiClient.createMagicLink.mockResolvedValue(mockToken);

    render(
      <MemoryRouter>
        <MagicLinkManager />
      </MemoryRouter>,
    );

    await screen.findByText(/no active links/i);
    fireEvent.click(screen.getByRole("button", { name: /create link/i }));

    await waitFor(() => {
      expect(apiClient.createMagicLink).toHaveBeenCalledWith("rep-1");
      expect(apiClient.listMagicLinks).toHaveBeenCalledTimes(2);
    });
  });

  it("revokes a link and refreshes the list", async () => {
    apiClient.listMagicLinks
      .mockResolvedValueOnce({ tokens: [mockToken] })
      .mockResolvedValueOnce({ tokens: [] });
    apiClient.revokeMagicLink.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <MagicLinkManager />
      </MemoryRouter>,
    );

    await screen.findByText(/localhost\/client\/abc123/);
    fireEvent.click(screen.getByRole("button", { name: /revoke/i }));

    await waitFor(() => {
      expect(apiClient.revokeMagicLink).toHaveBeenCalledWith("rep-1", "tok-1");
      expect(apiClient.listMagicLinks).toHaveBeenCalledTimes(2);
    });
  });
});
