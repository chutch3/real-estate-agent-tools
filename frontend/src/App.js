import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import AddressInput from './components/AddressInput';
import AgentInfo from './components/AgentInfo';
import PostEditor from './components/PostEditor';
import MapComponent from './components/MapComponent';
import CacheInspector from './pages/CacheInspector';
import NavMenu from './components/NavMenu';
import ImageUploader from './components/ImageUploader';
import { ClipLoader } from 'react-spinners';
import apiClient from './apiClient';
import './App.css';

function App() {
  const [post, setPost] = useState('');
  const [postStatus, setPostStatus] = useState('');
  const [mapCenter, setMapCenter] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [template, setTemplate] = useState('');
  const [defaultTemplate, setDefaultTemplate] = useState('');
  const [agentInfo, setAgentInfo] = useState({
    agentName: '',
    agentCompany: '',
    agentContact: ''
  });
  const [selectedImages, setSelectedImages] = useState([]);

  useEffect(() => {
    async function fetchDefaultTemplate() {
      try {
        const response = await apiClient.getDefaultTemplate();
        setDefaultTemplate(response.template);
        setTemplate(response.template);
      } catch (error) {
        console.error('Error fetching default template:', error);
        setError('Failed to load the default template. Please try refreshing the page.');
      }
    }
    fetchDefaultTemplate();
  }, []); // Removed apiClient from the dependency array

  const generatePost = async (address) => {
    try {
      setIsLoading(true);
      setError('');
      const data = await apiClient.generatePost(address, agentInfo, template !== defaultTemplate ? template : null);
      setPost(data.post);
      setPostStatus('');

      const location = await apiClient.geocodeAddress(address);
      setMapCenter(location);
    } catch (error) {
      console.error('Error generating post:', error);
      setError(error.response?.data?.error || 'An unexpected error occurred. Please try again later.');
      setPost('');
      setMapCenter(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImagesSelected = (files) => {
    setSelectedImages(files);
  };

  const handleImageRemove = (index) => {
    setSelectedImages(prevImages => prevImages.filter((_, i) => i !== index));
  };

  const handlePostToInstagram = async () => {
    try {
      setIsLoading(true);
      setError('');

      // Upload images
      const formData = new FormData();
      selectedImages.forEach((file, index) => {
        formData.append(`image${index}`, file);
      });
      formData.append('post', post);

      // Post to Instagram
      await apiClient.postToInstagram(formData);

      setPostStatus('Post submitted successfully to Instagram!');
    } catch (error) {
      console.error('Error posting to Instagram:', error);
      setError('Failed to post to Instagram. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Router>
      <div className="App">
        <NavMenu />
        <main className="App-main">
          <Routes>
            <Route path="/cache-inspector" element={<CacheInspector />} />
            <Route path="/" element={
              <>
                <h1>Instagram Post Generator</h1>
                <div className="app-sections">
                  <section className="agent-section">
                    <h2>Agent Information</h2>
                    <AgentInfo agentInfo={agentInfo} setAgentInfo={setAgentInfo} />
                  </section>
                  <section className="address-section">
                    <h2>Property Address</h2>
                    <AddressInput onGenerate={generatePost} />
                  </section>
                  {isLoading && (
                    <div className="loader-container">
                      <ClipLoader color="#007bff" size={50} />
                      <p>Generating post...</p>
                    </div>
                  )}
                  {error && <div className="error-message">{error}</div>}
                  {mapCenter && <MapComponent center={mapCenter} />}
                  {post && !isLoading && (
                    <>
                      <section className="image-upload-section">
                        <h2>Add Images</h2>
                        <ImageUploader
                          selectedImages={selectedImages}
                          onImagesSelected={handleImagesSelected}
                          onImageRemove={handleImageRemove}
                        />
                      </section>
                      <section className="post-section">
                        <h2>Generated Post</h2>
                        <PostEditor
                          post={post}
                          setPost={setPost}
                          postStatus={postStatus}
                          setPostStatus={setPostStatus}
                        />
                        <button 
                          onClick={handlePostToInstagram} 
                          disabled={isLoading || selectedImages.length === 0}
                          className="post-button"
                        >
                          Post to Instagram
                        </button>
                      </section>
                    </>
                  )}
                </div>
              </>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
