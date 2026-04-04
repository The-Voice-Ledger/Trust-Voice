import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { HiOutlineBars3, HiOutlineXMark } from '../../components/icons';

/**
 * ProjectNavbar -- warm, minimal sticky nav.
 * Transparent over the hero, frosted glass on scroll.
 */
export default function ProjectNavbar({ config }) {
  const { nav, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const navigate = useNavigate();

  const scrollTo = (href) => {
    setMobileOpen(false);
    if (href.startsWith('#')) {
      const el = document.querySelector(href);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      navigate(href);
    }
  };

  return (
    <nav
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-white/80 backdrop-blur-xl shadow-sm shadow-black/[0.03] border-b border-gray-200/60'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-6 h-[60px] flex items-center justify-between">
        {/* Logo */}
        <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="flex items-center gap-2.5 group">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors duration-300"
            style={{ backgroundColor: scrolled ? `${p}12` : 'rgba(255,255,255,0.1)' }}
          >
            <svg viewBox="0 0 20 20" className="w-4 h-4" fill="none">
              <path
                d="M10 2C10 2 5 8 5 12a5 5 0 0010 0c0-4-5-10-5-10z"
                fill={scrolled ? p : 'rgba(255,255,255,0.7)'}
                className="transition-colors duration-300"
              />
              <path d="M10 6c0 0-2.5 3-2.5 5a2.5 2.5 0 005 0c0-2-2.5-5-2.5-5z" fill={scrolled ? `${p}44` : 'rgba(255,255,255,0.25)'} className="transition-colors duration-300" />
            </svg>
          </div>
          <span className={`font-display font-semibold text-[15px] tracking-tight transition-colors duration-300 ${scrolled ? 'text-gray-900' : 'text-white'}`}>
            {nav.logo}
          </span>
        </button>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {nav.links.map((link) => (
            <button
              key={link.href}
              onClick={() => scrollTo(link.href)}
              className={`px-3 py-1.5 text-[13px] font-medium rounded-lg transition-all duration-200 ${
                scrolled
                  ? 'text-gray-500 hover:text-gray-900 hover:bg-gray-100/60'
                  : 'text-white/60 hover:text-white hover:bg-white/[0.08]'
              }`}
            >
              {link.label}
            </button>
          ))}
          {/* Separator + VBV home */}
          <span className={`mx-1 text-[11px] ${scrolled ? 'text-gray-300' : 'text-white/20'}`}>|</span>
          <Link
            to="/"
            className={`px-3 py-1.5 text-[13px] font-medium rounded-lg transition-all duration-200 flex items-center gap-1 ${
              scrolled
                ? 'text-indigo-500 hover:text-indigo-700 hover:bg-indigo-50/60'
                : 'text-indigo-300/70 hover:text-white hover:bg-white/[0.08]'
            }`}
          >
            VBV
            <svg className="w-3 h-3 opacity-60" viewBox="0 0 12 12" fill="none"><path d="M3 9L9 3M9 3H4.5M9 3V7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </Link>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <Link
            to={nav.ctaLink}
            className="hidden sm:inline-flex items-center px-5 py-2 rounded-lg text-[13px] font-semibold text-white transition-all duration-200 hover:opacity-90"
            style={{ backgroundColor: p }}
          >
            {nav.ctaLabel}
          </Link>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className={`md:hidden w-9 h-9 flex items-center justify-center rounded-lg transition ${
              scrolled ? 'text-gray-600 hover:bg-gray-100' : 'text-white/70 hover:bg-white/10'
            }`}
          >
            {mobileOpen ? <HiOutlineXMark className="w-5 h-5" /> : <HiOutlineBars3 className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className={`md:hidden px-6 pb-5 pt-1 ${scrolled ? 'bg-white/90 backdrop-blur-xl' : 'bg-gray-950/90 backdrop-blur-xl'}`}>
          <div className="space-y-0.5">
            {nav.links.map((link) => (
              <button
                key={link.href}
                onClick={() => scrollTo(link.href)}
                className={`w-full text-left px-4 py-2.5 text-sm font-medium rounded-lg transition ${
                  scrolled ? 'text-gray-600 hover:text-gray-900 hover:bg-gray-50' : 'text-gray-300 hover:text-white hover:bg-white/5'
                }`}
              >
                {link.label}
              </button>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-gray-200/10 space-y-2">
            <Link
              to={nav.ctaLink}
              className="block text-center px-4 py-2.5 rounded-lg text-sm font-semibold text-white"
              style={{ backgroundColor: p }}
            >
              {nav.ctaLabel}
            </Link>
            <Link
              to="/"
              className={`flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition ${
                scrolled ? 'text-indigo-600 hover:bg-indigo-50' : 'text-indigo-300 hover:bg-white/5'
              }`}
            >
              VBV Home
              <svg className="w-3.5 h-3.5 opacity-60" viewBox="0 0 12 12" fill="none"><path d="M3 9L9 3M9 3H4.5M9 3V7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
