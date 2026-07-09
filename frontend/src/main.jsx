import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import Vineyard from './pages/Vineyard.jsx'
import Receipts from './pages/Receipts.jsx'
import RestorationFramework from './pages/RestorationFramework.jsx'
import Singularity from './pages/Singularity.jsx'
import Echosystem from './pages/Echosystem.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/vineyard" element={<Vineyard />} />
        <Route path="/receipts" element={<Receipts />} />
        <Route path="/restoration-framework" element={<RestorationFramework />} />
        <Route path="/singularity" element={<Singularity />} />
        <Route path="/echosystem" element={<Echosystem />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
