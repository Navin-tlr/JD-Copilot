interface ChatHistoryArrowProps {
  isOrangeTheme?: boolean;
}

export default function ChatHistoryArrow({ isOrangeTheme = false }: ChatHistoryArrowProps) {
  const handleHistoryClick = () => {
    console.log("Chat history clicked");
  };

  const strokeColor = isOrangeTheme ? "#464646" : "#C1C1C1";

  return (
    <button
      onClick={handleHistoryClick}
      className="w-[21px] h-[21px] hover:bg-white/10 rounded transition-colors p-1"
    >
      <svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clipPath="url(#clip0_1_57)">
          <path
            d="M0.75 9V2.25C0.75 1.85218 0.908035 1.47064 1.18934 1.18934C1.47064 0.908035 1.85218 0.75 2.25 0.75H18.75C19.1478 0.75 19.5294 0.908035 19.8107 1.18934C20.092 1.47064 20.25 1.85218 20.25 2.25V18.75C20.25 19.1478 20.092 19.5294 19.8107 19.8107C19.5294 20.092 19.1478 20.25 18.75 20.25H12"
            stroke={strokeColor}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M6 20.25H0.75V15"
            stroke={strokeColor}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M0.75 20.25L10.5 10.5"
            stroke={strokeColor}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>
        <defs>
          <clipPath id="clip0_1_57">
            <rect width="21" height="21" fill="white"/>
          </clipPath>
        </defs>
      </svg>
    </button>
  );
}
