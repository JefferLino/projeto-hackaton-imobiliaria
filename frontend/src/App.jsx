import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import CorretoresPage from './pages/CorretoresPage'
import ImoveisPage from './pages/ImoveisPage'
import PipelinePage from './pages/PipelinePage'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster richColors position="top-right" />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" />
            <Route path="/corretores" element={<CorretoresPage />} />
            <Route path="/imoveis" element={<ImoveisPage />} />
            <Route path="/dashboard" element={<PipelinePage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
