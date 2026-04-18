import axios from 'axios';
import { ApiClient } from '../../src/apiClient';
import { TextEncoder, TextDecoder } from 'util';

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    interceptors: { response: { use: jest.fn() } },
  })),
}));

describe('ApiClient', () => {
  let subject;
  let mockAxiosInstance;

  beforeEach(() => {
    mockAxiosInstance = {
      get: jest.fn(),
      post: jest.fn(),
      interceptors: {
        response: {
          use: jest.fn(),
        },
      },
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

  describe('getMe', () => {
    it('calls GET /users/me and returns the data', async () => {
      const user = { id: 'u1', email: 'agent@acme.com', role: 'AGENT' };
      mockAxiosInstance.get.mockResolvedValue({ data: user });

      const result = await subject.getMe();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/users/me');
      expect(result).toEqual(user);
    });
  });

  describe('login', () => {
    it('calls POST /auth/token with url-encoded credentials', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { token_type: 'bearer' } });

      await subject.login('agent@acme.com', 'password123');

      const [path, body, config] = mockAxiosInstance.post.mock.calls[0];
      expect(path).toBe('/auth/token');
      expect(body.get('username')).toBe('agent@acme.com');
      expect(body.get('password')).toBe('password123');
      expect(config.headers['Content-Type']).toBe('application/x-www-form-urlencoded');
    });
  });

  describe('logout', () => {
    it('calls POST /auth/logout', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });

      await subject.logout();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/logout');
    });
  });

  describe('getNetSheet', () => {
    it('calls GET /representations/:id/net-sheet and returns the data', async () => {
      const sheet = { id: 'sheet-1', representation_id: 'rep-1', scenarios: [] };
      mockAxiosInstance.get.mockResolvedValue({ data: sheet });

      const result = await subject.getNetSheet('rep-1');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/representations/rep-1/net-sheet');
      expect(result).toEqual(sheet);
    });
  });

  describe('addScenario', () => {
    it('calls POST /representations/:id/net-sheet/scenarios and returns the updated sheet', async () => {
      const scenario = { name: 'Scenario 1', sale_price: 350000 };
      const updatedSheet = { id: 'sheet-1', representation_id: 'rep-1', scenarios: [{ id: 's-1', ...scenario }] };
      mockAxiosInstance.post.mockResolvedValue({ data: updatedSheet });

      const result = await subject.addScenario('rep-1', scenario);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/representations/rep-1/net-sheet/scenarios',
        scenario,
      );
      expect(result).toEqual(updatedSheet);
    });
  });

  describe('updateScenario', () => {
    it('calls PATCH /representations/:id/net-sheet/scenarios/:sid and returns the updated sheet', async () => {
      const updates = { sale_price: 345000 };
      const updatedSheet = { id: 'sheet-1', representation_id: 'rep-1', scenarios: [{ id: 's-1', sale_price: 345000 }] };
      mockAxiosInstance.patch = jest.fn().mockResolvedValue({ data: updatedSheet });

      const result = await subject.updateScenario('rep-1', 's-1', updates);

      expect(mockAxiosInstance.patch).toHaveBeenCalledWith(
        '/representations/rep-1/net-sheet/scenarios/s-1',
        updates,
      );
      expect(result).toEqual(updatedSheet);
    });
  });

  describe('deleteScenario', () => {
    it('calls DELETE /representations/:id/net-sheet/scenarios/:sid and returns the updated sheet', async () => {
      const updatedSheet = { id: 'sheet-1', representation_id: 'rep-1', scenarios: [] };
      mockAxiosInstance.delete = jest.fn().mockResolvedValue({ data: updatedSheet });

      const result = await subject.deleteScenario('rep-1', 's-1');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/representations/rep-1/net-sheet/scenarios/s-1',
      );
      expect(result).toEqual(updatedSheet);
    });
  });

  describe('401 interceptor', () => {
    let onRejected;

    beforeEach(() => {
      delete window.location;
      window.location = { href: '', pathname: '/' };
      onRejected = mockAxiosInstance.interceptors.response.use.mock.calls[0]?.[1];
    });

    it('registers a response interceptor on construction', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalledTimes(1);
    });

    it('redirects to /login on a 401 response', async () => {
      await onRejected({ response: { status: 401 } }).catch(() => {});

      expect(window.location.href).toBe('/login');
    });

    it('does not redirect when already on /login', async () => {
      window.location.pathname = '/login';

      await onRejected({ response: { status: 401 } }).catch(() => {});

      expect(window.location.href).toBe('');
    });

    it('re-rejects the error so callers still receive it', async () => {
      const error = { response: { status: 401 } };

      await expect(onRejected(error)).rejects.toEqual(error);
    });
  });
});
