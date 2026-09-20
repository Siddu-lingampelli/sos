import { StrictMode, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import './index.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const CAMERA_SOURCE: string = import.meta.env.VITE_CAMERA_SOURCE ?? ''

// Level 1 placeholders + Camera Stream integration
const Login = () => <div className="p-8"><h1 className="text-2xl font-bold text-red-600">Login</h1><p>Level 2 task...</p></div>;

const CameraFeed = ({ source }: { source: string }) => {
  const [offline, setOffline] = useState(false);
  // Reset offline flag whenever the source changes
  const [lastSource, setLastSource] = useState(source);
  if (lastSource !== source) {
    setLastSource(source);
    setOffline(false);
  }
  if (!source) {
    return <span className="text-slate-500">Select a camera above to start the feed</span>;
  }
  if (offline) {
    return <span className="text-slate-500">Camera Offline (Verify Backend at {API_URL})</span>;
  }
  return (
    <img
      key={source}
      src={`${API_URL}/api/stream/video?source=${encodeURIComponent(source)}`}
      alt="Live AI Feed"
      className="w-full h-full object-cover"
      onError={() => setOffline(true)}
    />
  );
};

const Dashboard = () => {
  const [mode, setMode] = useState<'laptop' | 'mobile'>(CAMERA_SOURCE === '0' ? 'laptop' : 'mobile');
  const [mobileUrl, setMobileUrl] = useState(
    CAMERA_SOURCE && CAMERA_SOURCE !== '0' ? CAMERA_SOURCE : 'http://192.168.1.33:8080/video'
  );
  const activeSource = mode === 'laptop' ? '0' : mobileUrl;
  const btn = (active: boolean) =>
    `px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${active ? 'bg-slate-900 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}`;
  return (
  <div className="p-8">
    <h1 className="text-2xl font-bold mb-4">Live Dashboard</h1>
    {/* Camera source picker */}
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <span className="text-sm font-medium text-slate-600">Camera:</span>
      <button className={btn(mode === 'laptop')} onClick={() => setMode('laptop')}>Laptop webcam</button>
      <button className={btn(mode === 'mobile')} onClick={() => setMode('mobile')}>Mobile camera</button>
      {mode === 'mobile' && (
        <input
          value={mobileUrl}
          onChange={(e) => setMobileUrl(e.target.value)}
          placeholder="http://192.168.1.33:8080/video"
          className="flex-1 min-w-64 px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-900"
        />
      )}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Live AI Camera Stream Block */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
        <h2 className="font-semibold mb-2">
          {mode === 'laptop' ? 'Laptop webcam' : 'Mobile camera'}
        </h2>
        <div className="bg-slate-900 rounded-lg overflow-hidden aspect-video flex items-center justify-center">
          <CameraFeed source={activeSource} />
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
};

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
