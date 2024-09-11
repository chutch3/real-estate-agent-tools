import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import apiClient from './apiClient';

const root = createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App apiClient={apiClient} />
  </React.StrictMode>
);
