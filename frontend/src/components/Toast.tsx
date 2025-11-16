/**
 * Toast Notification System
 *
 * Displays temporary notification messages to users.
 * Useful for success messages, errors, warnings, and info.
 *
 * Usage:
 *   import { toast } from './components/Toast'
 *
 *   toast.success('Transaction approved!')
 *   toast.error('Failed to load data')
 *   toast.warning('High risk detected')
 *   toast.info('Processing...')
 *
 * Features:
 * - Auto-dismisses after 5 seconds
 * - Manual dismiss with X button
 * - Animated entrance/exit
 * - Stacks multiple toasts
 * - Icons based on type
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { createRoot } from 'react-dom/client'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastMessage {
  id: string
  type: ToastType
  message: string
  duration?: number
}

// Global toast state
let toastContainer: HTMLDivElement | null = null
let toastRoot: any = null
const toastMessages: ToastMessage[] = []
let updateToasts: ((messages: ToastMessage[]) => void) | null = null

// Get icon based on toast type
const getIcon = (type: ToastType) => {
  switch (type) {
    case 'success':
      return <CheckCircle2 className="w-5 h-5" />
    case 'error':
      return <XCircle className="w-5 h-5" />
    case 'warning':
      return <AlertTriangle className="w-5 h-5" />
    case 'info':
      return <Info className="w-5 h-5" />
  }
}

// Get colors based on toast type
const getColors = (type: ToastType) => {
  switch (type) {
    case 'success':
      return 'bg-green-500/20 border-green-500/50 text-green-400'
    case 'error':
      return 'bg-red-500/20 border-red-500/50 text-red-400'
    case 'warning':
      return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400'
    case 'info':
      return 'bg-blue-500/20 border-blue-500/50 text-blue-400'
  }
}

// Toast Component
function ToastContainer() {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  useEffect(() => {
    // Register update function
    updateToasts = setMessages
    return () => {
      updateToasts = null
    }
  }, [])

  const removeToast = (id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id))
  }

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 pointer-events-none">
      <AnimatePresence>
        {messages.map(msg => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="pointer-events-auto"
          >
            <div
              className={`
                flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-lg
                shadow-lg min-w-[320px] max-w-md
                ${getColors(msg.type)}
              `}
            >
              {/* Icon */}
              <div className="flex-shrink-0">
                {getIcon(msg.type)}
              </div>

              {/* Message */}
              <p className="flex-1 text-sm font-medium">
                {msg.message}
              </p>

              {/* Close Button */}
              <button
                onClick={() => removeToast(msg.id)}
                className="flex-shrink-0 hover:opacity-70 transition-opacity"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}

// Initialize toast container
function initToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div')
    toastContainer.id = 'toast-container'
    document.body.appendChild(toastContainer)
    toastRoot = createRoot(toastContainer)
    toastRoot.render(<ToastContainer />)
  }
}

// Add a toast message
function addToast(type: ToastType, message: string, duration = 5000) {
  initToastContainer()

  const id = `toast-${Date.now()}-${Math.random()}`
  const newToast: ToastMessage = { id, type, message, duration }

  toastMessages.push(newToast)
  updateToasts?.([ ...toastMessages])

  // Auto-remove after duration
  if (duration > 0) {
    setTimeout(() => {
      const index = toastMessages.findIndex(msg => msg.id === id)
      if (index > -1) {
        toastMessages.splice(index, 1)
        updateToasts?.([...toastMessages])
      }
    }, duration)
  }

  return id
}

// Public API
export const toast = {
  /**
   * Show success toast
   * @param message - Success message to display
   * @param duration - How long to show toast (ms), default 5000
   */
  success: (message: string, duration?: number) =>
    addToast('success', message, duration),

  /**
   * Show error toast
   * @param message - Error message to display
   * @param duration - How long to show toast (ms), default 5000
   */
  error: (message: string, duration?: number) =>
    addToast('error', message, duration),

  /**
   * Show warning toast
   * @param message - Warning message to display
   * @param duration - How long to show toast (ms), default 5000
   */
  warning: (message: string, duration?: number) =>
    addToast('warning', message, duration),

  /**
   * Show info toast
   * @param message - Info message to display
   * @param duration - How long to show toast (ms), default 5000
   */
  info: (message: string, duration?: number) =>
    addToast('info', message, duration),
}

export default toast
