/**
 * Consortium Intelligence Dashboard
 *
 * Visualizes cross-lender fraud patterns and consortium alerts.
 * This is Sentinel's unique competitive advantage - showing real-time
 * fraud intelligence shared across participating Nigerian lenders.
 *
 * Features:
 * - Cross-lender fraud patterns
 * - Loan stacking visualization
 * - Shared fraud network
 * - Real-time consortium alerts
 */

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Users, Shield, AlertTriangle, TrendingUp, Network, Eye } from 'lucide-react'
import Layout from '../components/Layout'
import StatCard from '../components/StatCard'
import { DashboardSkeleton } from '../components/LoadingSkeleton'

export default function ConsortiumDashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    // Simulate loading consortium data
    // In production, this would call: fraudAPI.getConsortiumStats()
    setTimeout(() => {
      setStats({
        total_members: 12,
        fraud_cases_shared: 1234,
        loan_stacking_detected: 89,
        amount_protected: 45600000,
        this_week: {
          new_alerts: 23,
          lenders_involved: 8,
          total_applications: 156,
        }
      })
      setLoading(false)
    }, 1000)
  }, [])

  if (loading) {
    return (
      <Layout>
        <DashboardSkeleton />
      </Layout>
    )
  }

  const formatCurrency = (amount: number) => {
    return `₦${(amount / 1000000).toFixed(1)}M`
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">Consortium Intelligence</h1>
          <p className="text-gray-400">
            Cross-lender fraud detection powered by shared intelligence from {stats.total_members} Nigerian lenders
          </p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Consortium Members"
            value={stats.total_members}
            change={2}
            trend="up"
            icon={Users}
            delay={0}
          />
          <StatCard
            title="Fraud Cases Shared"
            value={stats.fraud_cases_shared.toLocaleString()}
            change={15}
            trend="up"
            icon={Shield}
            delay={0.1}
          />
          <StatCard
            title="Loan Stacking Detected"
            value={stats.loan_stacking_detected}
            change={8}
            trend="down"
            icon={AlertTriangle}
            delay={0.2}
          />
          <StatCard
            title="Amount Protected"
            value={formatCurrency(stats.amount_protected)}
            change={23}
            trend="up"
            icon={TrendingUp}
            delay={0.3}
          />
        </div>

        {/* This Week's Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass rounded-2xl p-6"
        >
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Network className="w-6 h-6 text-purple-400" />
            This Week's Consortium Activity
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white/5 rounded-lg p-6 text-center">
              <p className="text-4xl font-bold text-purple-400 mb-2">
                {stats.this_week.new_alerts}
              </p>
              <p className="text-sm text-gray-400">New Consortium Alerts</p>
            </div>
            <div className="bg-white/5 rounded-lg p-6 text-center">
              <p className="text-4xl font-bold text-pink-400 mb-2">
                {stats.this_week.lenders_involved}
              </p>
              <p className="text-sm text-gray-400">Lenders Involved</p>
            </div>
            <div className="bg-white/5 rounded-lg p-6 text-center">
              <p className="text-4xl font-bold text-blue-400 mb-2">
                {stats.this_week.total_applications}
              </p>
              <p className="text-sm text-gray-400">Cross-Lender Applications</p>
            </div>
          </div>
        </motion.div>

        {/* Recent Consortium Alerts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass rounded-2xl p-6"
        >
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-orange-400" />
            Recent Consortium Alerts
          </h3>

          <div className="space-y-3">
            {/* Sample Alerts */}
            {[
              {
                id: 1,
                type: 'Loan Stacking',
                message: 'User applied to 5 lenders in the last 48 hours',
                lenders: 5,
                severity: 'critical',
                time: '2 hours ago'
              },
              {
                id: 2,
                type: 'SIM Swap Pattern',
                message: 'Device changed across 3 different lenders',
                lenders: 3,
                severity: 'high',
                time: '5 hours ago'
              },
              {
                id: 3,
                type: 'Multiple Applications',
                message: 'Same BVN used in 4 simultaneous applications',
                lenders: 4,
                severity: 'high',
                time: '1 day ago'
              },
              {
                id: 4,
                type: 'Fraud Network',
                message: 'Linked to 12 other flagged accounts via device sharing',
                lenders: 6,
                severity: 'critical',
                time: '1 day ago'
              },
            ].map((alert, index) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                className={`bg-black/30 border rounded-lg p-4 ${
                  alert.severity === 'critical'
                    ? 'border-red-500/50'
                    : 'border-orange-500/50'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold">{alert.type}</h4>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        alert.severity === 'critical'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-orange-500/20 text-orange-400'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{alert.message}</p>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                    {alert.time}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Users className="w-4 h-4" />
                  <span>{alert.lenders} lenders affected</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* How It Works */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="glass rounded-2xl p-6"
        >
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Eye className="w-6 h-6 text-blue-400" />
            How Consortium Intelligence Works
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-purple-500/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl font-bold text-purple-400">1</span>
              </div>
              <h4 className="font-semibold mb-2">Anonymous Sharing</h4>
              <p className="text-sm text-gray-400">
                Lenders share fraud signals using hashed identifiers (BVN, phone, device ID)
              </p>
            </div>

            <div className="text-center">
              <div className="bg-pink-500/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl font-bold text-pink-400">2</span>
              </div>
              <h4 className="font-semibold mb-2">Pattern Detection</h4>
              <p className="text-sm text-gray-400">
                AI detects cross-lender patterns like loan stacking and fraud networks
              </p>
            </div>

            <div className="text-center">
              <div className="bg-blue-500/20 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl font-bold text-blue-400">3</span>
              </div>
              <h4 className="font-semibold mb-2">Real-Time Alerts</h4>
              <p className="text-sm text-gray-400">
                All members receive instant alerts when fraud patterns are detected
              </p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <p className="text-sm text-green-400 text-center">
              <strong>Privacy Guarantee:</strong> All data is anonymized using SHA-256 hashing.
              No lender can identify another lender's customers.
            </p>
          </div>
        </motion.div>
      </div>
    </Layout>
  )
}
