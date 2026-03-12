import { useRef, useState, useEffect } from 'react';

/**
 * ProjectVideoShowcase -- cinematic full-width video section.
 *
 * Designed to sit directly after the hero as a powerful "see this place"
 * moment before the story unfolds. Dark band, single large player,
 * elegant play overlay, and a minimal caption beneath.
 */

/* ---------- tiny play-triangle icon ---------- */
function PlayIcon() {
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      <circle cx="32" cy="32" r="31" stroke="white" strokeWidth="2" opacity="0.4" />
      <polygon points="26,20 26,44 46,32" fill="white" opacity="0.9" />
    </svg>
  );
}

/* ---------- decorative film-grain overlay ---------- */
function FilmGrain() {
  return (
    <div
      className="pointer-events-none absolute inset-0 z-10 mix-blend-overlay opacity-[0.035]"
      style={{
        backgroundImage:
          'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.85\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\'/%3E%3C/svg%3E")',
        backgroundSize: '128px 128px',
      }}
    />
  );
}

export default function ProjectVideoShowcase({ config }) {
  const { videoShowcase, theme } = config;
  if (!videoShowcase) return null;

  const ref = useRef(null);
  const videoRef = useRef(null);
  const [visible, setVisible] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  /* scroll-triggered entrance */
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true); },
      { threshold: 0.15 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  /* play handler for the overlay button */
  const handlePlay = () => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = false;
    v.play();
    setPlaying(true);
    setHasInteracted(true);
  };

  const p = theme.primary;

  return (
    <section
      id="video-showcase"
      ref={ref}
      className="relative overflow-hidden bg-gradient-to-b from-stone-950 via-stone-950 to-stone-900"
    >
      <FilmGrain />

      {/* subtle top fade from hero */}
      <div className="absolute top-0 left-0 right-0 h-24 bg-gradient-to-b from-black/40 to-transparent z-[5]" />

      <div
        className={`relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-20 sm:py-28
          transition-all duration-[1200ms] ease-out
          ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}
      >
        {/* section label */}
        <div className="text-center mb-10">
          <span
            className="inline-block text-[11px] font-semibold tracking-[0.2em] uppercase mb-3"
            style={{ color: p, opacity: 0.7 }}
          >
            {videoShowcase.sectionLabel || 'See the Oasis'}
          </span>
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-white/90 tracking-tight leading-tight">
            {videoShowcase.heading || 'Step Inside the Farm'}
          </h2>
        </div>

        {/* video container */}
        <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-black/50 ring-1 ring-white/[0.06]">
          {/* 16:9 aspect wrapper */}
          <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
            <video
              ref={videoRef}
              className="absolute inset-0 w-full h-full object-cover"
              muted
              playsInline
              preload="metadata"
              poster={videoShowcase.poster || undefined}
              controls={hasInteracted}
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
            >
              <source src={videoShowcase.url} type="video/mp4" />
            </video>

            {/* play overlay -- shown until user interacts */}
            {!hasInteracted && (
              <button
                onClick={handlePlay}
                className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-4
                  bg-black/30 backdrop-blur-[2px] transition-all duration-500 hover:bg-black/20
                  cursor-pointer group"
                aria-label="Play video"
              >
                <div className="transition-transform duration-300 group-hover:scale-110">
                  <PlayIcon />
                </div>
                <span className="text-white/60 text-sm font-medium tracking-wide">
                  {videoShowcase.playLabel || 'Watch the full tour'}
                </span>
              </button>
            )}
          </div>
        </div>

        {/* caption */}
        {videoShowcase.caption && (
          <p className="text-center text-white/30 text-sm mt-6 max-w-lg mx-auto leading-relaxed">
            {videoShowcase.caption}
          </p>
        )}
      </div>

      {/* subtle bottom fade into next section */}
      <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-stone-900/80 to-transparent z-[5]" />
    </section>
  );
}
