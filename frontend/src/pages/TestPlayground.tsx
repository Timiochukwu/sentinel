/**
 * Transaction Testing Playground
 *
 * Interactive page for testing fraud detection in real-time.
 * Users can input transaction data and see fraud analysis results immediately.
 *
 * Features:
 * - Pre-filled sample data for different fraud scenarios
 * - Form validation
 * - Real-time fraud detection
 * - Visual display of results (risk score, flags, recommendation)
 * - Copy-paste JSON support
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Play, AlertTriangle, CheckCircle2, Info, Copy } from 'lucide-react'
import Layout from '../components/Layout'
import { fraudAPI } from '../lib/api'
import { toast } from '../components/Toast'

// Sample transaction scenarios
const SAMPLE_SCENARIOS = {
  legitimate: {
    name: 'Legitimate Transaction',
    data: {
      transaction_id: 'txn_legit_001',
      user_id: 'user_12345',
      amount: 15000,
      transaction_type: 'loan_disbursement',
      device_id: 'iphone_abc123',
      ip_address: '197.210.52.34',
      account_age_days: 180,
      transaction_count: 15,
      phone_changed_recently: false,
      email_changed_recently: false,
    },
  },
  sim_swap: {
    name: 'SIM Swap Attack',
    data: {
      transaction_id: 'txn_sim_swap_001',
      user_id: 'user_99999',
      amount: 500000,
      transaction_type: 'withdrawal',
      device_id: 'android_new_device',
      ip_address: '197.210.53.100',
      account_age_days: 5,
      transaction_count: 2,
      phone_changed_recently: true,
      email_changed_recently: false,
      is_first_transaction: false,
    },
  },
  loan_stacking: {
    name: 'Loan Stacking',
    data: {
      transaction_id: 'txn_stacking_001',
      user_id: 'user_stacker',
      amount: 300000,
      transaction_type: 'loan_disbursement',
      device_id: 'samsung_s21',
      ip_address: '197.210.54.20',
      account_age_days: 2,
      transaction_count: 0,
      phone: '+2348012345678',
      bvn: '12345678901',
      is_first_transaction: true,
    },
  },
  new_account: {
    name: 'New Account Large Amount',
    data: {
      transaction_id: 'txn_new_001',
      user_id: 'user_newbie',
      amount: 450000,
      transaction_type: 'loan_disbursement',
      device_id: 'iphone_13',
      ip_address: '197.210.55.99',
      account_age_days: 1,
      transaction_count: 0,
      is_first_transaction: true,
    },
  },
}

export default function TestPlayground() {
  const [transactionData, setTransactionData] = useState(JSON.stringify(SAMPLE_SCENARIOS.legitimate.data, null, 2))
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load a sample scenario
  const loadScenario = (scenarioKey: keyof typeof SAMPLE_SCENARIOS) => {
    const scenario = SAMPLE_SCENARIOS[scenarioKey]
    setTransactionData(JSON.stringify(scenario.data, null, 2))
    setResult(null)
    setError(null)
    toast.info(`Loaded: ${scenario.name}`)
  }

  // Submit transaction for fraud checking
  const handleSubmit = async () => {
    setError(null)
    setLoading(true)

    try {
      // Parse JSON input
      const transaction = JSON.parse(transactionData)

      // Call fraud detection API
      const response = await fraudAPI.checkTransaction(transaction)

      setResult(response)
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format. Please check your input.')
        toast.error('Invalid JSON format')
      } else {
        setError(err.message || 'Failed to check transaction')
      }
    } finally {
      setLoading(false)
    }
  }

  // Copy result to clipboard
  const copyResult = () => {
    if (result) {
      navigator.clipboard.writeText(JSON.stringify(result, null, 2))
      toast.success('Result copied to clipboard')
    }
  }

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

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">Transaction Testing Playground</h1>
          <p className="text-gray-400">Test fraud detection with sample or custom transaction data</p>
        </div>

        {/* Sample Scenarios */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-xl font-bold mb-4">Sample Scenarios</h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(SAMPLE_SCENARIOS).map(([key, scenario]) => (
              <button
                key={key}
                onClick={() => loadScenario(key as keyof typeof SAMPLE_SCENARIOS)}
                className="px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all text-left"
              >
                <p className="font-medium">{scenario.name}</p>
                <p className="text-xs text-gray-400 mt-1">
                  ₦{scenario.data.amount.toLocaleString()}
                </p>
              </button>
            ))}
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass rounded-2xl p-6"
          >
            <h3 className="text-xl font-bold mb-4">Transaction Data</h3>

            <textarea
              value={transactionData}
              onChange={(e) => setTransactionData(e.target.value)}
              className="w-full h-96 bg-black/50 border border-white/10 rounded-lg p-4 font-mono text-sm focus:border-purple-500 focus:outline-none resize-none"
              placeholder="Enter transaction JSON data..."
            />

            {error && (
              <div className="mt-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full mt-4 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  >
                    <Play className="w-5 h-5" />
                  </motion.div>
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Check for Fraud
                </>
              )}
            </button>
          </motion.div>

          {/* Results Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Fraud Analysis Results</h3>
              {result && (
                <button
                  onClick={copyResult}
                  className="p-2 hover:bg-white/10 rounded-lg transition-all"
                  title="Copy to clipboard"
                >
                  <Copy className="w-4 h-4" />
                </button>
              )}
            </div>

            {!result ? (
              <div className="flex flex-col items-center justify-center h-96 text-gray-500">
                <Info className="w-12 h-12 mb-4" />
                <p>Submit a transaction to see fraud analysis results</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Risk Score Badge */}
                <div className="text-center">
                  <div
                    className={`inline-block px-6 py-3 rounded-lg border ${getRiskColor(result.risk_level)}`}
                  >
                    <p className="text-sm font-medium mb-1">Risk Score</p>
                    <p className="text-4xl font-bold">{result.risk_score}</p>
                    <p className="text-xs mt-1 uppercase">{result.risk_level} Risk</p>
                  </div>
                </div>

                {/* Decision */}
                <div>
                  <p className="text-sm text-gray-400 mb-2">Decision</p>
                  <div className="flex items-center gap-2">
                    {result.decision === 'approve' ? (
                      <CheckCircle2 className="w-5 h-5 text-green-400" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                    )}
                    <p className="font-medium uppercase">{result.decision}</p>
                  </div>
                </div>

                {/* Recommendation */}
                {result.recommendation && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Recommendation</p>
                    <p className="text-sm bg-black/50 p-3 rounded-lg border border-white/10">
                      {result.recommendation}
                    </p>
                  </div>
                )}

                {/* Fraud Flags */}
                {result.flags && result.flags.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-400 mb-2">Fraud Flags ({result.flags.length})</p>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {result.flags.map((flag: any, index: number) => (
                        <div
                          key={index}
                          className="bg-black/50 p-3 rounded-lg border border-white/10"
                        >
                          <div className="flex items-start justify-between mb-1">
                            <p className="font-medium text-sm">{flag.type.replace(/_/g, ' ').toUpperCase()}</p>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              flag.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                              flag.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                              flag.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-blue-500/20 text-blue-400'
                            }`}>
                              {flag.severity}
                            </span>
                          </div>
                          <p className="text-xs text-gray-400">{flag.message}</p>
                          <div className="flex gap-3 mt-2 text-xs text-gray-500">
                            <span>Score: +{flag.score}</span>
                            {flag.confidence && <span>Confidence: {(flag.confidence * 100).toFixed(0)}%</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Processing Time */}
                <div className="text-center text-sm text-gray-500">
                  Processed in {result.processing_time_ms}ms
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </Layout>
  )
}
