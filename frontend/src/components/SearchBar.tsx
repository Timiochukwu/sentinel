/**
 * Search Bar Component
 *
 * Allows searching transactions by:
 * - Transaction ID
 * - User ID
 * - Amount
 *
 * Features:
 * - Real-time search
 * - Keyboard shortcut (/)
 * - Clear button
 *
 * Usage:
 *   <SearchBar
 *     onSearch={(query) => handleSearch(query)}
 *     placeholder="Search transactions..."
 *   />
 */

import { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string) => void
  placeholder?: string
}

export default function SearchBar({ onSearch, placeholder = 'Search...' }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  // Keyboard shortcut: "/" to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault()
        inputRef.current?.focus()
      }

      // Escape to clear search
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        handleClear()
        inputRef.current?.blur()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleChange = (value: string) => {
    setQuery(value)
    onSearch(value)
  }

  const handleClear = () => {
    setQuery('')
    onSearch('')
  }

  return (
    <div className="relative">
      <div className="relative">
        {/* Search Icon */}
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => handleChange(e.target.value)}
          placeholder={placeholder}
          className="w-full pl-10 pr-20 py-2.5 bg-white/5 border border-white/10 rounded-lg focus:border-purple-500 focus:outline-none transition-all"
        />

        {/* Keyboard Hint */}
        {!query && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
            <kbd className="px-2 py-1 bg-white/10 border border-white/20 rounded text-xs text-gray-400">
              /
            </kbd>
          </div>
        )}

        {/* Clear Button */}
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-white/10 rounded transition-all"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        )}
      </div>

      {/* Search Tips */}
      {query && (
        <div className="absolute left-0 top-full mt-2 w-full glass rounded-lg p-3 text-xs text-gray-400 z-10">
          <p className="mb-1">
            <span className="text-purple-400">Tip:</span> Search by transaction ID, user ID, or amount
          </p>
          <p>
            Press <kbd className="px-1.5 py-0.5 bg-white/10 rounded">Esc</kbd> to clear
          </p>
        </div>
      )}
    </div>
  )
}
