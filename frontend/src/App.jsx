import { BrowserRouter, Routes, Route } from 'react-router-dom'
import CorretoresPage from './pages/CorretoresPage'

function Dashboard() {
  return <h1>Dashboard do Corretor</h1>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<CorretoresPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
