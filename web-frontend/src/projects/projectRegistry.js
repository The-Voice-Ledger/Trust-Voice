/**
 * Project Registry -- config-driven project landing pages.
 *
 * Each entry defines a complete micro-site that reuses TrustVoice's
 * shared components, donation flow, and backend.  To add a new project,
 * simply add an object to PROJECTS and it will be routable at
 * /project/:slug.
 */

const PROJECTS = {
  /* -----------------------------------------------
   *  UKULIMA: MORINGA OASIS ZIMBABWE (flagship)
   * ----------------------------------------------- */
  ukulima: {
    slug: 'ukulima',
    name: 'Ukulima',
    tagline: 'Moringa Oasis Zimbabwe',
    poweredBy: 'TrustVoice',

    /* -- Theme -- */
    theme: {
      primary: '#059669',     // emerald-600
      secondary: '#D97706',   // amber-600
      accent: '#065F46',      // emerald-800
      heroBg: 'from-emerald-950 via-green-950 to-stone-950',
      heroText: 'from-white via-emerald-200 to-amber-200',
      pattern: 'topography',
    },

    /* -- Navigation -- */
    nav: {
      logo: 'Ukulima',
      links: [
        { label: 'Vision', href: '#vision' },
        { label: 'Our Story', href: '#narrative' },
        { label: 'Market', href: '#market' },
        { label: 'Experience', href: '#experience' },
        { label: 'Financials', href: '#financials' },
      ],
      ctaLabel: 'Back This Project',
      ctaLink: '/donate',
    },

    /* -- Hero -- */
    hero: {
      badge: 'Impact Investment  ·  Agritourism  ·  Superfood',
      overtitle: 'Moringa Oasis Zimbabwe',
      title: 'Where Ancient Wisdom\nMeets the Future of Food',
      subtitle:
        'A 10-hectare vertically integrated sanctuary combining high-density Moringa production, an industrial processing facility, and a premium eco-lodge. Real agriculture. Real impact. Real returns.',
      stats: [
        { value: '$400K', label: 'Seed Round' },
        { value: '10 ha', label: 'Integrated Facility' },
        { value: '8x', label: 'Annual Harvests' },
      ],
      ctaLabel: 'Back This Project',
      ctaLink: '/donate',
      secondaryLabel: 'Talk to the AI Assistant',
      secondaryLink: '/assistant',
    },

    /* -- Vision (The Core Vision) -- */
    vision: {
      sectionLabel: 'The Core Vision',
      heading: 'Seed to Supplement. Farm to Future.',
      items: [
        {
          label: 'The Concept',
          icon: 'leaf',
          bespoke: 'leaf',
          text: 'A 10-hectare vertically integrated facility combining high-density Moringa production, industrial-grade processing, and a premium "Live-Work-Learn" eco-lodge.',
        },
        {
          label: 'The Mission',
          icon: 'globe',
          bespoke: 'globe',
          text: 'To capture the full Moringa value chain, from seed to supplement, while monetizing global "Impact Tourism" demand.',
        },
        {
          label: 'The Investment',
          icon: 'money',
          bespoke: 'money',
          text: '$400,000 Seed Round for land preparation, industrial processing machinery, and luxury solar-powered hospitality infrastructure.',
        },
      ],
    },

    /* -- Narrative (The Spirit of the Oasis) -- */
    narrative: {
      sectionLabel: 'The Spirit of the Oasis',
      heading: 'A Story of Adventure,\nAncient Wisdom, and Legacy',
      blocks: [
        {
          title: 'The Ancient Pulse of the Land',
          icon: 'leaf',
          bespoke: 'leaf',
          text: 'Before the first maps were drawn of the Southern African interior, the Moringa Oleifera stood as a silent sentinel of health. Known to the ancients as the "Miracle Tree," it is a biological marvel, a plant that breathes life back into the soil and the body. At Ukulima, we are not just farming; we are reviving a piece of ancient wisdom and grounding it in 21st-century innovation.',
        },
        {
          title: 'The Adventure of the "Green Gold" Frontier',
          icon: 'mountain',
          bespoke: 'mountain',
          text: 'For the seeker, the adventurer, and the one who finds peace at the end of a dusty trail, this is the ultimate destination. The journey to the Moringa Oasis is a physical rush, navigating the untamed, vibrant dirt trails of Zimbabwe to find a sanctuary that is entirely off-grid and powered by the sun. This is where the thrill of the "untamed" meets the precision of high-tech agriculture.',
        },
        {
          title: 'A Legacy You Can Touch',
          icon: 'cottage',
          bespoke: 'cottage',
          text: 'This is not a "paper" investment. It is a tangible oasis. It is 10 hectares of precision-irrigated life. It is 6 luxury eco-lodge cottages, hand-built from local stone and sustainable timber, offering a real-world asset that generates both revenue and impact. It is the smell of fresh earth during a dawn harvest and the gold of cold-pressed oil. This is real estate with a heartbeat.',
        },
        {
          title: 'Join the "Live-Work-Learn" Movement',
          icon: 'users',
          bespoke: 'users',
          text: 'We invite you to do more than just invest; we invite you to contribute. From dawn harvests in the African bush to formulating your own custom tea blends, you step directly into our ecosystem. Witness the 800% margin increase of our on-site value-add facility first-hand. You are a partner in breaking the "commodity trap" and building a sustainable future for African agriculture.',
        },
      ],
    },

    /* -- Market (The "Green Gold" Economy) -- */
    market: {
      sectionLabel: 'Market Dynamics',
      heading: 'The "Green Gold" Economy',
      tam: {
        value: '$10.78B',
        label: 'Total Addressable Market',
        detail: 'Global Moringa market by 2026 (9.7% CAGR)',
        icon: 'trending',
        bespoke: 'trending',
      },
      sam: {
        value: '$1.2B',
        label: 'Serviceable Market',
        detail: 'EU/UK/UAE nutraceutical and organic skincare corridors',
        icon: 'chart',
        bespoke: 'chart',
      },
      revenue: {
        value: '$3.1M',
        label: 'Obtainable Revenue',
        detail: 'Targeted annual revenue by Year 4 from the pilot facility',
        icon: 'money',
        bespoke: 'money',
      },
    },

    /* -- Revenue Pillars (Three-Pronged Resilience) -- */
    pillars: {
      sectionLabel: 'Revenue Pillars',
      heading: 'Three-Pronged Resilience',
      subtitle: 'A diversified revenue engine that insulates the project from single-point-of-failure risk.',
      items: [
        {
          title: 'Industrial B2B',
          description: 'Bulk export of organic-certified powder and oil to European wellness brands.',
          icon: 'building',
          bespoke: 'building',
          highlight: 'Bulk Export Pipeline',
        },
        {
          title: 'Premium B2C',
          description: 'Direct-to-consumer sales via on-site retail and global e-commerce.',
          icon: 'creditcard',
          bespoke: 'creditcard',
          highlight: 'Direct Sales Channel',
        },
        {
          title: 'Experiential Hospitality',
          description: '"Work-Stay-Learn" packages at $150/night for high-net-worth wellness travelers and adventurers.',
          icon: 'cottage',
          bespoke: 'cottage',
          highlight: '$150/Night Packages',
        },
      ],
    },

    /* -- Strategic Advantages -- */
    advantages: {
      sectionLabel: 'Why Ukulima',
      heading: 'Strategic Advantages',
      items: [
        {
          title: 'Value Addition',
          text: 'On-site milling, cold-pressing, and packaging increases margins by 800% compared to raw leaf export.',
          metric: '800%',
          metricLabel: 'Margin Increase',
          icon: 'chart',
          bespoke: 'chart',
        },
        {
          title: 'Ideal Climate',
          text: 'Zimbabwe offers year-round growing conditions for Moringa with up to 8 harvests annually.',
          metric: '8x',
          metricLabel: 'Harvests Per Year',
          icon: 'sun',
          bespoke: 'sun',
        },
        {
          title: 'Off-Grid Sustainability',
          text: '100% solar-powered operation; no chemical pesticides; trees sequestering approximately 200 tonnes of CO2 annually.',
          metric: '200t',
          metricLabel: 'CO2 Sequestered / yr',
          icon: 'globe',
          bespoke: 'globe',
        },
        {
          title: 'First-Mover Edge',
          text: 'Dominating the "Agritourism + Superfood" niche in Southern Africa.',
          metric: '#1',
          metricLabel: 'In Category',
          icon: 'rocket',
          bespoke: 'rocket',
        },
      ],
    },

    /* -- Experience Timeline (Live-Work-Learn) -- */
    experience: {
      sectionLabel: 'The Guest Experience',
      heading: 'Live. Work. Learn.',
      subtitle: 'A three-day immersion into the heart of the Moringa Oasis, designed for wellness travelers, impact investors, and curious adventurers.',
      days: [
        {
          day: 'Day 1',
          title: 'Connection',
          description: 'Welcome tea ceremony and food-forest tours. Your first breath of the Oasis air sets the tone: earthy, warm, alive.',
          icon: 'leaf',
          bespoke: 'leaf',
        },
        {
          day: 'Day 2',
          title: 'Contribution',
          description: 'Dawn harvest and cold-press oil extraction workshops. Get your hands in the soil and witness the 800% value-add transformation firsthand.',
          icon: 'sun',
          bespoke: 'sun',
        },
        {
          day: 'Day 3',
          title: 'Creation',
          description: 'Product formulation (custom blends) and business scaling seminars. Leave with your own branded product and the knowledge to build with purpose.',
          icon: 'sparkles',
          bespoke: 'sparkles',
        },
      ],
    },

    /* -- Financials -- */
    financials: {
      sectionLabel: 'Investment',
      heading: 'Investment & Projections',
      totalRaise: '$400,000',
      totalRaiseLabel: 'Seed Round',
      capex: [
        { item: 'Agri-Infrastructure', amount: '$110K', detail: 'Solar drip irrigation, borehole, and high-yield seeds' },
        { item: 'Processing Plant', amount: '$50K', detail: 'Industrial dehydrators, pulverizers, and cold-press oil expellers' },
        { item: 'Eco-Lodging', amount: '$180K', detail: '6 luxury solar-powered cottages ($30K each) using sustainable local materials' },
        { item: 'Operations & Certification', amount: '$60K', detail: 'EU/UK Organic certification and global marketing' },
      ],
      projections: [
        { year: 'Year 1', label: 'Setup', revenue: '$180K', ebitda: null },
        { year: 'Year 2', label: 'Growth', revenue: '$1.25M', ebitda: '$570K' },
        { year: 'Year 3', label: 'Maturity', revenue: '$3.1M', ebitda: '$2.18M' },
      ],
    },

    /* -- CTA -- */
    cta: {
      heading: 'Be Part of the Oasis',
      subheading: 'Backed by blockchain-verified transparency. Every dollar tracked, every impact measured. Join us in building something real.',
      primaryLabel: 'Invest Now',
      primaryLink: '/donate',
      secondaryLabel: 'Talk to the AI Assistant',
      secondaryLink: '/assistant',
    },

    /* -- Footer -- */
    footer: {
      description: 'A 10-hectare vertically integrated Moringa farm, processing facility, and eco-lodge in Zimbabwe. Reviving ancient wisdom through modern innovation.',
      columns: [
        {
          title: 'Explore',
          links: [
            { label: 'Our Vision', href: '#vision' },
            { label: 'The Story', href: '#narrative' },
            { label: 'Market', href: '#market' },
            { label: 'Experience', href: '#experience' },
          ],
        },
        {
          title: 'Invest',
          links: [
            { label: 'Back This Project', href: '/donate' },
            { label: 'Revenue Model', href: '#pillars' },
            { label: 'Financials', href: '#financials' },
            { label: 'Advantages', href: '#advantages' },
          ],
        },
        {
          title: 'Connect',
          links: [
            { label: 'AI Assistant', href: '/assistant' },
            { label: 'TrustVoice Platform', href: '/' },
          ],
        },
      ],
      legal: 'This is an informational overview and does not constitute a formal investment offering or financial advice.',
    },

    /* -- Sections to render (order matters) -- */
    sections: ['hero', 'vision', 'narrative', 'market', 'pillars', 'advantages', 'experience', 'financials', 'cta'],
  },
};

/* -- Public API -- */
export function getProject(slug) {
  return PROJECTS[slug] || null;
}

export function getAllProjectSlugs() {
  return Object.keys(PROJECTS);
}

export default PROJECTS;
