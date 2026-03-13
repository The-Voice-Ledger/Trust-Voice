import { Link } from 'react-router-dom';
import { HiOutlineMicrophone } from './icons';
import {
  HiOutlineGlobeAlt, HiOutlineBanknotes, HiOutlineChartBar,
  HiOutlineBuildingOffice2, HiOutlinePlusCircle, HiOutlineCamera,
  HiOutlineShieldCheck, HiOutlineMapPin, HiOutlineDocumentText,
} from './icons';
import { CircuitTrace } from './SvgDecorations';

export default function Footer() {
  return (
    <footer className="relative border-t border-gray-100 bg-white hidden sm:block overflow-hidden">
      <CircuitTrace className="absolute inset-0 w-full h-full text-gray-400" />
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-8">
          {/* Platform */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3 font-display">Platform</h4>
            <nav className="space-y-2.5">
              <FooterLink to="/campaigns" Icon={HiOutlineGlobeAlt}>Campaigns</FooterLink>
              <FooterLink to="/projects" Icon={HiOutlineMapPin}>Projects</FooterLink>
              <FooterLink to="/fund" Icon={HiOutlineBanknotes}>Fund</FooterLink>
              <FooterLink to="/analytics" Icon={HiOutlineChartBar}>Analytics</FooterLink>
            </nav>
          </div>

          {/* Get Involved */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3 font-display">Get Involved</h4>
            <nav className="space-y-2.5">
              <FooterLink to="/register-ngo" Icon={HiOutlineBuildingOffice2}>Register NGO</FooterLink>
              <FooterLink to="/create-campaign" Icon={HiOutlinePlusCircle}>Create Campaign</FooterLink>
              <FooterLink to="/field-agent" Icon={HiOutlineCamera}>Field Agent</FooterLink>
            </nav>
          </div>

          {/* Trust & Transparency */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3 font-display">Trust</h4>
            <div className="space-y-2.5">
              <TrustItem Icon={HiOutlineShieldCheck}>Blockchain Verified</TrustItem>
              <TrustItem Icon={HiOutlineMapPin}>GPS Field Reports</TrustItem>
              <TrustItem Icon={HiOutlineDocumentText}>Tax Receipts</TrustItem>
            </div>
          </div>

          {/* About */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3 font-display">About</h4>
            <div className="space-y-2.5">
              <p className="text-sm text-gray-500">Voice-First Platform</p>
              <p className="text-sm text-gray-500">Open Source</p>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-100 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-600 to-green-700 flex items-center justify-center">
              <HiOutlineMicrophone className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-bold text-gray-800 tracking-tight font-display">VBV</span>
          </div>
          <p className="text-xs text-gray-400">
            © {new Date().getFullYear()} VBV
          </p>
        </div>
      </div>
    </footer>
  );
}

function FooterLink({ to, Icon, children }) {
  return (
    <Link to={to} className="flex items-center gap-2 text-sm text-gray-500 hover:text-emerald-600 transition group">
      <Icon className="w-4 h-4 text-gray-400 group-hover:text-emerald-500 transition" />
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
