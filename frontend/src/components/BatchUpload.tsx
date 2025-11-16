/**
 * Batch CSV Upload Component
 *
 * Allows users to upload a CSV file with multiple transactions
 * and get fraud detection results for all of them at once.
 *
 * Features:
 * - Drag & drop CSV upload
 * - CSV parsing and validation
 * - Batch fraud detection (up to 100 transactions)
 * - Results download
 * - Progress tracking
 *
 * CSV Format:
 *   transaction_id,user_id,amount,transaction_type,device_id,ip_address,...
 *
 * Usage:
 *   <BatchUpload onComplete={(results) => handleResults(results)} />
 */

import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileText, Download, X } from 'lucide-react'
import { fraudAPI } from '../lib/api'
import { toast } from './Toast'
import { exportToCSV } from '../utils/export'

export default function BatchUpload({ onComplete }: { onComplete?: (results: any) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [progress, setProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Parse CSV file
  const parseCSV = (text: string): any[] => {
    const lines = text.trim().split('\n')
    if (lines.length < 2) {
      throw new Error('CSV file must have at least a header and one data row')
    }

    // Get headers
    const headers = lines[0].split(',').map(h => h.trim())

    // Parse rows
    const transactions = lines.slice(1).map((line, index) => {
      const values = line.split(',').map(v => v.trim())

      const transaction: any = {}
      headers.forEach((header, i) => {
        const value = values[i]

        // Convert to appropriate types
        if (header === 'amount' || header === 'account_age_days' || header === 'transaction_count') {
          transaction[header] = parseFloat(value) || 0
        } else if (header === 'phone_changed_recently' || header === 'email_changed_recently' || header === 'is_first_transaction') {
          transaction[header] = value.toLowerCase() === 'true'
        } else {
          transaction[header] = value
        }
      })

      // Add index as transaction_id if not provided
      if (!transaction.transaction_id) {
        transaction.transaction_id = `batch_${Date.now()}_${index}`
      }

      return transaction
    })

    return transactions
  }

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        toast.error('Please select a CSV file')
        return
      }

      if (selectedFile.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('File size must be less than 5MB')
        return
      }

      setFile(selectedFile)
      setResults(null)
      toast.success(`File selected: ${selectedFile.name}`)
    }
  }

  // Handle drag and drop
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      setFile(droppedFile)
      setResults(null)
      toast.success(`File selected: ${droppedFile.name}`)
    } else {
      toast.error('Please drop a CSV file')
    }
  }

  // Process batch upload
  const handleProcess = async () => {
    if (!file) return

    setProcessing(true)
    setProgress(0)

    try {
      // Read file
      const text = await file.text()

      // Parse CSV
      toast.info('Parsing CSV file...')
      const transactions = parseCSV(text)

      if (transactions.length === 0) {
        throw new Error('No transactions found in CSV')
      }

      if (transactions.length > 100) {
        throw new Error('Maximum 100 transactions per batch. Please split your file.')
      }

      toast.info(`Processing ${transactions.length} transactions...`)

      // Send to batch API
      setProgress(50)
      const result = await fraudAPI.checkTransactionsBatch(transactions)

      setProgress(100)
      setResults(result)

      toast.success(`Successfully processed ${transactions.length} transactions!`)

      if (onComplete) {
        onComplete(result)
      }
    } catch (error: any) {
      console.error('Batch processing failed:', error)
      toast.error(error.message || 'Failed to process batch upload')
    } finally {
      setProcessing(false)
    }
  }

  // Download results
  const handleDownloadResults = () => {
    if (!results || !results.results) return

    // Format results for CSV
    const formattedResults = results.results.map((r: any) => ({
      transaction_id: r.transaction_id,
      risk_score: r.risk_score,
      risk_level: r.risk_level,
      decision: r.decision,
      flags_count: r.flags?.length || 0,
      recommendation: r.recommendation,
    }))

    exportToCSV(formattedResults, `fraud-check-results-${Date.now()}.csv`)
    toast.success('Results downloaded!')
  }

  // Reset
  const handleReset = () => {
    setFile(null)
    setResults(null)
    setProgress(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      {!results && (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center hover:border-purple-500/50 transition-all"
        >
          <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />

          <h3 className="text-lg font-semibold mb-2">Upload CSV File</h3>
          <p className="text-sm text-gray-400 mb-4">
            Drag and drop your CSV file here, or click to browse
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
          >
            Choose File
          </button>

          {file && (
            <div className="mt-4 flex items-center justify-center gap-2 text-sm">
              <FileText className="w-4 h-4 text-green-400" />
              <span className="text-green-400">{file.name}</span>
              <button
                onClick={handleReset}
                className="ml-2 p-1 hover:bg-white/10 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* CSV Format Help */}
          <div className="mt-6 text-left bg-white/5 rounded-lg p-4 text-xs">
            <p className="font-semibold mb-2">CSV Format Example:</p>
            <pre className="text-gray-400 overflow-x-auto">
              transaction_id,user_id,amount,transaction_type,device_id,ip_address
            </pre>
            <p className="text-gray-500 mt-2">
              * Maximum 100 transactions per batch
              <br />* Required fields: transaction_id, user_id, amount
            </p>
          </div>
        </div>
      )}

      {/* Processing */}
      {processing && (
        <div className="glass rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="font-semibold">Processing...</span>
            <span className="text-sm text-gray-400">{progress}%</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
            />
          </div>
        </div>
      )}

      {/* Results */}
      {results && results.summary && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="glass rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Batch Results</h3>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm transition-all"
              >
                Upload Another
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-sm text-gray-400 mb-1">Total Processed</p>
                <p className="text-2xl font-bold">{results.summary.total}</p>
              </div>
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <p className="text-sm text-red-400 mb-1">High Risk</p>
                <p className="text-2xl font-bold text-red-400">{results.summary.high_risk}</p>
              </div>
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                <p className="text-sm text-yellow-400 mb-1">Medium Risk</p>
                <p className="text-2xl font-bold text-yellow-400">{results.summary.medium_risk}</p>
              </div>
              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <p className="text-sm text-green-400 mb-1">Low Risk</p>
                <p className="text-2xl font-bold text-green-400">{results.summary.low_risk}</p>
              </div>
            </div>

            <button
              onClick={handleDownloadResults}
              className="w-full mt-4 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download Results (CSV)
            </button>
          </div>

          {/* Individual Results Preview */}
          <div className="glass rounded-lg p-6">
            <h4 className="font-semibold mb-4">Results Preview (First 5)</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {results.results.slice(0, 5).map((result: any, index: number) => (
                <div key={index} className="bg-white/5 rounded-lg p-3 flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-mono text-sm">{result.transaction_id}</p>
                    <p className="text-xs text-gray-400">Score: {result.risk_score}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs ${
                    result.risk_level === 'high' ? 'bg-red-500/20 text-red-400' :
                    result.risk_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>
                    {result.risk_level}
                  </span>
                </div>
              ))}
            </div>
            {results.results.length > 5 && (
              <p className="text-sm text-gray-400 text-center mt-3">
                + {results.results.length - 5} more (download CSV for full results)
              </p>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {file && !processing && !results && (
        <div className="flex justify-center">
          <button
            onClick={handleProcess}
            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all font-medium"
          >
            Process Batch
          </button>
        </div>
      )}
    </div>
  )
}
