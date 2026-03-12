/**
 * Project Registry -- config-driven project landing pages.
 *
 * Each entry defines a complete micro-site that reuses TrustVoice's
 * shared components, funding flow, and backend.  To add a new project,
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
        { label: 'The Opportunity', href: '#market' },
        { label: 'Experience', href: '#experience' },
        { label: 'The Plan', href: '#financials' },
      ],
      ctaLabel: 'Build the Farm',
      ctaLink: '/fund',
    },

    /* -- Hero -- */
    hero: {
      badge: 'Community Farm  ·  Agritourism  ·  Superfood',
      overtitle: 'Moringa Oasis Zimbabwe',
      title: 'Where Ancient Wisdom\nMeets the Future of Food',
      subtitle:
        'A 10-hectare sanctuary combining Moringa production, on-site processing, and eco-lodging. Help us build it, come live and learn on it, and watch the farm grow itself. Real agriculture. Real impact. Real community.',
      stats: [],
      ctaLabel: 'Build the Farm',
      ctaLink: '/fund',
      secondaryLabel: 'Talk to the AI Assistant',
      secondaryLink: '/assistant',
    },

    /* -- Video Showcase (right after hero) -- */
    videoShowcase: {
      sectionLabel: 'See the Oasis',
      heading: 'Step Inside the Farm',
      url: 'https://violet-rainy-toad-577.mypinata.cloud/ipfs/bafybeif4fgejblthfvw3lyc677ncy5nlcex4xwgo3evb7yrwnoynzfczla',
      playLabel: 'Watch the full tour',
      caption: 'A 3-minute walk through the Moringa Oasis. The land, the trees, and the vision taking root.',
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
          text: 'A 10-hectare sanctuary combining high-density Moringa production, on-site processing, and a "Live-Work-Learn" eco-lodge where contributors become community.',
        },
        {
          label: 'The Mission',
          icon: 'globe',
          bespoke: 'globe',
          text: 'Build a self-sustaining ecosystem where Moringa sales fund growth, the farm feeds itself, and every contributor can come live, learn, and work on the land.',
        },
        {
          label: 'The Opportunity',
          icon: 'heart',
          bespoke: 'heart',
          text: 'Help us raise $400,000 to build the farm, the processing facility, and the eco-lodge. In return, come be part of it. Stay, harvest, create, and grow with us.',
        },
      ],
    },

    /* -- Narrative (The Spirit of the Oasis) -- */
    narrative: {
      sectionLabel: 'The Spirit of the Oasis',
      heading: 'A Story of Adventure,\nAncient Wisdom, and Community',
      blocks: [
        {
          title: 'The Ancient Pulse of the Land',
          icon: 'leaf',
          bespoke: 'leaf',
          video: 'https://violet-rainy-toad-577.mypinata.cloud/ipfs/bafybeidz6ruy6664r4g2merc4wa4dsise6or772fwvyzh2ihezpah2nora',
          text: 'Before the first maps were drawn of the Southern African interior, the Moringa Oleifera stood as a silent sentinel of health. Known to the ancients as the "Miracle Tree," it is a biological marvel, a plant that breathes life back into the soil and the body. At Ukulima, we are not just farming; we are reviving a piece of ancient wisdom and grounding it in 21st-century innovation.',
        },
        {
          title: 'The Adventure of the "Green Gold" Frontier',
          icon: 'mountain',
          bespoke: 'mountain',
          video: 'https://violet-rainy-toad-577.mypinata.cloud/ipfs/bafybeigvetbiczwjfiaxyo3ym5ctcwlnb4lklgkdecnbddwoqj6yrpgejm',
          text: 'For the seeker, the adventurer, and the one who finds peace at the end of a dusty trail, this is the ultimate destination. The journey to the Moringa Oasis is a physical rush, navigating the untamed, vibrant dirt trails of Zimbabwe to find a sanctuary that is entirely off-grid and powered by the sun. This is where the thrill of the "untamed" meets the precision of high-tech agriculture.',
        },
        {
          title: 'A Place You Can Touch',
          icon: 'cottage',
          bespoke: 'cottage',
          video: 'https://violet-rainy-toad-577.mypinata.cloud/ipfs/bafybeigigk3grv3dujef6jootye6vctt3scdpdrrg7agufzbrh64lukgqm',
          text: 'This is not a spectator project. It is a living, breathing oasis: 10 hectares of precision-irrigated life, 6 eco-lodge cottages hand-built from local stone and sustainable timber, and a community you help create. It is the smell of fresh earth during a dawn harvest and the gold of cold-pressed oil. A place with a heartbeat that you helped bring to life.',
        },
        {
          title: 'Join the "Live-Work-Learn" Community',
          icon: 'users',
          bespoke: 'users',
          video: 'https://violet-rainy-toad-577.mypinata.cloud/ipfs/bafybeicefidoqs2ipsbvdi6fqcyfqwavgt2xo2324vyml4m6omaejrwanu',
          text: 'We invite you to do more than fund. We invite you to come and be part of it. From dawn harvests in the African bush to formulating your own custom tea blends, you step directly into the ecosystem. The moringa we grow and sell funds the next phase. Every contributor is welcome to come stay, work alongside us, and learn the craft, building a sustainable future for African agriculture, together.',
        },
      ],
    },

    /* -- Market (Why the Farm Sustains Itself) -- */
    market: {
      sectionLabel: 'The Opportunity',
      heading: 'Why the Farm Grows Itself',
      tam: {
        value: '$10.78B',
        label: 'Global Demand',
        detail: 'The global Moringa market is booming at 9.7% annual growth. There is no shortage of buyers.',
        icon: 'trending',
        bespoke: 'trending',
      },
      sam: {
        value: '$1.2B',
        label: 'Our Corridors',
        detail: 'EU, UK, and UAE nutraceutical and organic skincare markets hungry for certified African-origin Moringa.',
        icon: 'chart',
        bespoke: 'chart',
      },
      revenue: {
        value: '$3.1M',
        label: 'Farm Revenue by Year 4',
        detail: 'Projected annual sales that fund operations, expansion, and community growth. No further fundraising needed.',
        icon: 'money',
        bespoke: 'money',
      },
    },

    /* -- Revenue Pillars (How the Farm Grows Itself) -- */
    pillars: {
      sectionLabel: 'How It Works',
      heading: 'How the Farm Grows Itself',
      subtitle: 'Three income streams that keep the oasis self-sustaining. Every sale funds the next phase of growth.',
      items: [
        {
          title: 'Moringa Sales (B2B)',
          description: 'Organic-certified powder and oil exported to European wellness brands. This is the engine that funds everything.',
          icon: 'building',
          bespoke: 'building',
          highlight: 'Funds Operations & Growth',
        },
        {
          title: 'Moringa Sales (Direct)',
          description: 'Premium products sold on-site and via e-commerce. Higher margins go straight back into the farm.',
          icon: 'creditcard',
          bespoke: 'creditcard',
          highlight: 'Funds Expansion',
        },
        {
          title: 'Live-Work-Learn Stays',
          description: 'Contributors and travelers stay at the eco-lodge, join harvests, learn the craft. Stays fund the community experience.',
          icon: 'cottage',
          bespoke: 'cottage',
          highlight: 'Funds the Community',
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

    /* -- Video Showcase 2 (visitors at the farm) -- */
    videoShowcase2: {
      sectionLabel: 'Visitors on the Ground',
      heading: 'See Who\u2019s Already Walking the Land',
      url: 'https://violet-rainy-toad-577.mypinata.cloud/ipfs/bafybeibgz2tbx7ivgoqzxuum6mdekcl75zu7aha26shldv7ds7vzlbpujm',
      playLabel: 'Watch the visit',
      caption: 'Real people, real soil, real progress. Visitors experiencing the Moringa Oasis first-hand.',
    },

    /* -- Experience Timeline (Live-Work-Learn) -- */
    experience: {
      sectionLabel: 'The Experience',
      heading: 'Live. Work. Learn.',
      subtitle: 'A three-day immersion into the heart of the Moringa Oasis. This is what you get to be part of, open to every contributor, traveler, and curious soul.',
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

    /* -- Financials (Building the Oasis) -- */
    financials: {
      sectionLabel: 'The Plan',
      heading: 'Building the Oasis',
      totalRaise: '$400,000',
      totalRaiseLabel: 'Fundraising Goal',
      capex: [
        { item: 'Agri-Infrastructure', amount: '$110K', detail: 'Solar drip irrigation, borehole, and high-yield Moringa seedlings' },
        { item: 'Processing Facility', amount: '$50K', detail: 'Industrial dehydrators, pulverizers, and cold-press oil expellers. This is where the value gets created' },
        { item: 'Eco-Lodge', amount: '$180K', detail: '6 solar-powered cottages ($30K each) for contributors and travelers to live and learn on the farm' },
        { item: 'Operations & Certification', amount: '$60K', detail: 'EU/UK Organic certification and market access so the farm can sell globally from day one' },
      ],
      projections: [
        { year: 'Year 1', label: 'Building', revenue: '$180K', ebitda: null },
        { year: 'Year 2', label: 'Growing', revenue: '$1.25M', ebitda: null },
        { year: 'Year 3', label: 'Self-Sustaining', revenue: '$3.1M', ebitda: null },
      ],
    },

    /* -- CTA -- */
    cta: {
      heading: 'Pioneer the Oasis',
      subheading: 'Every contribution is tracked with immutable transparency. Fund the farm, come live and learn on it, and watch it grow itself.',
      primaryLabel: 'Build The Farm',
      primaryLink: '/fund',
      secondaryLabel: 'Talk to the AI Assistant',
      secondaryLink: '/assistant',
    },

    /* -- Footer -- */
    footer: {
      description: 'A 10-hectare Moringa farm, processing facility, and eco-lodge in Zimbabwe. Community-funded. Self-sustaining. Open to all who want to be part of it.',
      columns: [
        {
          title: 'Explore',
          links: [
            { label: 'Our Vision', href: '#vision' },
            { label: 'The Story', href: '#narrative' },
            { label: 'The Opportunity', href: '#market' },
            { label: 'Experience', href: '#experience' },
          ],
        },
        {
          title: 'Get Involved',
          links: [
            { label: 'Fund the Farm', href: '/fund' },
            { label: 'How It Works', href: '#pillars' },
            { label: 'The Plan', href: '#financials' },
            { label: 'Why Ukulima', href: '#advantages' },
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
      legal: 'This is an informational overview of the Ukulima project. All contributions are transparently tracked via the TrustVoice platform.',
    },

    /* -- Sections to render (order matters) -- */
    sections: ['hero', 'videoShowcase', 'vision', 'narrative', 'market', 'pipeline', 'pillars', 'advantages', 'videoShowcase2', 'experience', 'financials', 'cta'],
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
