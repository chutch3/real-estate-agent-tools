import axios from 'axios';
import { ApiClient } from '../../src/apiClient';
import { TextEncoder, TextDecoder } from 'util';

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

jest.mock('axios');

describe('ApiClient', () => {
  let subject;
  let mockAxiosInstance;

  beforeEach(() => {
    mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn(),
    };
    axios.create.mockReturnValue(mockAxiosInstance);
    subject = new ApiClient();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('listProperties', () => {
    it('calls GET /properties/list and returns the data', async () => {
      const properties = [
        { id: 'prop-1', latitude: 37.4225, longitude: -122.0847 },
      ];
      mockAxiosInstance.get.mockResolvedValue({ data: properties });

      const result = await subject.listProperties();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/properties/list');
      expect(result).toEqual(properties);
    });
  });

  describe('addProperty', () => {
    it('calls POST /properties with JSON body', async () => {
      const propertyData = { latitude: 37.4225, longitude: -122.0847 };
      mockAxiosInstance.post.mockResolvedValue({ data: { id: 'prop-1' } });

      const result = await subject.addProperty(propertyData);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/properties', propertyData);
      expect(result).toEqual({ id: 'prop-1' });
    });
  });

  describe('addDocumentToProperty', () => {
    it('calls PATCH /properties/:id/documents with doc id and filename', async () => {
      const updated = { id: 'prop-1', documents: [{ id: 'doc-1', filename: 'listing.pdf' }] };
      mockAxiosInstance.patch = jest.fn().mockResolvedValue({ data: updated });

      const result = await subject.addDocumentToProperty('prop-1', 'doc-1', 'listing.pdf');

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith(
        '/properties/prop-1/documents',
        { id: 'doc-1', filename: 'listing.pdf' }
      );
      expect(result).toEqual(updated);
    });
  });

  describe('getChatHistory', () => {
    it('calls GET /properties/:id/chat and returns the data', async () => {
      const messages = [
        { id: 'msg-1', role: 'user', content: 'Hi', created_at: '2026-01-01T00:00:00' },
      ];
      mockAxiosInstance.get.mockResolvedValue({ data: messages });

      const result = await subject.getChatHistory('prop-1');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/properties/prop-1/chat');
      expect(result).toEqual(messages);
    });
  });

  describe('sendChatMessage', () => {
    it('calls fetch POST /properties/:id/chat and handles the stream', async () => {
      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Hello') })
          .mockResolvedValueOnce({ done: true }),
      };
      const mockResponse = {
        ok: true,
        body: {
          getReader: jest.fn().mockReturnValue(mockReader),
        },
      };
      global.fetch = jest.fn().mockResolvedValue(mockResponse);
      const onChunk = jest.fn();

      await subject.sendChatMessage('prop-1', 'Hi', onChunk);

      expect(global.fetch).toHaveBeenCalledWith(
        `${subject.baseURL}/properties/prop-1/chat`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ message: 'Hi' }),
        })
      );
      expect(onChunk).toHaveBeenCalledWith('Hello');
    });
  });

  describe('deleteDocument', () => {
    it('calls DELETE /properties/:propertyId/documents/:docId and returns the updated property', async () => {
      const updated = { id: 'prop-1', documents: [] };
      mockAxiosInstance.delete = jest.fn().mockResolvedValue({ data: updated });

      const result = await subject.deleteDocument('prop-1', 'doc-1');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/properties/prop-1/documents/doc-1'
      );
      expect(result).toEqual(updated);
    });
  });

  describe('geocodeAddress', () => {
    it('calls POST /geocode with address in JSON body', async () => {
      const location = { lat: 37.4225, lng: -122.0847 };
      mockAxiosInstance.post.mockResolvedValue({ data: { location } });

      const result = await subject.geocodeAddress('1600 Amphitheatre Pkwy');

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/geocode', {
        address: '1600 Amphitheatre Pkwy',
      });
      expect(result).toEqual({ location });
    });
  });
});
