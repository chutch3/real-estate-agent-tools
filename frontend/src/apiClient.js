import axios from "axios";

class ApiClient {
  constructor() {
    this.baseURL =
      process.env.REACT_APP_API_BASE_URL || "http://localhost:5000";
    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        "Content-Type": "application/json",
      },
      withCredentials: true,
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (
          error.response?.status === 401 &&
          window.location.pathname !== "/login"
        ) {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      },
    );
  }

  async getMe() {
    const response = await this.client.get("/users/me");
    return response.data;
  }

  async login(email, password) {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);
    await this.client.post("/auth/token", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  }

  async logout() {
    await this.client.post("/auth/logout");
  }

  async getDefaultTemplate() {
    try {
      const response = await this.client.get("/templates/default");
      return response.data;
    } catch (error) {
      console.error("Error fetching default template:", error);
      throw error;
    }
  }

  async uploadDocument(file) {
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await this.client.post("/documents", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data.id;
    } catch (error) {
      console.error("Error uploading document:", error);
      throw error;
    }
  }

  async generatePost(address, agentInfo, customTemplate = null) {
    try {
      const response = await this.client.post("/posts", {
        address,
        agent_info: agentInfo,
        custom_template: customTemplate,
      });
      return response.data;
    } catch (error) {
      console.error("Error generating post:", error);
      throw error;
    }
  }

  async postToInstagram(formData) {
    try {
      const response = await this.client.post("/posts-to-instagram", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (error) {
      console.error("Error posting to Instagram:", error);
      throw error;
    }
  }

  async postToSocialMedia(formData) {
    try {
      const response = await this.client.post(
        "/posts-to-social-media",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );
      return response.data;
    } catch (error) {
      console.error("Error posting to social media:", error);
      throw error;
    }
  }

  async listProperties() {
    try {
      const response = await this.client.get("/properties/list");
      return response.data;
    } catch (error) {
      console.error("Error listing properties:", error);
      throw error;
    }
  }

  async addProperty(propertyData) {
    try {
      const response = await this.client.post("/properties", propertyData);
      return response.data;
    } catch (error) {
      console.error("Error adding property:", error);
      throw error;
    }
  }

  async addDocumentToProperty(propertyId, docId, filename) {
    try {
      const response = await this.client.patch(
        `/properties/${propertyId}/documents`,
        { id: docId, filename },
      );
      return response.data;
    } catch (error) {
      console.error("Error adding document to property:", error);
      throw error;
    }
  }

  async deleteDocument(propertyId, docId) {
    try {
      const response = await this.client.delete(
        `/properties/${propertyId}/documents/${docId}`,
      );
      return response.data;
    } catch (error) {
      console.error("Error deleting document:", error);
      throw error;
    }
  }

  async getChatHistory(propertyId) {
    const response = await this.client.get(`/properties/${propertyId}/chat`);
    return response.data;
  }

  async sendChatMessage(propertyId, message, onChunk) {
    const response = await fetch(
      `${this.baseURL}/properties/${propertyId}/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      },
    );
    if (!response.ok)
      throw new Error(`Chat request failed: ${response.status}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      onChunk(decoder.decode(value, { stream: true }));
    }
  }

  async getNetSheet(propertyId) {
    const response = await this.client.get(
      `/properties/${propertyId}/net-sheet`,
    );
    return response.data;
  }

  async addScenario(propertyId, scenario) {
    const response = await this.client.post(
      `/properties/${propertyId}/net-sheet/scenarios`,
      scenario,
    );
    return response.data;
  }

  async updateScenario(propertyId, scenarioId, updates) {
    const response = await this.client.patch(
      `/properties/${propertyId}/net-sheet/scenarios/${scenarioId}`,
      updates,
    );
    return response.data;
  }

  async deleteScenario(propertyId, scenarioId) {
    const response = await this.client.delete(
      `/properties/${propertyId}/net-sheet/scenarios/${scenarioId}`,
    );
    return response.data;
  }

  async geocodeAddress(address) {
    try {
      const response = await this.client.post("/geocode", { address });
      return response.data;
    } catch (error) {
      console.error("Error geocoding address:", error);
      throw error;
    }
  }

  async getPropertyDetails(address) {
    try {
      const response = await this.client.get("/properties", {
        params: { address: encodeURIComponent(address) },
      });
      return response.data;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return null; // Property not found
      }
      console.error("Error fetching property details:", error);
      throw error;
    }
  }
}

export { ApiClient };
const apiClient = new ApiClient();
export default apiClient;
