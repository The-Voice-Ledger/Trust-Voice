/**
 * Bespoke SVG icon library — geometric "tech" style.
 * 24×24 viewBox · 1.75 stroke · round caps/joins · angular forms.
 * Each icon is a named export accepting { className }.
 */

/* ── Base wrappers ─────────────────────── */
const O = ({ children, className = '', ...p }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" {...p}>
    {children}
  </svg>
);
const F = ({ children, className = '', ...p }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor" {...p}>
    {children}
  </svg>
);

/* ═══════════════════════════════════════════
   NAVIGATION & ARROWS
   ═════════════════════════════════════════ */

export function IconArrowLeft({ className }) {
  return <O className={className}><path d="M19 12H5M5 12l6-6M5 12l6 6" /></O>;
}
export function IconArrowRight({ className }) {
  return <O className={className}><path d="M5 12h14M19 12l-6-6M19 12l-6 6" /></O>;
}
export function IconArrowLeftOnRectangle({ className }) {
  return <O className={className}><path d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6A2.25 2.25 0 005.25 5.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M18 12H9m0 0l3-3m-3 3l3 3" /></O>;
}
export function IconArrowRightOnRectangle({ className }) {
  return <O className={className}><path d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6A2.25 2.25 0 005.25 5.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 12h9m0 0l-3-3m3 3l-3 3" /></O>;
}
export function IconArrowTrendingUp({ className }) {
  return <O className={className}><path d="M2.25 18L9 11.25l4 4L21.75 6M21.75 6h-6M21.75 6v6" /></O>;
}
export function IconArrowTrendingDown({ className }) {
  return <O className={className}><path d="M2.25 6L9 12.75l4-4L21.75 18M21.75 18h-6M21.75 18v-6" /></O>;
}
export function IconChevronDown({ className }) {
  return <O className={className}><path d="M6 9l6 6 6-6" /></O>;
}
export function IconBars3({ className }) {
  return <O className={className}><path d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" /></O>;
}
export function IconXMark({ className }) {
  return <O className={className}><path d="M6 18L18 6M6 6l12 12" /></O>;
}
export function IconEllipsisHorizontal({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="5" cy="12" r="1" fill="currentColor" stroke="none" /><circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" /></O>;
}

/* ═══════════════════════════════════════════
   ACTIONS
   ═════════════════════════════════════════ */

export function IconHeart({ className }) {
  return <O className={className}><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" /></O>;
}
export function IconPlusCircle({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="9" /><path d="M12 8v8M8 12h8" /></O>;
}
export function IconCheck({ className }) {
  return <O className={className}><path d="M4.5 12.75l6 6 9-13.5" /></O>;
}
export function IconCheckCircle({ className }) {
  return <O className={className}><path d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></O>;
}
export function IconCheckBadge({ className }) {
  return <O className={className}><path d="M9 12.75L11.25 15 15 9.75" /><path d="M12 2l2.4 3.6H18l.6 3.6L22 12l-3.4 2.8-.6 3.6h-3.6L12 22l-2.4-3.6H6l-.6-3.6L2 12l3.4-2.8.6-3.6h3.6L12 2z" /></O>;
}
export function IconMagnifyingGlass({ className }) {
  return <O className={className}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /></O>;
}
export function IconPaperAirplane({ className }) {
  return <O className={className}><path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" fill="currentColor" stroke="none" /></O>;
}

/* ═══════════════════════════════════════════
   MEDIA & AUDIO
   ═════════════════════════════════════════ */

export function IconMicrophone({ className }) {
  return <O className={className}><path d="M12 2a3 3 0 00-3 3v5a3 3 0 006 0V5a3 3 0 00-3-3z" /><path d="M19 10v1a7 7 0 01-14 0v-1M12 18v4M8 22h8" /></O>;
}
export function IconCamera({ className }) {
  return <O className={className}><path d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" /><circle cx="12" cy="13.5" r="3.75" /></O>;
}
export function IconFilm({ className }) {
  return <O className={className}><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M2 8h20M2 16h20M6 4v4M6 16v4M18 4v4M18 16v4" /></O>;
}
export function IconPlayCircle({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="9.75" /><path d="M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z" fill="currentColor" stroke="none" /></O>;
}
export function IconVideoCameraSlash({ className }) {
  return <O className={className}><path d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M2.25 18.75h12A2.25 2.25 0 0016.5 16.5V7.5a2.25 2.25 0 00-2.25-2.25h-12" /><path d="M3.75 3.75l16.5 16.5" /></O>;
}
export function IconSpeakerWave({ className }) {
  return <O className={className}><path d="M11 5L6 9H2v6h4l5 4V5z" /><path d="M15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" /></O>;
}
export function IconSpeakerXMark({ className }) {
  return <O className={className}><path d="M11 5L6 9H2v6h4l5 4V5z" /><path d="M16 9l6 6M22 9l-6 6" /></O>;
}
export function IconEye({ className }) {
  return <O className={className}><path d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5s8.577 3.01 9.964 7.178c.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5s-8.577-3.01-9.964-7.178z" /><circle cx="12" cy="12" r="3" /></O>;
}

/* ═══════════════════════════════════════════
   COMMUNICATION & AI
   ═════════════════════════════════════════ */

export function IconChatBubbleLeftRight({ className }) {
  return <O className={className}><path d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" /></O>;
}
export function IconSparkles({ className }) {
  return <O className={className}><path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" /></O>;
}
export function IconQuestionMarkCircle({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="9" /><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01" /></O>;
}
export function IconInformationCircle({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="9" /><path d="M12 16v-4M12 8h.01" /></O>;
}

/* ═══════════════════════════════════════════
   DATA, CHARTS, STATUS
   ═════════════════════════════════════════ */

export function IconChartBar({ className }) {
  return <O className={className}><path d="M3 20h18M5 20V10M9 20V4M13 20v-8M17 20V7M21 20v-5" /></O>;
}
export function IconChartBarSquare({ className }) {
  return <O className={className}><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M7 17V13M12 17V8M17 17V11" /></O>;
}
export function IconRocketLaunch({ className }) {
  return <O className={className}><path d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.63 8.41m5.96 5.96a14.926 14.926 0 01-5.84 2.58m0 0a6 6 0 01-7.38-5.84h4.8" /><path d="M14.5 9.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" /><path d="M2.9 17.8a3 3 0 003.3 3.3" /></O>;
}
export function IconShieldCheck({ className }) {
  return <O className={className}><path d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></O>;
}
export function IconXCircle({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="9" /><path d="M15 9l-6 6M9 9l6 6" /></O>;
}

/* ═══════════════════════════════════════════
   OBJECTS & UI
   ═════════════════════════════════════════ */

export function IconGlobeAlt({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="9.75" /><path d="M3.6 9h16.8M3.6 15h16.8M11.683 2.26c-2.45 3.1-3.87 7-3.87 9.74s1.42 6.64 3.87 9.74M12.317 2.26c2.45 3.1 3.87 7 3.87 9.74s-1.42 6.64-3.87 9.74" /></O>;
}
export function IconBuildingOffice2({ className }) {
  return <O className={className}><path d="M3 21h18M3 21V6l7-3v18M10 21V3l11 4.5V21M7 9h.01M7 12h.01M7 15h.01M14 9h.01M14 12h.01M14 15h.01M17 9h.01M17 12h.01M17 15h.01" /></O>;
}
export function IconCog6Tooth({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="3" /><path d="M10.325 4.317c.42-1.756 2.93-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.42 1.756 2.93 0 3.35a1.723 1.723 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.42 1.756-2.93 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.42-1.756-2.93 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37 1.066.648 2.447-.118 2.573-1.066z" /></O>;
}
export function IconLockClosed({ className }) {
  return <O className={className}><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /><circle cx="12" cy="16" r="1" fill="currentColor" stroke="none" /></O>;
}
export function IconFingerPrint({ className }) {
  return <O className={className}><path d="M7.864 4.243A7.5 7.5 0 0119.5 10.5c0 2.92-.556 5.709-1.568 8.268M5.742 6.364A7.465 7.465 0 004.5 10.5a48.667 48.667 0 00-1.077 8.438M12 10.5a3 3 0 11-6 0 3 3 0 016 0zM12 10.5c0 4.024-.531 7.921-1.518 11.633M9 10.5a48.57 48.57 0 01-1.168 8.617" /></O>;
}
export function IconMapPin({ className }) {
  return <O className={className}><path d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" /><path d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" /></O>;
}
export function IconWallet({ className }) {
  return <O className={className}><path d="M21 12V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2h14a2 2 0 002-2v-3" /><path d="M16 12h5v4h-5a2 2 0 010-4z" /><circle cx="18" cy="14" r=".5" fill="currentColor" stroke="none" /></O>;
}
export function IconCreditCard({ className }) {
  return <O className={className}><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20M6 14h2M12 14h2" /></O>;
}
export function IconClock({ className }) {
  return <O className={className}><circle cx="12" cy="12" r="9" /><path d="M12 6v6l4 2" /></O>;
}
export function IconDocumentText({ className }) {
  return <O className={className}><path d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></O>;
}
export function IconUserGroup({ className }) {
  return <O className={className}><path d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" /></O>;
}
export function IconUser({ className }) {
  return <O className={className}><path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></O>;
}
export function IconBanknotes({ className }) {
  return <O className={className}><rect x="1" y="6" width="22" height="12" rx="2" /><circle cx="12" cy="12" r="3" /><path d="M5 12h.01M19 12h.01" /></O>;
}

/* ═══════════════════════════════════════════
   CATEGORY ICONS (filled geometric)
   ═════════════════════════════════════════ */

export function IconWaterDrop({ className }) {
  return <F className={className}><path d="M12 2.69l.94 1.11C14.76 6.1 18 10.2 18 13.5a6 6 0 01-12 0c0-3.3 3.24-7.4 5.06-9.7L12 2.69z" /></F>;
}
export function IconSchool({ className }) {
  return <F className={className}><path d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm0 12.55L5 12.45l7-3.82 7 3.82-7 3.1z" /></F>;
}
export function IconHospital({ className }) {
  return <F className={className}><path d="M19 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2V5a2 2 0 00-2-2zm-4 11h-2v2a1 1 0 01-2 0v-2H9a1 1 0 010-2h2v-2a1 1 0 012 0v2h2a1 1 0 010 2z" /></F>;
}
export function IconConstruction({ className }) {
  return <F className={className}><path d="M13.783 2.217a.75.75 0 00-1.06 0l-2.25 2.25a.75.75 0 000 1.06l.97.97-7.216 7.216-1.06-.97a.75.75 0 00-1.06 0l-1.5 1.5a.75.75 0 000 1.06l3.5 3.5a.75.75 0 001.06 0l1.5-1.5a.75.75 0 000-1.06l-.97-1.06 7.216-7.216.97.97a.75.75 0 001.06 0l2.25-2.25a.75.75 0 000-1.06l-3.41-3.41z" /></F>;
}
export function IconRestaurant({ className }) {
  return <F className={className}><path d="M7 2v9a3 3 0 003 3v8h2V2h-1v7a1 1 0 01-2 0V2H7zm10 0v7h-2V2h-2v9a4 4 0 003 3.87V22h2V2h-1z" /></F>;
}
export function IconForest({ className }) {
  return <F className={className}><path d="M12 2L6 10h3l-4 6h4l-3 4h12l-3-4h4l-4-6h3L12 2z" /><rect x="11" y="18" width="2" height="4" /></F>;
}
export function IconHouse({ className }) {
  return <F className={className}><path d="M12 2.1L1 12h3v9h6v-6h4v6h6v-9h3L12 2.1z" /></F>;
}
export function IconChildCare({ className }) {
  return <F className={className}><circle cx="12" cy="8" r="5" /><path d="M12 13c-4 0-8 2-8 5v2h16v-2c0-3-4-5-8-5z" /><circle cx="10" cy="7.5" r="1" fill="white" /><circle cx="14" cy="7.5" r="1" fill="white" /><path d="M10 10a2 2 0 004 0" stroke="white" strokeWidth="1" fill="none" /></F>;
}
export function IconHandshake({ className }) {
  return <F className={className}><path d="M11.5 3.5l-5 5L9 11l2-2 4 4 5-5-2.5-2.5-3 3-3-4.5zm-6 8l-3 3 2.5 2.5 3-3-2.5-2.5zm13 0l-2.5 2.5 3 3L21.5 14.5l-3-3z" /></F>;
}
export function IconAttachMoney({ className }) {
  return <F className={className}><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z" /></F>;
}
export function IconBookmarkAdded({ className }) {
  return <F className={className}><path d="M17 3H7a2 2 0 00-2 2v16l7-3 7 3V5a2 2 0 00-2-2zm-2 8l-3 3-1.5-1.5L9 14l3 3 4.5-4.5L15 11z" /></F>;
}
export function IconPushPin({ className }) {
  return <F className={className}><path d="M16 9V4h1a1 1 0 100-2H7a1 1 0 100 2h1v5a2 2 0 01-2 2v2h5.5v7l1 1 1-1v-7H19v-2a2 2 0 01-2-2z" /></F>;
}

/* ═══════════════════════════════════════════
   ALIASES (match old import names exactly)
   ═════════════════════════════════════════ */
export {
  IconArrowLeft as HiOutlineArrowLeft,
  IconArrowRight as HiOutlineArrowRight,
  IconArrowLeftOnRectangle as HiOutlineArrowLeftOnRectangle,
  IconArrowRightOnRectangle as HiOutlineArrowRightOnRectangle,
  IconArrowTrendingUp as HiOutlineArrowTrendingUp,
  IconArrowTrendingDown as HiOutlineArrowTrendingDown,
  IconChevronDown as HiOutlineChevronDown,
  IconBars3 as HiOutlineBars3,
  IconXMark as HiOutlineXMark,
  IconEllipsisHorizontal as HiOutlineEllipsisHorizontal,
  IconHeart as HiOutlineHeart,
  IconPlusCircle as HiOutlinePlusCircle,
  IconCheck as HiOutlineCheck,
  IconCheckCircle as HiOutlineCheckCircle,
  IconCheckBadge as HiOutlineCheckBadge,
  IconMagnifyingGlass as HiOutlineMagnifyingGlass,
  IconPaperAirplane as HiOutlinePaperAirplane,
  IconMicrophone as HiOutlineMicrophone,
  IconCamera as HiOutlineCamera,
  IconFilm as HiOutlineFilm,
  IconPlayCircle as HiOutlinePlayCircle,
  IconVideoCameraSlash as HiOutlineVideoCameraSlash,
  IconSpeakerWave as HiOutlineSpeakerWave,
  IconSpeakerXMark as HiOutlineSpeakerXMark,
  IconEye as HiOutlineEye,
  IconChatBubbleLeftRight as HiOutlineChatBubbleLeftRight,
  IconSparkles as HiOutlineSparkles,
  IconQuestionMarkCircle as HiOutlineQuestionMarkCircle,
  IconInformationCircle as HiOutlineInformationCircle,
  IconChartBar as HiOutlineChartBar,
  IconChartBarSquare as HiOutlineChartBarSquare,
  IconRocketLaunch as HiOutlineRocketLaunch,
  IconShieldCheck as HiOutlineShieldCheck,
  IconXCircle as HiOutlineXCircle,
  IconGlobeAlt as HiOutlineGlobeAlt,
  IconBuildingOffice2 as HiOutlineBuildingOffice2,
  IconCog6Tooth as HiOutlineCog6Tooth,
  IconLockClosed as HiOutlineLockClosed,
  IconFingerPrint as HiOutlineFingerPrint,
  IconMapPin as HiOutlineMapPin,
  IconWallet as HiOutlineWallet,
  IconCreditCard as HiOutlineCreditCard,
  IconClock as HiOutlineClock,
  IconDocumentText as HiOutlineDocumentText,
  IconUserGroup as HiOutlineUserGroup,
  IconUser as HiOutlineUser,
  IconBanknotes as HiOutlineBanknotes,
  IconWaterDrop as MdOutlineWaterDrop,
  IconSchool as MdOutlineSchool,
  IconHospital as MdOutlineLocalHospital,
  IconConstruction as MdOutlineConstruction,
  IconRestaurant as MdOutlineRestaurant,
  IconForest as MdOutlineForest,
  IconHouse as MdOutlineHouse,
  IconChildCare as MdOutlineChildCare,
  IconHandshake as MdHandshake,
  IconAttachMoney as MdOutlineAttachMoney,
  IconBookmarkAdded as MdOutlineBookmarkAdded,
  IconPushPin as MdOutlinePushPin,
};
