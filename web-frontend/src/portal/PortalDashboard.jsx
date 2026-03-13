/**
 * PortalDashboard — role-contextual landing page for the portal.
 *
 * Renders a different dashboard depending on the authenticated user's role:
 *   DONOR          → Funder overview (recent donations, funded campaigns)
 *   NGO_ADMIN /
 *   CAMPAIGN_CREATOR → Project owner overview (campaigns, milestones, funds)
 *   SUPER_ADMIN /
 *   SYSTEM_ADMIN    → Platform admin overview (pending approvals, stats)
 *   FIELD_AGENT     → Agent overview (verification queue, earnings)
 */
import useAuthStore from '../stores/authStore';
import FunderDashboard from './FunderDashboard';
import NgoOverview from './NgoOverview';
import AdminDashboard from './AdminDashboard';
import AgentDashboard from './AgentDashboard';

export default function PortalDashboard() {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;

  const role = (user.role || '').toUpperCase();

  if (role === 'SUPER_ADMIN' || role === 'SYSTEM_ADMIN')
    return <AdminDashboard user={user} />;

  if (role === 'NGO_ADMIN' || role === 'CAMPAIGN_CREATOR')
    return <NgoOverview user={user} />;

  if (role === 'FIELD_AGENT')
    return <AgentDashboard user={user} />;

  // Default: Funder / Donor / Viewer
  return <FunderDashboard user={user} />;
}
