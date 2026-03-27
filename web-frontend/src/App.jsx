import { Component } from 'react'
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
import DonationHistory from './portal/DonationHistory'
import PortalAdminSection from './portal/PortalAdminSection'
import PortalVerify from './portal/PortalVerify'
import PortalHistory from './portal/PortalHistory'

/* ── Global Error Boundary ─────────────────────────────────── */
class GlobalErrorBoundary extends Component {
  state = { hasError: false, error: null, errorInfo: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('[GlobalErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: '#0a0a0a', color: '#fff', fontFamily: 'system-ui, sans-serif',
          padding: '2rem'
        }}>
          <div style={{ maxWidth: '36rem', textAlign: 'center' }}>
            <div style={{
              width: 56, height: 56, margin: '0 auto 1.5rem', borderRadius: '50%',
              background: 'rgba(239,68,68,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F87171" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
              </svg>
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>Something went wrong</h2>
            <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.875rem', marginBottom: '1rem' }}>
              The app encountered an unexpected error.
            </p>
            <pre style={{
              background: 'rgba(255,255,255,0.05)', borderRadius: '0.5rem', padding: '1rem',
              fontSize: '0.75rem', color: '#F87171', textAlign: 'left', overflow: 'auto',
              maxHeight: '12rem', marginBottom: '1.5rem', border: '1px solid rgba(255,255,255,0.1)'
            }}>
              {this.state.error?.message}\n\n{this.state.error?.stack}
            </pre>
            {this.state.errorInfo?.componentStack && (
              <details style={{ textAlign: 'left', marginBottom: '1.5rem' }}>
                <summary style={{ cursor: 'pointer', fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)' }}>
                  Component stack
                </summary>
                <pre style={{
                  background: 'rgba(255,255,255,0.05)', borderRadius: '0.5rem', padding: '0.75rem',
                  fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', overflow: 'auto', maxHeight: '10rem',
                  marginTop: '0.5rem'
                }}>
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            <button
              onClick={() => { this.setState({ hasError: false, error: null, errorInfo: null }); }}
              style={{
                padding: '0.625rem 1.5rem', borderRadius: '0.5rem', background: 'rgba(255,255,255,0.1)',
                color: '#fff', border: 'none', cursor: 'pointer', fontSize: '0.875rem', marginRight: '0.75rem'
              }}
            >
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '0.625rem 1.5rem', borderRadius: '0.5rem', background: '#10B981',
                color: '#fff', border: 'none', cursor: 'pointer', fontSize: '0.875rem'
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

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

/* Assistant layout — no footer, full viewport height for chat */
function AssistantLayout() {
  return (
    <div className="h-[100dvh] flex flex-col bg-gradient-to-b from-stone-50 via-emerald-50/30 to-amber-50/20">
      <Navbar />
      <main className="flex-1 min-h-0">
        <Assistant />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <GlobalErrorBoundary>
    <Routes>
      {/* Project pages — their own layout */}
      <Route path="/project/:slug" element={<ProjectLanding />} />

      {/* Assistant — own layout, no footer */}
      <Route path="/assistant" element={<AssistantLayout />} />

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
        <Route path="donations" element={<DonationHistory />} />
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
    </GlobalErrorBoundary>
  )
}
