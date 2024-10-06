import React, { useState } from 'react';
import { Stepper, Step, StepLabel, Button, Typography, Box, Modal } from '@mui/material';
import LookupProperty from './AddProperty/LookupProperty';
import MissingDetails from './AddProperty/MissingDetails';
import AddPictures from './AddProperty/AddPictures';
import SupportingDocumentation from './AddProperty/SupportingDocumentation';
import PropertySummary from './AddProperty/PropertySummary';
import apiClient from '../apiClient';
import { CircularProgress } from '@mui/material';
import { CheckCircleOutline } from '@mui/icons-material';

const propertySteps = ['Look up property', 'Missing Details', 'Add pictures', 'Add Supporting Documentation', 'Summary'];

function AddProperty() {
  const [activeStep, setActiveStep] = useState(0);
  const [propertyData, setPropertyData] = useState({});
  const [selectedImages, setSelectedImages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [supportingDocs, setSupportingDocs] = useState([]);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handlePropertyDataChange = (newData) => {
    setPropertyData((prevData) => ({ ...prevData, ...newData }));
  };

  const handleImagesSelected = (files) => {
    setSelectedImages(files);
  };


  const handleSupportingDocsChange = (files) => {
    setSupportingDocs(files);
  };

  const handleFinish = async () => {
    try {
      setIsLoading(true);
      setError('');
      await apiClient.addProperty({ ...propertyData, images: selectedImages, supportingDocs });
      setShowSuccessModal(true);
      // Reset form
      setActiveStep(0);
      setPropertyData({});
      setSelectedImages([]);
      setSupportingDocs([]);
    } catch (error) {
      console.error('Error adding property:', error);
      setError('Failed to add property. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return <LookupProperty onDataChange={handlePropertyDataChange} />;
      case 1:
        return <MissingDetails propertyData={propertyData} onDataChange={handlePropertyDataChange} />;
      case 2:
        return <AddPictures 
          selectedImages={selectedImages} 
          onImagesSelected={handleImagesSelected} 
        />;
      case 3:
        return <SupportingDocumentation onFilesChange={handleSupportingDocsChange} />;
      case 4:
        return <PropertySummary 
          propertyData={propertyData} 
          images={selectedImages} 
          supportingDocs={supportingDocs}
        />;
      default:
        return 'Unknown step';
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <Stepper activeStep={activeStep}>
        {propertySteps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      <Box sx={{ mt: 2, mb: 1 }}>
        <Typography>Step {activeStep + 1}</Typography>
        {getStepContent(activeStep)}
      </Box>
      <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
        <Button
          color="inherit"
          disabled={activeStep === 0 || isLoading}
          onClick={handleBack}
          sx={{ mr: 1 }}
        >
          Back
        </Button>
        <Box sx={{ flex: '1 1 auto' }} />
        {activeStep === propertySteps.length - 1 ? (
          <Button onClick={handleFinish} disabled={isLoading}>
            {isLoading ? <CircularProgress size={24} /> : 'Finish'}
          </Button>
        ) : (
          <Button onClick={handleNext}>Next</Button>
        )}
      </Box>
      {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}

      <Modal
        open={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        aria-labelledby="success-modal-title"
        aria-describedby="success-modal-description"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 4,
          textAlign: 'center',
        }}>
          <CheckCircleOutline sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
          <Typography id="success-modal-title" variant="h5" component="h2">
            Added!
          </Typography>
          <Typography id="success-modal-description" sx={{ mt: 2 }}>
            Property has been successfully added.
          </Typography>
        </Box>
      </Modal>
    </Box>
  );
}

export default AddProperty;
