export default function RAGWelcome() {
  return (
    <div className="relative w-[308px] mx-auto mb-8">
      {/* Drop shadow container */}
      <div className="absolute inset-0 bg-black/25 rounded-md translate-y-1 blur-[6.5px]" />
      
      {/* Main welcome card */}
      <div className="relative bg-[#424242] rounded-md p-6 border border-white/10">
        {/* Mascot character */}
        <div className="absolute -top-3 left-6">
          <svg width="50" height="40" viewBox="0 0 80 50" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Green mascot body */}
            <ellipse 
              cx="40" 
              cy="25" 
              rx="35" 
              ry="20" 
              fill="#51DA7F" 
              stroke="black" 
              strokeWidth="0.5"
              transform="rotate(-25 40 25)"
            />
            {/* Pink eye */}
            <circle 
              cx="42" 
              cy="20" 
              r="8" 
              fill="#F8CEEE" 
              stroke="black" 
              strokeWidth="0.5"
              transform="rotate(-25 42 20)"
            />
            {/* Black pupil */}
            <circle 
              cx="43" 
              cy="16" 
              r="2.5" 
              fill="black"
              transform="rotate(-25 43 16)"
            />
            {/* Character outline detail */}
            <path 
              d="M15 30C13 27 10 20 15 15C20 8 38 5 35 15" 
              stroke="black" 
              strokeWidth="0.5" 
              fill="none"
            />
          </svg>
        </div>

        {/* Welcome text */}
        <div className="pt-8">
          <h3 className="font-hack text-[11px] font-bold text-[#BDB6B6] mb-4">
            Welcome to RAG.
          </h3>
          
          <p className="font-hack text-[11px] text-[#BDB6B6] leading-relaxed">
            It digs through job descriptions so<br />
            you don't have to. Ask a sharp question,<br />
            or don't bother
          </p>
        </div>
      </div>
    </div>
  );
}
