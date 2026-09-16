import { BrowserRouter, Routes, Route } from 'react-router-dom'

function Home() {
  return <h1>Hello World</h1>
}

function Dashboard() {
  return <h1>Dashboard do Corretor</h1>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
