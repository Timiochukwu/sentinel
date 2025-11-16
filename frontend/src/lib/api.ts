/**
 * Enhanced API Client for Sentinel
 *
 * Features:
 * - Automatic retry logic for failed requests
 * - Better error handling with user-friendly messages
 * - Request/response interceptors
 * - API health checking
 * - Rate limit tracking
 * - Timeout handling
 *
 * Usage:
 *   import { fraudAPI } from './lib/api'
 *
 *   const stats = await fraudAPI.getStats()  // Automatically retries on failure
 */

import axios, { AxiosError } from 'axios'
import { toast } from '../components/Toast'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api/v1'
const API_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Delay function for retry logic
 */
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * Check if error is retryable
 * Retry on network errors and 5xx server errors, but not on 4xx client errors
 */
const isRetryableError = (error: AxiosError): boolean => {
  if (!error.response) {
    // Network error, DNS error, or request timeout
    return true
  }

  const status = error.response.status
  // Retry on 5xx server errors and 429 (rate limit)
  return status >= 500 || status === 429
}

/**
 * Get user-friendly error message
 */
const getErrorMessage = (error: AxiosError): string => {
  if (!error.response) {
    return 'Network error. Please check your internet connection.'
  }

  const status = error.response.status
  const data: any = error.response.data

  // Use server's error message if available
  if (data?.detail) {
    return data.detail
  }

  // Default messages based on status code
  switch (status) {
    case 400:
      return 'Invalid request. Please check your data.'
    case 401:
      return 'Unauthorized. Please log in again.'
    case 403:
      return 'Access forbidden. You don\'t have permission.'
    case 404:
      return 'Resource not found.'
    case 429:
      return 'Rate limit exceeded. Please slow down.'
    case 500:
      return 'Server error. Our team has been notified.'
    case 503:
      return 'Service temporarily unavailable. Please try again later.'
    default:
      return `Request failed with status ${status}`
  }
}

// REQUEST INTERCEPTOR
// Adds API key to all requests
api.interceptors.request.use(
  (config) => {
    // Get API key from localStorage or use demo key
    const apiKey = localStorage.getItem('apiKey') || 'demo_api_key'
    config.headers['X-API-Key'] = apiKey

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// RESPONSE INTERCEPTOR
// Handles rate limiting and errors
api.interceptors.response.use(
  (response) => {
    // Track rate limit headers
    const rateLimitRemaining = response.headers['x-ratelimit-remaining']
    const rateLimitReset = response.headers['x-ratelimit-reset']

    if (rateLimitRemaining !== undefined) {
      // Store rate limit info
      localStorage.setItem('rateLimitRemaining', rateLimitRemaining)
      localStorage.setItem('rateLimitReset', rateLimitReset)

      // Warn user if running low on requests
      if (parseInt(rateLimitRemaining) < 10) {
        toast.warning(`Only ${rateLimitRemaining} API requests remaining this minute`)
      }
    }

    return response
  },
  async (error: AxiosError) => {
    const config: any = error.config

    // Initialize retry count
    if (!config._retryCount) {
      config._retryCount = 0
    }

    // Check if we should retry
    if (config._retryCount < MAX_RETRIES && isRetryableError(error)) {
      config._retryCount++

      // Calculate delay with exponential backoff
      const retryDelay = RETRY_DELAY * Math.pow(2, config._retryCount - 1)

      console.log(`Retry attempt ${config._retryCount}/${MAX_RETRIES} after ${retryDelay}ms`)

      // Wait before retrying
      await delay(retryDelay)

      // Retry the request
      return api(config)
    }

    // Max retries exceeded or non-retryable error
    const userMessage = getErrorMessage(error)

    // Don't show toast for 401 errors (handled by auth system)
    if (error.response?.status !== 401) {
      toast.error(userMessage)
    }

    return Promise.reject(error)
  }
)

/**
 * API Health Check
 * Checks if the backend API is reachable
 */
export const checkAPIHealth = async (): Promise<{
  healthy: boolean
  message: string
  latency?: number
}> => {
  try {
    const startTime = Date.now()
    await api.get('/health')
    const latency = Date.now() - startTime

    return {
      healthy: true,
      message: 'API is healthy',
      latency,
    }
  } catch (error) {
    return {
      healthy: false,
      message: 'API is unreachable',
    }
  }
}

/**
 * Get current rate limit status
 */
export const getRateLimitStatus = () => {
  const remaining = localStorage.getItem('rateLimitRemaining')
  const reset = localStorage.getItem('rateLimitReset')

  return {
    remaining: remaining ? parseInt(remaining) : null,
    resetAt: reset ? new Date(parseInt(reset) * 1000) : null,
  }
}

// =============================================================================
// FRAUD DETECTION API METHODS
// =============================================================================

export const fraudAPI = {
  /**
   * Get dashboard statistics
   * Returns today's and this month's fraud detection metrics
   */
  async getStats() {
    const { data } = await api.get('/dashboard/stats')
    return data
  },

  /**
   * Get transaction list with optional filters
   * @param params - Filter parameters (risk_level, outcome, limit, offset)
   */
  async getTransactions(params?: {
    risk_level?: string
    outcome?: string
    limit?: number
    offset?: number
  }) {
    const { data } = await api.get('/dashboard/transactions', { params })
    return data
  },

  /**
   * Check a transaction for fraud
   * @param transaction - Transaction data to check
   * @returns Fraud detection result with risk score, flags, and recommendation
   */
  async checkTransaction(transaction: any) {
    try {
      const { data } = await api.post('/fraud-detection/check-transaction', transaction)

      // Show success toast with risk level
      const riskLevel = data.risk_level
      const riskScore = data.risk_score

      if (riskLevel === 'high') {
        toast.warning(`High risk detected! Score: ${riskScore}`)
      } else if (riskLevel === 'medium') {
        toast.info(`Medium risk. Score: ${riskScore}`)
      } else {
        toast.success(`Low risk. Score: ${riskScore}`)
      }

      return data
    } catch (error) {
      // Error already handled by interceptor
      throw error
    }
  },

  /**
   * Check multiple transactions in a batch
   * @param transactions - Array of transactions to check
   */
  async checkTransactionsBatch(transactions: any[]) {
    const { data } = await api.post('/fraud-detection/check-transactions-batch', transactions)

    toast.success(`Processed ${transactions.length} transactions successfully`)

    return data
  },

  /**
   * Submit feedback for a transaction
   * @param feedback - Feedback data (transaction_id, actual_outcome, etc.)
   */
  async submitFeedback(feedback: any) {
    const { data } = await api.post('/fraud-detection/feedback', feedback)

    toast.success('Feedback submitted successfully')

    return data
  },

  /**
   * Get client information
   * Returns client account details, usage stats, and subscription info
   */
  async getClientInfo() {
    const { data } = await api.get('/dashboard/client-info')
    return data
  },

  /**
   * Get rule accuracy metrics
   * Returns performance metrics for each fraud detection rule
   */
  async getRuleAccuracy() {
    const { data } = await api.get('/dashboard/rule-accuracy')
    return data
  },

  /**
   * Get cache statistics
   * Shows cache hit rate and performance metrics
   */
  async getCacheStats() {
    const { data } = await api.get('/fraud-detection/cache-stats')
    return data
  },
}

export default api
