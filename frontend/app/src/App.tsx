import { AuthProvider } from './AuthContext'
import LoginPage from './LoginPage'
import Dashboard from './Dashboard'
import { useAuth } from './AuthContext'

function AppContent() {
  const { session } = useAuth()
  return session ? <Dashboard /> : <LoginPage />
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}