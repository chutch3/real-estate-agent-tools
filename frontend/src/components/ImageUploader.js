import React, { useRef } from 'react';

function ImageUploader({ selectedImages, onImagesSelected, onImageRemove }) {
  const fileInputRef = useRef(null);

  const handleImageUpload = (event) => {
    if (event.target.files) {
      const files = Array.from(event.target.files);
      onImagesSelected([...selectedImages, ...files]);
    }
  };

  const handleRemove = (index) => {
    onImageRemove(index);
    if (selectedImages.length === 1) {
      // Clear the file input when removing the last image
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="image-uploader">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        multiple
        onChange={handleImageUpload}
        aria-label="Add Pictures"
      />
      <div className="image-previews">
        {selectedImages.map((file, index) => (
          <div key={index} className="image-preview-container">
            <img
              src={URL.createObjectURL(file)}
              alt={`Preview ${index + 1}`}
              className="image-preview"
            />
            <button
              onClick={() => handleRemove(index)}
              className="remove-image-button"
              aria-label={`Remove image ${index + 1}`}
            >
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ImageUploader;
