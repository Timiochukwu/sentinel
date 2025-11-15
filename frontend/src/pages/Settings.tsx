import { useState } from 'react'
import { motion } from 'framer-motion'
import { Key, Webhook, Bell, Shield, Save } from 'lucide-react'
import Layout from '../components/Layout'
import Background3D from '../components/Background3D'

export default function Settings() {
  const [apiKey, setApiKey] = useState('sk_live_********************************')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [mlEnabled, setMlEnabled] = useState(true)

  const handleSave = () => {
    // Save settings logic
    alert('Settings saved successfully!')
  }

  return (
    <Layout>
      <Background3D />

      <div className="space-y-8 max-w-4xl">
        <div>
          <h1 className="text-4xl font-bold text-gradient mb-2">Settings</h1>
          <p className="text-gray-400">Configure your fraud detection platform</p>
        </div>

        <div className="space-y-6">
          {/* API Key */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Key className="w-6 h-6 text-purple-400" />
              <h3 className="text-xl font-bold">API Key</h3>
            </div>
            <p className="text-sm text-gray-400 mb-4">
              Your API key for authenticating requests
            </p>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-4 py-3 glass-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono"
              readOnly
            />
          </motion.div>

          {/* Webhook Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Webhook className="w-6 h-6 text-purple-400" />
              <h3 className="text-xl font-bold">Webhook URL</h3>
            </div>
            <p className="text-sm text-gray-400 mb-4">
              Receive real-time notifications for high-risk transactions
            </p>
            <input
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://your-app.com/webhooks/sentinel"
              className="w-full px-4 py-3 glass-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </motion.div>

          {/* ML Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-6 h-6 text-purple-400" />
              <h3 className="text-xl font-bold">Machine Learning</h3>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium mb-1">Enable ML Predictions</p>
                <p className="text-sm text-gray-400">
                  Use machine learning for 85%+ accuracy
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={mlEnabled}
                  onChange={(e) => setMlEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-14 h-7 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>
          </motion.div>

          {/* Notifications */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-2xl p-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <Bell className="w-6 h-6 text-purple-400" />
              <h3 className="text-xl font-bold">Notifications</h3>
            </div>
            <div className="space-y-4">
              {['High Risk Transactions', 'Fraud Confirmed', 'Daily Summary'].map((item) => (
                <div key={item} className="flex items-center justify-between">
                  <span className="text-gray-300">{item}</span>
                  <input type="checkbox" defaultChecked className="w-5 h-5 rounded accent-purple-500" />
                </div>
              ))}
            </div>
          </motion.div>

          {/* Save Button */}
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-xl font-bold flex items-center justify-center gap-3 hover:shadow-lg hover:shadow-purple-500/50 transition-all"
          >
            <Save className="w-5 h-5" />
            Save Settings
          </motion.button>
        </div>
      </div>
    </Layout>
  )
}
