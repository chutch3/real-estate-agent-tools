import React from 'react';
import { Card, CardContent, Typography } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';

function PropertyIcon({ property }) {
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <CardContent>
        <HomeIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Typography variant="body2" component="div" sx={{ mt: 1 }}>
          {property.name || 'Property'}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default PropertyIcon;
