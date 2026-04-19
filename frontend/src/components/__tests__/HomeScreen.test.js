import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import HomeScreen from "../HomeScreen";
import apiClient from "../../apiClient";
import useLayers from "../../hooks/useLayers";

jest.mock("../../apiClient", () => ({
  listProperties: jest.fn(),
  uploadDocument: jest.fn(),
  addDocumentToProperty: jest.fn(),
  updateDocumentVisibility: jest.fn(),
}));

jest.mock("../../hooks/useLayers");

jest.mock("react-map-gl/mapbox", () => {
  const React = require("react");
  return {
    Map: React.forwardRef(function MockMap({ children }, ref) {
      return React.createElement(
        "div",
        { "data-testid": "mapbox-map" },
        children,
      );
    }),
    Marker: ({ latitude, longitude, onClick }) =>
      React.createElement("button", {
        "data-testid": `marker-${latitude}-${longitude}`,
        onClick,
      }),
    Source: jest.fn(({ children }) => children || null),
    Layer: jest.fn(() => null),
  };
});

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => jest.fn(),
}));

describe("HomeScreen", () => {
  const mockProperties = [
    {
      id: "prop-1",
      latitude: 37.4225,
      longitude: -122.0847,
      formatted_address: "1600 Amphitheatre Pkwy",
    },
    {
      id: "prop-2",
      latitude: 37.3382,
      longitude: -121.8863,
      formatted_address: "1 Infinite Loop",
    },
  ];

  beforeEach(() => {
    apiClient.listProperties.mockResolvedValue(mockProperties);
    useLayers.mockReturnValue({
      groups: [],
      isActive: jest.fn().mockReturnValue(false),
      toggle: jest.fn(),
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("fetches and displays properties on mount", async () => {
    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(apiClient.listProperties).toHaveBeenCalledTimes(1);
      expect(
        screen.getByTestId("marker-37.4225--122.0847"),
      ).toBeInTheDocument();
    });
  });

  it("renders a map", async () => {
    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("mapbox-map")).toBeInTheDocument(),
    );
  });

  it("renders a marker for each property", async () => {
    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(
        screen.getByTestId("marker-37.4225--122.0847"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("marker-37.3382--121.8863"),
      ).toBeInTheDocument();
    });
  });

  it("opens a detail panel when a marker is clicked", async () => {
    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );
    await waitFor(() => screen.getByTestId("marker-37.4225--122.0847"));
    fireEvent.click(screen.getByTestId("marker-37.4225--122.0847"));
    const panel = screen.getByTestId("property-detail-panel");
    expect(panel).toBeInTheDocument();
    expect(
      within(panel).getByText("1600 Amphitheatre Pkwy"),
    ).toBeInTheDocument();
  });

  it("renders an Add New Property button", async () => {
    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Add new property")).toBeInTheDocument(),
    );
  });

  it("shows an upload error in the detail panel when the upload fails", async () => {
    apiClient.uploadDocument.mockRejectedValue(new Error("network error"));
    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );
    await waitFor(() => screen.getByTestId("marker-37.4225--122.0847"));
    fireEvent.click(screen.getByTestId("marker-37.4225--122.0847"));
    const file = new File(["content"], "contract.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(document.querySelector('input[type="file"]'), {
      target: { files: [file] },
    });
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("navigates to /add-property when the add button is clicked", async () => {
    const navigateMock = jest.fn();
    jest
      .spyOn(require("react-router-dom"), "useNavigate")
      .mockReturnValue(navigateMock);
    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );
    await waitFor(() => screen.getByLabelText("Add new property"));
    fireEvent.click(screen.getByLabelText("Add new property"));
    expect(navigateMock).toHaveBeenCalledWith("/add-property");
  });

  it("calls updateDocumentVisibility and refreshes list when eye toggle is clicked", async () => {
    apiClient.listProperties.mockResolvedValue([
      {
        id: "prop-1",
        latitude: 37.4225,
        longitude: -122.0847,
        formatted_address: "1600 Amphitheatre Pkwy",
        documents: [
          { id: "doc-1", filename: "contract.pdf", consumer_visible: false },
        ],
      },
    ]);
    apiClient.updateDocumentVisibility.mockResolvedValue({
      id: "doc-1",
      filename: "contract.pdf",
      consumer_visible: true,
    });

    render(
      <MemoryRouter>
        <HomeScreen />
      </MemoryRouter>,
    );

    await waitFor(() => screen.getByTestId("marker-37.4225--122.0847"));
    fireEvent.click(screen.getByTestId("marker-37.4225--122.0847"));
    await waitFor(() => screen.getByTestId("property-detail-panel"));

    fireEvent.click(
      screen.getByRole("button", { name: "Show contract.pdf to client" }),
    );

    await waitFor(() => {
      expect(apiClient.updateDocumentVisibility).toHaveBeenCalledWith(
        "prop-1",
        "doc-1",
        true,
      );
      expect(apiClient.listProperties).toHaveBeenCalledTimes(2);
    });
  });
});
