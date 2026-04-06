import React from "react";
import { render, screen } from "@testing-library/react";
import MapComponent from "../MapComponent";

const mockFlyTo = jest.fn();

jest.mock("react-map-gl/mapbox", () => {
  const React = require("react");
  return {
    Map: React.forwardRef(function MockMap({ children }, ref) {
      React.useImperativeHandle(ref, () => ({ flyTo: mockFlyTo }), []);
      return React.createElement(
        "div",
        { "data-testid": "map-component" },
        children,
      );
    }),
    Marker: jest.fn(() => null),
  };
});

describe("MapComponent", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the map container", () => {
    const center = { lat: 37.7749, lng: -122.4194 };
    render(<MapComponent center={center} />);
    expect(screen.getByTestId("map-component")).toBeInTheDocument();
  });

  it("renders a Marker at the given center", () => {
    const { Marker } = require("react-map-gl/mapbox");
    const center = { lat: 37.7749, lng: -122.4194 };
    render(<MapComponent center={center} />);
    expect(Marker).toHaveBeenCalledWith(
      expect.objectContaining({ latitude: 37.7749, longitude: -122.4194 }),
      expect.anything(),
    );
  });

  it("flies to the center when center prop is provided", () => {
    const center = { lat: 37.7749, lng: -122.4194 };
    render(<MapComponent center={center} />);
    expect(mockFlyTo).toHaveBeenCalledWith(
      expect.objectContaining({ center: [-122.4194, 37.7749], zoom: 18 }),
    );
  });
});
