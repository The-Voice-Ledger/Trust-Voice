/**
 * SkeletonCard — shimmer placeholder while campaigns load.
 */
export default function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
      <div className="h-36 animate-shimmer rounded-none" />
      <div className="p-4 space-y-3">
        <div className="h-4 animate-shimmer rounded-full w-3/4" />
        <div className="h-4 animate-shimmer rounded-full w-1/2" />
        <div className="h-2 animate-shimmer rounded-full" />
        <div className="flex justify-between">
          <div className="h-3 animate-shimmer rounded-full w-16" />
          <div className="h-3 animate-shimmer rounded-full w-24" />
        </div>
      </div>
    </div>
  );
}
