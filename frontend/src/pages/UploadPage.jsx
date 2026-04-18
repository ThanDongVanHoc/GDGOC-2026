import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import NavBar from '../components/NavBar'

/* ── Icon component (same as LandingPage) ── */
function Icon({ name, className = '', filled = false }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={{
        fontFamily: "'Material Symbols Outlined'",
        fontVariationSettings: filled
          ? "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24"
          : "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24",
        WebkitFontSmoothing: 'antialiased',
      }}
    >
      {name}
    </span>
  )
}

/* ── Live log entry ── */
function LogLine({ time, level, msg }) {
  const colors = {
    INFO: 'text-on-surface',
    EXEC: 'text-primary',
    WARN: 'text-error',
    HOOK: 'text-error',
    DONE: 'text-[#6ee7b7]',
  }
  return (
    <div className="flex items-start gap-2">
      <span className="text-outline shrink-0">[{time}]</span>
      <span className={`font-bold shrink-0 ${colors[level] || 'text-on-surface-variant'}`}>{level}:</span>
      <span className="text-on-surface-variant/80">{msg}</span>
    </div>
  )
}

/* ── Pipeline node states ── */
const NODES_IDLE = [
  { id: 'p1', label: 'Ingestion', sub: 'Orchestrator Agent', icon: 'hub',        status: 'idle' },
  { id: 'p2', label: 'Translation', sub: 'Translator + Reviser', icon: 'translate', status: 'idle' },
  { id: 'p3', label: 'Localization', sub: 'Loc. + Council', icon: 'psychology',  status: 'idle' },
  { id: 'p4', label: 'Typesetting', sub: 'Layout + Vision', icon: 'view_quilt',  status: 'idle' },
  { id: 'p5', label: 'Final QA', sub: 'QA Agent (VLM)', icon: 'fact_check',   status: 'idle' },
]

export default function UploadPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const logsEndRef = useRef(null)

  const [pdfFile, setPdfFile] = useState(null)
  const [brief, setBrief] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  /* Idle animated log lines shown before launch */
  const idleLogs = [
    { time: '--:--:--', level: 'INFO', msg: 'OmniLocal workspace ready. Upload a PDF to begin.' },
    { time: '--:--:--', level: 'INFO', msg: 'System: All 5 agents on standby.' },
  ]
  const [logs, setLogs] = useState(idleLogs)

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const addLog = (level, msg) => {
    const now = new Date()
    const time = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`
    setLogs(prev => [...prev, { time, level, msg }])
  }

  /* ── Drag & Drop ── */
  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation()
    setDragActive(e.type === 'dragenter' || e.type === 'dragover')
  }
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) { setPdfFile(file); addLog('INFO', `File loaded: ${file.name} (${formatSize(file.size)})`) }
  }
  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) { setPdfFile(file); addLog('INFO', `File loaded: ${file.name} (${formatSize(file.size)})`) }
  }

  /* ── Submit ── */
  const handleSubmit = async () => {
    if (!pdfFile) { addLog('WARN', 'No PDF file selected. Please upload a source file.'); return }
    if (!brief.trim()) { addLog('WARN', 'Localization brief is empty. Please describe your target parameters.'); return }

    setIsUploading(true)
    addLog('EXEC', `Launching pipeline for: ${pdfFile.name}`)
    addLog('INFO', 'Sending payload to Orchestrator Agent...')

    try {
      const formData = new FormData()
      formData.append('file', pdfFile)
      formData.append('brief', brief)

      const API_BASE = "https://strips-proxy-medicines-perfect.trycloudflare.com";
      const response = await fetch(`${API_BASE}/api/v1/pipeline/upload-and-start`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data = await response.json()
      addLog('DONE', `Pipeline started. Thread ID: ${data.thread_id}`)
      addLog('INFO', 'Redirecting to Live Execution Graph...')

      setTimeout(() => {
        navigate('/pipeline', {
          state: { threadId: data.thread_id, pdfName: pdfFile.name, brief }
        })
      }, 800)
    } catch (err) {
      console.error(err)
      addLog('WARN', `Failed to start pipeline: ${err.message}. Is the backend running?`)
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
    <div className="bg-surface text-on-surface font-body min-h-screen flex flex-col antialiased dark selection:bg-primary-container selection:text-on-primary-container" style={{ fontFamily: 'Inter' }}>

      {/* ── TopNavBar ── */}
      <NavBar />

      {/* ── Main Workspace ── */}
      <main className="flex-1 flex overflow-hidden" style={{ height: 'calc(100vh - 73px)' }}>

        {/* ── Left Column: Setup Panel (30%) ── */}
        <aside className="w-[30%] min-w-[300px] max-w-[420px] bg-surface-container-low flex flex-col border-r border-outline-variant/15 overflow-y-auto">
          <div className="p-6 flex flex-col h-full gap-6">

            {/* Header */}
            <div>
              <h1 className="font-headline text-lg font-bold tracking-tight text-on-surface mb-1">Setup Panel</h1>
              <p className="text-sm text-on-surface-variant">Configure your localization workflow.</p>
            </div>

            {/* Upload Area */}
            <div className="flex flex-col gap-3">
              <label className="text-sm font-semibold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>
                Source Material
                <span className="ml-2 font-mono text-[10px] text-on-surface-variant/50 normal-case">PDF only</span>
              </label>

              <div
                className={`border border-dashed rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 group relative
                  ${dragActive
                    ? 'border-primary bg-primary/5 shadow-[0_0_24px_rgba(255,87,27,0.1)]'
                    : pdfFile
                      ? 'border-primary/40 bg-surface-container-high'
                      : 'border-outline-variant/30 bg-surface-container hover:bg-surface-container-high hover:border-outline-variant/60'
                  }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileChange} hidden />

                {pdfFile ? (
                  <div className="flex flex-col items-center gap-3 w-full">
                    <div className="w-10 h-10 rounded-xl bg-primary/15 flex items-center justify-center border border-primary/30">
                      <Icon name="description" className="text-primary" />
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-medium text-on-surface truncate max-w-[220px]">{pdfFile.name}</p>
                      <p className="font-mono text-xs text-on-surface-variant mt-1">{formatSize(pdfFile.size)}</p>
                    </div>
                    <button
                      className="mt-1 text-xs text-on-surface-variant/60 hover:text-error transition-colors flex items-center gap-1"
                      onClick={(e) => { e.stopPropagation(); setPdfFile(null); addLog('INFO', 'File cleared.') }}
                    >
                      <Icon name="close" className="text-sm" />
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-2 text-center">
                    <Icon name="upload_file" className="text-outline group-hover:text-primary transition-colors text-4xl mb-1" />
                    <p className="text-sm font-medium text-on-surface">Click to upload or drag files</p>
                    <p className="text-xs text-on-surface-variant">PDF files · Max 50MB</p>
                  </div>
                )}
              </div>
            </div>

            {/* Localization Brief — IDE Style */}
            <div className="flex flex-col gap-3 flex-1 min-h-[200px]">
              <div className="flex justify-between items-end">
                <label className="text-sm font-semibold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>Localization Brief</label>
                <span className="font-mono text-[10px] text-on-surface-variant">yaml</span>
              </div>

              <div className="bg-surface-container-lowest rounded-lg border border-outline-variant/15 flex-1 flex flex-col focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary/30 transition-all">
                {/* Fake line number header */}
                <div className="flex text-[10px] font-mono text-outline-variant/60 px-3 py-2 border-b border-outline-variant/10 bg-surface-container-low/50 rounded-t-lg shrink-0">
                  <span className="mr-4 select-none">1</span>
                  <span className="text-on-surface-variant/40">// Define your localization parameters</span>
                </div>
                <textarea
                  className="w-full flex-1 bg-transparent border-none outline-none text-sm font-mono text-on-surface p-4 resize-none placeholder:text-on-surface-variant/30"
                  style={{ fontFamily: 'JetBrains Mono' }}
                  placeholder={`target_locale: vi_VN\ntone: friendly\npreserve_names: true\nage_group: "8-12"\nno_taboos: true\nnotes: >\n  Localize for Vietnamese highland\n  children. Replace foreign scenes\n  with local cultural equivalents.`}
                  value={brief}
                  onChange={(e) => setBrief(e.target.value)}
                />
              </div>
              <div className="flex justify-between items-center text-[10px] font-mono text-on-surface-variant/40">
                <span>{brief.split('\n').length} lines</span>
                <span>{brief.length} chars</span>
              </div>
            </div>

            {/* Pipeline Progress — shows idle phases */}
            <div className="flex flex-col gap-2 border-t border-outline-variant/10 pt-4">
              <span className="text-[10px] font-mono text-on-surface-variant/50 uppercase tracking-widest mb-1">Pipeline Status</span>
              {NODES_IDLE.map((node) => (
                <div key={node.id} className="flex items-center gap-3 py-1.5">
                  <div className="w-6 h-6 rounded bg-surface-container-high flex items-center justify-center shrink-0">
                    <Icon name={node.icon} className="text-outline-variant" style={{ fontSize: '14px' }} />
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-medium text-on-surface">{node.label}</div>
                    <div className="font-mono text-[9px] text-on-surface-variant/50 uppercase tracking-wider">{node.sub}</div>
                  </div>
                  <span className="font-mono text-[9px] text-on-surface-variant/40 uppercase">Idle</span>
                </div>
              ))}
            </div>

            {/* Launch Button */}
            <button
              className="mt-auto w-full bg-gradient-to-r from-primary to-primary-container text-on-primary py-3.5 rounded-lg font-bold tracking-wide hover:opacity-90 hover:shadow-[0_0_32px_rgba(255,87,27,0.3)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,87,27,0.15)] disabled:opacity-50"
              onClick={handleSubmit}
              disabled={isUploading}
            >
              <Icon name={isUploading ? 'sync' : 'rocket_launch'} className={isUploading ? 'text-lg animate-spin' : 'text-lg'} />
              {isUploading ? 'Initializing Pipeline...' : 'Launch Supply Chain'}
            </button>

          </div>
        </aside>

        {/* ── Right Column: Live Execution Graph (70%) ── */}
        <section className="flex-1 bg-surface flex flex-col overflow-hidden">

          {/* Graph Header */}
          <div className="px-8 py-5 flex justify-between items-center bg-surface-container-low/80 backdrop-blur-md border-b border-outline-variant/10 shrink-0">
            <div className="flex items-center gap-4">
              <h2 className="font-headline text-base font-bold tracking-tight text-on-surface">Live Execution Graph</h2>
              <span className="bg-surface-container-highest text-on-surface-variant font-mono text-[10px] px-2.5 py-1 rounded border border-outline-variant/20 flex items-center gap-2 uppercase tracking-wider">
                <span className="w-1.5 h-1.5 rounded-full bg-on-surface-variant/40"></span>
                Awaiting Launch
              </span>
            </div>
            <div className="flex gap-2">
              {['zoom_in', 'zoom_out', 'fit_screen', 'settings'].map(icon => (
                <button key={icon} className="p-2 bg-surface-container hover:bg-surface-container-high rounded transition-colors text-on-surface-variant border border-outline-variant/15">
                  <Icon name={icon} className="text-sm" style={{ fontSize: '16px' }} />
                </button>
              ))}
            </div>
          </div>

          {/* Graph Canvas */}
          <div className="flex-1 relative overflow-hidden flex flex-col">
            <div className="flex-1 relative p-8 flex items-center justify-center overflow-auto bg-[radial-gradient(ellipse_at_center,_#201f1f_0%,_#131313_100%)]">
              {/* Dot grid texture */}
              <div className="absolute inset-0 pointer-events-none" style={{
                backgroundSize: '40px 40px',
                backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.025) 1px, transparent 1px)'
              }}></div>

              {/* Node canvas */}
              <div className="relative w-full" style={{ height: '480px' }}>

                {/* SVG connection lines */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 800 480" preserveAspectRatio="xMidYMid meet" style={{ zIndex: 0 }}>
                  {/* P1 → P2 */}
                  <path d="M 130 240 L 260 140" fill="none" stroke="#353534" strokeWidth="1.5" />
                  {/* P2 → P3 */}
                  <path d="M 390 140 L 490 240" fill="none" stroke="#353534" strokeWidth="1.5" />
                  {/* P2 → P5 (dashed, down) */}
                  <path d="M 390 160 L 390 360" fill="none" stroke="#353534" strokeDasharray="5 5" strokeWidth="1.5" />
                  {/* P3 → P4 */}
                  <path d="M 620 240 L 620 360" fill="none" stroke="#353534" strokeWidth="1.5" />
                  {/* P4 → P5 */}
                  <path d="M 555 400 L 450 400" fill="none" stroke="#353534" strokeWidth="1.5" />
                  {/* Feedback loop arc: P4 back to P3 */}
                  <path d="M 620 395 C 710 395, 710 240, 620 240" fill="none" stroke="#5c4038" strokeDasharray="6 6" strokeWidth="1.5" />
                  <circle cx="680" cy="318" r="3" fill="#5c4038" />
                  <text x="688" y="322" fill="#5c4038" fontSize="9" fontFamily="JetBrains Mono">feedback</text>
                </svg>

                {/* Phase 1: Ingestion */}
                <div className="absolute" style={{ top: '208px', left: '0%', width: '150px', zIndex: 10 }}>
                  <div className="bg-surface-container-highest border border-outline-variant/20 rounded-lg p-3 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="w-6 h-6 rounded bg-surface-container-lowest flex items-center justify-center shrink-0">
                        <Icon name="hub" className="text-outline-variant" style={{ fontSize: '14px' }} />
                      </div>
                      <span className="text-xs font-semibold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>P1: Ingestion</span>
                    </div>
                    <div className="font-mono text-[9px] text-on-surface-variant/60 uppercase tracking-wider">Orchestrator · Idle</div>
                  </div>
                </div>

                {/* Phase 2: Translation */}
                <div className="absolute" style={{ top: '104px', left: '27%', width: '155px', zIndex: 10 }}>
                  <div className="bg-surface-container-highest border border-outline-variant/20 rounded-lg p-3 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="w-6 h-6 rounded bg-surface-container-lowest flex items-center justify-center shrink-0">
                        <Icon name="translate" className="text-outline-variant" style={{ fontSize: '14px' }} />
                      </div>
                      <span className="text-xs font-semibold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>P2: Translation</span>
                    </div>
                    <div className="font-mono text-[9px] text-on-surface-variant/60 uppercase tracking-wider">Translator + Reviser · Idle</div>
                  </div>
                </div>

                {/* Phase 3: Localization — Active style */}
                <div className="absolute" style={{ top: '205px', left: '55%', width: '160px', zIndex: 10 }}>
                  <div className="bg-surface-container-high border border-primary/30 rounded-lg p-3 shadow-[0_0_24px_rgba(255,87,27,0.12)] relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-primary rounded-l-lg"></div>
                    <div className="flex items-center gap-2 mb-1.5 pl-2">
                      <div className="w-6 h-6 rounded bg-primary/10 flex items-center justify-center shrink-0">
                        <Icon name="psychology" className="text-primary" filled style={{ fontSize: '14px' }} />
                      </div>
                      <span className="text-xs font-semibold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>P3: Localization</span>
                    </div>
                    <div className="font-mono text-[9px] text-on-surface-variant/60 uppercase tracking-wider pl-2">Council Agent · Idle</div>
                  </div>
                </div>

                {/* Phase 4: Typesetting */}
                <div className="absolute" style={{ top: '360px', left: '55%', width: '160px', zIndex: 10 }}>
                  <div className="bg-surface-container border border-outline-variant/20 rounded-lg p-3 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="w-6 h-6 rounded bg-surface-container-lowest flex items-center justify-center shrink-0">
                        <Icon name="view_quilt" className="text-outline-variant" style={{ fontSize: '14px' }} />
                      </div>
                      <span className="text-xs font-semibold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>P4: Typesetting</span>
                    </div>
                    <div className="font-mono text-[9px] text-on-surface-variant/60 uppercase tracking-wider">Layout + Vision · Idle</div>
                  </div>
                </div>

                {/* Phase 5: Final QA — dimmed */}
                <div className="absolute" style={{ top: '375px', left: '29%', width: '155px', zIndex: 10 }}>
                  <div className="bg-surface-container-low border border-outline-variant/15 rounded-lg p-3 opacity-55">
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="w-6 h-6 rounded bg-surface-container-lowest flex items-center justify-center shrink-0">
                        <Icon name="fact_check" className="text-outline-variant" style={{ fontSize: '14px' }} />
                      </div>
                      <span className="text-xs font-semibold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>P5: Final QA</span>
                    </div>
                    <div className="font-mono text-[9px] text-on-surface-variant/50 uppercase tracking-wider">QA Agent (VLM) · Waiting</div>
                  </div>
                </div>

                {/* Idle overlay */}
                {!isUploading && (
                  <div className="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
                    <div className="bg-surface/60 backdrop-blur-sm rounded-2xl px-8 py-5 text-center border border-outline-variant/15">
                      <Icon name="rocket_launch" className="text-on-surface-variant/40 text-4xl mb-2 block mx-auto" />
                      <p className="font-mono text-xs text-on-surface-variant/50 uppercase tracking-widest">Upload a PDF and click Launch</p>
                    </div>
                  </div>
                )}

                {/* Legend */}
                <div className="absolute bottom-3 left-3 flex items-center gap-4 z-10">
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-on-surface-variant/50">
                    <span className="w-2 h-2 rounded-full bg-primary/40 border border-primary/60"></span>Active
                  </div>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-on-surface-variant/50">
                    <span className="w-2 h-2 rounded-full bg-surface-container-highest border border-outline-variant/30"></span>Idle
                  </div>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-on-surface-variant/50">
                    <span className="w-2 h-2 rounded-full bg-surface-container-low border border-outline-variant/20 opacity-50"></span>Waiting
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Live Log Terminal */}
            <div className="bg-surface-container-lowest border-t border-outline-variant/15 flex flex-col shrink-0" style={{ height: '180px' }}>
              <div className="px-4 py-2.5 border-b border-outline-variant/10 bg-surface-container/50 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-on-surface-variant uppercase tracking-widest" style={{ fontFamily: 'Space Grotesk' }}>System Logs</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-on-surface-variant/30 animate-pulse"></span>
                </div>
                <button
                  className="text-on-surface-variant/50 hover:text-on-surface text-[10px] font-mono transition-colors"
                  onClick={() => setLogs(idleLogs)}
                >
                  Clear
                </button>
              </div>
              <div className="flex-1 p-4 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-1">
                {logs.map((log, i) => (
                  <LogLine key={i} {...log} />
                ))}
                <div ref={logsEndRef} />
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
