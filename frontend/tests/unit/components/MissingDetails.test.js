import React from 'react';
import { render, screen } from '@testing-library/react';
import MissingDetails from '../../../src/components/AddProperty/MissingDetails';

const snakeCaseProperty = {
  formatted_address: '123 Main St, Springfield, IL 62701',
  address_line1: '123 Main St',
  city: 'Springfield',
  state: 'IL',
  zip_code: '62701',
  property_type: 'Single Family',
  bedrooms: 3,
  bathrooms: 2,
  square_footage: 1800,
  lot_size: 5000,
  year_built: 1995,
  latitude: 39.7817,
  longitude: -89.6501,
};

describe('MissingDetails', () => {
  it('pre-populates address fields from snake_case API response', () => {
    render(<MissingDetails propertyData={snakeCaseProperty} onDataChange={jest.fn()} />);

    expect(screen.getByDisplayValue('123 Main St, Springfield, IL 62701')).toBeInTheDocument();
    expect(screen.getByDisplayValue('123 Main St')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Springfield')).toBeInTheDocument();
    expect(screen.getByDisplayValue('IL')).toBeInTheDocument();
    expect(screen.getByDisplayValue('62701')).toBeInTheDocument();
  });

  it('pre-populates property characteristics from snake_case API response', () => {
    render(<MissingDetails propertyData={snakeCaseProperty} onDataChange={jest.fn()} />);

    expect(screen.getByDisplayValue('Single Family')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1800')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1995')).toBeInTheDocument();
  });
});
