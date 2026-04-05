import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Plus, Bed, Bath } from 'lucide-react';
import PropertyMap from './PropertyMap';
import PropertyDetailPanel from './PropertyDetailPanel';
import apiClient from '../apiClient';

function HomeScreen() {
  const navigate = useNavigate();
  const [properties, setProperties] = useState([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [deleteError, setDeleteError] = useState(null);

  const selectedProperty = properties.find(p => p.id === selectedPropertyId) ?? null;

  useEffect(() => {
    apiClient.listProperties()
      .then(setProperties)
      .catch((err) => console.error('Error loading properties:', err));
  }, []);

  const handleUploadDocument = async (property, files) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      let updated = property;
      for (const file of files) {
        const docId = await apiClient.uploadDocument(file);
        updated = await apiClient.addDocumentToProperty(updated.id, docId, file.name);
      }
      setProperties(prev => prev.map(p => p.id === updated.id ? updated : p));
    } catch {
      setUploadError('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (property, docId) => {
    setDeleteError(null);
    try {
      const updated = await apiClient.deleteDocument(property.id, docId);
      setProperties(prev => prev.map(p => p.id === updated.id ? updated : p));
    } catch {
      setDeleteError('Failed to delete document. Please try again.');
    }
  };

  const handleGeneratePost = (property) => {
    navigate('/generate-post', { state: { property } });
  };

  const handleChat = (property) => {
    navigate('/chat', { state: { property } });
  };

  return (
    <div
      className="fixed inset-0 flex"
      style={{ top: '56px' }}
      aria-label="Property map and listings"
    >
      {/* Sidebar */}
      <aside
        className="flex flex-col bg-white border-r border-linen-200 overflow-hidden shrink-0"
        style={{ width: '340px' }}
        aria-label="Property list"
      >
        {/* Sidebar header */}
        <div className="px-5 py-4 border-b border-linen-200">
          <h1 className="font-serif text-2xl text-ink-900 leading-none">Properties</h1>
          <p className="font-sans text-xs text-ink-400 mt-1.5 tracking-wide">
            {properties.length} {properties.length === 1 ? 'listing' : 'listings'}
          </p>
        </div>

        {/* Property list */}
        <div className="flex-1 overflow-y-auto">
          {properties.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-ink-300 px-6 text-center">
              <MapPin size={28} strokeWidth={1} className="mb-3" />
              <p className="font-sans text-sm">No properties yet</p>
              <p className="font-sans text-xs text-ink-200 mt-1">Add your first property below</p>
            </div>
          ) : (
            properties.map((property, i) => (
              <button
                key={property.id}
                onClick={() => setSelectedPropertyId(property.id)}
                className={`w-full text-left px-5 py-4 border-b border-linen-100 transition-colors hover:bg-linen-50 focus:outline-none focus:bg-linen-100 animate-fade-up opacity-0
                  ${selectedProperty?.id === property.id ? 'bg-linen-100 border-l-2 border-l-bronze-400' : ''}`}
                style={{ animationDelay: `${i * 40}ms`, animationFillMode: 'forwards' }}
                aria-pressed={selectedProperty?.id === property.id}
                aria-label={`Select ${property.formatted_address}`}
              >
                <div className="flex items-start gap-3">
                  <MapPin
                    size={13}
                    className="text-bronze-400 mt-0.5 flex-shrink-0"
                    strokeWidth={2}
                  />
                  <div className="min-w-0">
                    <p className="font-sans text-sm font-medium text-ink-800 leading-snug truncate">
                      {property.formatted_address}
                    </p>
                    <div className="flex items-center gap-3 mt-1">
                      {property.property_type && (
                        <span className="font-sans text-xs text-ink-400">
                          {property.property_type}
                        </span>
                      )}
                      {property.bedrooms > 0 && (
                        <span className="flex items-center gap-1 font-sans text-xs text-ink-400">
                          <Bed size={10} />
                          {property.bedrooms}
                        </span>
                      )}
                      {property.bathrooms > 0 && (
                        <span className="flex items-center gap-1 font-sans text-xs text-ink-400">
                          <Bath size={10} />
                          {property.bathrooms}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Add property button */}
        <div className="p-4 border-t border-linen-200">
          <button
            onClick={() => navigate('/add-property')}
            className="w-full flex items-center justify-center gap-2 bg-bronze-500 hover:bg-bronze-600 active:bg-bronze-700 text-white font-sans text-sm font-medium py-2.5 px-4 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-bronze-400 focus:ring-offset-1"
            aria-label="Add new property"
          >
            <Plus size={15} strokeWidth={2.5} />
            Add Property
          </button>
        </div>
      </aside>

      {/* Map area */}
      <div className="relative flex-1 overflow-hidden">
        <PropertyMap
          properties={properties}
          onPropertySelect={(property) => setSelectedPropertyId(property.id)}
          selectedProperty={selectedProperty}
        />
        <PropertyDetailPanel
          property={selectedProperty}
          onClose={() => setSelectedPropertyId(null)}
          onChat={handleChat}
          onGeneratePost={handleGeneratePost}
          onUploadDocument={handleUploadDocument}
          onDeleteDocument={handleDeleteDocument}
          isUploading={isUploading}
          uploadError={uploadError}
          deleteError={deleteError}
        />
      </div>
    </div>
  );
}

export default HomeScreen;
