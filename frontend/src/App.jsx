import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage.jsx'
import UploadPage from './pages/UploadPage.jsx'
import PipelinePage from './pages/PipelinePage.jsx'
import AboutPage from './pages/AboutPage.jsx'
import BlogPage from './pages/BlogPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/pipeline" element={<PipelinePage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/blog" element={<BlogPage />} />
    </Routes>
  )
}
