import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import MapLayerControls from "../MapLayerControls";

const GROUPS = [
  {
    id: "crime",
    label: "Crime",
    categories: [
      {
        id: "crime-violent",
        label: "Violent Crime",
        available: true,
        unavailable_reason: null,
      },
      {
        id: "crime-property",
        label: "Property Crime",
        available: true,
        unavailable_reason: null,
      },
    ],
  },
];

describe("MapLayerControls", () => {
  it("renders a button for each category", () => {
    render(
      <MapLayerControls
        groups={GROUPS}
        isActive={jest.fn().mockReturnValue(false)}
        onToggle={jest.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Violent Crime" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Property Crime" }),
    ).toBeInTheDocument();
  });

  it("shows the category label text in each segment", () => {
    render(
      <MapLayerControls
        groups={GROUPS}
        isActive={jest.fn().mockReturnValue(false)}
        onToggle={jest.fn()}
      />,
    );
    expect(screen.getByText("Violent Crime")).toBeInTheDocument();
    expect(screen.getByText("Property Crime")).toBeInTheDocument();
  });

  it("sets aria-pressed true on active segments", () => {
    const isActive = jest.fn((id) => id === "crime-violent");
    render(
      <MapLayerControls
        groups={GROUPS}
        isActive={isActive}
        onToggle={jest.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Violent Crime" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: "Property Crime" }),
    ).toHaveAttribute("aria-pressed", "false");
  });

  it("calls onToggle with the correct category id when a segment is clicked", () => {
    const onToggle = jest.fn();
    render(
      <MapLayerControls
        groups={GROUPS}
        isActive={jest.fn().mockReturnValue(false)}
        onToggle={onToggle}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Violent Crime" }));
    expect(onToggle).toHaveBeenCalledWith("crime-violent");
  });

  it("renders segments for all categories across multiple groups", () => {
    const multiGroups = [
      {
        id: "crime",
        label: "Crime",
        categories: [
          {
            id: "crime-violent",
            label: "Violent Crime",
            available: true,
            unavailable_reason: null,
          },
        ],
      },
      {
        id: "zoning",
        label: "Zoning",
        categories: [
          {
            id: "zoning-residential",
            label: "Residential",
            available: true,
            unavailable_reason: null,
          },
        ],
      },
    ];
    render(
      <MapLayerControls
        groups={multiGroups}
        isActive={jest.fn().mockReturnValue(false)}
        onToggle={jest.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Violent Crime" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Residential" }),
    ).toBeInTheDocument();
  });
});
