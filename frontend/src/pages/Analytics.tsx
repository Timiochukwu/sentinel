import { motion } from 'framer-motion'
import Layout from '../components/Layout'
import Background3D from '../components/Background3D'
import { TrendingUp, Target, Zap, Award } from 'lucide-react'

export default function Analytics() {
  return (
    <Layout>
      <Background3D />

      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">Analytics</h1>
          <p className="text-gray-400">Advanced fraud detection insights</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass rounded-2xl p-8 text-center"
          >
            <TrendingUp className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-2">Coming Soon</h3>
            <p className="text-gray-400">
              Advanced analytics and machine learning insights are being developed
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-2xl p-8 text-center"
          >
            <Target className="w-16 h-16 text-pink-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-2">Predictive Models</h3>
            <p className="text-gray-400">
              ML-powered predictions with 85%+ accuracy
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-2xl p-8 text-center"
          >
            <Zap className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-2">Real-time Alerts</h3>
            <p className="text-gray-400">
              Instant notifications for high-risk transactions
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-2xl p-8 text-center"
          >
            <Award className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-2">Performance Tracking</h3>
            <p className="text-gray-400">
              Monitor accuracy, precision, and recall metrics
            </p>
          </motion.div>
        </div>
      </div>
    </Layout>
  )
}
