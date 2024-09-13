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
      const response = await this.client.get('/default-template');
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
      const response = await this.client.post('/document/upload', formData, {
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

  async generatePost(address, agentInfo, customTemplate = null, documentIds = null) {
    try {
      const response = await this.client.post('/generate-post', {
        address,
        agent_info: agentInfo,
        custom_template: customTemplate,
        document_ids: documentIds,
      });
      return response.data;
    } catch (error) {
      console.error('Error generating post:', error);
      throw error;
    }
  }

  async savePost(post) {
    try {
      const response = await this.client.post('/save-post', { post });
      return response.data;
    } catch (error) {
      console.error('Error saving post:', error);
      throw error;
    }
  }

  async postToInstagram(formData) {
    try {
      const response = await this.client.post('/post-to-instagram', formData, {
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
      const response = await this.client.post('/post-to-social-media', formData, {
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
}

const apiClient = new ApiClient();
export default apiClient;
