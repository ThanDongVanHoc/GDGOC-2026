import { Link, useNavigate, useLocation } from 'react-router-dom'

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

export default function NavBar() {
  const navigate = useNavigate()
  const location = useLocation()
  const path = location.pathname

  const isLinkActive = (href) => path === href

  return (
    <nav className="fixed top-0 w-full z-50 bg-[#201f1f]/80 backdrop-blur-xl shadow-[0_4px_20px_rgba(0,0,0,0.4)] border-b border-outline-variant/10">
      <div className="flex justify-between items-center h-20 px-8 w-full max-w-[1920px] mx-auto">
        {/* Brand */}
        <div className="flex items-center gap-8">
          <Link to="/" className="text-2xl font-black tracking-tighter text-[#FA500F] uppercase cursor-pointer active:scale-[0.98] transition-transform">
            OmniLocal
          </Link>
          <div className="hidden md:flex gap-6 items-center text-sm font-headline tracking-tight font-medium">
            <Link 
              to="/" 
              className={`${isLinkActive('/') ? 'text-[#FA500F] border-b-2 border-[#FA500F] pb-1' : 'text-[#e5e2e1] opacity-60 hover:opacity-100'} px-2 py-1 transition-all duration-150`}
            >
              Framework
            </Link>
            <Link 
              to="/upload" 
              className={`${isLinkActive('/upload') || isLinkActive('/pipeline') ? 'text-[#FA500F] border-b-2 border-[#FA500F] pb-1' : 'text-[#e5e2e1] opacity-60 hover:opacity-100'} px-2 py-1 transition-all duration-150`}
            >
              Workspace
            </Link>
            <Link 
              to="/blog" 
              className={`${isLinkActive('/blog') ? 'text-[#FA500F] border-b-2 border-[#FA500F] pb-1' : 'text-[#e5e2e1] opacity-60 hover:opacity-100'} px-2 py-1 transition-all duration-150`}
            >
              Blog
            </Link>
            <Link 
              to="/about" 
              className={`${isLinkActive('/about') ? 'text-[#FA500F] border-b-2 border-[#FA500F] pb-1' : 'text-[#e5e2e1] opacity-60 hover:opacity-100'} px-2 py-1 transition-all duration-150`}
            >
              About
            </Link>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <button className="text-[#e5e2e1] opacity-60 hover:opacity-100 transition-opacity px-4 py-2 rounded text-sm font-medium">
            System Status
          </button>
          <button 
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 bg-gradient-to-r from-[#FA500F] to-[#cc3f09] text-[#000000] px-6 py-2.5 rounded font-bold text-sm tracking-wide shadow-[0_0_20px_rgba(255,87,27,0.2)] hover:opacity-90 active:scale-[0.98] transition-all"
          >
            <Icon name="rocket_launch" className="text-base" />
            Deploy Agent
          </button>
        </div>
      </div>
    </nav>
  )
}
