import { useNavigate } from 'react-router-dom'
import './LandingPage.css'

const FEATURES = [
  {
    icon: '📖',
    title: 'Structural Parsing',
    desc: 'AI-powered ingestion that understands book layouts, fonts, and text hierarchy.',
    phase: 'Phase 1',
    color: '#6366f1',
  },
  {
    icon: '🌐',
    title: 'Context-Aware Translation',
    desc: 'LLM-driven translation that preserves meaning, tone, and literary style.',
    phase: 'Phase 2',
    color: '#a855f7',
  },
  {
    icon: '🦋',
    title: 'Butterfly Effect Guard',
    desc: 'Detects cascading inconsistencies across chapters before they propagate.',
    phase: 'Phase 3',
    color: '#22d3ee',
  },
  {
    icon: '🎨',
    title: 'Visual Reconstruction',
    desc: 'Inpaints and composites text onto original layouts with pixel-perfect precision.',
    phase: 'Phase 4',
    color: '#34d399',
  },
  {
    icon: '✅',
    title: 'Quality Assurance',
    desc: 'Automated QA with feedback loops that catch errors humans might miss.',
    phase: 'Phase 5',
    color: '#fbbf24',
  },
]

const STATS = [
  { value: '5', label: 'AI Phases' },
  { value: '∞', label: 'Languages' },
  { value: '<2', label: 'QA Loops' },
  { value: '0', label: 'Manual Steps' },
]

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="landing">
      {/* ── Navbar ─────────────────────────────────────── */}
      <nav className="navbar">
        <a href="/" className="navbar-brand">
          <div className="logo-icon">🌏</div>
          <span className="gradient-text">OmniLocal</span>
        </a>
        <ul className="navbar-links">
          <li><a href="#features">Features</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="https://github.com/ThanDongVanHoc/GDGOC-2026" target="_blank" rel="noopener">GitHub</a></li>
        </ul>
        <div className="navbar-actions">
          <button className="btn btn-primary" onClick={() => navigate('/upload')}>
            Try It
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
          </button>
        </div>
      </nav>

      {/* ── Hero Section ──────────────────────────────── */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-orb hero-orb-1"></div>
          <div className="hero-orb hero-orb-2"></div>
          <div className="hero-orb hero-orb-3"></div>
          <div className="hero-grid"></div>
        </div>

        <div className="hero-content">
          <div className="hero-badge animate-fade-in-up">
            <span className="badge-dot"></span>
            GDGoC 2026 — AI Innovation Challenge
          </div>

          <h1 className="hero-title animate-fade-in-up animate-delay-1">
            Cross-Cultural Book
            <br />
            <span className="gradient-text">Localization Pipeline</span>
          </h1>

          <p className="hero-subtitle animate-fade-in-up animate-delay-2">
            Transform books across languages and cultures with a 5-phase AI pipeline.
            <br />
            Powered by LangGraph orchestration, built for production.
          </p>

          <div className="hero-actions animate-fade-in-up animate-delay-3">
            <button className="btn btn-primary btn-lg" id="cta-try" onClick={() => navigate('/upload')}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Start Localizing
            </button>
            <button className="btn btn-outline btn-lg" onClick={() => navigate('/pipeline')}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m-7-7h6m6 0h6"/></svg>
              View Pipeline
            </button>
          </div>

          <div className="hero-stats animate-fade-in-up animate-delay-4">
            {STATS.map((s, i) => (
              <div key={i} className="stat-item">
                <span className="stat-value">{s.value}</span>
                <span className="stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────── */}
      <section className="features" id="features">
        <div className="section-header">
          <span className="section-tag">Features</span>
          <h2>Five Phases, One Pipeline</h2>
          <p>Each phase is a specialized microservice orchestrated by LangGraph.</p>
        </div>

        <div className="features-grid">
          {FEATURES.map((f, i) => (
            <div
              key={i}
              className="feature-card glass-card"
              style={{ '--card-accent': f.color }}
            >
              <div className="feature-icon">{f.icon}</div>
              <span className="feature-phase" style={{ color: f.color }}>{f.phase}</span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ──────────────────────────────── */}
      <section className="how-it-works" id="how-it-works">
        <div className="section-header">
          <span className="section-tag">Architecture</span>
          <h2>How It Works</h2>
          <p>Orchestrated by LangGraph with interrupt/resume pattern for async processing.</p>
        </div>

        <div className="arch-flow">
          {['Upload PDF', 'Phase 1\nIngestion', 'Phase 2\nTranslation', 'Phase 3\nLocalization', 'Phase 4\nVisual', 'Phase 5\nQA', 'Done ✅'].map((label, i) => (
            <div key={i} className="arch-step">
              <div className="arch-node" style={{
                background: i === 0 ? 'var(--bg-elevated)' :
                  i === 6 ? 'linear-gradient(135deg, #34d399, #22d3ee)' :
                  `linear-gradient(135deg, ${FEATURES[i-1]?.color || '#6366f1'}22, ${FEATURES[i-1]?.color || '#6366f1'}44)`,
                borderColor: i === 0 ? 'var(--border-hover)' :
                  i === 6 ? '#34d399' :
                  FEATURES[i-1]?.color || 'var(--border)',
              }}>
                <span className="arch-label">{label}</span>
              </div>
              {i < 6 && (
                <div className="arch-arrow">
                  <svg width="32" height="16" viewBox="0 0 32 16"><path d="M0 8h28m-6-6 6 6-6 6" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA Section ──────────────────────────────── */}
      <section className="cta-section">
        <div className="cta-card glass-card">
          <h2>Ready to Localize?</h2>
          <p>Upload your PDF and let the AI pipeline handle the rest.</p>
          <button className="btn btn-primary btn-lg" onClick={() => navigate('/upload')}>
            Get Started →
          </button>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="footer">
        <div className="footer-content">
          <span className="gradient-text footer-brand">OmniLocal</span>
          <span className="footer-text">Built for GDGoC 2026 AI Innovation Challenge</span>
        </div>
      </footer>
    </div>
  )
}
