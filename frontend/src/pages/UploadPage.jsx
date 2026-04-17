import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import './UploadPage.css'

export default function UploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [pdfFile, setPdfFile] = useState(null)
  const [brief, setBrief] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file && file.type === 'application/pdf') setPdfFile(file)
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) setPdfFile(file)
  }

  const [isUploading, setIsUploading] = useState(false)

  const handleSubmit = async () => {
    if (!pdfFile || !brief) {
      alert("Please upload a PDF and write a brief.")
      return
    }

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append("file", pdfFile)
      formData.append("brief", brief)

      const response = await fetch("/api/v1/pipeline/upload-and-start", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }

      const data = await response.json()
      
      // Navigate to pipeline view with real thread_id
      navigate('/pipeline', {
        state: {
          threadId: data.thread_id,
          pdfName: pdfFile.name,
          brief: brief,
        }
      })
    } catch (err) {
      console.error(err)
      alert("Failed to start pipeline. Is the backend running?")
    } finally {
      setIsUploading(false)
    }
  }

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="upload-page">
      {/* Navbar */}
      <nav className="navbar">
        <a href="/" className="navbar-brand" onClick={(e) => { e.preventDefault(); navigate('/') }}>
          <div className="logo-icon">🌏</div>
          <span className="gradient-text">OmniLocal</span>
        </a>
        <div className="navbar-actions">
          <button className="btn btn-ghost" onClick={() => navigate('/')}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
            Back
          </button>
        </div>
      </nav>

      <div className="upload-container">
        <div className="upload-header animate-fade-in-up">
          <span className="section-tag">New Pipeline</span>
          <h1>Upload Your Book</h1>
          <p>Upload a source PDF and describe your localization brief to begin.</p>
        </div>

        <div className="upload-grid">
          {/* PDF Upload */}
          <div className="upload-card glass-card animate-fade-in-up animate-delay-1">
            <div className="card-header">
              <div className="card-icon" style={{ background: 'rgba(99, 102, 241, 0.1)', color: '#818cf8' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div>
                <h3>Source PDF</h3>
                <p className="card-desc">The original book file to localize</p>
              </div>
            </div>

            <div
              className={`drop-zone ${dragActive ? 'drag-active' : ''} ${pdfFile ? 'has-file' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                hidden
              />

              {pdfFile ? (
                <div className="file-info">
                  <div className="file-icon">📄</div>
                  <div className="file-details">
                    <span className="file-name">{pdfFile.name}</span>
                    <span className="file-size">{formatSize(pdfFile.size)}</span>
                  </div>
                  <button className="file-remove" onClick={(e) => { e.stopPropagation(); setPdfFile(null) }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                  </button>
                </div>
              ) : (
                <div className="drop-placeholder">
                  <div className="drop-icon">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                  </div>
                  <p><strong>Click to upload</strong> or drag and drop</p>
                  <span className="drop-hint">PDF files only</span>
                </div>
              )}
            </div>
          </div>

          {/* Brief Input */}
          <div className="upload-card glass-card animate-fade-in-up animate-delay-2">
            <div className="card-header">
              <div className="card-icon" style={{ background: 'rgba(168, 85, 247, 0.1)', color: '#c084fc' }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
              </div>
              <div>
                <h3>Localization Brief</h3>
                <p className="card-desc">Describe target audience, rules, and constraints</p>
              </div>
            </div>

            <textarea
              className="brief-input"
              placeholder="e.g., Localize this children's book for the Vietnamese market. Preserve character names (Harry, Luna). Target age: 8-12. Tone: friendly, engaging. No cultural taboos. Keep SFX untranslated..."
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              rows={8}
            />

            <div className="brief-footer">
              <span className="char-count">{brief.length} characters</span>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="upload-submit animate-fade-in-up animate-delay-3">
          <button
            className="btn btn-primary btn-lg submit-btn"
            onClick={handleSubmit}
            id="submit-pipeline"
            disabled={isUploading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            {isUploading ? "Uploading..." : "Launch Pipeline"}
          </button>
          <p className="submit-hint">This will start the 5-phase localization pipeline</p>
        </div>
      </div>
    </div>
  )
}
