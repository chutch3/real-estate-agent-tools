import React from 'react';
import { Grid, IconButton, Tooltip, Typography, Box } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { useNavigate } from 'react-router-dom';
import PropertyIcon from './PropertyIcon'; // This import should now work

function HomeScreen({ properties }) {
  const navigate = useNavigate();

  const handleAddProperty = () => {
    navigate('/add-property');
  };

  return (
    <Box sx={{ padding: 3 }}>
      <Typography variant="h4" sx={{ mb: 3 }}>My Properties</Typography>
      <Grid container spacing={2}>
        {properties.map((property) => (
          <Grid item key={property.id} xs={6} sm={4} md={3} lg={2}>
            <PropertyIcon property={property} />
          </Grid>
        ))}
        <Grid item xs={6} sm={4} md={3} lg={2}>
          <Tooltip title="Add New Property" arrow>
            <IconButton
              onClick={handleAddProperty}
              aria-label="Add New Property"
              sx={{
                width: '120px',  // Increased from 80px to 120px
                height: '120px', // Increased from 80px to 120px
                backgroundColor: '#D3D3D3',
                color: '#4A4A4A',
                borderRadius: '8px', // Slightly increased for proportion
                boxShadow: '0px 3px 6px rgba(0, 0, 0, 0.1)', // Slightly increased shadow
                '&:hover': {
                  backgroundColor: '#C0C0C0',
                },
                '&:active': {
                  backgroundColor: '#B0B0B0',
                  boxShadow: 'inset 0px 3px 6px rgba(0, 0, 0, 0.1)',
                },
              }}
            >
              <AddIcon sx={{ fontSize: 72 }} />
            </IconButton>
          </Tooltip>
        </Grid>
      </Grid>
    </Box>
  );
}

export default HomeScreen;
