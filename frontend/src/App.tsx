import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import { useAuthStore } from './store/authStore'

// Components
import LoginPage from './features/auth/LoginPage'
import Dashboard from './features/dashboard/Dashboard'
import StudyList from './features/studies/StudyList'
import StudyDetail from './features/studies/StudyDetail'
import Worksheet from './features/worksheet/Worksheet'
import Reports from './features/reports/Reports'
import Settings from './features/settings/Settings'

const { Header, Content } = Layout

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isAuthenticated && (
        <Header style={{ display: 'flex', alignItems: 'center', color: '#fff' }}>
          <div style={{ fontSize: 18, fontWeight: 'bold', marginRight: 40 }}>
            EHAZOP Platform
          </div>
        </Header>
      )}
      <Content style={{ padding: '0 50px', marginTop: isAuthenticated ? 64 : 0 }}>
        <Routes>
          <Route 
            path="/login" 
            element={isAuthenticated ? <Navigate to="/" /> : <LoginPage />} 
          />
          <Route 
            path="/" 
            element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/studies" 
            element={isAuthenticated ? <StudyList /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/studies/:studyId" 
            element={isAuthenticated ? <StudyDetail /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/studies/:studyId/worksheet" 
            element={isAuthenticated ? <Worksheet /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/studies/:studyId/reports" 
            element={isAuthenticated ? <Reports /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/settings" 
            element={isAuthenticated ? <Settings /> : <Navigate to="/login" />} 
          />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App