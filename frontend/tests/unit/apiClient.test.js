import axios from 'axios';
import { ApiClient } from '../../src/apiClient';

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
