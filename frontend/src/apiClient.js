import axios from 'axios';

class ApiClient {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getDefaultTemplate() {
    try {
      const response = await this.client.get('/templates/default');
      return response.data;
    } catch (error) {
      console.error('Error fetching default template:', error);
      throw error;
    }
  }

  async uploadDocument(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await this.client.post('/documents', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.id;
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    }
  }

  async generatePost(address, agentInfo, customTemplate = null) {
    try {
      const response = await this.client.post('/posts', {
        address,
        agent_info: agentInfo,
        custom_template: customTemplate,
      });
      return response.data;
    } catch (error) {
      console.error('Error generating post:', error);
      throw error;
    }
  }

  async postToInstagram(formData) {
    try {
      const response = await this.client.post('/posts-to-instagram', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error posting to Instagram:', error);
      throw error;
    }
  }

  async postToSocialMedia(formData) {
    try {
      const response = await this.client.post('/posts-to-social-media', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error posting to social media:', error);
      throw error;
    }
  }

  async listProperties() {
    try {
      const response = await this.client.get('/properties/list');
      return response.data;
    } catch (error) {
      console.error('Error listing properties:', error);
      throw error;
    }
  }

  async addProperty(propertyData) {
    try {
      const response = await this.client.post('/properties', propertyData);
      return response.data;
    } catch (error) {
      console.error('Error adding property:', error);
      throw error;
    }
  }

  async addDocumentToProperty(propertyId, docId, filename) {
    try {
      const response = await this.client.patch(`/properties/${propertyId}/documents`, { id: docId, filename });
      return response.data;
    } catch (error) {
      console.error('Error adding document to property:', error);
      throw error;
    }
  }

  async geocodeAddress(address) {
    try {
      const response = await this.client.post('/geocode', { address });
      return response.data;
    } catch (error) {
      console.error('Error geocoding address:', error);
      throw error;
    }
  }

  async getPropertyDetails(address) {
    try {
      const response = await this.client.get('/properties', { params: { address: encodeURIComponent(address) } });
      return response.data;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return null; // Property not found
      }
      console.error('Error fetching property details:', error);
      throw error;
    }
  }
}

export { ApiClient };
const apiClient = new ApiClient();
export default apiClient;
