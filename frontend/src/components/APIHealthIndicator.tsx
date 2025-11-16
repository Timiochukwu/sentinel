/**
 * API Health Indicator
 *
 * Shows real-time status of the backend API in the header.
 * Helps users know if issues are on their end or the server's end.
 *
 * Status colors:
 * - Green: API healthy and responsive
 * - Yellow: API slow (>500ms response)
 * - Red: API unreachable or error
 *
 * Usage:
 *   <APIHealthIndicator />  // In header/nav
 */

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, AlertCircle, CheckCircle2, Clock } from 'lucide-react'
import { checkAPIHealth } from '../lib/api'

type HealthStatus = 'healthy' | 'slow' | 'error' | 'checking'

export default function APIHealthIndicator() {
  const [status, setStatus] = useState<HealthStatus>('checking')
  const [latency, setLatency] = useState<number | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [lastCheck, setLastCheck] = useState<Date>(new Date())

  // Check API health on mount and every 30 seconds
  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const checkHealth = async () => {
    setStatus('checking')

    try {
      const result = await checkAPIHealth()
      setLastCheck(new Date())

      if (result.healthy) {
        setLatency(result.latency || null)

        // Healthy if < 500ms, slow if >= 500ms
        if (result.latency && result.latency >= 500) {
          setStatus('slow')
        } else {
          setStatus('healthy')
        }
      } else {
        setStatus('error')
        setLatency(null)
      }
    } catch (error) {
      setStatus('error')
      setLatency(null)
    }
  }

  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          color: 'bg-green-500',
          icon: CheckCircle2,
          text: 'API Healthy',
          textColor: 'text-green-400',
        }
      case 'slow':
        return {
          color: 'bg-yellow-500',
          icon: Clock,
          text: 'API Slow',
          textColor: 'text-yellow-400',
        }
      case 'error':
        return {
          color: 'bg-red-500',
          icon: AlertCircle,
          text: 'API Error',
          textColor: 'text-red-400',
        }
      case 'checking':
        return {
          color: 'bg-gray-500',
          icon: Activity,
          text: 'Checking...',
          textColor: 'text-gray-400',
        }
    }
  }

  const config = getStatusConfig()
  const StatusIcon = config.icon

  return (
    <div className="relative">
      {/* Status indicator button */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-all"
      >
        {/* Pulsing dot */}
        <div className="relative">
          <div className={`w-2 h-2 rounded-full ${config.color}`} />
          {status === 'healthy' && (
            <motion.div
              className={`absolute inset-0 rounded-full ${config.color}`}
              animate={{ scale: [1, 2, 1], opacity: [1, 0, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          )}
        </div>

        {/* Latency (optional) */}
        {latency !== null && (
          <span className="text-xs text-gray-400 hidden sm:inline">
            {latency}ms
          </span>
        )}
      </button>

      {/* Details popup */}
      <AnimatePresence>
        {showDetails && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowDetails(false)}
            />

            {/* Popup */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-2 w-64 glass rounded-lg p-4 z-50 shadow-xl border border-white/10"
            >
              {/* Header */}
              <div className="flex items-center gap-2 mb-3">
                <StatusIcon className={`w-5 h-5 ${config.textColor}`} />
                <h4 className="font-medium">{config.text}</h4>
              </div>

              {/* Details */}
              <div className="space-y-2 text-sm">
                {latency !== null && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Response Time:</span>
                    <span className="font-medium">{latency}ms</span>
                  </div>
                )}

                <div className="flex justify-between">
                  <span className="text-gray-400">Last Check:</span>
                  <span className="font-medium">
                    {lastCheck.toLocaleTimeString()}
                  </span>
                </div>

                {status === 'error' && (
                  <div className="mt-3 p-2 bg-red-500/20 border border-red-500/50 rounded text-xs text-red-400">
                    Unable to reach API. Check your connection or backend server.
                  </div>
                )}

                {status === 'slow' && (
                  <div className="mt-3 p-2 bg-yellow-500/20 border border-yellow-500/50 rounded text-xs text-yellow-400">
                    API is responding slowly. Performance may be degraded.
                  </div>
                )}
              </div>

              {/* Refresh button */}
              <button
                onClick={() => {
                  checkHealth()
                  setShowDetails(false)
                }}
                className="w-full mt-3 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm transition-all"
              >
                Check Now
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
