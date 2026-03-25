import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SupportingDocumentation from '../../../src/components/AddProperty/SupportingDocumentation';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient', () => ({
  uploadDocument: jest.fn(),
}));

describe('SupportingDocumentation', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('calls onDataChange with documents (id + filename) after upload', async () => {
    apiClient.uploadDocument.mockResolvedValue('doc-uuid-1');
    const onDataChange = jest.fn();
    render(<SupportingDocumentation onDataChange={onDataChange} />);

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(onDataChange).toHaveBeenCalledWith({
        documents: [{ id: 'doc-uuid-1', filename: 'test.pdf' }],
      });
    });
  });

  it('accumulates multiple uploads across calls', async () => {
    apiClient.uploadDocument
      .mockResolvedValueOnce('doc-uuid-1')
      .mockResolvedValueOnce('doc-uuid-2');
    const onDataChange = jest.fn();
    render(<SupportingDocumentation onDataChange={onDataChange} />);

    const input = document.querySelector('input[type="file"]');

    fireEvent.change(input, {
      target: { files: [new File(['a'], 'a.pdf', { type: 'application/pdf' })] },
    });
    await waitFor(() =>
      expect(onDataChange).toHaveBeenCalledWith({
        documents: [{ id: 'doc-uuid-1', filename: 'a.pdf' }],
      })
    );

    fireEvent.change(input, {
      target: { files: [new File(['b'], 'b.pdf', { type: 'application/pdf' })] },
    });
    await waitFor(() =>
      expect(onDataChange).toHaveBeenCalledWith({
        documents: [
          { id: 'doc-uuid-1', filename: 'a.pdf' },
          { id: 'doc-uuid-2', filename: 'b.pdf' },
        ],
      })
    );
  });

  it('shows uploaded file names in the list', async () => {
    apiClient.uploadDocument.mockResolvedValue('doc-uuid-1');
    render(<SupportingDocumentation onDataChange={jest.fn()} />);

    const file = new File(['content'], 'my-doc.pdf', { type: 'application/pdf' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('my-doc.pdf')).toBeInTheDocument();
    });
  });
});
