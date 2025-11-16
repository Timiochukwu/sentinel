/**
 * Loading Skeleton Components
 *
 * Shows placeholder content while data is loading.
 * Much better UX than spinners - gives users a sense of what's coming.
 *
 * Usage:
 *   {loading ? <StatCardSkeleton /> : <StatCard {...props} />}
 *   {loading ? <ChartSkeleton /> : <Chart {...props} />}
 */

// Base skeleton element with shimmer effect
function SkeletonElement({ className = '', style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div className={`bg-white/5 rounded animate-pulse ${className}`} style={style}>
      <div className="shimmer" />
    </div>
  )
}

// Skeleton for stat cards
export function StatCardSkeleton() {
  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <SkeletonElement className="h-4 w-24 mb-3" />
          <SkeletonElement className="h-8 w-32 mb-2" />
          <SkeletonElement className="h-3 w-20" />
        </div>
        <SkeletonElement className="h-12 w-12 rounded-lg" />
      </div>
    </div>
  )
}

// Skeleton for charts
export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="glass rounded-2xl p-6">
      <SkeletonElement className="h-6 w-48 mb-6" />
      <SkeletonElement className={`w-full`} style={{ height: `${height}px` }} />
    </div>
  )
}

// Skeleton for transaction table rows
export function TransactionRowSkeleton() {
  return (
    <div className="glass rounded-lg p-4 mb-3">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <SkeletonElement className="h-4 w-32 mb-2" />
          <SkeletonElement className="h-3 w-24" />
        </div>
        <div className="flex items-center gap-4">
          <SkeletonElement className="h-6 w-20 rounded-full" />
          <SkeletonElement className="h-8 w-24 rounded-lg" />
        </div>
      </div>
    </div>
  )
}

// Skeleton for dashboard grid
export function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* Header skeleton */}
      <div>
        <SkeletonElement className="h-10 w-64 mb-2" />
        <SkeletonElement className="h-5 w-96" />
      </div>

      {/* Stats grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>

      {/* Charts skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartSkeleton />
        <ChartSkeleton />
      </div>
    </div>
  )
}

// Skeleton for transaction list
export function TransactionListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {[...Array(count)].map((_, i) => (
        <TransactionRowSkeleton key={i} />
      ))}
    </div>
  )
}

// Add shimmer animation CSS to your global styles
// This should go in index.css:
/*
@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.shimmer {
  background: linear-gradient(
    to right,
    transparent 0%,
    rgba(255, 255, 255, 0.1) 50%,
    transparent 100%
  );
  background-size: 1000px 100%;
  animation: shimmer 2s infinite;
}
*/
