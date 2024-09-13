import React from 'react';
import { TextField, Box } from '@mui/material';

function AgentInfo({ agentInfo, setAgentInfo }) {
  const handleChange = (field) => (event) => {
    setAgentInfo({ ...agentInfo, [field]: event.target.value });
  };

  return (
    <Box sx={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
      <TextField
        fullWidth
        label="Agent Name"
        variant="outlined"
        value={agentInfo.agent_name || ''}
        onChange={handleChange('agent_name')}
        margin="normal"
      />
      <TextField
        fullWidth
        label="Agent Company"
        variant="outlined"
        value={agentInfo.agent_company || ''}
        onChange={handleChange('agent_company')}
        margin="normal"
      />
      <TextField
        fullWidth
        label="Agent Contact"
        variant="outlined"
        value={agentInfo.agent_contact || ''}
        onChange={handleChange('agent_contact')}
        margin="normal"
      />
    </Box>
  );
}

export default AgentInfo;
