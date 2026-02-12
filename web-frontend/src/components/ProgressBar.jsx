/**
 * ProgressBar — animated fundraising progress bar.
 */
export default function ProgressBar({ percentage = 0, className = '' }) {
  const clamped = Math.min(100, Math.max(0, percentage));
  return (
    <div className={`w-full bg-gray-100 rounded-full h-2 overflow-hidden ${className}`}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-700 ease-out"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
