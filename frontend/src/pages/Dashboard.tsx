import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  AlertTriangle,
  Shield,
  DollarSign,
  Activity,
  CheckCircle2,
  FileX,
} from 'lucide-react'
import Layout from '../components/Layout'
import Background3D from '../components/Background3D'
import StatCard from '../components/StatCard'
import EmptyState from '../components/EmptyState'
import { DashboardSkeleton } from '../components/LoadingSkeleton'
import { fraudAPI } from '../lib/api'
import { DashboardStats as StatsType } from '../types'
import { useNavigate } from 'react-router-dom'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

export default function Dashboard() {
  const [stats, setStats] = useState<StatsType | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await fraudAPI.getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  // Show loading skeleton
  if (loading) {
    return (
      <Layout>
        <Background3D />
        <DashboardSkeleton />
      </Layout>
    )
  }

  // Show empty state if no data
  if (!stats || (stats.today_transactions === 0 && stats.month_transactions === 0)) {
    return (
      <Layout>
        <Background3D />
        <EmptyState
          icon={FileX}
          title="No transactions yet"
          description="Start by testing fraud detection in the playground or integrate with your API to begin seeing analytics."
          action={{
            label: "Go to Test Playground",
            onClick: () => navigate('/test')
          }}
        />
      </Layout>
    )
  }

  const formatCurrency = (amount: number) => {
    return `₦${(amount / 1000000).toFixed(1)}M`
  }

  const riskData = stats
    ? [
        { name: 'Low Risk', value: stats.risk_distribution.low, color: '#22c55e' },
        { name: 'Medium Risk', value: stats.risk_distribution.medium, color: '#f59e0b' },
        { name: 'High Risk', value: stats.risk_distribution.high, color: '#ef4444' },
      ]
    : []

  const fraudTypesData = stats
    ? Object.entries(stats.fraud_types).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value,
      }))
    : []

  return (
    <Layout>
      <Background3D />

      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">Dashboard</h1>
          <p className="text-gray-400">Real-time fraud detection analytics</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            title="Today's Transactions"
            value={stats?.today_transactions?.toLocaleString() || '0'}
            change={12}
            trend="up"
            icon={Activity}
            delay={0}
          />
          <StatCard
            title="High Risk Detected"
            value={stats?.today_high_risk || 0}
            change={8}
            trend="down"
            icon={AlertTriangle}
            delay={0.1}
          />
          <StatCard
            title="Fraud Prevented Today"
            value={formatCurrency(stats?.today_fraud_prevented_amount || 0)}
            change={15}
            trend="up"
            icon={Shield}
            delay={0.2}
          />
          <StatCard
            title="Month Transactions"
            value={stats?.month_transactions?.toLocaleString() || '0'}
            change={23}
            trend="up"
            icon={TrendingUp}
            delay={0.3}
          />
          <StatCard
            title="Detection Accuracy"
            value={`${((stats?.month_accuracy || 0) * 100).toFixed(1)}%`}
            change={5}
            trend="up"
            icon={CheckCircle2}
            delay={0.4}
          />
          <StatCard
            title="Total Fraud Prevented"
            value={formatCurrency(stats?.month_fraud_prevented_amount || 0)}
            change={28}
            trend="up"
            icon={DollarSign}
            delay={0.5}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Risk Distribution */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="glass rounded-2xl p-6"
          >
            <h3 className="text-xl font-bold mb-6">Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: '1px rgba(255, 255, 255, 0.2)',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Fraud Types */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            className="glass rounded-2xl p-6"
          >
            <h3 className="text-xl font-bold mb-6">Top Fraud Types</h3>
            <div className="space-y-4">
              {fraudTypesData.slice(0, 5).map((item, index) => {
                const maxValue = Math.max(...fraudTypesData.map(d => d.value))
                const percentage = (item.value / maxValue) * 100

                return (
                  <div key={index}>
                    <div className="flex justify-between mb-2">
                      <span className="text-sm text-gray-300">{item.name}</span>
                      <span className="text-sm font-bold">{item.value}</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ delay: 0.8 + index * 0.1, duration: 0.5 }}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </motion.div>
        </div>

        {/* Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="glass rounded-2xl p-6"
        >
          <h3 className="text-xl font-bold mb-6">Performance Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-4xl font-bold text-gradient mb-2">
                {((stats?.month_accuracy || 0) * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-400">Detection Accuracy</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-gradient mb-2">
                {((1 - (stats?.month_false_positive_rate || 0)) * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-gray-400">Precision</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-gradient mb-2">
                {stats?.month_fraud_caught || 0}
              </p>
              <p className="text-sm text-gray-400">Fraud Cases Caught</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-gradient mb-2">
                &lt;100ms
              </p>
              <p className="text-sm text-gray-400">Avg Response Time</p>
            </div>
          </div>
        </motion.div>
      </div>
    </Layout>
  )
}
