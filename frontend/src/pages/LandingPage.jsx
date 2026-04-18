import { useNavigate } from 'react-router-dom';
import { useEffect, useRef } from 'react';

/* ── Icon component: forces Material Symbols font-family ── */
function Icon({ name, className = '', filled = false, style = {} }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={{
        fontFamily: "'Material Symbols Outlined'",
        fontVariationSettings: filled
          ? "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24"
          : "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24",
        WebkitFontSmoothing: 'antialiased',
        ...style,
      }}
    >
      {name}
    </span>
  );
}

/* ── Scroll-reveal hook ── */
function useScrollReveal() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -48px 0px' }
    );
    document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);
}

export default function LandingPage() {
  const navigate = useNavigate();
  useScrollReveal();

  return (
    <div className="bg-background text-on-surface font-body antialiased selection:bg-primary-container selection:text-white min-h-screen flex flex-col dark noise-overlay">

      {/* ── TopNavBar ── */}
      <nav className="fixed top-0 left-0 w-full z-50 bg-[#131313]/80 backdrop-blur-2xl border-b border-white/5 shadow-[0_1px_0_rgba(255,255,255,0.05)]">
        <div className="flex justify-between items-center h-20 px-8 max-w-[1440px] mx-auto">
          <div className="text-2xl font-black tracking-tighter text-[#FA500F] uppercase" style={{ fontFamily: 'Inter' }}>OmniLocal</div>
          <div className="hidden md:flex items-center gap-8">
            {[
              { label: 'Framework', href: '#overview' },
              { label: 'Solutions', href: '#showcase' },
              { label: 'Architecture', href: '#architecture' },
              { label: 'Pipeline', href: '#pipeline' },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-[#e5e2e1]/60 hover:text-white transition-colors duration-150 tracking-tight text-sm font-medium"
                style={{ fontFamily: 'Inter' }}
              >
                {item.label}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-4">
            <button className="hidden md:block text-primary text-sm font-medium hover:bg-[#2a2a2a] transition-all duration-150 px-4 py-2 rounded">
              System Status
            </button>
            <button
              onClick={() => navigate('/upload')}
              className="relative overflow-hidden bg-gradient-to-r from-primary to-primary-container text-on-primary font-bold px-6 py-2.5 rounded-lg hover:opacity-90 hover:scale-[1.02] transition-all duration-150 active:scale-95 shadow-[0_0_32px_rgba(255,87,27,0.25)]"
              style={{ fontFamily: 'Inter' }}
            >
              Deploy Agent
            </button>
          </div>
        </div>
      </nav>

      <main className="flex-grow">

        {/* ── Hero Section ── */}
        <section id="overview" className="relative pt-40 pb-32 px-8 max-w-7xl mx-auto flex flex-col md:flex-row items-start justify-between gap-16 overflow-hidden">
          {/* Background radial glow */}
          <div className="absolute top-0 left-1/4 w-[800px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none -translate-y-1/2"></div>

          {/* Left Column */}
          <div className="max-w-3xl z-10 flex flex-col items-start">
            {/* Badge */}
            <div className="reveal inline-flex items-center gap-2 px-4 py-1.5 mb-8 rounded-full bg-surface-container-high border border-primary/20">
              <Icon name="emoji_events" className="text-primary text-sm" filled />
              <span className="text-xs font-bold text-primary uppercase tracking-wider" style={{ fontFamily: 'Space Grotesk' }}>
                GDGoC Hackathon Vietnam 2026
              </span>
            </div>

            {/* H1 */}
            <h1 className="reveal reveal-delay-1 font-headline text-5xl md:text-7xl font-black tracking-tighter text-on-surface leading-[1.05] mb-6">
              OmniLocal: An Agentic Framework for{' '}
              <span
                className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-[#ff8a65] to-primary-fixed-dim gradient-animate"
              >
                Cross-Cultural Multimodal Content Adaptation
              </span>
            </h1>

            {/* H2 */}
            <p className="reveal reveal-delay-2 text-xl md:text-2xl font-medium text-on-surface-variant tracking-tight mb-12 max-w-2xl leading-relaxed">
              An <span className="text-white font-semibold">Autonomous Content Supply Chain</span> that eliminates cultural context gaps through a 5-phase Multi-Agent pipeline — from raw asset ingestion to zero-error publishing.
            </p>

            {/* CTAs */}
            <div className="reveal reveal-delay-3 flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
              <button
                onClick={() => navigate('/upload')}
                className="group bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold text-base px-8 py-4 rounded-lg transition-all duration-200 active:scale-95 shadow-[0_0_48px_rgba(255,87,27,0.3)] hover:shadow-[0_0_64px_rgba(255,87,27,0.45)] hover:scale-[1.02] flex justify-center items-center gap-2"
                style={{ fontFamily: 'Space Grotesk' }}
              >
                Start Localizing
                <Icon name="arrow_forward" className="text-xl group-hover:translate-x-1 transition-transform" />
              </button>
              <a
                href="https://github.com/ThanDongVanHoc/GDGOC-2026"
                target="_blank"
                rel="noreferrer"
                className="bg-surface-container-highest border border-outline-variant/20 text-on-surface text-base font-medium px-8 py-4 rounded-lg transition-all duration-150 hover:bg-surface-container-high hover:border-primary/30 flex justify-center items-center gap-2"
                style={{ fontFamily: 'Space Grotesk' }}
              >
                <Icon name="code" className="text-xl text-primary" />
                View on GitHub
              </a>
            </div>

            {/* Trust badges */}
            <div className="reveal reveal-delay-4 flex items-center gap-6 mt-10">
              <div className="flex items-center gap-2 text-xs text-on-surface-variant">
                <Icon name="verified" className="text-primary text-sm" filled />
                <span>Open Source</span>
              </div>
              <div className="w-px h-4 bg-outline-variant/30"></div>
              <div className="flex items-center gap-2 text-xs text-on-surface-variant">
                <Icon name="speed" className="text-primary text-sm" />
                <span>35-60 min SLA</span>
              </div>
              <div className="w-px h-4 bg-outline-variant/30"></div>
              <div className="flex items-center gap-2 text-xs text-on-surface-variant">
                <Icon name="savings" className="text-primary text-sm" />
                <span>$1.37 / chapter</span>
              </div>
            </div>
          </div>

          {/* Right Column: Live node display */}
          <div className="reveal reveal-delay-2 w-full md:w-[420px] h-[420px] relative hidden md:block">
            {/* Outer ring */}
            <div className="absolute inset-0 rounded-2xl border border-primary/10 bg-surface-container-low overflow-hidden">
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(255,87,27,0.08)_0%,transparent_70%)]"></div>
              {/* Rotating rings */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 border border-primary/15 rounded-full animate-[spin_60s_linear_infinite]"></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-52 h-52 border border-primary/25 rounded-full border-dashed animate-[spin_35s_linear_infinite_reverse]"></div>
              {/* Center orb */}
              <div className="float-orb absolute top-1/2 left-1/2 w-24 h-24 bg-primary/8 rounded-full flex items-center justify-center backdrop-blur-md border border-primary/30 shadow-[0_0_48px_rgba(255,87,27,0.2)]">
                <Icon name="language" className="text-4xl text-primary" filled />
              </div>
              {/* Scan line */}
              <div className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent scan-line"></div>
              {/* Corner status */}
              <div className="absolute top-4 left-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                <span className="font-mono text-[10px] text-primary uppercase tracking-widest">SYSTEM: ACTIVE</span>
              </div>
              <div className="absolute bottom-4 right-4 font-mono text-[10px] text-on-surface-variant">v1.0.0-alpha</div>
            </div>
          </div>
        </section>

        {/* ── Inference Showcase ── */}
        <section id="showcase" className="py-16 px-8 max-w-7xl mx-auto">
          <div className="reveal mb-12">
            <span className="font-label text-primary text-sm tracking-widest uppercase" style={{ fontFamily: 'Space Grotesk' }}>Inference Showcase</span>
            <h3 className="font-headline text-3xl font-bold tracking-tight text-on-surface mt-2 mb-2">From Global to Local</h3>
            <p className="font-body text-on-surface-variant text-lg max-w-2xl">Real-time multimodal adaptation preserving art style while localizing text, currency, and cultural context.</p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Source */}
            <div className="reveal bg-surface-container-low border border-outline-variant/20 rounded-xl overflow-hidden flex flex-col hover:border-outline-variant/40 transition-colors duration-300">
              <div className="px-4 py-3 bg-surface-container flex items-center justify-between border-b border-outline-variant/20">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-outline-variant"></span>
                  <span className="font-mono text-xs text-on-surface-variant uppercase tracking-wider">Source Material [JA]</span>
                </div>
              </div>
              <div className="p-6 flex-grow bg-background flex flex-col items-center justify-center relative min-h-[320px]">
                <img alt="Original Manga Panel with Japanese Text" className="w-full max-w-sm rounded-lg shadow-lg border border-outline-variant/10" src="/manga_original.png" />
                <div className="absolute bottom-10 left-10 right-10 flex justify-between">
                  <span className="bg-surface/80 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-mono text-on-surface border border-outline-variant/30">TEXT: JP_KANJI</span>
                  <span className="bg-surface/80 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-mono text-on-surface border border-outline-variant/30">CURRENCY: JPY (¥)</span>
                </div>
              </div>
            </div>

            {/* Adapted */}
            <div className="reveal reveal-delay-2 bg-surface-container-low border border-outline-variant/20 rounded-xl overflow-hidden flex flex-col relative hover:border-primary/30 transition-colors duration-300">
              <div className="px-4 py-3 bg-primary/5 flex items-center justify-between border-b border-primary/20">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                  <span className="font-mono text-xs text-primary uppercase tracking-wider">Adapted Material [VI]</span>
                </div>
                <div className="flex items-center gap-1">
                  <Icon name="check_circle" className="text-primary text-sm" />
                  <span className="font-mono text-[10px] text-primary-fixed">VERIFIED</span>
                </div>
              </div>
              <div className="p-6 flex-grow bg-background flex flex-col items-center justify-center relative min-h-[320px]">
                <img alt="Adapted Manga Panel with Vietnamese Text" className="w-full max-w-sm rounded-lg shadow-[0_0_30px_rgba(255,87,27,0.1)] border border-primary/20" src="/manga_localized.png" />
                <div className="absolute bottom-10 left-10 right-10 flex justify-between">
                  <span className="bg-primary/10 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-mono text-primary border border-primary/30">TEXT: VI_LATIN</span>
                  <span className="bg-primary/10 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-mono text-primary border border-primary/30">CURRENCY: VND (₫)</span>
                </div>
              </div>
              <div className="hidden lg:flex absolute top-1/2 -left-6 w-12 h-12 bg-surface-container-high rounded-full border border-outline-variant/30 items-center justify-center shadow-lg -translate-y-1/2 z-10">
                <Icon name="arrow_forward" className="text-primary" />
              </div>
            </div>
          </div>
        </section>

        {/* ── Performance Metrics / The Pulse ── */}
        <section className="py-12 px-8 border-y border-outline-variant/10 bg-surface-container-lowest">
          <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { label: 'OPEX Reduction', value: '98.8%', width: '75%', desc: 'vs manual pipeline' },
              { label: 'SLA Turnaround', value: '35-60m', width: '50%', desc: 'vs 7-10 days' },
              { label: 'Autonomous Agents', value: '5+', width: '100%', desc: 'per pipeline run' },
              { label: 'Manual Feedback Loops', value: '0', width: '100%', desc: 'fully automated' },
            ].map((m, i) => (
              <div key={m.label} className={`reveal reveal-delay-${i + 1} flex flex-col gap-2 group cursor-default`}>
                <span className="text-xs text-on-surface-variant uppercase tracking-widest" style={{ fontFamily: 'Space Grotesk' }}>{m.label}</span>
                <div className="font-mono text-4xl font-bold text-on-surface group-hover:text-primary transition-colors duration-300 shimmer">{m.value}</div>
                <p className="text-on-surface-variant text-xs">{m.desc}</p>
                <div className="h-px w-full bg-surface-container rounded-full mt-1 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-transparent via-primary/50 to-primary bar-animated" style={{ '--bar-w': m.width, width: m.width }}></div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Core Capabilities Bento Grid ── */}
        <section className="py-24 px-8 max-w-7xl mx-auto">
          <div className="reveal mb-16">
            <span className="font-label text-primary text-sm tracking-widest uppercase" style={{ fontFamily: 'Space Grotesk' }}>Capabilities</span>
            <h3 className="font-headline text-3xl font-bold tracking-tight text-on-surface mt-2">Core Capabilities</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6" style={{ gridAutoRows: '280px' }}>
            {/* Card 1 */}
            <div className="reveal md:col-span-2 bg-surface-container hover:bg-surface-container-high transition-colors duration-200 rounded-xl p-8 flex flex-col justify-between relative overflow-hidden group cursor-default">
              <div className="z-10">
                <Icon name="model_training" className="text-primary mb-4 text-3xl" />
                <h4 className="font-headline text-2xl font-bold text-on-surface mb-2">Spatial-Semantic Feedback Loop</h4>
                <p className="font-body text-on-surface-variant max-w-md">Continuous optimization bridging visual context with linguistic nuances. When text overflows, Layout Agent auto-negotiates with Localization Agent to summarize while preserving keywords.</p>
              </div>
              <div className="absolute -bottom-10 -right-10 w-64 h-64 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/12 transition-colors duration-500"></div>
            </div>

            {/* Card 2 */}
            <div className="reveal reveal-delay-2 bg-surface-container hover:bg-surface-container-high transition-colors duration-200 rounded-xl p-8 flex flex-col justify-between group cursor-default">
              <div>
                <Icon name="brush" className="text-primary mb-4 text-3xl" />
                <h4 className="font-headline text-xl font-bold text-on-surface mb-2">Constrained Multimodal Localization</h4>
                <p className="font-body text-on-surface-variant text-sm">ControlNet locks 100% art-style fidelity during inpainting. Cultural entities replaced autonomously via RAG + NER with zero art-style drift.</p>
              </div>
            </div>

            {/* Card 3 */}
            <div className="reveal reveal-delay-1 md:col-span-3 bg-surface-container hover:bg-surface-container-high transition-colors duration-200 rounded-xl p-8 flex flex-col md:flex-row items-center justify-between gap-8 border border-outline-variant/10 group cursor-default">
              <div className="max-w-xl">
                <Icon name="account_tree" className="text-primary mb-4 text-3xl" />
                <h4 className="font-headline text-2xl font-bold text-on-surface mb-2">Workflow-as-Architecture</h4>
                <p className="font-body text-on-surface-variant">The pipeline itself is the product. 5 modular agents (Orchestrator, Translator, Reviser, Localization, Council, Layout, Vision, QA) replace fragmented Waterfall departments with observable, strictly typed interactions.</p>
              </div>
              <div className="bg-surface-container-lowest p-4 rounded-lg w-full md:w-auto border border-outline-variant/20 shadow-[0_8px_32px_rgba(0,0,0,0.5)] flex-shrink-0">
                <pre className="font-mono text-xs text-primary-fixed leading-relaxed">
                  <span className="text-tertiary-fixed">type</span> <span className="text-primary">AgentNode</span> {`= {`}{'\n'}
                  {'  '}phase: <span className="text-secondary-fixed">"P1" | "P2" | "P3" | "P4" | "P5"</span>;{'\n'}
                  {'  '}input: <span className="text-tertiary-fixed">MultimodalState</span>;{'\n'}
                  {'  '}constraints: <span className="text-tertiary-fixed">GlobalConstraints</span>;{'\n'}
                  {'  '}execute(): <span className="text-tertiary-fixed">Promise</span>&lt;<span className="text-tertiary-fixed">PhaseResult</span>&gt;;{'\n'}
                  {`}`}
                  <span className="cursor-blink text-primary ml-px">▌</span>
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* ── The Butterfly Effect Mitigation ── */}
        <section className="py-24 px-8 max-w-7xl mx-auto flex flex-col lg:flex-row gap-16 items-start">
          <div className="lg:w-1/2 flex flex-col gap-6">
            <div className="reveal">
              <span className="font-label text-primary text-sm tracking-widest uppercase" style={{ fontFamily: 'Space Grotesk' }}>System Architecture</span>
              <h2 className="font-headline text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight mt-2">
                The "Butterfly Effect" Mitigation
              </h2>
            </div>
            <p className="reveal reveal-delay-1 text-on-surface-variant text-lg leading-relaxed max-w-xl">
              In continuous narrative translation, minor contextual errors compound exponentially. OmniLocal's{' '}
              <span className="text-white font-medium">Council Agent</span> maintains global narrative logic across all chapters via RAG-powered Context Memory.
            </p>
            <div className="flex flex-col gap-4 mt-4">
              {[
                {
                  icon: 'memory', title: 'Vector Memory Context',
                  desc: 'Maintains a continuity ledger of character traits, plot points, and regional idioms to prevent temporal paradoxes in dialogue across chapters.',
                  delay: 2,
                },
                {
                  icon: 'rule', title: 'Semantic Assertion Validation',
                  desc: 'Post-translation evaluation checks against the global truth state before committing strings to the layout engine. Deviation > 15% triggers auto-reject.',
                  delay: 3,
                },
                {
                  icon: 'psychology', title: 'Council Agent Simulation',
                  desc: 'Runs butterfly-effect simulation for every cultural entity swap — if a context change breaks downstream plot logic, it is rejected with structured feedback.',
                  delay: 4,
                },
              ].map((item) => (
                <div key={item.title} className={`reveal reveal-delay-${item.delay} bg-surface-container-low p-6 rounded-xl flex items-start gap-4 hover:bg-surface-container transition-colors duration-150 group`}>
                  <Icon name={item.icon} className="text-primary mt-1 group-hover:scale-110 transition-transform" filled />
                  <div>
                    <h4 className="font-headline font-bold text-white mb-2">{item.title}</h4>
                    <p className="text-on-surface-variant text-sm">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Live terminal visualization */}
          <div className="reveal reveal-delay-2 lg:w-1/2 relative w-full aspect-[4/3] rounded-2xl overflow-hidden bg-surface-container flex items-center justify-center p-8">
            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary via-background to-background"></div>
            <div className="relative z-10 w-full h-full border border-outline-variant/30 rounded-xl bg-surface-container-lowest p-6 flex flex-col justify-between">
              <div className="flex justify-between items-center border-b border-outline-variant/30 pb-4">
                <span className="text-xs text-on-surface-variant" style={{ fontFamily: 'Space Grotesk' }}>
                  NODE_STATE: <span className="font-mono text-primary">STABLE</span>
                </span>
                <Icon name="all_inclusive" className="text-on-surface-variant" />
              </div>
              <div className="flex-grow flex flex-col justify-center gap-6 py-8">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center border border-outline-variant/50 shrink-0">
                    <Icon name="translate" className="text-on-surface text-sm" />
                  </div>
                  <div className="h-px bg-outline-variant/50 flex-grow relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary to-transparent opacity-60" style={{ animation: 'scan 2.5s linear infinite' }}></div>
                  </div>
                  <div className="w-16 h-16 rounded-lg bg-surface-bright flex items-center justify-center border border-primary/50 shadow-[0_0_24px_rgba(255,181,158,0.15)] relative node-active shrink-0">
                    <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-primary animate-ping opacity-60"></div>
                    <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-primary"></div>
                    <Icon name="gavel" className="text-primary" filled />
                  </div>
                  <div className="h-px bg-outline-variant/50 flex-grow relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary to-transparent opacity-60" style={{ animation: 'scan 2.5s linear 1.25s infinite' }}></div>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center border border-outline-variant/50 shrink-0">
                    <Icon name="done_all" className="text-on-surface text-sm" />
                  </div>
                </div>
                <div className="bg-surface-container-low rounded-lg p-4 font-mono text-[10px] text-on-surface-variant overflow-hidden border border-outline-variant/20">
                  <div className="opacity-40">&gt; ANALYZING BRANCH_0x4F2A — chapter_07.json</div>
                  <div className="text-primary mt-1">&gt; ANOMALY: PRONOUN_MISMATCH (entity: "Nobita" → "Nam")</div>
                  <div>&gt; TRIGGERING COUNCIL_AGENT PRE-COMMIT HOOK...</div>
                  <div className="text-tertiary-fixed-dim mt-1">&gt; RUNNING BUTTERFLY SIMULATION (14 downstream scenes)</div>
                  <div className="text-white mt-1">&gt; RESOLVED: CONTEXT RESTORED TO BASELINE ✓</div>
                  <div className="mt-2 flex items-center gap-1 text-primary/60">
                    &gt; <span className="cursor-blink">▌</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Case Studies ── */}
        <section className="py-24 px-8 max-w-7xl mx-auto flex flex-col gap-12">
          <div className="reveal flex flex-col gap-4 max-w-2xl">
            <span className="font-label text-primary text-sm tracking-widest uppercase" style={{ fontFamily: 'Space Grotesk' }}>Case Studies</span>
            <h2 className="font-headline text-4xl font-extrabold tracking-tight">Resolution in Edge Cases</h2>
            <p className="text-on-surface-variant text-lg">Demonstrating the layout and preservation agents in complex production environments.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Doraemon */}
            <div className="reveal bg-surface-container-lowest border border-outline-variant/20 rounded-2xl overflow-hidden group hover:bg-surface-container-low hover:border-outline-variant/40 transition-all duration-300">
              <div className="h-64 bg-surface-container relative overflow-hidden">
                <img alt="Art preservation" className="w-full h-full object-cover opacity-60 group-hover:opacity-80 group-hover:scale-[1.03] transition-all duration-500" src="/art_preservation.png" />
                <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest to-transparent"></div>
                <div className="absolute bottom-6 left-6 flex gap-2">
                  <span className="bg-background/80 backdrop-blur-md px-3 py-1 rounded-full text-xs text-primary border border-primary/30" style={{ fontFamily: 'Space Grotesk' }}>Art Preservation</span>
                  <span className="bg-background/80 backdrop-blur-md px-3 py-1 rounded-full text-xs text-white border border-outline-variant/50" style={{ fontFamily: 'Space Grotesk' }}>Doraemon</span>
                </div>
              </div>
              <div className="p-8 flex flex-col gap-4">
                <h3 className="font-headline text-2xl font-bold text-white">Non-Destructive Redraw</h3>
                <p className="text-on-surface-variant text-sm leading-relaxed">
                  When translating localised sound effects overlaid on complex character art, the Vision Agent reconstructs occluded background layers with 99.4% pixel-perfect fidelity using ControlNet art-style constraints before applying the new text layer.
                </p>
                <div className="mt-4 pt-4 border-t border-outline-variant/20 flex justify-between items-center font-mono text-xs">
                  <div className="flex flex-col gap-1">
                    <span className="text-on-surface-variant">Artifact Rate</span>
                    <span className="text-white">&lt; 0.01%</span>
                  </div>
                  <div className="flex flex-col gap-1 text-right">
                    <span className="text-on-surface-variant">Processing Time</span>
                    <span className="text-white">1.2s / frame</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Death Note */}
            <div className="reveal reveal-delay-2 bg-surface-container-lowest border border-outline-variant/20 rounded-2xl overflow-hidden group hover:bg-surface-container-low hover:border-outline-variant/40 transition-all duration-300">
              <div className="h-64 bg-surface-container relative overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center p-8">
                  <div className="w-full h-full bg-background rounded-lg border border-outline-variant/50 p-4 font-mono text-xs text-on-surface-variant flex flex-col gap-2 relative shadow-inner">
                    <div className="w-full h-2 bg-surface-bright rounded mb-2"></div>
                    <div className="w-3/4 h-2 bg-surface-bright rounded"></div>
                    <div className="w-full h-2 bg-surface-bright rounded"></div>
                    <div className="w-5/6 h-2 bg-surface-bright rounded"></div>
                    <div className="w-full h-2 bg-surface-bright rounded mb-2"></div>
                    <div className="absolute right-4 bottom-4 w-32 h-16 border-2 border-primary border-dashed rounded-lg flex items-center justify-center bg-primary/10 animate-pulse">
                      <span className="text-primary font-bold text-xs">OVERFLOW +28%</span>
                    </div>
                  </div>
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest to-transparent"></div>
                <div className="absolute bottom-6 left-6 flex gap-2">
                  <span className="bg-background/80 backdrop-blur-md px-3 py-1 rounded-full text-xs text-primary border border-primary/30" style={{ fontFamily: 'Space Grotesk' }}>Text Overflow</span>
                  <span className="bg-background/80 backdrop-blur-md px-3 py-1 rounded-full text-xs text-white border border-outline-variant/50" style={{ fontFamily: 'Space Grotesk' }}>Death Note</span>
                </div>
              </div>
              <div className="p-8 flex flex-col gap-4">
                <h3 className="font-headline text-2xl font-bold text-white">Text Overflow Negotiation</h3>
                <p className="text-on-surface-variant text-sm leading-relaxed">
                  Vietnamese expands 20-30% beyond Japanese speech bubbles. Layout Agent autonomously negotiates font scaling, leading adjustment, and bubble geometry expansion — then acks Localization Agent to summarize text to fit, creating a closed feedback loop.
                </p>
                <div className="mt-4 pt-4 border-t border-outline-variant/20 flex justify-between items-center font-mono text-xs">
                  <div className="flex flex-col gap-1">
                    <span className="text-on-surface-variant">Expansion Tolerance</span>
                    <span className="text-white">+15% Area</span>
                  </div>
                  <div className="flex flex-col gap-1 text-right">
                    <span className="text-on-surface-variant">Font Scaling Min</span>
                    <span className="text-white">8pt</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Unit Economics ── */}
        <section className="py-24 px-8 max-w-7xl mx-auto">
          <div className="reveal bg-surface-container rounded-3xl p-8 lg:p-16 border border-outline-variant/10 relative overflow-hidden">
            <div className="absolute -right-64 -top-64 w-[512px] h-[512px] bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>
            <div className="flex flex-col lg:flex-row justify-between items-start gap-16 relative z-10">
              <div className="lg:w-1/3 flex flex-col gap-6">
                <span className="font-label text-primary text-sm tracking-widest uppercase" style={{ fontFamily: 'Space Grotesk' }}>Unit Economics</span>
                <h2 className="font-headline text-4xl font-extrabold tracking-tight">98.8% OPEX Reduction</h2>
                <p className="text-on-surface-variant text-base leading-relaxed">
                  Transitioning from manual localization pipelines to OmniLocal's autonomous framework reduces per-chapter operational expenditure by 98.8% while maintaining enterprise quality SLAs.
                </p>
                <div className="mt-4">
                  <div className="font-mono text-5xl text-white font-bold tracking-tight mb-2">
                    $1.37 <span className="text-lg text-primary font-normal">/ chapter</span>
                  </div>
                  <div className="text-on-surface-variant text-sm flex items-center gap-2 mt-1">
                    <Icon name="trending_down" className="text-primary text-sm" />
                    Down from $115.00 manual DTP pipeline
                  </div>
                  <div className="text-on-surface-variant text-sm flex items-center gap-2 mt-1">
                    <Icon name="schedule" className="text-primary text-sm" />
                    35–60 min vs 7–10 days turnaround
                  </div>
                </div>
              </div>

              <div className="lg:w-2/3 w-full">
                <div className="bg-surface-container-lowest rounded-xl border border-outline-variant/20 p-6 flex flex-col gap-6">
                  <div className="flex justify-between items-end border-b border-outline-variant/20 pb-4">
                    <h4 className="font-headline font-bold text-white">Cost Breakdown (Per Chapter)</h4>
                    <span className="font-mono text-xs text-on-surface-variant">ESTIMATED COMPUTE</span>
                  </div>
                  <div className="flex flex-col gap-4 font-mono text-sm">
                    {[
                      { label: 'Translation & Vector Ops (Phase 1-2)', cost: '$0.42', pct: '30%', color: 'bg-surface-bright' },
                      { label: 'Vision & Layout Negotiation (Phase 4)', cost: '$0.85', pct: '62%', color: 'bg-primary-container' },
                      { label: 'Council Agent Verification (Phase 3)', cost: '$0.10', pct: '8%', color: 'bg-primary' },
                    ].map((row) => (
                      <div key={row.label}>
                        <div className="flex justify-between items-center group mb-2">
                          <div className="flex items-center gap-3 text-on-surface-variant group-hover:text-white transition-colors">
                            <span className={`w-2 h-2 rounded-full ${row.color} shrink-0`}></span>
                            {row.label}
                          </div>
                          <div className="text-white ml-4 shrink-0">{row.cost}</div>
                        </div>
                        <div className="w-full bg-surface-container h-1 rounded-full overflow-hidden">
                          <div className={`${row.color} h-full bar-animated`} style={{ width: row.pct }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-outline-variant/20 flex justify-between items-center font-mono font-bold text-lg">
                    <span className="text-white">Total</span>
                    <span className="text-primary">$1.37</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Agent Logic Map (5 Phases — correct from Proposal) ── */}
        <section id="architecture" className="py-24 px-8 max-w-7xl mx-auto flex flex-col gap-12 border-t border-outline-variant/10">
          <div className="reveal flex flex-col gap-4 text-center items-center">
            <span className="font-label text-primary text-sm tracking-widest uppercase" style={{ fontFamily: 'Space Grotesk' }}>Pipeline Execution</span>
            <h2 className="font-headline text-4xl font-extrabold tracking-tight">Agent Logic Map</h2>
            <p className="text-on-surface-variant text-lg max-w-2xl">The 5-phase autonomous sequence orchestrating raw project package to zero-error published asset.</p>
          </div>

          <div className="relative w-full max-w-4xl mx-auto py-12">
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-outline-variant/20 -translate-x-1/2"></div>
            <div className="flex flex-col gap-20 relative z-10">

              {/* Phase 1 */}
              <div className="reveal flex items-center justify-between w-full group">
                <div className="w-[45%] text-right pr-8 flex flex-col gap-2">
                  <div className="font-mono text-xs text-primary uppercase tracking-widest mb-1">Phase 1</div>
                  <h4 className="font-headline text-xl font-bold text-white group-hover:text-primary transition-colors">Ingestion & Planning</h4>
                  <p className="text-sm text-on-surface-variant">Orchestrator Agent parses raw project packages (PDF/IDML + metadata), builds Task Graph, and dispatches structured payloads to downstream agents.</p>
                </div>
                <div className="w-14 h-14 rounded-xl bg-surface-container-highest border border-outline-variant/50 flex items-center justify-center relative shrink-0 group-hover:border-primary group-hover:shadow-[0_0_24px_rgba(255,87,27,0.1)] transition-all duration-200">
                  <Icon name="hub" className="text-on-surface group-hover:text-primary transition-colors" />
                </div>
                <div className="w-[45%] pl-8"></div>
              </div>

              {/* Phase 2 */}
              <div className="reveal flex items-center justify-between w-full group">
                <div className="w-[45%] pr-8"></div>
                <div className="w-14 h-14 rounded-xl bg-surface-container-highest border border-outline-variant/50 flex items-center justify-center relative shrink-0 group-hover:border-primary group-hover:shadow-[0_0_24px_rgba(255,87,27,0.1)] transition-all duration-200">
                  <Icon name="translate" className="text-on-surface group-hover:text-primary transition-colors" />
                </div>
                <div className="w-[45%] pl-8 flex flex-col gap-2">
                  <div className="font-mono text-xs text-primary uppercase tracking-widest mb-1">Phase 2</div>
                  <h4 className="font-headline text-xl font-bold text-white group-hover:text-primary transition-colors">Translation & Bilingual Revision</h4>
                  <p className="text-sm text-on-surface-variant">Translator Agent → Reviser Agent cross-validation loop. Semantic Similarity Score enforces &le;15% deviation. Auto-prompts Translator on reject until threshold is cleared.</p>
                </div>
              </div>

              {/* Phase 3 */}
              <div className="reveal flex items-center justify-between w-full group">
                <div className="w-[45%] text-right pr-8 flex flex-col gap-2">
                  <div className="font-mono text-xs text-primary uppercase tracking-widest mb-1">Phase 3</div>
                  <h4 className="font-headline text-xl font-bold text-white group-hover:text-primary transition-colors">Localization & Context Review</h4>
                  <p className="text-sm text-on-surface-variant">Localization Agent uses RAG + NER to swap cultural entities. Council Agent runs butterfly-effect simulation across all chapters — rejects on logic risk with structured feedback.</p>
                </div>
                <div className="w-14 h-14 rounded-xl bg-primary/10 border border-primary/40 flex items-center justify-center relative shrink-0 node-active group-hover:shadow-[0_0_32px_rgba(255,87,27,0.2)] transition-all duration-200">
                  <Icon name="psychology" className="text-primary" />
                  <div className="absolute -top-1.5 -right-1.5 w-3.5 h-3.5 rounded-full bg-primary border-2 border-background animate-pulse"></div>
                </div>
                <div className="w-[45%] pl-8"></div>
              </div>

              {/* Phase 4 */}
              <div className="reveal flex items-center justify-between w-full group">
                <div className="w-[45%] pr-8"></div>
                <div className="w-14 h-14 rounded-xl bg-surface-container-highest border border-outline-variant/50 flex items-center justify-center relative shrink-0 group-hover:border-primary group-hover:shadow-[0_0_24px_rgba(255,87,27,0.1)] transition-all duration-200">
                  <Icon name="view_quilt" className="text-on-surface group-hover:text-primary transition-colors" />
                </div>
                <div className="w-[45%] pl-8 flex flex-col gap-2">
                  <div className="font-mono text-xs text-primary uppercase tracking-widest mb-1">Phase 4</div>
                  <h4 className="font-headline text-xl font-bold text-white group-hover:text-primary transition-colors">Typesetting & Graphic Recreation</h4>
                  <p className="text-sm text-on-surface-variant">Layout Agent typesets text into bounding boxes. Vision Agent runs Inpainting + ControlNet art-style lock for image localization. Feedback loop auto-resolves text overflow with Phase 3.</p>
                </div>
              </div>

              {/* Phase 5 */}
              <div className="reveal flex items-center justify-between w-full group">
                <div className="w-[45%] text-right pr-8 flex flex-col gap-2">
                  <div className="font-mono text-xs text-primary uppercase tracking-widest mb-1">Phase 5</div>
                  <h4 className="font-headline text-xl font-bold text-white group-hover:text-primary transition-colors">Final QA & Publishing</h4>
                  <p className="text-sm text-on-surface-variant">QA Agent (VLM) reads each page visually — detects typos, position overlay, contrast issues. Loops back to Layout/Localization agents until Zero-error Approved state. Exports print-ready file.</p>
                </div>
                <div className="w-14 h-14 rounded-xl bg-surface-container-highest border border-outline-variant/50 flex items-center justify-center relative shrink-0 group-hover:border-primary group-hover:shadow-[0_0_24px_rgba(255,87,27,0.1)] transition-all duration-200">
                  <Icon name="fact_check" className="text-on-surface group-hover:text-primary transition-colors" />
                </div>
                <div className="w-[45%] pl-8"></div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Autonomous Pipeline Diagram (horizontal) ── */}
        <section id="pipeline" className="py-24 px-8 max-w-7xl mx-auto bg-surface-container-low rounded-3xl mb-24 border border-outline-variant/5">
          <div className="reveal text-center mb-16">
            <span className="font-label text-primary text-sm tracking-widest uppercase" style={{ fontFamily: 'Space Grotesk' }}>System Flow</span>
            <h3 className="font-headline text-3xl font-bold tracking-tight text-on-surface mt-2 mb-4">Autonomous Pipeline Architecture</h3>
            <p className="font-body text-on-surface-variant max-w-2xl mx-auto">5-Phase flow executing tasks in parallel and sequential order with zero human intervention.</p>
          </div>

          <div className="flex flex-col md:flex-row items-center justify-between gap-4 md:gap-2 relative py-8 overflow-x-auto w-full">
            <div className="hidden md:block absolute top-1/2 left-10 right-10 h-px bg-outline-variant/20 -translate-y-1/2 z-0"></div>

            {/* Phase 1 */}
            <div className="reveal flex flex-col items-center gap-4 z-10 w-full md:w-auto">
              <div className="w-16 h-16 rounded-xl bg-surface-container-high border border-outline-variant/30 flex items-center justify-center shadow-[0_0_24px_rgba(0,0,0,0.5)] relative hover:border-primary/50 hover:shadow-[0_0_32px_rgba(255,87,27,0.1)] transition-all duration-200 group">
                <Icon name="hub" className="text-primary group-hover:scale-110 transition-transform" />
                <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-tertiary-container border-2 border-surface-container-high"></div>
              </div>
              <div className="text-center">
                <div className="font-mono text-[9px] text-primary/60 uppercase tracking-widest mb-0.5">Phase 1</div>
                <div className="font-label text-sm font-bold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>Ingestion</div>
                <div className="font-mono text-[9px] text-on-surface-variant mt-1 uppercase tracking-wider">Orchestrator</div>
              </div>
            </div>
            <Icon name="arrow_forward" className="text-outline-variant/50 z-10 hidden md:block" />

            {/* Phase 2 */}
            <div className="reveal reveal-delay-1 flex flex-col items-center gap-4 z-10 w-full md:w-auto">
              <div className="w-16 h-16 rounded-xl bg-surface-container-high border border-outline-variant/30 flex items-center justify-center shadow-[0_0_24px_rgba(0,0,0,0.5)] relative hover:border-primary/50 hover:shadow-[0_0_32px_rgba(255,87,27,0.1)] transition-all duration-200 group">
                <Icon name="translate" className="text-primary group-hover:scale-110 transition-transform" />
                <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-secondary border-2 border-surface-container-high"></div>
              </div>
              <div className="text-center">
                <div className="font-mono text-[9px] text-primary/60 uppercase tracking-widest mb-0.5">Phase 2</div>
                <div className="font-label text-sm font-bold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>Translation</div>
                <div className="font-mono text-[9px] text-on-surface-variant mt-1 uppercase tracking-wider">Translator + Reviser</div>
              </div>
            </div>
            <Icon name="arrow_forward" className="text-outline-variant/50 z-10 hidden md:block" />

            {/* Phase 3 — Active */}
            <div className="reveal reveal-delay-2 flex flex-col items-center gap-4 z-10 w-full md:w-auto">
              <div className="w-20 h-20 rounded-xl bg-primary/10 border border-primary/40 flex items-center justify-center shadow-[0_0_32px_rgba(255,87,27,0.15)] relative transform scale-110 node-active">
                <Icon name="psychology" className="text-primary text-3xl" />
                <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-primary border-2 border-surface-container-high animate-pulse"></div>
              </div>
              <div className="text-center">
                <div className="font-mono text-[9px] text-primary/80 uppercase tracking-widest mb-0.5">Phase 3</div>
                <div className="font-label text-base font-bold text-primary" style={{ fontFamily: 'Space Grotesk' }}>Localization</div>
                <div className="font-mono text-[9px] text-primary/70 mt-1 uppercase tracking-wider">Loc. + Council</div>
              </div>
            </div>
            <Icon name="arrow_forward" className="text-outline-variant/50 z-10 hidden md:block" />

            {/* Phase 4 */}
            <div className="reveal reveal-delay-3 flex flex-col items-center gap-4 z-10 w-full md:w-auto">
              <div className="w-16 h-16 rounded-xl bg-surface-container-high border border-outline-variant/30 flex items-center justify-center shadow-[0_0_24px_rgba(0,0,0,0.5)] relative hover:border-primary/50 hover:shadow-[0_0_32px_rgba(255,87,27,0.1)] transition-all duration-200 group">
                <Icon name="view_quilt" className="text-primary group-hover:scale-110 transition-transform" />
                <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-surface-container border-2 border-surface-container-high"></div>
              </div>
              <div className="text-center">
                <div className="font-mono text-[9px] text-primary/60 uppercase tracking-widest mb-0.5">Phase 4</div>
                <div className="font-label text-sm font-bold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>Typesetting</div>
                <div className="font-mono text-[9px] text-on-surface-variant mt-1 uppercase tracking-wider">Layout + Vision</div>
              </div>
            </div>
            <Icon name="arrow_forward" className="text-outline-variant/50 z-10 hidden md:block" />

            {/* Phase 5 */}
            <div className="reveal reveal-delay-4 flex flex-col items-center gap-4 z-10 w-full md:w-auto">
              <div className="w-16 h-16 rounded-xl bg-surface-container-high border border-outline-variant/30 flex items-center justify-center shadow-[0_0_24px_rgba(0,0,0,0.5)] relative hover:border-primary/50 hover:shadow-[0_0_32px_rgba(255,87,27,0.1)] transition-all duration-200 group">
                <Icon name="fact_check" className="text-primary group-hover:scale-110 transition-transform" />
                <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-surface-container border-2 border-surface-container-high"></div>
              </div>
              <div className="text-center">
                <div className="font-mono text-[9px] text-primary/60 uppercase tracking-widest mb-0.5">Phase 5</div>
                <div className="font-label text-sm font-bold text-on-surface" style={{ fontFamily: 'Space Grotesk' }}>Final QA</div>
                <div className="font-mono text-[9px] text-on-surface-variant mt-1 uppercase tracking-wider">QA Agent (VLM)</div>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="reveal flex flex-wrap justify-center gap-6 mt-8 pt-8 border-t border-outline-variant/10">
            <div className="flex items-center gap-2 text-xs text-on-surface-variant">
              <span className="w-3 h-3 rounded-full bg-tertiary-container"></span>Pending
            </div>
            <div className="flex items-center gap-2 text-xs text-on-surface-variant">
              <span className="w-3 h-3 rounded-full bg-secondary"></span>Active
            </div>
            <div className="flex items-center gap-2 text-xs text-primary">
              <span className="w-3 h-3 rounded-full bg-primary animate-pulse"></span>Processing (Phase 3)
            </div>
            <div className="flex items-center gap-2 text-xs text-on-surface-variant">
              <span className="w-3 h-3 rounded-full bg-surface-container border border-outline-variant/50"></span>Queued
            </div>
          </div>
        </section>

      </main>

      {/* ── Footer ── */}
      <footer className="w-full pt-20 pb-12 px-8 border-t border-outline-variant/10" style={{ background: 'linear-gradient(to bottom, #131313, #0e0e0e)' }}>
        <div className="max-w-[1440px] mx-auto">
          {/* Top row */}
          <div className="flex flex-col md:flex-row justify-between items-start gap-12 mb-12">
            {/* Brand */}
            <div className="flex flex-col gap-4 max-w-sm">
              <div className="text-[#FA500F] font-black text-2xl tracking-tighter" style={{ fontFamily: 'Inter' }}>OmniLocal</div>
              <p className="text-on-surface-variant text-sm leading-relaxed">
                An Agentic Framework for Cross-Cultural Multimodal Content Adaptation. Built for the autonomous publishing era.
              </p>
              <div className="font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-widest">GDGoC Hackathon Vietnam 2026</div>
            </div>

            {/* Links grid */}
            <div className="flex flex-wrap gap-x-16 gap-y-8">
              <div className="flex flex-col gap-3">
                <div className="font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-widest mb-1">Project</div>
                {['GitHub Repository', 'Proposal PDF', 'System Architecture', 'API Reference'].map(link => (
                  <a key={link} className="text-on-surface-variant/60 text-sm hover:text-[#FA500F] transition-colors" href="#">{link}</a>
                ))}
              </div>
              <div className="flex flex-col gap-3">
                <div className="font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-widest mb-1">Pipeline</div>
                {['Phase 1: Ingestion', 'Phase 2: Translation', 'Phase 3: Localization', 'Phase 4: Typesetting', 'Phase 5: Final QA'].map(link => (
                  <a key={link} className="text-on-surface-variant/60 text-sm hover:text-[#FA500F] transition-colors" href="#pipeline">{link}</a>
                ))}
              </div>
              <div className="flex flex-col gap-3">
                <div className="font-mono text-[10px] text-on-surface-variant/50 uppercase tracking-widest mb-1">System</div>
                {['System Status', 'Deploy Pipeline', 'Documentation', 'Changelog'].map(link => (
                  <a key={link} className="text-on-surface-variant/60 text-sm hover:text-[#FA500F] transition-colors" href="#">{link}</a>
                ))}
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-outline-variant/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            {/* Team credits */}
            <div className="flex flex-col gap-1">
              <div className="font-mono text-[11px] text-on-surface-variant/60 uppercase tracking-[0.12em]">
                © 2026 Team 24A01 · APCS — Advanced Program in Computer Science
              </div>
              <div className="font-mono text-[10px] text-on-surface-variant/35 uppercase tracking-[0.08em]">
                Trịnh Võ Nam Kiệt · Nguyễn Chí Tính · Đoàn Tuấn Anh · Dương Gia Khương
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="font-mono text-[10px] text-on-surface-variant/35 uppercase tracking-[0.08em]">OmniLocal Framework v1.0.0</span>
              <span className="w-px h-4 bg-outline-variant/20"></span>
              <span className="font-mono text-[10px] text-[#FA500F]/60 uppercase tracking-[0.08em]">Built with Agentic AI</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
