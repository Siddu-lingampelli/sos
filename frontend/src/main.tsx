import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";
import "./index.css";
import Layout from "./components/Layout";
import Alerts from "./pages/Alerts";
import Cameras from "./pages/Cameras";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import IncidentDetail from "./pages/IncidentDetail";
import Login from "./pages/Login";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/alert/:id" element={<IncidentDetail />} />
          <Route path="/history" element={<History />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/login" element={<Login />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
