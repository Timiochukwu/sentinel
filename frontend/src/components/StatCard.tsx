import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  icon: LucideIcon
  trend?: 'up' | 'down'
  delay?: number
}

export default function StatCard({
  title,
  value,
  change,
  icon: Icon,
  trend,
  delay = 0,
}: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ scale: 1.02 }}
      className="glass rounded-2xl p-6 hover:glow-effect transition-all"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <p className="text-3xl font-bold text-white mb-2">{value}</p>
          {change !== undefined && (
            <div className={`flex items-center text-sm ${
              trend === 'up' ? 'text-green-400' : 'text-red-400'
            }`}>
              <span>{trend === 'up' ? '↑' : '↓'}</span>
              <span className="ml-1">{Math.abs(change)}%</span>
              <span className="ml-1 text-gray-400">from last month</span>
            </div>
          )}
        </div>
        <div className="p-3 bg-purple-500/20 rounded-xl">
          <Icon className="w-6 h-6 text-purple-400" />
        </div>
      </div>
    </motion.div>
  )
}
