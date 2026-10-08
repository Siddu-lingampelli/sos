import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";
import "./index.css";
import { CameraProvider } from "./lib/camera";
import { LoginRoute, ProtectedRoute } from "./components/AuthGate";
import Layout from "./components/Layout";
import Alerts from "./pages/Alerts";
import Cameras from "./pages/Cameras";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import IncidentDetail from "./pages/IncidentDetail";
import Locations from "./pages/Locations";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route
          element={
            <CameraProvider>
              <Layout />
            </CameraProvider>
          }
        >
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
          <Route path="/alert/:id" element={<ProtectedRoute><IncidentDetail /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="/cameras" element={<ProtectedRoute><Cameras /></ProtectedRoute>} />
          <Route path="/locations" element={<ProtectedRoute><Locations /></ProtectedRoute>} />
          <Route path="/login" element={<LoginRoute />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
