import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Chat from '../../../src/pages/Chat';
import apiClient from '../../../src/apiClient';

jest.mock('../../../src/apiClient', () => ({
  getChatHistory: jest.fn(),
  sendChatMessage: jest.fn(),
}));

const mockProperty = {
  id: 'prop-1',
  formatted_address: '1600 Amphitheatre Pkwy, Mountain View, CA 94043',
};

function renderWithProperty(property) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/chat', state: { property } }]}>
      <Routes>
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('Chat', () => {
  beforeEach(() => {
    apiClient.getChatHistory.mockResolvedValue([]);
    apiClient.sendChatMessage.mockResolvedValue();
  });

  afterEach(() => jest.clearAllMocks());

  it('renders the chat page with the property address', async () => {
    renderWithProperty(mockProperty);
    expect(screen.getByTestId('chat-page')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('1600 Amphitheatre Pkwy, Mountain View, CA 94043')).toBeInTheDocument();
    });
  });

  it('loads and displays chat history on mount', async () => {
    apiClient.getChatHistory.mockResolvedValue([
      { id: 'msg-1', role: 'user', content: 'Hello there', created_at: '2026-01-01T00:00:00' },
      { id: 'msg-2', role: 'assistant', content: 'Hi! How can I help?', created_at: '2026-01-01T00:00:01' },
    ]);

    renderWithProperty(mockProperty);

    await waitFor(() => {
      expect(screen.getByText('Hello there')).toBeInTheDocument();
      expect(screen.getByText('Hi! How can I help?')).toBeInTheDocument();
    });
    expect(apiClient.getChatHistory).toHaveBeenCalledWith('prop-1');
  });

  it('sends a message when the send button is clicked', async () => {
    apiClient.sendChatMessage.mockImplementation(async (propertyId, message, onChunk) => {
      onChunk('The assistant');
      onChunk(' replies here');
    });

    renderWithProperty(mockProperty);

    const input = screen.getByLabelText('Message input');
    fireEvent.change(input, { target: { value: 'Tell me about this property' } });
    fireEvent.click(screen.getByLabelText('Send message'));

    await waitFor(() => {
      expect(apiClient.sendChatMessage).toHaveBeenCalledWith(
        'prop-1',
        'Tell me about this property',
        expect.any(Function)
      );
    });
  });

  it('sends a message when Enter is pressed', async () => {
    renderWithProperty(mockProperty);

    const input = screen.getByLabelText('Message input');
    fireEvent.change(input, { target: { value: 'What is the square footage?' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });

    await waitFor(() => {
      expect(apiClient.sendChatMessage).toHaveBeenCalledWith(
        'prop-1',
        'What is the square footage?',
        expect.any(Function)
      );
    });
  });

  it('streams assistant response chunks into the message', async () => {
    apiClient.sendChatMessage.mockImplementation(async (propertyId, message, onChunk) => {
      onChunk('Hello ');
      onChunk('World');
    });

    renderWithProperty(mockProperty);

    const input = screen.getByLabelText('Message input');
    fireEvent.change(input, { target: { value: 'Hi' } });
    fireEvent.click(screen.getByLabelText('Send message'));

    await waitFor(() => {
      expect(screen.getByText('Hello World')).toBeInTheDocument();
    });
  });

  it('renders markdown formatting in assistant messages', async () => {
    apiClient.getChatHistory.mockResolvedValue([
      { id: 'msg-1', role: 'assistant', content: '**important term**', created_at: '2026-01-01T00:00:00' },
    ]);

    renderWithProperty(mockProperty);

    await waitFor(() => {
      const bold = document.querySelector('strong');
      expect(bold).toBeInTheDocument();
      expect(bold).toHaveTextContent('important term');
    });
  });

  it('shows an error message when sending fails', async () => {
    apiClient.sendChatMessage.mockRejectedValue(new Error('Network error'));

    renderWithProperty(mockProperty);

    const input = screen.getByLabelText('Message input');
    fireEvent.change(input, { target: { value: 'Hi' } });
    fireEvent.click(screen.getByLabelText('Send message'));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Chat is currently unavailable. Please try again later.');
    });
  });

  it('disables input and send button after a failed request', async () => {
    apiClient.sendChatMessage.mockRejectedValue(new Error('503'));

    renderWithProperty(mockProperty);

    const input = screen.getByLabelText('Message input');
    fireEvent.change(input, { target: { value: 'Hi' } });
    fireEvent.click(screen.getByLabelText('Send message'));

    await waitFor(() => {
      expect(screen.getByLabelText('Message input')).toBeDisabled();
      expect(screen.getByLabelText('Send message')).toBeDisabled();
    });
  });
});
