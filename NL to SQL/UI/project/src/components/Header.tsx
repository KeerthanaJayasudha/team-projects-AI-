interface HeaderProps {
  onConfigureClick: () => void;
}

function Header({ onConfigureClick }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        
        {/* Logo + Title */}
        <div className="flex items-center gap-3">
          {/* SVG Logo: chat bubble + SQL cursor */}
          <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            {/* Chat bubble */}
            <rect x="2" y="2" width="20" height="14" rx="4" fill="#2563EB" />
            <path d="M6 16 L4 21 L11 17" fill="#2563EB" />
            {/* SQL "cursor" lines inside bubble */}
            <rect x="6" y="7" width="5" height="1.5" rx="0.75" fill="white" />
            <rect x="6" y="10" width="9" height="1.5" rx="0.75" fill="white" opacity="0.7" />
            {/* Spark dot — represents AI/analytics */}
            <circle cx="24" cy="6" r="3" fill="#F59E0B" />
            <path d="M24 3.5 L24.5 5.5 L26.5 6 L24.5 6.5 L24 8.5 L23.5 6.5 L21.5 6 L23.5 5.5 Z" fill="white" />
          </svg>

          <span className="text-xl font-semibold text-gray-900 tracking-tight">
            Insight<span className="text-blue-600">SQL</span>
          </span>
        </div>

        <button
          onClick={onConfigureClick}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          Configure Database
        </button>
      </div>
    </header>
  );
}

export default Header;
