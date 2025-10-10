import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import SapientLogo from '@/components/SapientLogo';
import ChatInput from '@/components/ChatInput';

export default function Benchmark() {
  const navigate = useNavigate();
  const [welcomeVisible, setWelcomeVisible] = useState(true);

  const handleSend = (value: string) => {
    setWelcomeVisible(false);
    console.log('Benchmark send:', value);
  };

  return (
    <div className="min-h-screen bg-[#E5E5E5] flex flex-col items-center justify-between py-12 px-4 relative animate-fade-in">
      {/* Freeze Overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Coming Soon</h2>
          <p className="text-gray-600">This feature is currently under development and will be available soon.</p>
        </div>
      </div>
      {/* Header */}
      <div className="w-full max-w-[1280px] flex items-center justify-between">
        <div className="pl-4">
          <SapientLogo variant="benchmark" />
        </div>

        {/* Chat History Arrow */}
        <button
          onClick={() => navigate('/history')}
          className="pr-4 transition-transform hover:scale-110"
        >
          <svg
            width="21"
            height="21"
            viewBox="0 0 21 21"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_93_320)">
              <path
                d="M0.75 9V2.25C0.75 1.85218 0.908035 1.47064 1.18934 1.18934C1.47064 0.908035 1.85218 0.75 2.25 0.75H18.75C19.1478 0.75 19.5294 0.908035 19.8107 1.18934C20.092 1.47064 20.25 1.85218 20.25 2.25V18.75C20.25 19.1478 20.092 19.5294 19.8107 19.8107C19.5294 20.092 19.1478 20.25 18.75 20.25H12"
                stroke="#464646"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M6 20.25H0.75V15"
                stroke="#464646"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M0.75 20.25L10.5 10.5"
                stroke="#464646"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <clipPath id="clip0_93_320">
                <rect width="21" height="21" fill="white" />
              </clipPath>
            </defs>
          </svg>
        </button>
      </div>

      {/* Content Area - Deep Research Icon and Description */}
      <div className="flex-1 w-full max-w-[1280px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-8">
          {/* Large Deep Research Icon */}
          <svg
            className="w-[175px] h-[175px] animate-fade-in"
            viewBox="0 0 175 175"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M56.2504 162.5C83.8647 162.5 106.25 140.114 106.25 112.5C106.25 84.886 83.8647 62.5002 56.2504 62.5002C28.6362 62.5002 6.25043 84.886 6.25043 112.5C6.25043 140.114 28.6362 162.5 56.2504 162.5Z"
              stroke="url(#paint0_linear_93_342)"
              strokeWidth="12.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M118.751 162.5C146.365 162.5 168.751 140.114 168.751 112.5C168.751 84.886 146.365 62.5002 118.751 62.5002C91.1364 62.5002 68.7507 84.886 68.7507 112.5C68.7507 140.114 91.1364 162.5 118.751 162.5Z"
              stroke="url(#paint1_linear_93_342)"
              strokeWidth="12.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M87.5005 112.5C115.115 112.5 137.501 90.1145 137.501 62.5002C137.501 34.886 115.115 12.5002 87.5005 12.5002C59.8863 12.5002 37.5005 34.886 37.5005 62.5002C37.5005 90.1145 59.8863 112.5 87.5005 112.5Z"
              stroke="url(#paint2_linear_93_342)"
              strokeWidth="12.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <defs>
              <linearGradient id="paint0_linear_93_342" x1="56.2504" y1="62.5002" x2="56.2504" y2="162.5" gradientUnits="userSpaceOnUse">
                <stop stopColor="#7D94C5" />
                <stop offset="0.461538" stopColor="#8483C3" />
                <stop offset="1" stopColor="#4B649A" />
              </linearGradient>
              <linearGradient id="paint1_linear_93_342" x1="118.751" y1="62.5002" x2="118.751" y2="162.5" gradientUnits="userSpaceOnUse">
                <stop stopColor="#7D94C5" />
                <stop offset="0.461538" stopColor="#8483C3" />
                <stop offset="1" stopColor="#4B649A" />
              </linearGradient>
              <linearGradient id="paint2_linear_93_342" x1="87.5005" y1="12.5002" x2="87.5005" y2="112.5" gradientUnits="userSpaceOnUse">
                <stop stopColor="#7D94C5" />
                <stop offset="0.461538" stopColor="#8483C3" />
                <stop offset="1" stopColor="#4B649A" />
              </linearGradient>
            </defs>
          </svg>

          {/* Description */}
          <div className="flex items-start gap-2 max-w-[247px]">
            <svg
              className="w-[13px] h-2 mt-[3px] flex-shrink-0"
              viewBox="0 0 13 8"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <g clipPath="url(#clip0_140_75)">
                <path
                  d="M3.64579 7.5L0.45575 4L3.64579 0.5"
                  stroke="#000001"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <path
                  d="M9.11444 7.5L12.3045 4L9.11444 0.5"
                  stroke="#000001"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
              <defs>
                <clipPath id="clip0_140_75">
                  <rect width="12.7601" height="8" fill="white" />
                </clipPath>
              </defs>
            </svg>
            <p className="text-[11px] leading-[15px] text-[#B00DBB]">
              Peer Benchmark: Don't worry this is anonymous and the main objective is to improve the collective competitiveness.
            </p>
          </div>
        </div>
      </div>

      {/* Chat Input */}
      <div className="w-full flex justify-center">
        <ChatInput variant="benchmark" />
      </div>
    </div>
  );
}
