import { Routes, Route, Navigate, useParams } from 'react-router-dom'
import Navbar from './components/Navbar'
import MobileBottomNav from './components/MobileBottomNav'
import Footer from './components/Footer'
import Landing from './pages/Landing'
import Home from './pages/Home'
import CampaignDetail from './pages/CampaignDetail'
import Login from './pages/Login'
import Analytics from './pages/Analytics'
import RegisterNgo from './pages/RegisterNgo'
import DonateCheckout from './pages/DonateCheckout'
import Assistant from './pages/Assistant'
import ProjectLanding from './projects/ProjectLanding'
import ProjectsIndex from './pages/ProjectsIndex'
import NgoProfile from './pages/NgoProfile'

/* Portal imports */
import PortalLayout from './portal/PortalLayout'
import PortalDashboard from './portal/PortalDashboard'
import ProjectsDashboard from './portal/ProjectsDashboard'
import PortalCampaignEditor from './portal/PortalCampaignEditor'
import PortalCampaignCreate from './portal/PortalCampaignCreate'
import MilestoneManager from './portal/MilestoneManager'
import CampaignFinancials from './portal/CampaignFinancials'
import FunderDashboard from './portal/FunderDashboard'
import PortalAdminSection from './portal/PortalAdminSection'
import PortalVerify from './portal/PortalVerify'
import PortalHistory from './portal/PortalHistory'

/* Redirect helper for parameterised donate routes */
function DonateRedirect() {
  const { campaignId } = useParams();
  return <Navigate to={campaignId ? `/fund/${campaignId}` : '/fund'} replace />;
}

/* Standard layout wrapper (Navbar + Footer) */
function StandardLayout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <main className="flex-1 pb-20 sm:pb-0">{children}</main>
      <Footer />
      <MobileBottomNav />
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      {/* Project pages — their own layout */}
      <Route path="/project/:slug" element={<ProjectLanding />} />

      {/* Portal — role-based sidebar layout */}
      <Route path="/portal" element={<PortalLayout />}>
        <Route index element={<PortalDashboard />} />
        {/* NGO / Project Owner */}
        <Route path="projects" element={<ProjectsDashboard />} />
        <Route path="projects/:id/edit" element={<PortalCampaignEditor />} />
        <Route path="projects/:id/milestones" element={<MilestoneManager />} />
        <Route path="projects/:id/financials" element={<CampaignFinancials />} />
        <Route path="create" element={<PortalCampaignCreate />} />
        {/* Funder */}
        <Route path="donations" element={<FunderDashboard />} />
        <Route path="receipts" element={<FunderDashboard />} />
        {/* Admin — each sub-route renders the correct CRUD section */}
        <Route path="admin/ngos" element={<PortalAdminSection />} />
        <Route path="admin/users" element={<PortalAdminSection />} />
        <Route path="admin/payouts" element={<PortalAdminSection />} />
        <Route path="admin/milestones" element={<PortalAdminSection />} />
        {/* Field Agent */}
        <Route path="verify" element={<PortalVerify />} />
        <Route path="history" element={<PortalHistory />} />
      </Route>

      {/* Standard app pages */}
      <Route
        path="*"
        element={
          <StandardLayout>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/campaigns" element={<Home />} />
              <Route path="/campaign/:id" element={<CampaignDetail />} />
              <Route path="/ngo/:id" element={<NgoProfile />} />
              <Route path="/fund" element={<DonateCheckout />} />
              <Route path="/fund/:campaignId" element={<DonateCheckout />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/register-ngo" element={<RegisterNgo />} />
              <Route path="/assistant" element={<Assistant />} />
              <Route path="/projects" element={<ProjectsIndex />} />
              <Route path="/login" element={<Login />} />
              {/* Redirects: old standalone pages → portal equivalents */}
              <Route path="/dashboard" element={<Navigate to="/portal" replace />} />
              <Route path="/admin" element={<Navigate to="/portal" replace />} />
              <Route path="/field-agent" element={<Navigate to="/portal/verify" replace />} />
              <Route path="/create-campaign" element={<Navigate to="/portal/create" replace />} />
              <Route path="/donate" element={<Navigate to="/fund" replace />} />
              <Route path="/donate/:campaignId" element={<DonateRedirect />} />
            </Routes>
          </StandardLayout>
        }
      />
    </Routes>
  )
}
