/**
 * Online Status Hook
 *
 * Detects when user goes offline/online and shows notifications.
 * Helps users understand if errors are due to network issues.
 *
 * Usage:
 *   const isOnline = useOnlineStatus()
 *
 *   if (!isOnline) {
 *     return <OfflineMessage />
 *   }
 */

import { useEffect, useState } from 'react'
import { toast } from '../components/Toast'

export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    // Handler for going online
    const handleOnline = () => {
      setIsOnline(true)
      toast.success('Back online! Connection restored.')
    }

    // Handler for going offline
    const handleOffline = () => {
      setIsOnline(false)
      toast.error('You are offline. Check your internet connection.', 0) // 0 = don't auto-dismiss
    }

    // Listen for online/offline events
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}

export default useOnlineStatus
