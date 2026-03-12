import { useParams, Link } from 'react-router-dom';
import { getProject } from './projectRegistry';
import ThemeScope from './ThemeScope';

/* Layout components */
import ProjectNavbar from './sections/ProjectNavbar';
import ProjectFooter from './sections/ProjectFooter';

/* Section components */
import ProjectHero from './sections/ProjectHero';
import ProjectVision from './sections/ProjectVision';
import ProjectNarrative from './sections/ProjectNarrative';
import ProjectMarket from './sections/ProjectMarket';
import ProjectPillars from './sections/ProjectPillars';
import ProjectAdvantages from './sections/ProjectAdvantages';
import ProjectExperience from './sections/ProjectExperience';
import ProjectFinancials from './sections/ProjectFinancials';
import ProjectCTA from './sections/ProjectCTA';

const SECTION_MAP = {
  hero: ProjectHero,
  vision: ProjectVision,
  narrative: ProjectNarrative,
  market: ProjectMarket,
  pillars: ProjectPillars,
  advantages: ProjectAdvantages,
  experience: ProjectExperience,
  financials: ProjectFinancials,
  cta: ProjectCTA,
};

/**
 * ProjectLanding -- full micro-site compositor.
 *
 * Reads the slug from the URL, looks up config in the registry,
 * then renders a complete standalone website with its own navbar,
 * sections, and footer. Bypasses the global TrustVoice layout.
 */
export default function ProjectLanding() {
  const { slug } = useParams();
  const config = getProject(slug);

  if (!config) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="font-display text-4xl font-bold text-gray-900 mb-4">Project Not Found</h1>
          <p className="text-gray-500 mb-8">
            No project matches <span className="font-mono text-gray-700">/{slug}</span>.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition"
          >
            Back to TrustVoice
          </Link>
        </div>
      </div>
    );
  }

  return (
    <ThemeScope theme={config.theme}>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <ProjectNavbar config={config} />

        <main className="flex-1">
          {config.sections.map((key) => {
            const Section = SECTION_MAP[key];
            if (!Section) return null;
            return <Section key={key} config={config} />;
          })}
        </main>

        <ProjectFooter config={config} />
      </div>
    </ThemeScope>
  );
}
