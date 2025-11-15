import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  Search,
  ChevronRight,
} from 'lucide-react'
import Layout from '../components/Layout'
import Background3D from '../components/Background3D'
import { fraudAPI } from '../lib/api'
import { Transaction } from '../types'
import { format } from 'date-fns'

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    loadTransactions()
  }, [filter])

  const loadTransactions = async () => {
    try {
      const params = filter !== 'all' ? { risk_level: filter } : {}
      const data = await fraudAPI.getTransactions(params)
      setTransactions(data)
    } catch (error) {
      console.error('Failed to load transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-red-400 bg-red-500/20'
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/20'
      default:
        return 'text-green-400 bg-green-500/20'
    }
  }

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'decline':
        return <AlertTriangle className="w-5 h-5 text-red-400" />
      case 'review':
        return <Clock className="w-5 h-5 text-yellow-400" />
      default:
        return <CheckCircle2 className="w-5 h-5 text-green-400" />
    }
  }

  const filteredTransactions = transactions.filter((txn) =>
    txn.transaction_id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <Layout>
      <Background3D />

      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gradient mb-2">Transactions</h1>
            <p className="text-gray-400">Review and manage fraud detection results</p>
          </div>

          {/* Search */}
          <div className="relative w-full lg:w-96">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by transaction ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 glass rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          {['all', 'high', 'medium', 'low'].map((level) => (
            <button
              key={level}
              onClick={() => setFilter(level as any)}
              className={`px-6 py-2 rounded-xl font-medium transition-all ${
                filter === level
                  ? 'bg-purple-500 text-white glow-effect'
                  : 'glass text-gray-300 hover:bg-white/10'
              }`}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)} Risk
            </button>
          ))}
        </div>

        {/* Transactions List */}
        <div className="space-y-4">
          {loading ? (
            <div className="glass rounded-2xl p-12 text-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="inline-block"
              >
                <AlertTriangle className="w-8 h-8 text-purple-400" />
              </motion.div>
              <p className="mt-4 text-gray-400">Loading transactions...</p>
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div className="glass rounded-2xl p-12 text-center">
              <p className="text-gray-400">No transactions found</p>
            </div>
          ) : (
            filteredTransactions.map((transaction, index) => (
              <motion.div
                key={transaction.transaction_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="glass rounded-2xl p-6 hover:glow-effect transition-all cursor-pointer"
              >
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="mt-1">{getDecisionIcon(transaction.decision)}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-mono font-bold text-white">
                          {transaction.transaction_id}
                        </h3>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskColor(
                            transaction.risk_level
                          )}`}
                        >
                          {transaction.risk_level.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
                        <span>Amount: ₦{transaction.amount.toLocaleString()}</span>
                        <span>•</span>
                        <span>Risk Score: {transaction.risk_score}</span>
                        <span>•</span>
                        <span>{format(new Date(transaction.created_at), 'MMM d, yyyy HH:mm')}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span
                        className={`px-4 py-2 rounded-lg font-medium ${
                          transaction.decision === 'decline'
                            ? 'bg-red-500/20 text-red-300'
                            : transaction.decision === 'review'
                            ? 'bg-yellow-500/20 text-yellow-300'
                            : 'bg-green-500/20 text-green-300'
                        }`}
                      >
                        {transaction.decision.toUpperCase()}
                      </span>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </div>

        {/* Load More */}
        {!loading && filteredTransactions.length > 0 && (
          <div className="text-center">
            <button className="px-8 py-3 glass rounded-xl hover:bg-white/10 transition-all">
              Load More
            </button>
          </div>
        )}
      </div>
    </Layout>
  )
}
