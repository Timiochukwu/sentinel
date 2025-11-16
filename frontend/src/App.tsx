import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { ErrorBoundary } from './components/ErrorBoundary'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import Login from './pages/Login'
import TestPlayground from './pages/TestPlayground'
import ConsortiumDashboard from './pages/ConsortiumDashboard'

function App() {
  // In production, check actual auth state
  const isAuthenticated = true

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AnimatePresence mode="wait">
          <Routes>
            <Route
              path="/login"
              element={isAuthenticated ? <Navigate to="/" /> : <Login />}
            />
            <Route
              path="/"
              element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/transactions"
              element={isAuthenticated ? <Transactions /> : <Navigate to="/login" />}
            />
            <Route
              path="/analytics"
              element={isAuthenticated ? <Analytics /> : <Navigate to="/login" />}
            />
            <Route
              path="/test"
              element={isAuthenticated ? <TestPlayground /> : <Navigate to="/login" />}
            />
            <Route
              path="/consortium"
              element={isAuthenticated ? <ConsortiumDashboard /> : <Navigate to="/login" />}
            />
            <Route
              path="/settings"
              element={isAuthenticated ? <Settings /> : <Navigate to="/login" />}
            />
          </Routes>
        </AnimatePresence>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
