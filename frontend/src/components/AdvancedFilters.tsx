/**
 * Advanced Filters Component
 *
 * Provides filtering options for transactions:
 * - Date range (last 7 days, 30 days, custom)
 * - Risk level (low, medium, high)
 * - Decision (approve, review, decline)
 * - Amount range
 *
 * Usage:
 *   <AdvancedFilters
 *     onFilterChange={(filters) => handleFilterChange(filters)}
 *     onReset={() => handleReset()}
 *   />
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Filter, X, Calendar, DollarSign, Shield } from 'lucide-react'

export interface FilterOptions {
  dateRange: 'all' | '7days' | '30days' | 'custom'
  customStartDate?: string
  customEndDate?: string
  riskLevels: string[]
  decisions: string[]
  minAmount?: number
  maxAmount?: number
}

interface AdvancedFiltersProps {
  onFilterChange: (filters: FilterOptions) => void
  onReset: () => void
}

export default function AdvancedFilters({ onFilterChange, onReset }: AdvancedFiltersProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [filters, setFilters] = useState<FilterOptions>({
    dateRange: 'all',
    riskLevels: [],
    decisions: [],
  })

  const riskLevels = [
    { value: 'low', label: 'Low Risk', color: 'text-green-400' },
    { value: 'medium', label: 'Medium Risk', color: 'text-yellow-400' },
    { value: 'high', label: 'High Risk', color: 'text-red-400' },
  ]

  const decisions = [
    { value: 'approve', label: 'Approve', color: 'text-green-400' },
    { value: 'review', label: 'Review', color: 'text-yellow-400' },
    { value: 'decline', label: 'Decline', color: 'text-red-400' },
  ]

  const dateRangeOptions = [
    { value: 'all', label: 'All Time' },
    { value: '7days', label: 'Last 7 Days' },
    { value: '30days', label: 'Last 30 Days' },
    { value: 'custom', label: 'Custom Range' },
  ]

  const handleDateRangeChange = (value: string) => {
    const newFilters = { ...filters, dateRange: value as any }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleRiskLevelToggle = (value: string) => {
    const newRiskLevels = filters.riskLevels.includes(value)
      ? filters.riskLevels.filter(r => r !== value)
      : [...filters.riskLevels, value]

    const newFilters = { ...filters, riskLevels: newRiskLevels }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleDecisionToggle = (value: string) => {
    const newDecisions = filters.decisions.includes(value)
      ? filters.decisions.filter(d => d !== value)
      : [...filters.decisions, value]

    const newFilters = { ...filters, decisions: newDecisions }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleAmountChange = (type: 'min' | 'max', value: string) => {
    const amount = value === '' ? undefined : parseFloat(value)
    const newFilters = {
      ...filters,
      [type === 'min' ? 'minAmount' : 'maxAmount']: amount,
    }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleCustomDateChange = (type: 'start' | 'end', value: string) => {
    const newFilters = {
      ...filters,
      [type === 'start' ? 'customStartDate' : 'customEndDate']: value,
    }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleReset = () => {
    const resetFilters: FilterOptions = {
      dateRange: 'all',
      riskLevels: [],
      decisions: [],
    }
    setFilters(resetFilters)
    onReset()
  }

  const getActiveFilterCount = () => {
    let count = 0
    if (filters.dateRange !== 'all') count++
    if (filters.riskLevels.length > 0) count++
    if (filters.decisions.length > 0) count++
    if (filters.minAmount !== undefined) count++
    if (filters.maxAmount !== undefined) count++
    return count
  }

  const activeCount = getActiveFilterCount()

  return (
    <div className="relative">
      {/* Filter Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all"
      >
        <Filter className="w-4 h-4" />
        <span>Filters</span>
        {activeCount > 0 && (
          <span className="bg-purple-500 text-white text-xs px-2 py-0.5 rounded-full">
            {activeCount}
          </span>
        )}
      </button>

      {/* Filter Panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="absolute right-0 top-full mt-2 w-96 glass rounded-lg p-6 z-50 shadow-xl border border-white/10"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold">Filters</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-white/10 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Date Range */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium mb-3">
                    <Calendar className="w-4 h-4" />
                    Date Range
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {dateRangeOptions.map(option => (
                      <button
                        key={option.value}
                        onClick={() => handleDateRangeChange(option.value)}
                        className={`px-3 py-2 rounded-lg text-sm transition-all ${
                          filters.dateRange === option.value
                            ? 'bg-purple-500/20 border border-purple-500/50 text-purple-300'
                            : 'bg-white/5 border border-white/10 hover:bg-white/10'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>

                  {/* Custom Date Inputs */}
                  {filters.dateRange === 'custom' && (
                    <div className="mt-3 space-y-2">
                      <input
                        type="date"
                        onChange={(e) => handleCustomDateChange('start', e.target.value)}
                        className="w-full px-3 py-2 bg-black/50 border border-white/10 rounded-lg text-sm focus:border-purple-500 focus:outline-none"
                        placeholder="Start date"
                      />
                      <input
                        type="date"
                        onChange={(e) => handleCustomDateChange('end', e.target.value)}
                        className="w-full px-3 py-2 bg-black/50 border border-white/10 rounded-lg text-sm focus:border-purple-500 focus:outline-none"
                        placeholder="End date"
                      />
                    </div>
                  )}
                </div>

                {/* Risk Levels */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium mb-3">
                    <Shield className="w-4 h-4" />
                    Risk Level
                  </label>
                  <div className="space-y-2">
                    {riskLevels.map(level => (
                      <label
                        key={level.value}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={filters.riskLevels.includes(level.value)}
                          onChange={() => handleRiskLevelToggle(level.value)}
                          className="w-4 h-4 rounded border-white/20 bg-white/5"
                        />
                        <span className={`text-sm ${level.color}`}>
                          {level.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Decisions */}
                <div>
                  <label className="text-sm font-medium mb-3 block">Decision</label>
                  <div className="space-y-2">
                    {decisions.map(decision => (
                      <label
                        key={decision.value}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={filters.decisions.includes(decision.value)}
                          onChange={() => handleDecisionToggle(decision.value)}
                          className="w-4 h-4 rounded border-white/20 bg-white/5"
                        />
                        <span className={`text-sm ${decision.color}`}>
                          {decision.label}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Amount Range */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium mb-3">
                    <DollarSign className="w-4 h-4" />
                    Amount Range (₦)
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={filters.minAmount || ''}
                      onChange={(e) => handleAmountChange('min', e.target.value)}
                      className="px-3 py-2 bg-black/50 border border-white/10 rounded-lg text-sm focus:border-purple-500 focus:outline-none"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      value={filters.maxAmount || ''}
                      onChange={(e) => handleAmountChange('max', e.target.value)}
                      className="px-3 py-2 bg-black/50 border border-white/10 rounded-lg text-sm focus:border-purple-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 mt-6 pt-6 border-t border-white/10">
                <button
                  onClick={handleReset}
                  className="flex-1 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm transition-all"
                >
                  Reset
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-lg text-sm transition-all"
                >
                  Apply
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
