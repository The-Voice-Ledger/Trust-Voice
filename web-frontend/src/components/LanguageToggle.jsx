import { useTranslation } from 'react-i18next';
import useVoiceStore from '../stores/voiceStore';

/**
 * LanguageToggle — switch between English and Amharic.
 */
export default function LanguageToggle({ className = '' }) {
  const { i18n } = useTranslation();
  const setLang = useVoiceStore((s) => s.setLanguage);

  const toggle = () => {
    const next = i18n.language === 'am' ? 'en' : 'am';
    i18n.changeLanguage(next);
    setLang(next);
  };

  return (
    <button
      onClick={toggle}
      className={`text-sm font-medium px-3 py-1.5 rounded-full border transition-colors
        ${i18n.language === 'am'
          ? 'bg-green-50 border-green-300 text-green-700'
          : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'}
        ${className}`}
      aria-label="Toggle language"
    >
      {i18n.language === 'am' ? '🇪🇹 አማ' : '🇬🇧 EN'}
    </button>
  );
}
