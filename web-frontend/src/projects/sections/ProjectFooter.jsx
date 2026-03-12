import { Link } from 'react-router-dom';
import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectFooter -- rich multi-column footer for project landing pages.
 */
export default function ProjectFooter({ config }) {
  const { footer, theme, name, tagline } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const handleAnchor = (href) => {
    if (href.startsWith('#')) {
      const el = document.querySelector(href);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <footer className="relative bg-gray-950 border-t border-white/5 overflow-hidden">
      {/* Decorative gradient line at top */}
      <div className="absolute top-0 left-0 right-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${p}, ${s}, transparent)` }} />

      <div className="max-w-6xl mx-auto px-6 pt-16 pb-10">
        {/* Top row: brand + columns */}
        <div className="grid md:grid-cols-5 gap-12 mb-12">
          {/* Brand column */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <HexIcon Icon={HiOutlineSparkles} accent={p} size="sm" bespoke="leaf" />
              <div>
                <span className="font-display font-bold text-white text-xl">{name}</span>
                <span className="block text-xs text-gray-500 mt-0.5">{tagline}</span>
              </div>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed max-w-xs">
              {footer.description}
            </p>
          </div>

          {/* Link columns */}
          {footer.columns.map((col, i) => (
            <div key={i}>
              <h4 className="text-xs font-bold uppercase tracking-[0.15em] text-gray-400 mb-4">{col.title}</h4>
              <ul className="space-y-2.5">
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
        <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-xs text-gray-600">
            <span>&copy; {new Date().getFullYear()} {name}</span>
            <span className="w-1 h-1 rounded-full bg-gray-700" />
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
