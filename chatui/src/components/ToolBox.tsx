type ActiveTool = "none" | "research" | "rag" | "whisper";

interface ToolBoxProps {
  activeTool: ActiveTool;
  onToolChange: (tool: ActiveTool) => void;
}

export default function ToolBox({ activeTool, onToolChange }: ToolBoxProps) {
  const handleToolClick = (tool: ActiveTool) => {
    // Toggle the tool - if it's already active, deactivate it
    if (activeTool === tool) {
      onToolChange("none");
    } else {
      onToolChange(tool);
    }
  };

  return (
    <div className="w-[155px] h-[40px] rounded-[5px] bg-tool-bg shadow-sm mx-auto">
      <div className="flex items-center justify-center h-full px-2 gap-[9px]">
        {/* Deep Research Tool */}
        <button
          onClick={() => handleToolClick("research")}
          className={`w-[38px] h-[31px] rounded-md shadow-sm hover:bg-tool-button/80 transition-all duration-300 flex items-center justify-center ${
            activeTool === "research" ? "bg-gradient-to-b from-[#F69F1C]/79 via-[#FBA11A]/80 to-[#F69F1C]/80" : "bg-tool-button"
          }`}
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g clipPath="url(#clip0_1_17)">
              <path 
                d="M7.07143 20.4285C10.5429 20.4285 13.3571 17.6143 13.3571 14.1428C13.3571 10.6713 10.5429 7.85712 7.07143 7.85712C3.59993 7.85712 0.785721 10.6713 0.785721 14.1428C0.785721 17.6143 3.59993 20.4285 7.07143 20.4285Z" 
                stroke="#C1C1C1" 
                strokeWidth="1.57143" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
              <path 
                d="M14.9286 20.4285C18.4001 20.4285 21.2143 17.6143 21.2143 14.1428C21.2143 10.6713 18.4001 7.85712 14.9286 7.85712C11.4571 7.85712 8.64287 10.6713 8.64287 14.1428C8.64287 17.6143 11.4571 20.4285 14.9286 20.4285Z" 
                stroke="#C1C1C1" 
                strokeWidth="1.57143" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
              <path 
                d="M11 14.1428C14.4715 14.1428 17.2857 11.3286 17.2857 7.85713C17.2857 4.38562 14.4715 1.57141 11 1.57141C7.5285 1.57141 4.71429 4.38562 4.71429 7.85713C4.71429 11.3286 7.5285 14.1428 11 14.1428Z" 
                stroke="#C1C1C1" 
                strokeWidth="1.57143" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <clipPath id="clip0_1_17">
                <rect width="22" height="22" fill="white"/>
              </clipPath>
            </defs>
          </svg>
        </button>

        {/* RAG Tool */}
        <button
          onClick={() => handleToolClick("rag")}
          className={`w-[38px] h-[31px] rounded-md shadow-sm hover:opacity-80 transition-all duration-300 flex items-center justify-center ${
            activeTool === "rag" ? "bg-[#F69F1C]/80" : "bg-tool-button"
          }`}
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g clipPath="url(#clip0_1_23)">
              <path
                d="M5.50001 15.7143H1.57144C1.1375 15.7143 0.785721 16.0661 0.785721 16.5V20.4286C0.785721 20.8625 1.1375 21.2143 1.57144 21.2143H5.50001C5.93394 21.2143 6.28572 20.8625 6.28572 20.4286V16.5C6.28572 16.0661 5.93394 15.7143 5.50001 15.7143Z"
                stroke={activeTool === "rag" ? "#191818" : "url(#paint0_linear_1_23)"}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M20.4286 15.7143H16.5C16.0661 15.7143 15.7143 16.0661 15.7143 16.5V20.4286C15.7143 20.8625 16.0661 21.2143 16.5 21.2143H20.4286C20.8625 21.2143 21.2143 20.8625 21.2143 20.4286V16.5C21.2143 16.0661 20.8625 15.7143 20.4286 15.7143Z"
                stroke={activeTool === "rag" ? "#191818" : "url(#paint1_linear_1_23)"}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M13.3571 0.785706H8.64286C8.20892 0.785706 7.85715 1.13748 7.85715 1.57142V6.28571C7.85715 6.71964 8.20892 7.07142 8.64286 7.07142H13.3571C13.7911 7.07142 14.1429 6.71964 14.1429 6.28571V1.57142C14.1429 1.13748 13.7911 0.785706 13.3571 0.785706Z"
                stroke={activeTool === "rag" ? "#191818" : "url(#paint2_linear_1_23)"}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M6.28572 18.8571H15.7143"
                stroke={activeTool === "rag" ? "#191818" : "url(#paint3_linear_1_23)"}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M7.99857 6.74139L3.92857 15.7143"
                stroke={activeTool === "rag" ? "#191818" : "url(#paint4_linear_1_23)"}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M14.0014 6.74139L18.0714 15.7143"
                stroke={activeTool === "rag" ? "#191818" : "url(#paint5_linear_1_23)"}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <linearGradient id="paint0_linear_1_23" x1="3.53572" y1="15.7143" x2="3.53572" y2="21.2143" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="0.677885" stopColor="#F68D51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint1_linear_1_23" x1="18.4643" y1="15.7143" x2="18.4643" y2="21.2143" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="0.677885" stopColor="#F68D51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint2_linear_1_23" x1="11" y1="0.785706" x2="11" y2="7.07142" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="0.677885" stopColor="#F68D51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint3_linear_1_23" x1="11" y1="18.8571" x2="11" y2="19.8571" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="0.677885" stopColor="#F68D51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint4_linear_1_23" x1="5.96357" y1="6.74139" x2="5.96357" y2="15.7143" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="0.677885" stopColor="#F68D51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint5_linear_1_23" x1="16.0364" y1="6.74139" x2="16.0364" y2="15.7143" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="0.677885" stopColor="#F68D51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <clipPath id="clip0_1_23">
                <rect width="22" height="22" fill="white"/>
              </clipPath>
            </defs>
          </svg>
        </button>
        {/* Whisper Tool */}
        <button
          onClick={() => handleToolClick("whisper")}
          className={`w-[38px] h-[31px] rounded-md shadow-sm hover:bg-tool-button/80 transition-all duration-300 flex items-center justify-center ${
            activeTool === "whisper" ? "bg-gradient-to-b from-[#F69F1C]/79 via-[#FBA11A]/80 to-[#F69F1C]/80" : "bg-tool-button"
          }`}
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g clipPath="url(#clip0_1_36)">
              <path 
                d="M11 14.1429C12.9527 14.1429 14.5357 12.5599 14.5357 10.6072C14.5357 8.65447 12.9527 7.07147 11 7.07147C9.04729 7.07147 7.46429 8.65447 7.46429 10.6072C7.46429 12.5599 9.04729 14.1429 11 14.1429Z" 
                stroke="#C1C1C1" 
                strokeWidth="1.57143" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
              <path 
                d="M17.2857 21.2144C16.6908 20.0601 15.7896 19.0919 14.6808 18.416C13.572 17.7401 12.2986 17.3825 11 17.3825C9.70146 17.3825 8.42798 17.7401 7.31921 18.416C6.21044 19.0919 5.30919 20.0601 4.71429 21.2144" 
                stroke="#C1C1C1" 
                strokeWidth="1.57143" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
              <path 
                d="M18.8571 16.5943C19.9723 15.1398 20.6582 13.4023 20.8373 11.5782C21.0164 9.75422 20.6815 7.91648 19.8705 6.27286C19.0596 4.62924 17.8049 3.24533 16.2484 2.27764C14.6919 1.30996 12.8957 0.797119 11.0629 0.797119C9.23006 0.797119 7.43383 1.30996 5.87732 2.27764C4.32081 3.24533 3.06612 4.62924 2.25517 6.27286C1.44421 7.91648 1.10934 9.75422 1.28843 11.5782C1.46752 13.4023 2.15343 15.1398 3.26857 16.5943" 
                stroke="#C1C1C1" 
                strokeWidth="1.57143" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <clipPath id="clip0_1_36">
                <rect width="22" height="22" fill="white"/>
              </clipPath>
            </defs>
          </svg>
        </button>
      </div>
    </div>
  );
}
