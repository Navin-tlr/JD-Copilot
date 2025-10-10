import { useNavigate } from 'react-router-dom';
import SapientLogo from '@/components/SapientLogo';
import ChatInput from '@/components/ChatInput';

export default function Index() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#313131] flex flex-col items-center justify-between py-12 px-4 relative animate-fade-in">
      {/* Header */}
      <div className="w-full max-w-[1280px] flex items-center justify-between">
        <div className="pl-4">
          <SapientLogo variant="default" />
        </div>
        
        {/* Chat History Arrow */}
        <button 
          onClick={() => navigate('/history')}
          className="pr-4 transition-transform hover:scale-110"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 21 21"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_93_79)">
              <path
                d="M0.75 9V2.25C0.75 1.85218 0.908035 1.47064 1.18934 1.18934C1.47064 0.908035 1.85218 0.75 2.25 0.75H18.75C19.1478 0.75 19.5294 0.908035 19.8107 1.18934C20.092 1.47064 20.25 1.85218 20.25 2.25V18.75C20.25 19.1478 20.092 19.5294 19.8107 19.8107C19.5294 20.092 19.1478 20.25 18.75 20.25H12"
                stroke="#C1C1C1"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M6 20.25H0.75V15"
                stroke="#C1C1C1"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M0.75 20.25L10.5 10.5"
                stroke="#C1C1C1"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <clipPath id="clip0_93_79">
                <rect width="21" height="21" fill="white"/>
              </clipPath>
            </defs>
          </svg>
        </button>
      </div>

      <div className="flex-1 w-full max-w-[1280px] flex items-center justify-center">
      </div>

      {/* Chat Input */}
      <div className="w-full flex justify-center">
        <ChatInput variant="default" />
      </div>
    </div>
  );
}
