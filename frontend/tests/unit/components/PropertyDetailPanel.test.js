import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PropertyDetailPanel from '../../../src/components/PropertyDetailPanel';

describe('PropertyDetailPanel', () => {
  const mockProperty = {
    id: 'prop-1',
    formatted_address: '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
    latitude: 37.4225,
    longitude: -122.0847,
    documents: [
      { id: 'doc-1', filename: 'listing.pdf' },
      { id: 'doc-2', filename: 'disclosure.pdf' },
    ],
  };

  it('is not visible when property is null', () => {
    render(
      <PropertyDetailPanel property={null} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.queryByTestId('property-detail-panel')).not.toBeInTheDocument();
  });

  it('shows property address when a property is selected', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument();
    expect(screen.getByText('1600 Amphitheatre Pkwy, Mountain View, CA 94043')).toBeInTheDocument();
  });

  it('renders Chat (disabled), Upload Docs, and Generate buttons', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.getByRole('button', { name: /chat/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /upload docs/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate/i })).toBeInTheDocument();
  });

  it('shows documents list with filenames when property has documents', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('listing.pdf')).toBeInTheDocument();
    expect(screen.getByText('disclosure.pdf')).toBeInTheDocument();
  });

  it('shows Ratings and Climate sections', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.getByText('Ratings')).toBeInTheDocument();
    expect(screen.getByText('Climate')).toBeInTheDocument();
  });

  it('calls onGeneratePost with the property when Generate is clicked', () => {
    const onGeneratePost = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={onGeneratePost} onUploadDocument={jest.fn()} />
    );
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    expect(onGeneratePost).toHaveBeenCalledWith(mockProperty);
  });

  it('calls onUploadDocument with property and file when a file is selected', () => {
    const onUploadDocument = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={onUploadDocument} />
    );
    const file = new File(['content'], 'listing.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    expect(onUploadDocument).toHaveBeenCalledWith(mockProperty, file);
  });

  it('disables Upload Docs button and shows uploading text while uploading', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} isUploading={true} />
    );
    const btn = screen.getByRole('button', { name: /uploading/i });
    expect(btn).toBeDisabled();
  });

  it('shows the selected filename with a spinner in the documents list immediately after file selection', () => {
    const onUploadDocument = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={onUploadDocument} isUploading={false} />
    );
    const file = new File(['content'], 'new-contract.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.getByText('new-contract.pdf')).toBeInTheDocument();
    expect(screen.getByLabelText('Uploading new-contract.pdf')).toBeInTheDocument();
  });

  it('removes the uploading indicator from the documents list when isUploading becomes false', () => {
    const { rerender } = render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} isUploading={true} />
    );
    const file = new File(['content'], 'new-contract.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    rerender(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} isUploading={false} />
    );
    expect(screen.queryByLabelText('Uploading new-contract.pdf')).not.toBeInTheDocument();
  });

  it('shows an error message when uploadError prop is set', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} uploadError="Upload failed. Please try again." />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Upload failed. Please try again.');
  });

  it('calls onClose when the panel is dismissed', () => {
    const onClose = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={onClose} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
