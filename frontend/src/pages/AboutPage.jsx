import { useNavigate, Link } from 'react-router-dom'
import { useEffect } from 'react'

function Icon({ name, className = '', filled = false }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      style={{
        fontFamily: "'Material Symbols Outlined'",
        fontVariationSettings: filled
          ? "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24"
          : "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24"
      }}
    >
      {name}
    </span>
  )
}

export default function AboutPage() {
  const navigate = useNavigate()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  return (
    <div className="bg-[#000000] text-[#ffffff] font-body min-h-screen flex flex-col antialiased selection:bg-[#FA500F] selection:text-[#000000]">
      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-[#000000]/80 backdrop-blur-xl shadow-[0_32px_64px_rgba(0,0,0,0.5)] border-b border-[#333333]">
        <div className="flex justify-between items-center h-20 px-12 w-full max-w-[1920px] mx-auto">
          {/* Brand */}
          <Link to="/" className="font-headline font-black tracking-tighter text-2xl text-[#FA500F]">
            MISTRAL.AI
          </Link>
          {/* Links */}
          <div className="hidden md:flex items-center gap-8 font-headline tracking-tight font-medium text-neutral-400">
            <Link to="/" className="hover:text-white transition-colors">Framework</Link>
            <a href="#" className="hover:text-white transition-colors">Documentation</a>
            <Link to="/blog" className="hover:text-white transition-colors">Blog</Link>
            <Link to="/about" className="text-white font-bold border-b-2 border-[#FA500F] pb-1">About</Link>
          </div>
          {/* Actions */}
          <div className="flex items-center gap-6">
            <div className="flex gap-4 text-[#FA500F]">
              <button className="hover:bg-[#111111] transition-all duration-150 p-2 rounded scale-98 active:opacity-80">
                <Icon name="terminal" />
              </button>
              <button className="hover:bg-[#111111] transition-all duration-150 p-2 rounded scale-98 active:opacity-80">
                <Icon name="settings" />
              </button>
            </div>
            <button 
              onClick={() => navigate('/upload')}
              className="bg-[#FA500F] text-black font-bold px-6 py-2 rounded hover:opacity-90 transition-opacity"
            >
              Deploy Agent
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content Canvas */}
      <main className="flex-grow pt-32 pb-24 px-6 md:px-12 max-w-[1920px] mx-auto w-full flex flex-col gap-32">
        {/* Hero Section: Editorial Asymmetry */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
          <div className="lg:col-span-7 flex flex-col gap-8">
            <h1 className="font-headline text-5xl md:text-7xl font-bold tracking-tighter leading-tight text-white">
              Engineering <br />
              <span className="text-[#FA500F]">Cultural Bridges</span>
            </h1>
            <p className="font-body text-xl text-neutral-400 max-w-2xl leading-relaxed">
              OmniLocal by MISTRAL.AI is not just translation. It is the real-time architectural synthesis of localized context, intent, and nuance at enterprise scale.
            </p>
            {/* Pulse Metric Component */}
            <div className="mt-8 flex items-baseline gap-6 border-l-2 border-[#FA500F] pl-6">
              <div>
                <div className="font-[JetBrains_Mono] text-4xl font-bold text-[#FA500F]" style={{ fontFamily: "'JetBrains Mono'" }}>0-Latency</div>
                <div className="font-[JetBrains_Mono] text-sm uppercase tracking-widest text-neutral-500 mt-1" style={{ fontFamily: "'JetBrains Mono'" }}>Contextual Pipeline</div>
              </div>
              <div className="w-32 h-12 flex items-end">
                <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 30">
                  <path className="text-[#FA500F]" d="M0 30 L20 20 L40 25 L60 10 L80 15 L100 0" fill="none" stroke="currentColor" strokeWidth="2"></path>
                </svg>
              </div>
            </div>
          </div>
          <div className="lg:col-span-5 relative h-[500px] w-full rounded-none overflow-hidden bg-[#111111]">
            <img 
              alt="Abstract visualization of global network nodes connecting across a dark blue gradient background with glowing data points" 
              className="object-cover w-full h-full opacity-60 mix-blend-luminosity grayscale" 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuApCk56JF6vv3nD-Tzx66QJnKLsextK2rx3v1FaMzCj_cFkRubHeNz9DopUHiXIRTSH0p_5k8vOf75kdBec2aHTjRqO7Vcy8BjpfwRu2tw-EHlb_hDZtO7TcswLxp2FRgkAWz7YfPr2UQDlRg0JVqyPfynhw1meyCNm2qO6ezcVa3NR3C0kKzKdYqObDjrvlbGYkitVyQD636E1BYd5mYJmIWwubSlakQbXxMoEibDCEA5Y_AE7rY_AeeCGxpGlbUt3fLJAaiur40Hb" 
            />
            <div className="absolute inset-0 bg-gradient-to-tr from-black via-transparent to-transparent"></div>
          </div>
        </section>

        {/* Mission & Values: Technical Line-Art */}
        <section className="flex flex-col gap-16">
          <div className="max-w-3xl">
            <h2 className="font-[JetBrains_Mono] text-sm uppercase tracking-widest text-[#FA500F] mb-4" style={{ fontFamily: "'JetBrains Mono'" }}>Core Telemetry</h2>
            <h3 className="font-headline text-3xl md:text-4xl font-bold tracking-tight text-white">Precision in Purpose</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Value 1 */}
            <div className="bg-[#111111] p-8 rounded-none border border-[#333333] group hover:border-[#FA500F] transition-colors duration-150 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Icon name="architecture" className="text-8xl text-white" />
              </div>
              <Icon name="architecture" className="text-4xl text-[#FA500F] mb-6 block" />
              <h4 className="font-headline text-xl font-bold text-white mb-3">Structural Integrity</h4>
              <p className="font-body text-neutral-400 leading-relaxed">
                We build linguistic models that respect the structural integrity of native syntaxes, ensuring absolute fidelity in high-stakes B2B communications.
              </p>
            </div>
            {/* Value 2 */}
            <div className="bg-[#111111] p-8 rounded-none border border-[#333333] group hover:border-[#FA500F] transition-colors duration-150 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Icon name="sync_alt" className="text-8xl text-white" />
              </div>
              <Icon name="sync_alt" className="text-4xl text-[#FA500F] mb-6 block" />
              <h4 className="font-headline text-xl font-bold text-white mb-3">Asynchronous Alignment</h4>
              <p className="font-body text-neutral-400 leading-relaxed">
                Cultural nuances are processed asynchronously, allowing for deep-contextual mapping without interrupting the real-time flow of enterprise data.
              </p>
            </div>
            {/* Value 3 */}
            <div className="bg-[#111111] p-8 rounded-none border border-[#333333] group hover:border-[#FA500F] transition-colors duration-150 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Icon name="verified_user" className="text-8xl text-white" />
              </div>
              <Icon name="verified_user" className="text-4xl text-[#FA500F] mb-6 block" />
              <h4 className="font-headline text-xl font-bold text-white mb-3">Zero-Trust Localism</h4>
              <p className="font-body text-neutral-400 leading-relaxed">
                Our models assume zero inherent bias, validating every contextual leap against localized, high-fidelity data nodes to ensure absolute accuracy.
              </p>
            </div>
          </div>
        </section>

        {/* Leadership Architecture: Bento Grid */}
        <section className="flex flex-col gap-16">
          <div className="flex justify-between items-end">
            <div>
              <h2 className="font-[JetBrains_Mono] text-sm uppercase tracking-widest text-[#FA500F] mb-4" style={{ fontFamily: "'JetBrains Mono'" }}>Node Operators</h2>
              <h3 className="font-headline text-3xl md:text-4xl font-bold tracking-tight text-white">Leadership Architecture</h3>
            </div>
            <button className="hidden md:flex items-center gap-2 text-[#FA500F] hover:text-white transition-colors font-[JetBrains_Mono] uppercase text-sm tracking-wider" style={{ fontFamily: "'JetBrains Mono'" }}>
              View Full Directory <Icon name="arrow_forward" className="text-sm" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 auto-rows-[minmax(300px,auto)]">
            {/* Lead Node */}
            <div className="md:col-span-8 bg-[#111111] rounded-none p-8 relative flex flex-col justify-end overflow-hidden group hover:border-[#FA500F] border border-[#333333] transition-colors duration-150">
              <img 
                alt="Trịnh Võ Nam Kiệt" 
                className="absolute inset-0 w-full h-full object-cover mix-blend-luminosity opacity-40 group-hover:opacity-50 transition-opacity grayscale" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDzWpZ5n3ye1b2Os1HhS3wQNCZU_v-F9aEu8I57uX54gi0fFeBSFTaRbo2gqc42aLQZ1bIMUEns3gPfH9lMT4ZBoWOFXc7CIN2rcXXLbKh_p8qpkrqQe793MyAnZIv9hKIKTpiAx2ZnLtTBfA15Sq5xorHBufp78ag53SNoW2wyD3KWCIxbd88c17jZ5pZzB-P8ykxv4jqoTm2ghbOekkwH0aLJXR0z6vf4O444DUN_H9i9_b1cZPdlcBHF4UfTFKWlYWNLiQh5FkXh" 
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent"></div>
              <div className="relative z-10">
                <div className="font-[JetBrains_Mono] text-xs text-[#FA500F] mb-2" style={{ fontFamily: "'JetBrains Mono'" }}>SYS.ARCHITECT // 001</div>
                <h4 className="font-headline text-3xl font-bold text-white mb-1">Trịnh Võ Nam Kiệt</h4>
                <p className="font-body text-neutral-400">Chief Executive Officer</p>
              </div>
            </div>
            {/* Node 2 */}
            <div className="md:col-span-4 bg-[#111111] rounded-none p-8 relative flex flex-col justify-end overflow-hidden group hover:border-[#FA500F] border border-[#333333] transition-colors duration-150">
              <img 
                alt="Lê Thị Mai Trang" 
                className="absolute inset-0 w-full h-full object-cover mix-blend-luminosity opacity-40 group-hover:opacity-50 transition-opacity grayscale" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuC8qbFHzJgwc-JwwpIKB31OE002YkHqimmXuHTMIgThgUON-eY62OhIPAJNl1tyGBhYBfdPDqxcooDN1B-3vLmMu2r5d5bE9sq5peT4e6yRbjbZZiD7uS2wDWykUGxZUw1T9kiCRfyHYTmsl1-A-wmQdb40Wv5smYlX6vhuuiZeFBQjbU5bqh05Mtw3xA1m4SlNgj9o0b8-OMvJ3Zb0hVKHJo_uZCsHBv_9aGoHbW31kEM8NKFCNIgDhlFk5nh5kRjNt09yt9d2iQ8o" 
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent"></div>
              <div className="relative z-10">
                <div className="font-[JetBrains_Mono] text-xs text-[#FA500F] mb-2" style={{ fontFamily: "'JetBrains Mono'" }}>DATA.LEAD // 002</div>
                <h4 className="font-headline text-xl font-bold text-white mb-1">Lê Thị Mai Trang</h4>
                <p className="font-body text-neutral-400 text-sm">Head of AI Research</p>
              </div>
            </div>
            {/* Node 3 */}
            <div className="md:col-span-4 bg-[#111111] rounded-none p-8 relative flex flex-col justify-end overflow-hidden group hover:border-[#FA500F] border border-[#333333] transition-colors duration-150">
              <img 
                alt="Nguyễn Hải Đăng" 
                className="absolute inset-0 w-full h-full object-cover mix-blend-luminosity opacity-40 group-hover:opacity-50 transition-opacity grayscale" 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuA73zWGzomiC5VcNBdNqWbslBgLQQW-5NLvP6ZReaZhcORZUKMTj5cCqO8mYZxz-dIZJS7b2DfNQIkl10G8gPtz2Y754fE-wmgcfnQejeGHodsONSVY1aE4Vp5nm3RpAZuRDBqT74AgJDEMMRJ9Hb6CiA2qo8yGaDtr6dPC1cHLjkZaCrlTCfdQQo0nyMO-HK-THzQDwioArXxGFuBc-gr4YQMnwiUQgvuBXVGX7Glr607YqqY1xewXKKxB0kK2DQoZuO7L4hAK3ch3" 
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent"></div>
              <div className="relative z-10">
                <div className="font-[JetBrains_Mono] text-xs text-[#FA500F] mb-2" style={{ fontFamily: "'JetBrains Mono'" }}>OPS.CORE // 003</div>
                <h4 className="font-headline text-xl font-bold text-white mb-1">Nguyễn Hải Đăng</h4>
                <p className="font-body text-neutral-400 text-sm">VP of Operations</p>
              </div>
            </div>
            {/* Stat Block */}
            <div className="md:col-span-8 bg-[#111111] border border-[#333333] rounded-none p-8 flex flex-col justify-center items-center text-center">
              <div className="font-[JetBrains_Mono] text-6xl font-bold text-[#FA500F] mb-4" style={{ fontFamily: "'JetBrains Mono'" }}>42+</div>
              <h4 className="font-headline text-xl font-bold text-white mb-2">Global Deployments</h4>
              <p className="font-body text-neutral-400 max-w-md">Nodes active across 15 timezones, ensuring localized latency under 50ms.</p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full py-16 px-12 border-t border-[#333333] bg-[#000000]">
        <div className="flex flex-col md:flex-row justify-between items-center max-w-[1920px] mx-auto w-full">
          <div className="font-headline font-black text-white mb-6 md:mb-0">MISTRAL.AI</div>
          <div className="flex gap-6 font-[JetBrains_Mono] text-[10px] uppercase tracking-wider text-neutral-500" style={{ fontFamily: "'JetBrains Mono'" }}>
            <a className="hover:text-[#FA500F] transition-colors" href="#">Privacy Policy</a>
            <a className="hover:text-[#FA500F] transition-colors" href="#">Security</a>
            <a className="hover:text-[#FA500F] transition-colors" href="#">Open Source</a>
            <a className="hover:text-[#FA500F] transition-colors" href="#">Changelog</a>
          </div>
          <div className="font-[JetBrains_Mono] text-[10px] uppercase tracking-wider text-neutral-500 mt-6 md:mt-0" style={{ fontFamily: "'JetBrains Mono'" }}>
            © 2024 Kinetic Monolith Systems. AI-Optimized.
          </div>
        </div>
      </footer>
    </div>
  )
}
