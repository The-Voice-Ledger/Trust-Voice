/**
 * ProgressBar — animated fundraising progress bar with optional label.
 */
export default function ProgressBar({ percentage = 0, showLabel = false, className = '' }) {
  const clamped = Math.min(100, Math.max(0, percentage));
  return (
    <div className={className}>
      {showLabel && (
        <div className="flex justify-end mb-1">
          <span className="text-xs font-bold text-blue-600">{Math.round(clamped)}%</span>
        </div>
      )}
      <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-blue-500 to-teal-500 transition-all duration-700 ease-out"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
