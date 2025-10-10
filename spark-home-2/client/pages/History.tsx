import { useNavigate } from 'react-router-dom';
import SapientLogo from '@/components/SapientLogo';

export default function History() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#313131] flex flex-col items-center py-12 px-4">
      {/* Header */}
      <div className="w-full max-w-[1280px] flex items-center justify-between mb-8">
        <div className="pl-4">
          <SapientLogo variant="default" />
        </div>
        
        {/* Back Arrow */}
        <button 
          onClick={() => navigate(-1)}
          className="pr-4 transition-transform hover:scale-110"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 21 21"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M13.125 5.25L7.875 10.5L13.125 15.75"
              stroke="#C1C1C1"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 w-full max-w-[1280px] flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl text-white mb-4">Chat History</h1>
          <p className="text-sm text-gray-400">
            Your conversation history will appear here
          </p>
        </div>
      </div>
    </div>
  );
}
