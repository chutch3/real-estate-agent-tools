import React, { useState } from 'react';
import { Button, Checkbox, FormControlLabel, FormGroup, Box, Typography } from '@mui/material';

function SocialMediaPoster({ onPost, isLoading }) {
  const [selectedPlatforms, setSelectedPlatforms] = useState({
    instagram: true,
    facebook: false,
    twitter: false,
  });

  const handleChange = (event) => {
    setSelectedPlatforms({
      ...selectedPlatforms,
      [event.target.name]: event.target.checked,
    });
  };

  const handlePost = () => {
    const platforms = Object.keys(selectedPlatforms).filter(
      (platform) => selectedPlatforms[platform]
    );
    onPost(platforms);
  };

  const isAnyPlatformSelected = Object.values(selectedPlatforms).some(Boolean);

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>
        Select Social Media Platforms
      </Typography>
      <FormGroup>
        <FormControlLabel
          control={<Checkbox checked={selectedPlatforms.instagram} onChange={handleChange} name="instagram" />}
          label="Instagram"
        />
        <FormControlLabel
          control={<Checkbox checked={selectedPlatforms.facebook} onChange={handleChange} name="facebook" />}
          label="Facebook"
        />
        <FormControlLabel
          control={<Checkbox checked={selectedPlatforms.twitter} onChange={handleChange} name="twitter" />}
          label="Twitter"
        />
      </FormGroup>
      <Button
        variant="contained"
        color="primary"
        onClick={handlePost}
        disabled={isLoading || !isAnyPlatformSelected}
        sx={{ mt: 2 }}
      >
        Post to Selected Platforms
      </Button>
    </Box>
  );
}

export default SocialMediaPoster;
