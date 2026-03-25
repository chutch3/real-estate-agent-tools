import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import NavMenu from './components/NavMenu';
import HomeScreen from './components/HomeScreen';
import AddProperty from './components/AddProperty';
import GeneratePost from './pages/GeneratePost';
import CacheInspector from './pages/CacheInspector';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-linen-100 font-sans">
        <NavMenu />
        <Routes>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/add-property" element={<AddProperty />} />
          <Route path="/generate-post" element={<GeneratePost />} />
          <Route path="/cache-inspector" element={<CacheInspector />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
