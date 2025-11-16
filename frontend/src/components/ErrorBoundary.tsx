/**
 * Error Boundary Component
 *
 * Catches React errors anywhere in the component tree and displays a fallback UI.
 * Prevents the entire app from crashing when a component throws an error.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <YourComponent />
 *   </ErrorBoundary>
 *
 * If YourComponent throws an error, it shows a nice error message instead of a blank screen.
 */

import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { motion } from 'framer-motion'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  // Called when a child component throws an error
  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  // Log error details for debugging
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by ErrorBoundary:', error, errorInfo)

    this.setState({
      error,
      errorInfo,
    })

    // In production, you'd send this to an error tracking service like Sentry
    // Example: Sentry.captureException(error, { extra: errorInfo })
  }

  // Reset error state and try again
  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI provided by parent
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default fallback UI
      return (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-gray-900 to-black flex items-center justify-center p-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-8 max-w-2xl w-full"
          >
            {/* Error Icon */}
            <div className="flex items-center justify-center mb-6">
              <div className="bg-red-500/20 p-4 rounded-full">
                <AlertTriangle className="w-12 h-12 text-red-400" />
              </div>
            </div>

            {/* Error Message */}
            <h1 className="text-3xl font-bold text-center mb-4">
              Oops! Something went wrong
            </h1>

            <p className="text-gray-400 text-center mb-6">
              We encountered an unexpected error. Don't worry, our team has been notified.
            </p>

            {/* Error Details (only in development) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-black/50 rounded-lg p-4 mb-6 overflow-auto max-h-64">
                <p className="text-red-400 font-mono text-sm mb-2">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <pre className="text-gray-500 text-xs">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-4 justify-center">
              <button
                onClick={this.handleReset}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>

              <button
                onClick={() => window.location.href = '/'}
                className="px-6 py-3 bg-white/10 rounded-lg font-medium hover:bg-white/20 transition-all"
              >
                Go to Dashboard
              </button>
            </div>

            {/* Help Text */}
            <p className="text-center text-sm text-gray-500 mt-6">
              If this problem persists, please contact support or{' '}
              <a
                href="https://github.com/Timiochukwu/sentinel/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-400 hover:text-purple-300 underline"
              >
                report an issue on GitHub
              </a>
            </p>
          </motion.div>
        </div>
      )
    }

    // No error, render children normally
    return this.props.children
  }
}

export default ErrorBoundary
