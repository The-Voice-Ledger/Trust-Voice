import { Link } from 'react-router-dom';
import { FooterMoonscape } from '../illustrations/ProjectScenes';

/**
 * ProjectFooter -- warm, clean footer for project micro-sites.
 */
export default function ProjectFooter({ config }) {
  const { footer, theme, name, tagline } = config;
  const p = theme.primary;

  const handleAnchor = (href) => {
    if (href.startsWith('#')) {
      const el = document.querySelector(href);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <footer className="relative bg-gray-950 border-t border-white/[0.06] overflow-hidden">
      {/* Moonlit mountain silhouette behind footer content */}
      <div className="absolute top-0 left-0 right-0 pointer-events-none opacity-60" style={{ height: '140px' }}>
        <FooterMoonscape />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 pt-14 pb-10">
        {/* Top row: brand + columns */}
        <div className="grid md:grid-cols-5 gap-10 mb-10">
          {/* Brand column */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p }} />
              <span className="font-display font-semibold text-white text-lg">{name}</span>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed max-w-xs">
              {footer.description}
            </p>
          </div>

          {/* Link columns */}
          {footer.columns.map((col, i) => (
            <div key={i}>
              <h4 className="text-xs font-medium uppercase tracking-[0.15em] text-gray-500 mb-4">{col.title}</h4>
              <ul className="space-y-2">
                {col.links.map((link, j) => (
                  <li key={j}>
                    {link.href.startsWith('#') ? (
                      <button
                        onClick={() => handleAnchor(link.href)}
                        className="text-sm text-gray-500 hover:text-white transition-colors duration-200"
                      >
                        {link.label}
                      </button>
                    ) : (
                      <Link
                        to={link.href}
                        className="text-sm text-gray-500 hover:text-white transition-colors duration-200"
                      >
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-white/[0.04] pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-xs text-gray-600">
            <span>&copy; {new Date().getFullYear()} {name}</span>
            <span className="text-gray-700">&middot;</span>
            <span>
              Powered by{' '}
              <Link to="/" className="text-indigo-400 hover:text-indigo-300 transition">TrustVoice</Link>
            </span>
          </div>
          <p className="text-[11px] text-gray-700 max-w-md text-center sm:text-right leading-relaxed">
            {footer.legal}
          </p>
        </div>
      </div>
    </footer>
  );
}
