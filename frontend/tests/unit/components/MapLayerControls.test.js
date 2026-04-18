import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MapLayerControls from '../../../src/components/MapLayerControls';

const makeGroups = (overrides = {}) => [
  {
    id: 'crime',
    label: 'Crime',
    categories: [
      {
        id: 'crime-violent',
        label: 'Violent Crime',
        available: true,
        unavailable_reason: null,
        ...overrides['crime-violent'],
      },
      {
        id: 'crime-property',
        label: 'Property Crime',
        available: true,
        unavailable_reason: null,
        ...overrides['crime-property'],
      },
    ],
  },
];

describe('MapLayerControls', () => {
  const isActive = jest.fn().mockReturnValue(false);
  const onToggle = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    isActive.mockReturnValue(false);
  });

  it('renders a button for each available category', () => {
    render(
      <MapLayerControls groups={makeGroups()} isActive={isActive} onToggle={onToggle} />,
    );

    expect(screen.getByRole('button', { name: 'Violent Crime' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Property Crime' })).toBeInTheDocument();
  });

  it('calls onToggle with category id when an available button is clicked', () => {
    render(
      <MapLayerControls groups={makeGroups()} isActive={isActive} onToggle={onToggle} />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Violent Crime' }));

    expect(onToggle).toHaveBeenCalledWith('crime-violent');
  });

  it('renders unavailable category as a disabled button', () => {
    const groups = makeGroups({
      'crime-property': { available: false, unavailable_reason: 'No data available for this area' },
    });

    render(
      <MapLayerControls groups={groups} isActive={isActive} onToggle={onToggle} />,
    );

    const btn = screen.getByRole('button', { name: /Property Crime/ });
    expect(btn).toBeDisabled();
  });

  it('does not call onToggle when an unavailable button is clicked', () => {
    const groups = makeGroups({
      'crime-property': { available: false, unavailable_reason: 'No data available for this area' },
    });

    render(
      <MapLayerControls groups={groups} isActive={isActive} onToggle={onToggle} />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Property Crime/ }));

    expect(onToggle).not.toHaveBeenCalledWith('crime-property');
  });

  it('renders unavailable category with a tooltip showing the unavailable_reason', () => {
    const groups = makeGroups({
      'crime-property': { available: false, unavailable_reason: 'No data available for this area' },
    });

    render(
      <MapLayerControls groups={groups} isActive={isActive} onToggle={onToggle} />,
    );

    const btn = screen.getByRole('button', { name: /Property Crime/ });
    expect(btn).toHaveAttribute('title', 'No data available for this area');
  });

  it('renders nothing when groups is empty', () => {
    const { container } = render(
      <MapLayerControls groups={[]} isActive={isActive} onToggle={onToggle} />,
    );

    expect(container.querySelectorAll('button')).toHaveLength(0);
  });
});
