import { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, Mail, Lock, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Background3D from '../components/Background3D'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    // In production, handle actual authentication
    navigate('/')
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Background3D />

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="glass rounded-3xl p-8 lg:p-12">
          {/* Logo */}
          <div className="flex items-center justify-center mb-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <Shield className="w-16 h-16 text-purple-400" />
            </motion.div>
          </div>

          {/* Title */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gradient mb-2">Welcome to Sentinel</h1>
            <p className="text-gray-400">Nigerian Fraud Detection Platform</p>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-12 pr-4 py-3 glass-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-12 pr-4 py-3 glass-dark rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center">
                <input type="checkbox" className="w-4 h-4 rounded accent-purple-500 mr-2" />
                <span className="text-gray-400">Remember me</span>
              </label>
              <a href="#" className="text-purple-400 hover:text-purple-300">
                Forgot password?
              </a>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-xl font-bold flex items-center justify-center gap-3 hover:shadow-lg hover:shadow-purple-500/50 transition-all"
            >
              Sign In
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-400">
              Don't have an account?{' '}
              <a href="#" className="text-purple-400 hover:text-purple-300 font-medium">
                Contact Sales
              </a>
            </p>
          </div>
        </div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-3 gap-4 mt-8"
        >
          <div className="text-center glass rounded-xl p-4">
            <p className="text-2xl font-bold text-gradient">85%+</p>
            <p className="text-xs text-gray-400">Accuracy</p>
          </div>
          <div className="text-center glass rounded-xl p-4">
            <p className="text-2xl font-bold text-gradient">&lt;100ms</p>
            <p className="text-xs text-gray-400">Response</p>
          </div>
          <div className="text-center glass rounded-xl p-4">
            <p className="text-2xl font-bold text-gradient">₦50B+</p>
            <p className="text-xs text-gray-400">Prevented</p>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
