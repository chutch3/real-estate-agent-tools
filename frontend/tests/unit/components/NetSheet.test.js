import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import NetSheet from '../../../src/pages/NetSheet';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient', () => ({
  getNetSheet: jest.fn(),
  addScenario: jest.fn(),
  updateScenario: jest.fn(),
  deleteScenario: jest.fn(),
}));

const mockProperty = {
  id: 'prop-1',
  formatted_address: '123 Main St, Jeffersonville IN 47130',
};

const mockEmptySheet = {
  id: 'sheet-1',
  property_id: 'prop-1',
  scenarios: [],
};

const mockScenario = {
  id: 's-1',
  name: 'List Price',
  sale_price: 350000,
  mortgage_payoff: 200000,
  listing_commission_pct: 3.0,
  buyers_agent_commission_pct: 3.0,
  seller_concessions: 0,
  annual_tax_amount: 2400,
  closing_date: '2026-06-15',
  closing_cost_items: [],
  total_commission: 21000,
  prorated_tax: 1084.93,
  tax_proration_breakdown: { formula: '$2,400.00 × 165 days ÷ 365 days = $1,084.93', days_from_jan1: 165 },
  total_closing_costs: 1084.93,
  total_deductions: 222084.93,
  net_proceeds: 127915.07,
  tax_lookup_url: 'https://gateway.ifionline.org/TaxBillLookUp/Default.aspx',
};

function renderWithProperty(property) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/net-sheet', state: { property } }]}>
      <Routes>
        <Route path="/net-sheet" element={<NetSheet />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('NetSheet', () => {
  beforeEach(() => {
    apiClient.getNetSheet.mockResolvedValue(mockEmptySheet);
  });

  afterEach(() => jest.clearAllMocks());

  it('renders the net sheet page with the property address', async () => {
    renderWithProperty(mockProperty);
    expect(screen.getByTestId('net-sheet-page')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('123 Main St, Jeffersonville IN 47130')).toBeInTheDocument();
    });
  });

  it('calls getNetSheet on mount with the property id', async () => {
    renderWithProperty(mockProperty);
    await waitFor(() => {
      expect(apiClient.getNetSheet).toHaveBeenCalledWith('prop-1');
    });
  });

  it('shows empty state when there are no scenarios', async () => {
    renderWithProperty(mockProperty);
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
  });

  it('shows an Add Scenario button', async () => {
    renderWithProperty(mockProperty);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add scenario/i })).toBeInTheDocument();
    });
  });

  it('calls addScenario without sale_price: null when Add Scenario is clicked', async () => {
    const sheetWithScenario = { ...mockEmptySheet, scenarios: [mockScenario] };
    apiClient.addScenario.mockResolvedValue(sheetWithScenario);

    renderWithProperty(mockProperty);

    await screen.findByTestId('empty-state');
    fireEvent.click(screen.getByRole('button', { name: /add scenario/i }));

    await waitFor(() => {
      const [, payload] = apiClient.addScenario.mock.calls[0];
      expect(payload).toHaveProperty('name', 'Scenario 1');
      expect(payload).not.toHaveProperty('sale_price', null);
      expect(screen.getByDisplayValue('List Price')).toBeInTheDocument();
    });
  });

  it('renders a scenario card for each scenario', async () => {
    apiClient.getNetSheet.mockResolvedValue({ ...mockEmptySheet, scenarios: [mockScenario] });

    renderWithProperty(mockProperty);

    await waitFor(() => {
      expect(screen.getByTestId('scenario-card')).toBeInTheDocument();
    });
  });

  it('hides empty state when scenarios are present', async () => {
    apiClient.getNetSheet.mockResolvedValue({ ...mockEmptySheet, scenarios: [mockScenario] });

    renderWithProperty(mockProperty);

    await waitFor(() => {
      expect(screen.queryByTestId('empty-state')).not.toBeInTheDocument();
    });
  });

  it('shows an error message when getNetSheet fails', async () => {
    apiClient.getNetSheet.mockRejectedValue(new Error('Network error'));

    renderWithProperty(mockProperty);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/failed to load/i);
    });
  });

  it('clears a previous error when Add Scenario succeeds', async () => {
    apiClient.getNetSheet.mockRejectedValue(new Error('Network error'));
    apiClient.addScenario.mockResolvedValue({ ...mockEmptySheet, scenarios: [mockScenario] });

    renderWithProperty(mockProperty);

    // Wait for the error from getNetSheet
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /add scenario/i }));

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
