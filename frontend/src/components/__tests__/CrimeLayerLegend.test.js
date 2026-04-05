import React from 'react';
import { render, screen } from '@testing-library/react';
import CrimeLayerLegend from '../CrimeLayerLegend';

const GROUPS = [
  {
    id: 'crime',
    label: 'Crime',
    categories: [
      {
        id: 'crime-violent',
        label: 'Violent Crime',
        date_from: '2025-04-01',
        date_to: '2026-04-01',
        record_count: 1234,
      },
      {
        id: 'crime-property',
        label: 'Property Crime',
        date_from: '2025-04-01',
        date_to: '2026-04-01',
        record_count: 4891,
      },
    ],
  },
];

describe('CrimeLayerLegend', () => {
  it('renders nothing when no layers are active', () => {
    const { container } = render(
      <CrimeLayerLegend groups={GROUPS} isActive={() => false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders only active layers', () => {
    render(
      <CrimeLayerLegend groups={GROUPS} isActive={(id) => id === 'crime-violent'} />
    );
    expect(screen.getByText('Violent Crime')).toBeInTheDocument();
    expect(screen.queryByText('Property Crime')).not.toBeInTheDocument();
  });

  it('renders the formatted date range for each active layer', () => {
    render(
      <CrimeLayerLegend groups={GROUPS} isActive={(id) => id === 'crime-violent'} />
    );
    expect(screen.getByText('Apr 2025 – Apr 2026')).toBeInTheDocument();
  });

  it('renders the formatted record count for each active layer', () => {
    render(
      <CrimeLayerLegend groups={GROUPS} isActive={(id) => id === 'crime-violent'} />
    );
    expect(screen.getByText('1,234 incidents')).toBeInTheDocument();
  });

  it('renders Low and High scale labels for each active layer', () => {
    render(
      <CrimeLayerLegend groups={GROUPS} isActive={() => true} />
    );
    expect(screen.getAllByText('Low')).toHaveLength(2);
    expect(screen.getAllByText('High')).toHaveLength(2);
  });

  it('renders with the correct aria label', () => {
    render(
      <CrimeLayerLegend groups={GROUPS} isActive={() => true} />
    );
    expect(
      screen.getByRole('img', { name: 'Crime density scale from low to high' })
    ).toBeInTheDocument();
  });

  it('uses a small right offset when the panel is not open', () => {
    render(
      <CrimeLayerLegend groups={GROUPS} isActive={() => true} panelOpen={false} />
    );
    const legend = screen.getByRole('img', { name: 'Crime density scale from low to high' });
    expect(legend.style.right).toBe('16px');
  });

  it('shifts left to avoid the panel when the panel is open', () => {
    render(
      <CrimeLayerLegend groups={GROUPS} isActive={() => true} panelOpen={true} />
    );
    const legend = screen.getByRole('img', { name: 'Crime density scale from low to high' });
    expect(legend.style.right).toBe('336px');
  });
});
