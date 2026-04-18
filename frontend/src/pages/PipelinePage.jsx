import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'
import './PipelinePage.css'

const INITIAL_PIPELINE = [
  { id: 1, title: 'Ingestion & Structural Parsing', status: 'pending', node: 'phase1', time: '--', dispatch: null },
  { id: 2, title: 'Context-Aware Translation', status: 'pending', node: 'phase2', time: '--', dispatch: null },
  { id: 3, title: 'Localization & Butterfly Effect', status: 'pending', node: 'phase3', time: '--', dispatch: null },
  { id: 4, title: 'Visual Reconstruction', status: 'pending', node: 'phase4', time: '--', dispatch: null },
  { id: 5, title: 'Quality Assurance', status: 'pending', node: 'phase5', time: '--', dispatch: null },
]

export default function PipelinePage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [pipeline, setPipeline] = useState(INITIAL_PIPELINE)
  const [overallStatus, setOverallStatus] = useState("STARTING...")
  const [selectedPayload, setSelectedPayload] = useState(null)
  
  // Dữ liệu từ UploadPage
  const { threadId, pdfName = 'document.pdf', brief = 'No brief provided' } = location.state || {}

  useEffect(() => {
    if (!threadId) return

      const fetchStatus = async () => {
      try {
        const API_BASE = "https://yellow-hired-starter-peninsula.trycloudflare.com";
        const res = await fetch(`${API_BASE}/api/v1/pipeline/${threadId}`)
        if (!res.ok) return
        const data = await res.json()
        
        setOverallStatus(data.status)
        
        setPipeline(prev => {
          return prev.map((node, index) => {
            const phaseNum = index + 1
            let newStatus = 'pending'
            
            // Map logic
            if (data.status === 'ERROR') {
              newStatus = phaseNum === data.current_phase ? 'error' : prev[index].status
            } else if (phaseNum < data.current_phase) {
              newStatus = 'completed'
            } else if (phaseNum === data.current_phase) {
              if (data.status === 'PROCESSING') newStatus = 'processing'
              else if (data.status === 'COMPLETED') newStatus = 'completed'
              else newStatus = 'pending'
            }
            
            // Extract dispatch info
            let dispatch = prev[index].dispatch
            if (data.dispatch_info && data.dispatch_info[`phase_${phaseNum}`]) {
              dispatch = data.dispatch_info[`phase_${phaseNum}`]
            }

            return { ...node, status: newStatus, dispatch }
          })
        })

      } catch (err) {
        console.error("Polling error", err)
      }
    }

    fetchStatus() // immediate first call
    const timer = setInterval(fetchStatus, 2000)
    return () => clearInterval(timer)
  }, [threadId])

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--emerald)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
      case 'processing':
        return <div className="spinner"></div>
      default:
        return <div className="circle-pending"></div>
    }
  }

  return (
    <div className="pipeline-page">
      {/* ── Navbar ───────────────────────────────────────── */}
      <NavBar />

      <div className="pipeline-container">
        {/* ── Context Sidebar ────────────────────────────── */}
        <aside className="context-sidebar glass-card">
          <div className="sidebar-header">
            <h3>Pipeline Context</h3>
            <span className={`status-badge ${overallStatus === 'PROCESSING' ? 'running animate-pulse' : ''}`}>
              {overallStatus}
            </span>
          </div>
          
          <div className="context-section">
            <h4>Source Document</h4>
            <div className="file-pill">
              📄 {pdfName}
            </div>
          </div>
          
          <div className="context-section">
            <h4>Localization Brief</h4>
            <div className="brief-preview">
              {brief}
            </div>
          </div>
          
          <div className="context-section">
            <h4>Global Metadata</h4>
            <ul className="meta-list">
              <li><span className="meta-key">Source</span><span className="meta-val">English</span></li>
              <li><span className="meta-key">Target</span><span className="meta-val">Vietnamese</span></li>
              <li><span className="meta-key">Safety</span><span className="meta-val">Strict</span></li>
            </ul>
          </div>
        </aside>

        {/* ── Visual Graph (n8n style) ───────────────────── */}
        <main className="graph-board glass-card">
          <div className="board-header">
            <h2>Execution Graph</h2>
            <div className="board-actions">
              <button className="icon-btn" title="Zoom In"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" x2="16.65" y1="21" y2="16.65"/><line x1="11" x2="11" y1="8" y2="14"/><line x1="8" x2="14" y1="11" y2="11"/></svg></button>
              <button className="icon-btn" title="Zoom Out"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" x2="16.65" y1="21" y2="16.65"/><line x1="8" x2="14" y1="11" y2="11"/></svg></button>
            </div>
          </div>

          <div className="nodes-container">
            {pipeline.map((node, i) => (
              <div key={node.id} className="node-wrapper">
                <div className={`pipeline-node status-${node.status} animate-fade-in-up`} style={{ animationDelay: `${i * 0.1}s` }}>
                  <div className="node-header">
                    <span className="node-id">Phase {node.id}</span>
                    <div className="node-icon">{getStatusIcon(node.status)}</div>
                  </div>
                  <div className="node-body">
                    <h3 className="node-title">{node.title}</h3>
                    <div className="node-meta">
                      <span className="node-time">{node.time}</span>
                      <span className="node-type">LangGraph Node</span>
                    </div>
                    {node.dispatch && (
                      <div className="node-dispatch-info">
                        <div className="dispatch-url" title={node.dispatch.url}>
                          <strong>POST</strong> <code>{node.dispatch.url}</code>
                          <div className="url-note">*(Can be changed in <code>orchestrator/app/config.py</code>)*</div>
                        </div>
                        <div className="dispatch-payload-wrapper">
                          <pre className="dispatch-payload">
                            {JSON.stringify(node.dispatch.payload, null, 2)}
                          </pre>
                          <button className="view-payload-btn" onClick={() => setSelectedPayload(node.dispatch.payload)}>
                            View Payload Modal ↗
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  {/* Socket connectors */}
                  {i > 0 && <div className="socket-in"></div>}
                  {i < pipeline.length - 1 && <div className="socket-out"></div>}
                </div>
                
                {/* Connecting Line */}
                {i < pipeline.length - 1 && (
                  <div className={`connection-line ${pipeline[i+1].status !== 'pending' ? 'active' : ''}`}>
                    <svg height="40" width="100%">
                      <path d="M 0 20 L 100% 20" stroke="currentColor" strokeWidth="2" fill="none" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <div className="board-footer">
            <div className="legend">
              <span className="legend-item"><div className="circle-pending"></div> Pending</span>
              <span className="legend-item"><div className="spinner"></div> Processing</span>
              <span className="legend-item"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--emerald)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Completed</span>
            </div>
          </div>
        </main>
      </div>

      {/* ── Payload Modal ────────────────────────────────────── */}
      {selectedPayload && (
        <div className="payload-modal-overlay" onClick={() => setSelectedPayload(null)}>
          <div className="payload-modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>API Payload JSON</h2>
              <button className="close-btn" onClick={() => setSelectedPayload(null)}>✖</button>
            </div>
            <div className="modal-body">
              <pre>{JSON.stringify(selectedPayload, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
