import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, CheckCircle } from 'lucide-react';
import LookupProperty from './AddProperty/LookupProperty';
import MissingDetails from './AddProperty/MissingDetails';
import SupportingDocumentation from './AddProperty/SupportingDocumentation';
import PropertySummary from './AddProperty/PropertySummary';
import apiClient from '../apiClient';

const STEPS = ['Look up', 'Details', 'Documents', 'Summary'];

function AddProperty() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [propertyData, setPropertyData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);

  const handlePropertyDataChange = (newData) => {
    setPropertyData((prev) => ({ ...prev, ...newData }));
  };

  const handleFinish = async () => {
    try {
      setIsLoading(true);
      setError('');
      await apiClient.addProperty({
        ...propertyData,
        documents: propertyData.documents || [],
      });
      setShowSuccess(true);
      setActiveStep(0);
      setPropertyData({});
    } catch (err) {
      console.error('Error adding property:', err);
      setError('Failed to add property. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0: return <LookupProperty onDataChange={handlePropertyDataChange} />;
      case 1: return <MissingDetails propertyData={propertyData} onDataChange={handlePropertyDataChange} />;
      case 2: return <SupportingDocumentation onDataChange={handlePropertyDataChange} />;
      case 3: return <PropertySummary propertyData={propertyData} />;
      default: return null;
    }
  };

  return (
    <main className="min-h-screen bg-linen-100 pt-14">
      <div className="max-w-3xl mx-auto px-6 py-10">
        {/* Page heading */}
        <div className="mb-8 animate-fade-up" style={{ animationFillMode: 'both' }}>
          <h1 className="font-serif text-4xl text-ink-900">Add Property</h1>
        </div>

        {/* Step indicator */}
        <nav
          aria-label="Progress steps"
          className="flex items-center mb-8 animate-fade-up"
          style={{ animationDelay: '40ms', animationFillMode: 'both' }}
        >
          {STEPS.map((step, i) => (
            <React.Fragment key={step}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-sans font-medium transition-all duration-300
                    ${i < activeStep
                      ? 'bg-bronze-500 text-white'
                      : i === activeStep
                        ? 'bg-ink-900 text-white'
                        : 'bg-linen-200 text-ink-400'
                    }`}
                  aria-current={i === activeStep ? 'step' : undefined}
                >
                  {i < activeStep ? <Check size={14} strokeWidth={2.5} /> : i + 1}
                </div>
                <span
                  className={`mt-1.5 font-sans text-xs transition-colors ${
                    i === activeStep ? 'text-ink-900 font-medium' : 'text-ink-400'
                  }`}
                >
                  {step}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-px mx-3 mb-5 transition-colors duration-300 ${
                    i < activeStep ? 'bg-bronze-400' : 'bg-linen-300'
                  }`}
                />
              )}
            </React.Fragment>
          ))}
        </nav>

        {/* Step content */}
        <div
          className="bg-white rounded-lg border border-linen-200 p-6 mb-6 animate-fade-up"
          style={{ animationDelay: '80ms', animationFillMode: 'both' }}
        >
          {getStepContent(activeStep)}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <button
            disabled={activeStep === 0 || isLoading}
            onClick={() => setActiveStep((s) => s - 1)}
            className="font-sans text-sm text-ink-500 hover:text-ink-900 disabled:text-ink-200 disabled:cursor-not-allowed transition-colors focus:outline-none"
          >
            Back
          </button>

          {activeStep === STEPS.length - 1 ? (
            <button
              onClick={handleFinish}
              disabled={isLoading}
              className="flex items-center gap-2 bg-bronze-500 hover:bg-bronze-600 disabled:bg-linen-300 text-white font-sans text-sm font-medium py-2.5 px-6 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-400"
            >
              {isLoading ? (
                <Loader2 size={15} className="animate-spin" />
              ) : null}
              {isLoading ? 'Saving…' : 'Add Property'}
            </button>
          ) : (
            <button
              onClick={() => setActiveStep((s) => s + 1)}
              className="bg-ink-900 hover:bg-ink-700 text-white font-sans text-sm font-medium py-2.5 px-6 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-ink-700"
            >
              Next
            </button>
          )}
        </div>

        {error && (
          <p className="font-sans text-sm text-red-700 mt-4" role="alert">
            {error}
          </p>
        )}
      </div>

      {/* Success modal */}
      {showSuccess && (
        <div
          className="fixed inset-0 bg-ink-900/30 flex items-center justify-center z-50 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="success-title"
        >
          <div className="bg-white rounded-xl p-8 text-center shadow-2xl max-w-sm w-full animate-fade-up" style={{ animationFillMode: 'both' }}>
            <CheckCircle
              size={48}
              className="text-bronze-500 mx-auto mb-4"
              strokeWidth={1.5}
            />
            <h2 id="success-title" className="font-serif text-2xl text-ink-900 mb-2">
              Added!
            </h2>
            <p className="font-sans text-sm text-ink-500 mb-6">
              Property has been successfully added.
            </p>
            <button
              onClick={() => {
                setShowSuccess(false);
                navigate('/');
              }}
              className="w-full bg-bronze-500 hover:bg-bronze-600 text-white font-sans text-sm font-medium py-2.5 px-6 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-400"
            >
              Back to Map
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

export default AddProperty;
