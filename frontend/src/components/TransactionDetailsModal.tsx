/**
 * Transaction Details Modal
 *
 * Shows comprehensive fraud analysis for a single transaction.
 * Displays all fraud flags, consortium alerts, device info, and recommendation.
 *
 * Usage:
 *   <TransactionDetailsModal
 *     transaction={transactionData}
 *     isOpen={showModal}
 *     onClose={() => setShowModal(false)}
 *   />
 */

import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle, Shield, MapPin, Smartphone, Clock, Users, TrendingUp } from 'lucide-react'
import { TransactionDetail } from '../types'

interface TransactionDetailsModalProps {
  transaction: TransactionDetail | null
  isOpen: boolean
  onClose: () => void
}

export default function TransactionDetailsModal({
  transaction,
  isOpen,
  onClose
}: TransactionDetailsModalProps) {
  if (!transaction) return null

  // Get risk color based on level
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-red-400 bg-red-500/20 border-red-500/50'
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50'
      case 'low':
        return 'text-green-400 bg-green-500/20 border-green-500/50'
      default:
        return 'text-gray-400 bg-gray-500/20 border-gray-500/50'
    }
  }

  // Format currency
  const formatCurrency = (amount: number) => {
    return `₦${amount.toLocaleString()}`
  }

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-NG', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="glass rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden pointer-events-auto"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                <div>
                  <h2 className="text-2xl font-bold">Transaction Details</h2>
                  <p className="text-sm text-gray-400 mt-1">
                    {transaction.transaction_id}
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/10 rounded-lg transition-all"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
                <div className="space-y-6">
                  {/* Risk Score Section */}
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold mb-4">Risk Assessment</h3>
                      <div className="flex items-center gap-4">
                        <div className={`px-6 py-4 rounded-lg border ${getRiskColor(transaction.risk_level)}`}>
                          <p className="text-sm opacity-70 mb-1">Risk Score</p>
                          <p className="text-3xl font-bold">{transaction.risk_score}</p>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm text-gray-400">Risk Level:</span>
                            <span className={`uppercase font-semibold ${
                              transaction.risk_level === 'high' ? 'text-red-400' :
                              transaction.risk_level === 'medium' ? 'text-yellow-400' :
                              'text-green-400'
                            }`}>
                              {transaction.risk_level}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm text-gray-400">Decision:</span>
                            <span className="uppercase font-semibold">{transaction.decision}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-gray-400" />
                            <span className="text-sm text-gray-400">
                              Processed in {transaction.processing_time_ms}ms
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Recommendation */}
                  {transaction.recommendation && (
                    <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-purple-400" />
                        Recommendation
                      </h4>
                      <p className="text-sm">{transaction.recommendation}</p>
                    </div>
                  )}

                  {/* Transaction Info */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Transaction Information</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white/5 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">Amount</p>
                        <p className="text-xl font-bold">{formatCurrency(transaction.amount)}</p>
                      </div>
                      <div className="bg-white/5 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">Type</p>
                        <p className="font-medium">{transaction.transaction_type}</p>
                      </div>
                      <div className="bg-white/5 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">User ID</p>
                        <p className="font-medium font-mono text-sm">{transaction.user_id}</p>
                      </div>
                      <div className="bg-white/5 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-1">Date & Time</p>
                        <p className="font-medium text-sm">{formatDate(transaction.created_at)}</p>
                      </div>
                    </div>
                  </div>

                  {/* Consortium Alerts - HIGHLIGHTED! */}
                  {transaction.consortium_alerts && transaction.consortium_alerts.length > 0 && (
                    <div className="bg-orange-500/10 border-2 border-orange-500/50 rounded-lg p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2 text-orange-400">
                        <Users className="w-5 h-5" />
                        Consortium Intelligence Alerts
                        <span className="ml-auto text-xs bg-orange-500/20 px-2 py-1 rounded">
                          {transaction.consortium_alerts.length} alert{transaction.consortium_alerts.length > 1 ? 's' : ''}
                        </span>
                      </h4>
                      <div className="space-y-2">
                        {transaction.consortium_alerts.map((alert, index) => (
                          <div key={index} className="flex items-start gap-2 text-sm">
                            <AlertTriangle className="w-4 h-4 text-orange-400 mt-0.5 flex-shrink-0" />
                            <p className="text-orange-200">{alert}</p>
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-orange-300/60 mt-3 italic">
                        * Consortium data is shared anonymously across participating lenders to detect cross-platform fraud patterns
                      </p>
                    </div>
                  )}

                  {/* Fraud Flags */}
                  {transaction.flags && transaction.flags.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        Fraud Flags ({transaction.flags.length})
                      </h3>
                      <div className="space-y-3">
                        {transaction.flags.map((flag, index) => (
                          <div
                            key={index}
                            className="bg-black/30 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-all"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <h4 className="font-semibold">
                                  {flag.type.replace(/_/g, ' ').toUpperCase()}
                                </h4>
                                <p className="text-sm text-gray-400 mt-1">{flag.message}</p>
                              </div>
                              <span className={`text-xs px-3 py-1 rounded-full ml-4 flex-shrink-0 ${
                                flag.severity === 'critical' ? 'bg-red-500/20 text-red-400 border border-red-500/50' :
                                flag.severity === 'high' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/50' :
                                flag.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50' :
                                'bg-blue-500/20 text-blue-400 border border-blue-500/50'
                              }`}>
                                {flag.severity}
                              </span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                              <div className="flex items-center gap-1">
                                <TrendingUp className="w-4 h-4" />
                                <span>Score: +{flag.score}</span>
                              </div>
                              {flag.confidence && (
                                <div className="flex items-center gap-1">
                                  <Shield className="w-4 h-4" />
                                  <span>Confidence: {(flag.confidence * 100).toFixed(0)}%</span>
                                </div>
                              )}
                            </div>
                            {flag.metadata && Object.keys(flag.metadata).length > 0 && (
                              <div className="mt-3 pt-3 border-t border-white/10">
                                <p className="text-xs text-gray-400 mb-2">Additional Details:</p>
                                <div className="space-y-1">
                                  {Object.entries(flag.metadata).map(([key, value]) => (
                                    <div key={key} className="flex gap-2 text-xs">
                                      <span className="text-gray-500">{key}:</span>
                                      <span className="text-gray-300">
                                        {Array.isArray(value) ? value.join(', ') : String(value)}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* No Fraud Flags */}
                  {(!transaction.flags || transaction.flags.length === 0) && (
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-6 text-center">
                      <Shield className="w-12 h-12 text-green-400 mx-auto mb-3" />
                      <p className="font-semibold text-green-400">No Fraud Flags Detected</p>
                      <p className="text-sm text-gray-400 mt-2">
                        This transaction passed all fraud detection rules
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 p-6 border-t border-white/10">
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition-all"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
