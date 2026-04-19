import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import NavMenu from "./components/NavMenu";
import HomeScreen from "./components/HomeScreen";
import AddProperty from "./components/AddProperty";
import Chat from "./pages/Chat";
import GeneratePost from "./pages/GeneratePost";
import NetSheet from "./pages/NetSheet";
import CacheInspector from "./pages/CacheInspector";
import LoginPage from "./pages/LoginPage";
import ConsumerPortal from "./pages/ConsumerPortal";
import MagicLinkManager from "./pages/MagicLinkManager";

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/client/:token" element={<ConsumerPortal />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <div className="min-h-screen bg-linen-100 font-sans">
                  <NavMenu />
                  <Routes>
                    <Route path="/" element={<HomeScreen />} />
                    <Route path="/add-property" element={<AddProperty />} />
                    <Route path="/chat" element={<Chat />} />
                    <Route path="/generate-post" element={<GeneratePost />} />
                    <Route path="/net-sheet" element={<NetSheet />} />
                    <Route
                      path="/cache-inspector"
                      element={<CacheInspector />}
                    />
                    <Route path="/magic-links" element={<MagicLinkManager />} />
                  </Routes>
                </div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
