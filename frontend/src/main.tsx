import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import './index.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const CAMERA_SOURCE: string = import.meta.env.VITE_CAMERA_SOURCE ?? ''

// Level 1 placeholders + Camera Stream integration
const Login = () => <div className="p-8"><h1 className="text-2xl font-bold text-red-600">Login</h1><p>Level 2 task...</p></div>;

const CameraFeed = () => {
  const [offline, setOffline] = useState(false);
  if (!CAMERA_SOURCE) {
    return <span className="text-slate-500">No camera configured — set VITE_CAMERA_SOURCE to your phone IP (e.g. http://192.168.1.33:8080/video)</span>;
  }
  if (offline) {
    return <span className="text-slate-500">Camera Offline (Verify Backend at {API_URL})</span>;
  }
  return (
    <img
      src={`${API_URL}/api/stream/video?source=${encodeURIComponent(CAMERA_SOURCE)}`}
      alt="Live AI Feed"
      className="w-full h-full object-cover"
      onError={() => setOffline(true)}
    />
  );
};

const Dashboard = () => (
  <div className="p-8">
    <h1 className="text-2xl font-bold mb-4">Live Dashboard</h1>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Live AI Camera Stream Block */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
        <h2 className="font-semibold mb-2">Camera 1 (Main Hallway)</h2>
        <div className="bg-slate-900 rounded-lg overflow-hidden aspect-video flex items-center justify-center">
          <CameraFeed />
        </div>
      </div>

      {/* Placeholder for Alerts */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
        <h2 className="font-semibold mb-2 text-red-600">Recent Alerts</h2>
        <p className="text-slate-500 text-sm">System monitoring active. No incidents reported today.</p>
      </div>
    </div>
  </div>
);

const ActiveAlert = () => <div className="p-8"><h1 className="text-2xl font-bold text-orange-500">Live Incident</h1></div>;
const History = () => <div className="p-8"><h1 className="text-2xl font-bold text-blue-600">Incident History</h1></div>;
const Cameras = () => <div className="p-8"><h1 className="text-2xl font-bold text-green-600">Cameras & Locations</h1></div>;

const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-slate-50 flex flex-col">
    <header className="bg-slate-900 text-white p-4 font-bold flex justify-between shadow-md">
      <span>SilentSOS Security</span>
      <nav className="flex gap-4 text-sm font-normal">
        <a href="/" className="hover:text-red-400 transition-colors">Dashboard</a>
        <a href="/alert/1" className="hover:text-red-400 transition-colors">Alert</a>
        <a href="/history" className="hover:text-red-400 transition-colors">History</a>
        <a href="/cameras" className="hover:text-red-400 transition-colors">Cameras</a>
        <a href="/login" className="hover:text-red-400 transition-colors">Login</a>
      </nav>
    </header>
    <main className="flex-1">{children}</main>
  </div>
);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/login" element={<Login />} />
          <Route path="/alert/:id" element={<ActiveAlert />} />
          <Route path="/history" element={<History />} />
          <Route path="/cameras" element={<Cameras />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </StrictMode>,
)
