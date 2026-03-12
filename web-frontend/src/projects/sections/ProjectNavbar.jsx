import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles, HiOutlineBars3, HiOutlineXMark } from '../../components/icons';

/**
 * ProjectNavbar -- full-featured sticky nav for project landing pages.
 * Includes logo, scroll-to-section links, mobile hamburger, and CTA.
 */
export default function ProjectNavbar({ config }) {
  const { nav, theme, name } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleAnchor = (href) => {
    setMobileOpen(false);
    if (href.startsWith('#')) {
      const el = document.querySelector(href);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <>
      <nav
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          scrolled
            ? 'bg-gray-950/90 backdrop-blur-xl border-b border-white/5 shadow-lg shadow-black/10'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Left: Logo */}
          <div className="flex items-center gap-3">
            <HexIcon Icon={HiOutlineSparkles} accent={p} size="xs" bespoke="leaf" />
            <div className="flex items-baseline gap-2">
              <span className="font-display font-bold text-white text-lg tracking-tight">{nav.logo}</span>
              <span className="text-[11px] text-gray-500 tracking-wider uppercase hidden sm:inline">
                Moringa Oasis
              </span>
            </div>
          </div>

          {/* Center: Desktop links */}
          <div className="hidden lg:flex items-center gap-1">
            {nav.links.map((link) => (
              <button
                key={link.href}
                onClick={() => handleAnchor(link.href)}
                className="px-3 py-1.5 text-[13px] font-medium text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition-all duration-200"
              >
                {link.label}
              </button>
            ))}
          </div>

          {/* Right: CTA + Mobile toggle */}
          <div className="flex items-center gap-3">
            <Link
              to={nav.ctaLink}
              className="hidden sm:inline-flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 hover:-translate-y-0.5 hover:shadow-lg"
              style={{ background: `linear-gradient(135deg, ${p}, ${s})` }}
            >
              {nav.ctaLabel}
            </Link>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden w-9 h-9 flex items-center justify-center rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition"
            >
              {mobileOpen ? <HiOutlineXMark className="w-5 h-5" /> : <HiOutlineBars3 className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="lg:hidden bg-gray-950/95 backdrop-blur-xl border-t border-white/5 px-6 pb-6 pt-2">
            <div className="space-y-1">
              {nav.links.map((link) => (
                <button
                  key={link.href}
                  onClick={() => handleAnchor(link.href)}
                  className="w-full text-left px-4 py-3 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 rounded-xl transition"
                >
                  {link.label}
                </button>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-white/5">
              <Link
                to={nav.ctaLink}
                className="block text-center px-5 py-3 rounded-xl text-sm font-semibold text-white"
                style={{ background: `linear-gradient(135deg, ${p}, ${s})` }}
              >
                {nav.ctaLabel}
              </Link>
            </div>
          </div>
        )}
      </nav>
    </>
  );
}
