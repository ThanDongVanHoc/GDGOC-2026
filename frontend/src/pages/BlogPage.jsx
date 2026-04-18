import { useNavigate, Link } from 'react-router-dom'
import { useEffect } from 'react'

export default function BlogPage() {
  const navigate = useNavigate()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="bg-[#000000] text-[#ffffff] font-body min-h-screen flex flex-col antialiased selection:bg-[#FA500F] selection:text-[#000000]">
      {/* TopNavBar */}
      <nav className="fixed top-0 w-full z-50 bg-[#000000]/80 backdrop-blur-xl shadow-[0_32px_64px_rgba(0,0,0,0.8)] border-b border-outline-variant/30">
        <div className="flex justify-between items-center h-20 px-12 w-full max-w-[1920px] mx-auto">
          {/* Brand */}
          <Link to="/" className="font-headline font-black tracking-tighter text-2xl text-[#FA500F]">
            MISTRAL.AI
          </Link>
          {/* Links (Web) */}
          <div className="hidden md:flex gap-8 items-center font-headline tracking-tight font-medium">
            <Link to="/" className="text-on-surface-variant hover:text-on-surface transition-colors py-2 px-3 rounded-lg hover:bg-surface-container transition-all duration-150">
              Framework
            </Link>
            <a href="#" className="text-on-surface-variant hover:text-on-surface transition-colors py-2 px-3 rounded-lg hover:bg-surface-container transition-all duration-150">
              Documentation
            </a>
            <Link to="/blog" className="text-[#FA500F] font-bold border-b-2 border-[#FA500F] pb-1 py-2 px-3 rounded-lg hover:bg-surface-container transition-all duration-150">
              Blog
            </Link>
            <Link to="/about" className="text-on-surface-variant hover:text-on-surface transition-colors py-2 px-3 rounded-lg hover:bg-surface-container transition-all duration-150">
              About
            </Link>
          </div>
          {/* Trailing Actions */}
          <div className="flex items-center gap-4">
            <div className="hidden md:flex gap-2">
              <button className="p-2 text-[#FA500F] hover:bg-surface-container transition-all duration-150 rounded-full flex items-center justify-center scale-98 active:opacity-80">
                <span className="material-symbols-outlined" data-icon="terminal">terminal</span>
              </button>
              <button className="p-2 text-[#FA500F] hover:bg-surface-container transition-all duration-150 rounded-full flex items-center justify-center scale-98 active:opacity-80">
                <span className="material-symbols-outlined" data-icon="settings">settings</span>
              </button>
            </div>
            <button 
              onClick={() => navigate('/upload')}
              className="hidden md:flex bg-[#FA500F] text-[#000000] px-6 py-2.5 rounded-lg font-bold text-sm tracking-wide scale-98 active:opacity-80 transition-transform hover:bg-[#cc3f09]"
            >
              Deploy Agent
            </button>
            {/* Mobile Menu Button */}
            <button className="md:hidden p-2 text-[#FA500F]">
              <span className="material-symbols-outlined">menu</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content Canvas */}
      <main className="flex-grow pt-32 pb-24 px-6 md:px-12 max-w-[1920px] mx-auto w-full flex flex-col gap-24">
        {/* Hero Section: Featured Article */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          <div className="lg:col-span-7 flex flex-col gap-6 items-start">
            <div className="flex items-center gap-3">
              <span className="bg-surface-container-high text-[#FA500F] px-3 py-1 rounded-full font-label text-xs tracking-wider uppercase border border-[#FA500F]/20">
                Featured
              </span>
              <span className="font-mono text-sm text-[#FA500F]">OCT 24, 2024</span>
            </div>
            <h1 className="font-headline text-5xl md:text-7xl font-bold tracking-tight text-white leading-none max-w-3xl">
              The Rise of <br />
              <span className="text-[#FA500F]">Agentic Workflows</span>
            </h1>
            <p className="font-body text-xl text-neutral-400 max-w-2xl leading-relaxed">
              How autonomous LLM chains are fundamentally restructuring enterprise data pipelines, moving from reactive querying to proactive task execution.
            </p>
            <div className="flex items-center gap-4 mt-4">
              <div className="w-10 h-10 rounded-full bg-surface-container-high overflow-hidden border border-[#FA500F]/20">
                <img 
                  alt="Author Avatar" 
                  className="w-full h-full object-cover" 
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuDZrv05v8LFOccPsVp-9eVYS_w7XUh6qSkHIA6_Gg1hCISzTGRx-5k8kdS_D2Ez_6FS7kEC0IJPMk5jknqgfHg5zLz2BQZw4nqeyjTcP-HADcaouEBdZLR2oQXrz7khCoI-1USC0Ang82jhZcimyKcuHv2jaxSupuevJcVPRSjAYOfXbk1Dxr6wnJSJtW0Xz71e3xkiVs0mny93LmkpcJP6LzrIL5lNFoxo3JpbLwaMrYys3sziso0ImGPgwyj_RrUaycwAEuD3OfpB" 
                />
              </div>
              <div>
                <p className="font-headline font-bold text-sm text-white">Dr. Elias Vance</p>
                <p className="font-mono text-xs text-[#FA500F]">Lead AI Architect</p>
              </div>
            </div>
          </div>
          <div className="lg:col-span-5 relative">
            <div className="aspect-[4/5] md:aspect-[3/4] w-full bg-surface-container-lowest rounded-xl overflow-hidden relative border border-[#FA500F]/20 shadow-[0_32px_64px_rgba(250,80,15,0.08)] group">
              <img 
                alt="Abstract Tech" 
                className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-700 ease-out" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuChYIuwzIcKocbA9_Nhnp-BAuI3U79ed1OYuxlUH1XQHE00T-V9zt25002K1W6uNNauALssVy4NAEMqpurv_6d7qQN-3SHxC_PtSAZO6TFrjouES_uu-XyW5caJcScGSFdkLL_ltp8xiZrJLvvKKD0lByohONIrtqGPZkL6QNYqRrvs_tTOizn4aZIr0uYBHBqW3cRhzfLDn4Qi9XIeDg4uuPxsuRc9TO1KlfvKQJWXNFO3txrK8dgc5yyQoFdb9QUS0Wm7DufgOGuK" 
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black to-transparent opacity-60"></div>
              {/* Overlay Data */}
              <div className="absolute bottom-6 left-6 right-6 flex justify-between items-end">
                <div className="bg-black/80 backdrop-blur-md border border-[#FA500F]/20 p-4 rounded-lg flex flex-col gap-1">
                  <span className="font-mono text-[10px] text-[#FA500F] uppercase">Read Time</span>
                  <span className="font-mono text-lg text-white">12 MIN</span>
                </div>
                <button className="w-12 h-12 bg-[#FA500F] text-black rounded-full flex items-center justify-center hover:bg-[#cc3f09] transition-colors shadow-lg">
                  <span className="material-symbols-outlined">arrow_forward</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Category Filters */}
        <section className="flex flex-wrap gap-4 items-center border-b border-[#1a1a1a] pb-6">
          <span className="font-label text-sm text-[#FA500F] uppercase tracking-wider mr-4">Filter by:</span>
          <button className="px-4 py-2 bg-[#1a1a1a] text-[#FA500F] font-mono text-sm rounded-lg border border-[#FA500F]/50">All Posts</button>
          <button className="px-4 py-2 bg-transparent hover:bg-[#111111] text-white font-mono text-sm rounded-lg border border-transparent hover:border-[#FA500F]/20 transition-all">Engineering</button>
          <button className="px-4 py-2 bg-transparent hover:bg-[#111111] text-white font-mono text-sm rounded-lg border border-transparent hover:border-[#FA500F]/20 transition-all">Case Studies</button>
          <button className="px-4 py-2 bg-transparent hover:bg-[#111111] text-white font-mono text-sm rounded-lg border border-transparent hover:border-[#FA500F]/20 transition-all">AI Ethics</button>
          <button className="px-4 py-2 bg-transparent hover:bg-[#111111] text-white font-mono text-sm rounded-lg border border-transparent hover:border-[#FA500F]/20 transition-all">Releases</button>
        </section>

        {/* Blog Grid (Bento Style) */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Article Card 1 */}
          <article className="group bg-[#111111] hover:bg-[#1a1a1a] rounded-xl p-6 flex flex-col gap-6 transition-all duration-150 cursor-pointer border border-[#333333]/30 hover:border-[#FA500F]/30">
            <div className="flex justify-between items-start">
              <span className="font-label text-xs text-[#FA500F] tracking-widest uppercase">Engineering</span>
              <span className="font-mono text-xs text-[#FA500F]">OCT 18</span>
            </div>
            <div className="flex-grow">
              <h3 className="font-headline text-2xl font-bold text-white mb-3 group-hover:text-[#FA500F] transition-colors">Optimizing Vector Databases for Latency</h3>
              <p className="font-body text-sm text-neutral-400 line-clamp-3">A deep dive into indexing strategies and query optimization techniques that reduced our retrieval times by 40% across distributed edge nodes.</p>
            </div>
            <div className="flex items-center gap-2 pt-4 border-t border-[#1a1a1a]">
              <span className="material-symbols-outlined text-[#FA500F] text-sm">person</span>
              <span className="font-mono text-xs text-white">SARAH CHEN</span>
            </div>
          </article>
          {/* Article Card 2 */}
          <article className="group bg-[#111111] hover:bg-[#1a1a1a] rounded-xl p-6 flex flex-col gap-6 transition-all duration-150 cursor-pointer border border-[#333333]/30 hover:border-[#FA500F]/30">
            <div className="flex justify-between items-start">
              <span className="font-label text-xs text-[#FA500F] tracking-widest uppercase">AI Ethics</span>
              <span className="font-mono text-xs text-[#FA500F]">OCT 12</span>
            </div>
            <div className="flex-grow">
              <h3 className="font-headline text-2xl font-bold text-white mb-3 group-hover:text-[#FA500F] transition-colors">Mitigating Hallucinations in Financial Summarization</h3>
              <p className="font-body text-sm text-neutral-400 line-clamp-3">Establishing robust grounding mechanisms and verification loops when deploying generative models in high-stakes regulatory environments.</p>
            </div>
            <div className="flex items-center gap-2 pt-4 border-t border-[#1a1a1a]">
              <span className="material-symbols-outlined text-[#FA500F] text-sm">person</span>
              <span className="font-mono text-xs text-white">DR. AMINA YUSUF</span>
            </div>
          </article>
          {/* Article Card 3 (Image focus) */}
          <article className="group relative bg-[#000000] rounded-xl overflow-hidden flex flex-col gap-6 transition-all duration-150 cursor-pointer border border-[#333333]/30 hover:border-[#FA500F]/30 min-h-[300px]">
            <img 
              alt="Data Visualization" 
              className="absolute inset-0 w-full h-full object-cover opacity-40 group-hover:opacity-60 group-hover:scale-105 transition-all duration-500" 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCyYS0pc0TcJ7HsHaZOJt_9SYB3aW9emWCXyt7AqOq9-0Zr2_wyDvtE6BhVnejeQdlxwgNvpjsoNLLB94JtDuKb2k1a1Ditmd0HvKBq7wd4ZLJPHRT89toUlnmyI7QVCg-rfiHcW7bPResHNudTEA74RWQek2sQ7CF7xQxDHc-DQe21U-ppQqNN8ahRuT5F1FR_ggI8-iKevn1bEPh6L7eP6V58_dlKbK_mB5F6L5y89AL32tC3nmdER9EyMeDk6XSGu_5rwVu2Enx8" 
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent"></div>
            <div className="relative z-10 p-6 flex flex-col h-full justify-end">
              <div className="flex justify-between items-start mb-4">
                <span className="font-label text-xs text-[#000000] tracking-widest uppercase bg-[#FA500F] px-2 py-1 rounded">Case Studies</span>
                <span className="font-mono text-xs text-[#FA500F]">OCT 05</span>
              </div>
              <h3 className="font-headline text-2xl font-bold text-white mb-2 group-hover:text-[#FA500F] transition-colors">Scaling to 1M RPM</h3>
              <p className="font-body text-sm text-neutral-400 mb-4">How OmniLocal architecture handled Black Friday transaction volumes.</p>
              <div className="flex items-center gap-2 pt-4 border-t border-[#1a1a1a]">
                <span className="font-mono text-xs text-[#FA500F] flex items-center gap-1">
                  READ FULL STUDY <span className="material-symbols-outlined text-xs">arrow_forward</span>
                </span>
              </div>
            </div>
          </article>
          {/* Article Card 4 */}
          <article className="group bg-[#111111] hover:bg-[#1a1a1a] rounded-xl p-6 flex flex-col gap-6 transition-all duration-150 cursor-pointer border border-[#333333]/30 hover:border-[#FA500F]/30">
            <div className="flex justify-between items-start">
              <span className="font-label text-xs text-[#FA500F] tracking-widest uppercase">Engineering</span>
              <span className="font-mono text-xs text-[#FA500F]">SEP 28</span>
            </div>
            <div className="flex-grow">
              <h3 className="font-headline text-2xl font-bold text-white mb-3 group-hover:text-[#FA500F] transition-colors">The Migration to Rust</h3>
              <p className="font-body text-sm text-neutral-400 line-clamp-3">Rewriting our core ingestion engine: The pain, the process, and the resulting 10x throughput performance gains.</p>
            </div>
            <div className="flex items-center gap-2 pt-4 border-t border-[#1a1a1a]">
              <span className="material-symbols-outlined text-[#FA500F] text-sm">person</span>
              <span className="font-mono text-xs text-white">MARCUS TRENT</span>
            </div>
          </article>
          {/* Article Card 5 */}
          <article className="group bg-[#111111] hover:bg-[#1a1a1a] rounded-xl p-6 flex flex-col gap-6 transition-all duration-150 cursor-pointer border border-[#333333]/30 hover:border-[#FA500F]/30">
            <div className="flex justify-between items-start">
              <span className="font-label text-xs text-[#FA500F] tracking-widest uppercase">Releases</span>
              <span className="font-mono text-xs text-[#FA500F]">SEP 20</span>
            </div>
            <div className="flex-grow">
              <h3 className="font-headline text-2xl font-bold text-white mb-3 group-hover:text-[#FA500F] transition-colors">OmniLocal v3.2 is Live</h3>
              <p className="font-body text-sm text-neutral-400 line-clamp-3">Introducing dynamic context windows, native WebSockets support, and the new telemetry dashboard.</p>
            </div>
            <div className="flex items-center gap-2 pt-4 border-t border-[#1a1a1a]">
              <span className="material-symbols-outlined text-[#FA500F] text-sm">person</span>
              <span className="font-mono text-xs text-white">PRODUCT TEAM</span>
            </div>
          </article>
        </section>

        {/* Newsletter Pulse */}
        <section className="bg-[#111111] border border-[#FA500F]/20 rounded-2xl p-12 flex flex-col md:flex-row items-center justify-between gap-8 my-12">
          <div className="max-w-xl">
            <h2 className="font-headline text-3xl font-bold text-white mb-4">Stay Synchronized</h2>
            <p className="font-body text-neutral-400">Get a monthly digest of our engineering teardowns, architecture decisions, and core model updates directly to your inbox. No marketing fluff.</p>
          </div>
          <div className="w-full md:w-auto flex flex-col sm:flex-row gap-4">
            <div className="relative w-full sm:w-72">
              <input 
                className="w-full bg-[#1a1a1a] border-none rounded-lg px-4 py-3 font-mono text-sm text-white focus:bg-[#222222] focus:ring-2 focus:ring-[#FA500F] transition-all outline-none placeholder-neutral-600" 
                placeholder="email@enterprise.com" 
                type="email" 
              />
            </div>
            <button className="bg-[#FA500F] text-black font-bold px-6 py-3 rounded-lg whitespace-nowrap hover:bg-[#cc3f09] transition-colors">
              Subscribe
            </button>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full py-16 px-12 border-t border-[#333333]/30 bg-[#000000]">
        <div className="flex flex-col md:flex-row justify-between items-center max-w-[1920px] mx-auto w-full gap-8">
          <div className="font-headline font-black tracking-tighter text-white text-lg">
            OMNILOCAL
          </div>
          <div className="flex gap-6 items-center">
            <a className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 hover:text-[#FA500F] transition-colors" href="#">Privacy Policy</a>
            <a className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 hover:text-[#FA500F] transition-colors" href="#">Security</a>
            <a className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 hover:text-[#FA500F] transition-colors" href="#">Open Source</a>
            <a className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 hover:text-[#FA500F] transition-colors" href="#">Changelog</a>
          </div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-neutral-500">
            © 2024 Kinetic Monolith Systems. AI-Optimized.
          </div>
        </div>
      </footer>
    </div>
  )
}
