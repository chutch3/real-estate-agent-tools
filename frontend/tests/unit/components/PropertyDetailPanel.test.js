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

  it('renders the backdrop with pointer-events-none so map zoom is not blocked', () => {
    const { container } = render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    const backdrop = container.querySelector('[aria-hidden="true"]');
    expect(backdrop).not.toBeNull();
    expect(backdrop.className).toMatch(/pointer-events-none/);
  });

  it('shows property address when a property is selected', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.getByTestId('property-detail-panel')).toBeInTheDocument();
    expect(screen.getByText('1600 Amphitheatre Pkwy, Mountain View, CA 94043')).toBeInTheDocument();
  });

  it('renders Chat, Upload Docs, and Generate buttons', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onChat={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.getByRole('button', { name: /chat/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload docs/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate/i })).toBeInTheDocument();
  });

  it('calls onChat with the property when Chat is clicked', () => {
    const onChat = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onChat={onChat} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    fireEvent.click(screen.getByRole('button', { name: /chat/i }));
    expect(onChat).toHaveBeenCalledWith(mockProperty);
  });

  it('shows documents list with filenames when property has documents', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('listing.pdf')).toBeInTheDocument();
    expect(screen.getByText('disclosure.pdf')).toBeInTheDocument();
  });

  it('renders each document as a link to the document API endpoint', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    const listingLink = screen.getByRole('link', { name: 'listing.pdf' });
    expect(listingLink).toHaveAttribute('href', expect.stringContaining('/documents/doc-1'));
    expect(listingLink).toHaveAttribute('target', '_blank');
    expect(listingLink).toHaveAttribute('rel', 'noreferrer');
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

  it('calls onUploadDocument with property and all selected files', () => {
    const onUploadDocument = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={onUploadDocument} />
    );
    const file1 = new File(['content'], 'listing.pdf', { type: 'application/pdf' });
    const file2 = new File(['content'], 'disclosure.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file1, file2] } });
    expect(onUploadDocument).toHaveBeenCalledWith(mockProperty, [file1, file2]);
  });

  it('the file input accepts multiple files', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    expect(document.querySelector('input[type="file"]')).toHaveAttribute('multiple');
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

  it('renders a delete button for each document', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} onDeleteDocument={jest.fn()} />
    );
    expect(screen.getByRole('button', { name: /delete listing\.pdf/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete disclosure\.pdf/i })).toBeInTheDocument();
  });

  it('calls onDeleteDocument with the property and doc id when delete is clicked', () => {
    const onDeleteDocument = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} onDeleteDocument={onDeleteDocument} />
    );
    fireEvent.click(screen.getByRole('button', { name: /delete listing\.pdf/i }));
    expect(onDeleteDocument).toHaveBeenCalledWith(mockProperty, 'doc-1');
  });

  it('shows a delete error message when deleteError prop is set', () => {
    render(
      <PropertyDetailPanel property={mockProperty} onClose={jest.fn()} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} onDeleteDocument={jest.fn()} deleteError="Failed to delete document." />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Failed to delete document.');
  });

  it('calls onClose when the panel is dismissed', () => {
    const onClose = jest.fn();
    render(
      <PropertyDetailPanel property={mockProperty} onClose={onClose} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it('does not call onClose when the backdrop is clicked (map pan simulation)', () => {
    const onClose = jest.fn();
    const { container } = render(
      <PropertyDetailPanel property={mockProperty} onClose={onClose} onGeneratePost={jest.fn()} onUploadDocument={jest.fn()} />
    );
    const backdrop = container.querySelector('[aria-hidden="true"]');
    fireEvent.click(backdrop);
    expect(onClose).not.toHaveBeenCalled();
  });
});
