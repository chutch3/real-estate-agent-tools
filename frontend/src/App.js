import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { Stepper, Step, StepLabel, Button, Typography, Box } from '@mui/material';
import AddressInput from './components/AddressInput';
import AgentInfo from './components/AgentInfo';
import PostEditor from './components/PostEditor';
import MapComponent from './components/MapComponent';
import CacheInspector from './pages/CacheInspector';
import NavMenu from './components/NavMenu';
import MaterialImageUploader from './components/MaterialImageUploader';
import DocumentUploader from './components/DocumentUploader';
import DefaultPromptEditor from './components/DefaultPromptEditor';
import SocialMediaPoster from './components/SocialMediaPoster';
import { ClipLoader } from 'react-spinners';
import apiClient from './apiClient';
import './App.css';
import AddProperty from './components/AddProperty';
import HomeScreen from './components/HomeScreen';

const steps = [
  'Agent Info',
  'Input Address',
  'Upload Documents',
  'Customize Prompt',
  'Generate Post',
  'Post to Socials',
  'Add Property'
];

function App() {
  const [activeStep, setActiveStep] = useState(0);
  const [post, setPost] = useState('');
  const [postStatus, setPostStatus] = useState('');
  const [mapCenter, setMapCenter] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [agentInfo, setAgentInfo] = useState({
    agent_name: '',
    agent_company: '',
    agent_contact: ''
  });
  const [selectedImages, setSelectedImages] = useState([]);
  const [uploadedDocumentId, setUploadedDocumentId] = useState(null);
  const [address, setAddress] = useState('');
  const [customTemplate, setCustomTemplate] = useState(null);
  const [propertyData, setPropertyData] = useState(null);
  const [properties, setProperties] = useState([]); // Add this line to manage properties

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleAddressChange = (newAddress, geocodedAddress) => {
    setAddress(newAddress);
  };

  const handleDocumentUpload = async (file) => {
    try {
      setIsLoading(true);
      setError('');
      const documentId = await apiClient.uploadDocument(file);
      setUploadedDocumentId(documentId);
    } catch (error) {
      console.error('Error uploading document:', error);
      setError('Failed to upload document. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCustomTemplateChange = (template) => {
    setCustomTemplate(template);
  };

  const generatePost = async () => {
    try {
      setIsLoading(true);
      setError('');

      const data = await apiClient.generatePost(address, agentInfo, customTemplate, uploadedDocumentId ? [uploadedDocumentId] : null);
      setPost(data.post);
      setPostStatus('');
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

  const handlePostToSocials = async (platforms) => {
    try {
      setIsLoading(true);
      setError('');

      // Upload images
      const formData = new FormData();
      selectedImages.forEach((file, index) => {
        formData.append(`image${index}`, file);
      });
      formData.append('post', post);
      formData.append('platforms', JSON.stringify(platforms));

      // Post to selected platforms
      await apiClient.postToSocialMedia(formData);

      setPostStatus('Post submitted successfully to selected social media platforms!');
    } catch (error) {
      console.error('Error posting to social media:', error);
      setError('Failed to post to social media. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const isStepComplete = (step) => {
    switch (step) {
      case 0:
        return agentInfo.agent_name && agentInfo.agent_company && agentInfo.agent_contact;
      case 1:
        return address.trim() !== '';
      case 2:
        return uploadedDocumentId !== null;
      case 3:
        return true; // Always allow proceeding from the Customize Prompt step
      case 4:
        return post !== '';
      case 5:
        return selectedImages.length > 0;
      default:
        return false;
    }
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return <AgentInfo agentInfo={agentInfo} setAgentInfo={setAgentInfo} />;
      case 1:
        return <AddressInput onAddressChange={(newAddress, geocodedAddress) => handleAddressChange(newAddress, geocodedAddress)} />;
      case 2:
        return (
          <DocumentUploader onUpload={handleDocumentUpload} uploadedDocumentId={uploadedDocumentId} />
        );
      case 3:
        return <DefaultPromptEditor onCustomTemplateChange={handleCustomTemplateChange} />;
      case 4:
        return (
          <>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <Button
                variant="contained"
                color="primary"
                onClick={generatePost}
                disabled={isLoading}
                sx={{ minWidth: '200px' }}
              >
                Generate Post
              </Button>
            </Box>
            {post && (
              <PostEditor
                post={post}
                setPost={setPost}
                postStatus={postStatus}
                setPostStatus={setPostStatus}
                setIsLoading={setIsLoading}
                setError={setError}
                selectedImages={selectedImages}
              />
            )}
            {mapCenter && <MapComponent center={mapCenter} />}
          </>
        );
      case 5:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <MaterialImageUploader
              selectedImages={selectedImages}
              onImagesSelected={handleImagesSelected}
              onImageRemove={handleImageRemove}
            />
            <SocialMediaPoster
              onPost={handlePostToSocials}
              isLoading={isLoading}
            />
          </Box>
        );
      case 6:
        return <AddProperty propertyData={propertyData} setPropertyData={setPropertyData} />;
      default:
        return 'Unknown step';
    }
  };

  return (
    <Router>
      <div className="App">
        <NavMenu />
        <main className="App-main">
          <Routes>
            <Route path="/cache-inspector" element={<CacheInspector />} />
            <Route path="/add-property" element={<AddProperty />} />
            <Route path="/" element={<HomeScreen properties={properties} />} />
            {/* ... other routes ... */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
