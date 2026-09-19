import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import './index.css'

// Level 1 placeholders
const Login = () => <div className="p-8"><h1 className="text-2xl font-bold text-red-600">Login</h1><p>Level 2 task...</p></div>;
const Dashboard = () => <div className="p-8"><h1 className="text-2xl font-bold">Dashboard</h1><p>Level 8 task...</p></div>;
const ActiveAlert = () => <div className="p-8"><h1 className="text-2xl font-bold text-orange-500">Live Incident</h1></div>;
const History = () => <div className="p-8"><h1 className="text-2xl font-bold text-blue-600">Incident History</h1></div>;
const Cameras = () => <div className="p-8"><h1 className="text-2xl font-bold text-green-600">Cameras & Locations</h1></div>;

const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-gray-50 flex flex-col">
    <header className="bg-slate-900 text-white p-4 font-bold flex justify-between">
      <span>SilentSOS</span>
      <nav className="flex gap-4 text-sm font-normal">
        <a href="/" className="hover:text-red-400">Dashboard</a>
        <a href="/alert/1" className="hover:text-red-400">Alert</a>
        <a href="/history" className="hover:text-red-400">History</a>
        <a href="/cameras" className="hover:text-red-400">Cameras</a>
        <a href="/login" className="hover:text-red-400">Login</a>
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
