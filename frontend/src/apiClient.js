import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';

class ApiClient {
  async generatePost(address, agentInfo, customTemplate = null) {
    const response = await axios.post(`${API_BASE_URL}/generate-post`, {
      address,
      "agent_info": {
        "agent_name": agentInfo['agentName'],
        "agent_company": agentInfo['agentCompany'],
        "agent_contact": agentInfo['agentContact']
      },
      "custom_template": customTemplate
    });
    return response.data;
  }

  async postToInstagram(formData) {
    const response = await axios.post(`${API_BASE_URL}/post-to-instagram`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async geocodeAddress(address) {
    const response = await axios.post(`${API_BASE_URL}/geocode`, { address });
    return response.data.location;
  }

  async getDefaultTemplate() {
    const response = await axios.get(`${API_BASE_URL}/default-template`);
    return response.data;
  }

  async getCacheData() {
    const response = await axios.get(`${API_BASE_URL}/cache`);
    return response.data;
  }

  async deleteCacheEntry(key) {
    const response = await axios.delete(`${API_BASE_URL}/cache/${encodeURIComponent(key)}`);
    return response.data;
  }

  async clearAllCache() {
    const response = await axios.delete(`${API_BASE_URL}/cache`);
    return response.data;
  }
}

const api_client = new ApiClient();

export default api_client;
