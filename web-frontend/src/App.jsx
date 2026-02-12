import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Home from './pages/Home'
import CampaignDetail from './pages/CampaignDetail'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import AdminPanel from './pages/AdminPanel'
import RegisterNgo from './pages/RegisterNgo'
import CreateCampaign from './pages/CreateCampaign'
import FieldAgent from './pages/FieldAgent'
import DonateCheckout from './pages/DonateCheckout'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/campaigns" element={<Home />} />
          <Route path="/campaign/:id" element={<CampaignDetail />} />
          <Route path="/donate" element={<DonateCheckout />} />
          <Route path="/donate/:campaignId" element={<DonateCheckout />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/register-ngo" element={<RegisterNgo />} />
          <Route path="/create-campaign" element={<CreateCampaign />} />
          <Route path="/field-agent" element={<FieldAgent />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </main>
      <footer className="border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-gray-400">© {new Date().getFullYear()} TrustVoice · Voice-First Donation Platform</p>
          <p className="text-xs text-gray-300">Built for Georgetown University STIA Program</p>
        </div>
      </footer>
    </div>
  )
}
