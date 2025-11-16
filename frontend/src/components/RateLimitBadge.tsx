/**
 * Rate Limit Badge
 *
 * Shows remaining API requests in the header.
 * Warns users when they're running low on requests.
 *
 * Usage:
 *   <RateLimitBadge />  // In header
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Zap, ZapOff } from 'lucide-react'
import { getRateLimitStatus } from '../lib/api'

export default function RateLimitBadge() {
  const [remaining, setRemaining] = useState<number | null>(null)
  const [resetAt, setResetAt] = useState<Date | null>(null)

  // Update rate limit status every second
  useEffect(() => {
    updateStatus()
    const interval = setInterval(updateStatus, 1000)
    return () => clearInterval(interval)
  }, [])

  const updateStatus = () => {
    const status = getRateLimitStatus()
    setRemaining(status.remaining)
    setResetAt(status.resetAt)
  }

  // Don't show if no rate limit data
  if (remaining === null) {
    return null
  }

  // Calculate percentage for color coding
  const percentage = (remaining / 100) * 100 // Assuming 100 req/min for starter plan

  // Color based on remaining requests
  const getColor = () => {
    if (remaining < 10) return 'text-red-400 bg-red-500/20'
    if (remaining < 30) return 'text-yellow-400 bg-yellow-500/20'
    return 'text-green-400 bg-green-500/20'
  }

  // Format time until reset
  const getTimeUntilReset = () => {
    if (!resetAt) return ''

    const now = new Date()
    const diff = resetAt.getTime() - now.getTime()

    if (diff <= 0) return 'Resetting...'

    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60

    if (minutes > 0) {
      return `${minutes}m ${secs}s`
    }
    return `${secs}s`
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getColor()}`}
    >
      {remaining < 10 ? (
        <ZapOff className="w-4 h-4" />
      ) : (
        <Zap className="w-4 h-4" />
      )}

      <div className="flex flex-col">
        <span className="text-xs font-medium">
          {remaining} requests left
        </span>
        {resetAt && (
          <span className="text-xs opacity-70">
            Resets in {getTimeUntilReset()}
          </span>
        )}
      </div>
    </motion.div>
  )
}
