import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage.jsx'
import UploadPage from './pages/UploadPage.jsx'
import PipelinePage from './pages/PipelinePage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/pipeline" element={<PipelinePage />} />
    </Routes>
  )
}
