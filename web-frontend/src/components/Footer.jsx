import { Link } from 'react-router-dom';
import { HiOutlineMicrophone } from 'react-icons/hi';
import {
  HiOutlineGlobeAlt, HiOutlineHeart, HiOutlineChartBar,
  HiOutlineBuildingOffice2, HiOutlinePlusCircle, HiOutlineCamera,
  HiOutlineShieldCheck, HiOutlineMapPin, HiOutlineDocumentText,
} from 'react-icons/hi2';

export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-white hidden sm:block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-8">
          {/* Platform */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Platform</h4>
            <nav className="space-y-2.5">
              <FooterLink to="/campaigns" Icon={HiOutlineGlobeAlt}>Campaigns</FooterLink>
              <FooterLink to="/donate" Icon={HiOutlineHeart}>Donate</FooterLink>
              <FooterLink to="/analytics" Icon={HiOutlineChartBar}>Analytics</FooterLink>
            </nav>
          </div>

          {/* Get Involved */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Get Involved</h4>
            <nav className="space-y-2.5">
              <FooterLink to="/register-ngo" Icon={HiOutlineBuildingOffice2}>Register NGO</FooterLink>
              <FooterLink to="/create-campaign" Icon={HiOutlinePlusCircle}>Create Campaign</FooterLink>
              <FooterLink to="/field-agent" Icon={HiOutlineCamera}>Field Agent</FooterLink>
            </nav>
          </div>

          {/* Trust & Transparency */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Trust</h4>
            <div className="space-y-2.5">
              <TrustItem Icon={HiOutlineShieldCheck}>Blockchain Verified</TrustItem>
              <TrustItem Icon={HiOutlineMapPin}>GPS Field Reports</TrustItem>
              <TrustItem Icon={HiOutlineDocumentText}>Tax Receipts</TrustItem>
            </div>
          </div>

          {/* About */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">About</h4>
            <div className="space-y-2.5">
              <p className="text-sm text-gray-500">Voice-First Platform</p>
              <p className="text-sm text-gray-500">Open Source</p>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-100 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-teal-600 flex items-center justify-center">
              <HiOutlineMicrophone className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-bold text-gray-800 tracking-tight">TrustVoice</span>
          </div>
          <p className="text-xs text-gray-400">
            © {new Date().getFullYear()} TrustVoice
          </p>
        </div>
      </div>
    </footer>
  );
}

function FooterLink({ to, Icon, children }) {
  return (
    <Link to={to} className="flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 transition group">
      <Icon className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition" />
      {children}
    </Link>
  );
}

function TrustItem({ Icon, children }) {
  return (
    <div className="flex items-center gap-2 text-sm text-gray-500">
      <Icon className="w-4 h-4 text-gray-400" />
      {children}
    </div>
  );
}
