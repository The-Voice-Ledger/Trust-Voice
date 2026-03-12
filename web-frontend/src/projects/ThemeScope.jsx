/**
 * ThemeScope - injects project-level CSS custom properties so all
 * child components can pick up the project's brand palette.
 *
 * Usage:
 *   <ThemeScope theme={config.theme}>
 *     <ProjectHero ... />
 *   </ThemeScope>
 */
export default function ThemeScope({ theme, children }) {
  return (
    <div
      style={{
        '--project-primary': theme.primary,
        '--project-secondary': theme.secondary,
        '--project-accent': theme.accent,
      }}
    >
      {children}
    </div>
  );
}
