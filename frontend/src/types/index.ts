export interface DashboardStats {
  today_transactions: number
  today_high_risk: number
  today_medium_risk: number
  today_low_risk: number
  today_fraud_prevented_amount: number
  month_transactions: number
  month_fraud_caught: number
  month_fraud_prevented_amount: number
  month_false_positive_rate: number
  month_accuracy: number
  risk_distribution: {
    low: number
    medium: number
    high: number
  }
  fraud_types: Record<string, number>
}

export interface Transaction {
  transaction_id: string
  amount: number
  risk_score: number
  risk_level: 'low' | 'medium' | 'high'
  decision: 'approve' | 'review' | 'decline'
  outcome?: 'fraud' | 'legitimate' | 'pending'
  created_at: string
}

export interface FraudFlag {
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  score: number
  confidence?: number
  metadata?: any
}

export interface TransactionDetail extends Transaction {
  user_id: string
  transaction_type: string
  flags: FraudFlag[]
  recommendation?: string
  processing_time_ms: number
  consortium_alerts?: string[]
}

export interface ClientInfo {
  client_id: string
  company_name: string
  plan: string
  status: string
  total_checks: number
  total_fraud_caught: number
  total_amount_saved: number
  created_at: string
}

export interface RuleAccuracy {
  rule_name: string
  triggered_count: number
  accuracy: number
  precision: number
  recall: number
  current_weight: number
}
