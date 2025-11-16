/**
 * Data Export Utilities
 *
 * Functions to export data in various formats (CSV, JSON, PDF).
 * Handles downloading files directly in the browser.
 *
 * Usage:
 *   exportToCSV(transactions, 'fraud-transactions.csv')
 *   exportToJSON(stats, 'dashboard-stats.json')
 */

import { Transaction, DashboardStats } from '../types'

/**
 * Export data to CSV format
 * @param data - Array of objects to export
 * @param filename - Name of the file to download
 */
export function exportToCSV(data: any[], filename: string) {
  if (!data || data.length === 0) {
    alert('No data to export')
    return
  }

  // Get all unique keys from all objects
  const keys = Array.from(
    new Set(data.flatMap(item => Object.keys(item)))
  )

  // Create CSV header
  const header = keys.join(',')

  // Create CSV rows
  const rows = data.map(item => {
    return keys.map(key => {
      const value = item[key]

      // Handle different data types
      if (value === null || value === undefined) {
        return ''
      }

      if (typeof value === 'object') {
        // Convert objects/arrays to JSON string
        return `"${JSON.stringify(value).replace(/"/g, '""')}"`
      }

      if (typeof value === 'string') {
        // Escape quotes in strings
        return `"${value.replace(/"/g, '""')}"`
      }

      return value
    }).join(',')
  })

  // Combine header and rows
  const csv = [header, ...rows].join('\n')

  // Create download
  downloadFile(csv, filename, 'text/csv')
}

/**
 * Export data to JSON format
 * @param data - Data to export (object or array)
 * @param filename - Name of the file to download
 */
export function exportToJSON(data: any, filename: string) {
  if (!data) {
    alert('No data to export')
    return
  }

  // Pretty-print JSON with 2-space indentation
  const json = JSON.stringify(data, null, 2)

  // Create download
  downloadFile(json, filename, 'application/json')
}

/**
 * Export transactions to CSV with custom formatting
 * @param transactions - Array of transactions
 * @param filename - Name of the file to download
 */
export function exportTransactionsToCSV(transactions: Transaction[], filename: string) {
  if (!transactions || transactions.length === 0) {
    alert('No transactions to export')
    return
  }

  // Format transactions for CSV (flatten nested objects)
  const formatted = transactions.map(txn => ({
    transaction_id: txn.transaction_id,
    amount: txn.amount,
    risk_score: txn.risk_score,
    risk_level: txn.risk_level,
    decision: txn.decision,
    outcome: txn.outcome || 'pending',
    created_at: new Date(txn.created_at).toLocaleString('en-NG'),
  }))

  exportToCSV(formatted, filename)
}

/**
 * Export dashboard stats to JSON
 * @param stats - Dashboard statistics
 * @param filename - Name of the file to download
 */
export function exportDashboardStats(stats: DashboardStats, filename: string) {
  const formatted = {
    exported_at: new Date().toISOString(),
    today: {
      transactions: stats.today_transactions,
      high_risk: stats.today_high_risk,
      medium_risk: stats.today_medium_risk,
      low_risk: stats.today_low_risk,
      fraud_prevented_amount: stats.today_fraud_prevented_amount,
    },
    month: {
      transactions: stats.month_transactions,
      fraud_caught: stats.month_fraud_caught,
      fraud_prevented_amount: stats.month_fraud_prevented_amount,
      false_positive_rate: stats.month_false_positive_rate,
      accuracy: stats.month_accuracy,
    },
    risk_distribution: stats.risk_distribution,
    fraud_types: stats.fraud_types,
  }

  exportToJSON(formatted, filename)
}

/**
 * Helper function to trigger file download
 * @param content - File content
 * @param filename - Name of the file
 * @param mimeType - MIME type of the file
 */
function downloadFile(content: string, filename: string, mimeType: string) {
  // Create blob
  const blob = new Blob([content], { type: mimeType })

  // Create download link
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename

  // Trigger download
  document.body.appendChild(link)
  link.click()

  // Cleanup
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Copy data to clipboard as JSON
 * @param data - Data to copy
 */
export async function copyToClipboard(data: any): Promise<boolean> {
  try {
    const json = JSON.stringify(data, null, 2)
    await navigator.clipboard.writeText(json)
    return true
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
    return false
  }
}
