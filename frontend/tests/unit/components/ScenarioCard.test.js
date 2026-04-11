import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import ScenarioCard from '../../../src/components/ScenarioCard';

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
  closing_cost_items: [{ label: 'Title Insurance', amount: 1500 }],
  total_commission: 21000,
  prorated_tax: 1084.93,
  tax_proration_breakdown: {
    formula: '$2,400.00 × 165 days ÷ 365 days = $1,084.93',
    days_from_jan1: 165,
    method: 'arrears',
    method_note: 'Indiana collects property taxes in arrears. Enter the prior year\'s annual tax bill as an estimate.',
  },
  total_closing_costs: 1084.93,
  total_deductions: 222084.93,
  net_proceeds: 127915.07,
  tax_lookup_url: 'https://gateway.ifionline.org/TaxBillLookUp/Default.aspx',
  tax_guidance: null,
};

describe('ScenarioCard', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders all input fields', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    expect(screen.getByLabelText('Sale Price')).toBeInTheDocument();
    expect(screen.getByLabelText('Mortgage Payoff')).toBeInTheDocument();
    expect(screen.getByLabelText('Listing Commission %')).toBeInTheDocument();
    expect(screen.getByLabelText("Buyer's Agent Commission %")).toBeInTheDocument();
    expect(screen.getByLabelText('Seller Concessions')).toBeInTheDocument();
    expect(screen.getByLabelText('Annual Tax Amount')).toBeInTheDocument();
    expect(screen.getByLabelText('Closing Date')).toBeInTheDocument();
  });

  it('renders computed net proceeds from scenario', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    expect(screen.getByTestId('net-proceeds')).toHaveTextContent('127,915.07');
  });

  it('renders the tax lookup link', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    const link = screen.getByRole('link', { name: /look up tax/i });
    expect(link).toHaveAttribute('href', 'https://gateway.ifionline.org/TaxBillLookUp/Default.aspx');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('calls onUpdate with the parsed float after 600ms debounce when sale price changes', () => {
    jest.useFakeTimers();
    const onUpdate = jest.fn();
    render(<ScenarioCard scenario={mockScenario} onUpdate={onUpdate} onDelete={jest.fn()} />);

    fireEvent.change(screen.getByLabelText('Sale Price'), { target: { value: '360000', name: 'sale_price' } });
    expect(onUpdate).not.toHaveBeenCalled();

    act(() => { jest.advanceTimersByTime(600); });
    expect(onUpdate).toHaveBeenCalledWith('s-1', { sale_price: 360000 });
    jest.useRealTimers();
  });

  it('resets the debounce timer when a second change arrives within 600ms', () => {
    jest.useFakeTimers();
    const onUpdate = jest.fn();
    render(<ScenarioCard scenario={mockScenario} onUpdate={onUpdate} onDelete={jest.fn()} />);

    fireEvent.change(screen.getByLabelText('Sale Price'), { target: { value: '360000', name: 'sale_price' } });
    act(() => { jest.advanceTimersByTime(400); });
    fireEvent.change(screen.getByLabelText('Sale Price'), { target: { value: '365000', name: 'sale_price' } });
    act(() => { jest.advanceTimersByTime(400); });
    expect(onUpdate).not.toHaveBeenCalled();

    act(() => { jest.advanceTimersByTime(200); });
    expect(onUpdate).toHaveBeenCalledTimes(1);
    expect(onUpdate).toHaveBeenCalledWith('s-1', { sale_price: 365000 });
    jest.useRealTimers();
  });

  it('shows Delete button and requires confirmation before calling onDelete', () => {
    const onDelete = jest.fn();
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={onDelete} />);

    fireEvent.click(screen.getByRole('button', { name: /^delete scenario$/i }));
    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /confirm delete/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /confirm delete/i }));
    expect(onDelete).toHaveBeenCalledWith('s-1');
  });

  it('renders the tax proration formula when breakdown is present', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    expect(screen.getByText('$2,400.00 × 165 days ÷ 365 days = $1,084.93')).toBeInTheDocument();
  });

  it('renders the arrears method note when breakdown is present', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    expect(screen.getByText(/indiana collects property taxes in arrears/i)).toBeInTheDocument();
  });

  it('renders tax guidance when annual_tax_amount is zero', () => {
    const noTaxScenario = {
      ...mockScenario,
      annual_tax_amount: 0,
      tax_proration_breakdown: null,
      tax_guidance: 'Annual tax amount not entered. Indiana collects property taxes in arrears: enter the prior year\'s annual tax bill.',
    };
    render(<ScenarioCard scenario={noTaxScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    expect(screen.getByText(/indiana collects property taxes in arrears/i)).toBeInTheDocument();
  });

  it('does not render tax guidance when annual_tax_amount is provided', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    // guidance is null on mockScenario — only the method_note from breakdown should show
    expect(screen.queryByTestId('tax-guidance')).not.toBeInTheDocument();
  });

  it('renders closing cost items from the scenario', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    expect(screen.getByDisplayValue('Title Insurance')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1500')).toBeInTheDocument();
  });

  it('adds a new blank closing cost item row when Add Item is clicked', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /add item/i }));
    const labelInputs = screen.getAllByPlaceholderText(/item description/i);
    expect(labelInputs).toHaveLength(2);
  });

  it('removes a closing cost item row when × is clicked', () => {
    render(<ScenarioCard scenario={mockScenario} onUpdate={jest.fn()} onDelete={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /remove title insurance/i }));
    expect(screen.queryByDisplayValue('Title Insurance')).not.toBeInTheDocument();
  });

  it('calls onUpdate with updated closing_cost_items after debounce when an item label changes', () => {
    jest.useFakeTimers();
    const onUpdate = jest.fn();
    render(<ScenarioCard scenario={mockScenario} onUpdate={onUpdate} onDelete={jest.fn()} />);

    fireEvent.change(screen.getByDisplayValue('Title Insurance'), { target: { value: 'Escrow Fee' } });
    act(() => { jest.advanceTimersByTime(600); });

    expect(onUpdate).toHaveBeenCalledWith('s-1', {
      closing_cost_items: [{ label: 'Escrow Fee', amount: 1500 }],
    });
    jest.useRealTimers();
  });
});
