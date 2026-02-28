import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import MobileBottomNav from './components/MobileBottomNav'
import Footer from './components/Footer'
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
import Assistant from './pages/Assistant'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <main className="flex-1 pb-20 sm:pb-0">
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
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </main>
      <Footer />
      <MobileBottomNav />
    </div>
  )
}
