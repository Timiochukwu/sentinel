/**
 * Empty State Component
 *
 * Displays a friendly message when there's no data to show.
 * Much better UX than showing blank space or just "No data".
 *
 * Usage:
 *   <EmptyState
 *     icon={FileX}
 *     title="No transactions yet"
 *     description="Start by testing fraud detection in the playground"
 *     action={{
 *       label: "Go to Playground",
 *       onClick: () => navigate('/test')
 *     }}
 *   />
 */

import { LucideIcon } from 'lucide-react'
import { motion } from 'framer-motion'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
}

export default function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      {/* Icon */}
      <div className="mb-4 p-4 bg-white/5 rounded-full">
        <Icon className="w-12 h-12 text-gray-400" />
      </div>

      {/* Title */}
      <h3 className="text-xl font-bold mb-2">{title}</h3>

      {/* Description */}
      <p className="text-gray-400 mb-6 max-w-md">{description}</p>

      {/* Action Button */}
      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  )
}
