import React from 'react';

function AgentInfo({ agentInfo, setAgentInfo }) {
  return (
    <div className="agent-info">
      <div className="agent-input-group">
        <label htmlFor="agentName">Name:</label>
        <input
          id="agentName"
          type="text"
          placeholder="Agent Name"
          value={agentInfo.agentName}
          onChange={(e) => setAgentInfo({...agentInfo, agentName: e.target.value})}
          className="agent-input"
        />
      </div>
      <div className="agent-input-group">
        <label htmlFor="agentCompany">Company:</label>
        <input
          id="agentCompany"
          type="text"
          placeholder="Agent Company"
          value={agentInfo.agentCompany}
          onChange={(e) => setAgentInfo({...agentInfo, agentCompany: e.target.value})}
          className="agent-input"
        />
      </div>
      <div className="agent-input-group">
        <label htmlFor="agentContact">Contact:</label>
        <input
          id="agentContact"
          type="text"
          placeholder="Agent Contact"
          value={agentInfo.agentContact}
          onChange={(e) => setAgentInfo({...agentInfo, agentContact: e.target.value})}
          className="agent-input"
        />
      </div>
    </div>
  );
}

export default AgentInfo;
