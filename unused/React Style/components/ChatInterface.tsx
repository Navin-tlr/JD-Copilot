import { useState } from 'react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  sessionId: string;
}

interface ChatInterfaceProps {
  onToggleTheme: () => void;
  isDarkMode: boolean;
}

export function ChatInterface({ onToggleTheme, isDarkMode }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId] = useState(`session_${Date.now()}_user`);
  // Removed showChat state - keeping consistent UI
  const [isFocused, setIsFocused] = useState(false);
  const [isHoveringCard, setIsHoveringCard] = useState(false);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;
    
    const userMessage: Message = {
      id: Date.now().toString(),
      content: content.trim(),
      sender: 'user',
      timestamp: new Date(),
      sessionId
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      // Send message to Python backend
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: content,
          session_id: sessionId
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.answer || 'I received your message but couldn\'t generate a response.',
          sender: 'ai',
          timestamp: new Date(),
          sessionId
        };
        
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error('Backend response error');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Fallback response when backend is not available
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Hello! I\'m your placement assistant. Please start the Python backend server to get real AI responses about placements and job descriptions.',
        sender: 'ai',
        timestamp: new Date(),
        sessionId
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isTyping) {
      handleSendMessage(input);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isTyping) {
        handleSendMessage(input);
      }
    }
    if (e.key === 'Escape') {
      setInput('');
    }
  };

  // Always use the same UI layout - don't change UI when messages are sent

  // Original project aesthetics with responsive design and minimal interactions
  return (
    <div className="flex flex-col bg-white min-h-screen">
      {/* Main content area with responsive container */}
      <div className="flex flex-col items-center self-stretch bg-white flex-1 px-4 sm:px-5 md:px-6 lg:px-8">
        
        {/* Messages area with proper spacing */}
        <div className="w-full max-w-sm sm:max-w-md md:max-w-lg lg:max-w-xl xl:max-w-2xl flex-1 overflow-y-auto">
          {messages.length > 0 && (
            <div className="pt-4 pb-6 space-y-4">
              {messages.map((message, index) => (
                <div 
                  key={message.id}
                  className="animate-fade-in"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  {message.sender === 'user' ? (
                    // User message with original styling
                    <div className="flex justify-end">
                      <div className="bg-[#8C57FF] text-white rounded-lg px-4 py-2 max-w-[80%] shadow-sm">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                      </div>
                    </div>
                  ) : (
                    // AI message with clean design
                    <div className="flex justify-start">
                      <div className="bg-gray-50 text-gray-800 rounded-lg px-4 py-2 max-w-[80%] shadow-sm border border-gray-100">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              
              {/* Minimal typing indicator */}
              {isTyping && (
                <div className="flex justify-start animate-fade-in">
                  <div className="bg-gray-50 border border-gray-100 rounded-lg px-4 py-2 shadow-sm">
                    <div className="flex items-center gap-1">
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Center icon when no messages - responsive sizing */}
        <div className={`flex flex-col items-center transition-all duration-300 ${
          messages.length > 0 ? 'mt-0 mb-4' : 'mt-[25vh] sm:mt-[30vh] md:mt-[35vh] mb-[20vh] sm:mb-[25vh] md:mb-[30vh]'
        }`}>
          <img
            src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/06qqsua7_expires_30_days.png"} 
            alt="JD Copilot"
            className={`object-fill transition-all duration-300 hover:scale-105 ${
              messages.length > 0 ? 'w-8 h-8' : 'w-[60px] h-[60px] sm:w-[75px] sm:h-[76px]'
            }`}
          />
        </div>

        {/* Input card with original styling - responsive */}
        <div className={`w-full max-w-sm sm:max-w-md md:max-w-lg lg:max-w-xl mb-6 sm:mb-8 ${
          messages.length > 0 ? 'mt-auto' : ''
        }`}>
          <div 
            className="flex flex-col items-start bg-white py-[11px] rounded-[5px] transition-all duration-200 hover:shadow-lg"
            style={{
              boxShadow: isHoveringCard || isFocused 
                ? "0px 2px 12px rgba(0, 0, 0, 0.15)" 
                : "0px 0px 6px #00000040"
            }}
            onMouseEnter={() => setIsHoveringCard(true)}
            onMouseLeave={() => setIsHoveringCard(false)}
          >
            {/* RAG Button with original styling */}
            <div className="flex items-center bg-[#8C57FF] py-[5px] px-[9px] mb-[9px] ml-3 gap-[5px] rounded-sm transition-all duration-200 hover:bg-[#7B4AE8] active:scale-98 cursor-pointer" 
              style={{
                boxShadow: "0px 1px 4px #00000040"
              }}
              onClick={() => {
                const inputElement = document.querySelector('input[type="text"]') as HTMLInputElement;
                inputElement?.focus();
              }}>
              <div className="flex flex-col shrink-0 items-center">
                <img
                  src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/klyra8z8_expires_30_days.png"} 
                  alt="RAG icon"
                  className="w-3.5 h-4 object-fill"
                />
              </div>
              <span className="text-[#ECECEC] text-[10px] font-bold">
                RAG
              </span>
            </div>
            
            {/* Input text area */}
            <div className="w-full px-3.5 mb-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onKeyDown={handleKeyDown}
                placeholder={isTyping ? "AI is thinking..." : "Ask, search and I'll answer...."}
                className={`w-full text-xs bg-transparent border-none outline-none transition-colors duration-200 resize-none ${
                  isFocused 
                    ? 'text-gray-800 placeholder:text-[#8C57FF]' 
                    : 'text-[#575353] placeholder:text-[#575353]'
                }`}
                disabled={isTyping}
              />
            </div>
            
            {/* Bottom icons row with original layout */}
            <div className="flex justify-between items-center self-stretch mx-3.5">
              <div className="flex flex-col shrink-0 items-center pb-[1px]">
                <img
                  src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/c9tf2e84_expires_30_days.png"} 
                  alt="Gallery icon"
                  className="w-[23px] h-[23px] object-fill cursor-pointer transition-opacity duration-200 hover:opacity-70 active:scale-95"
                />
              </div>
              
              {/* Send button with activation state */}
              <button
                onClick={() => {
                  if (input.trim()) {
                    handleSendMessage(input);
                  }
                }}
                disabled={!input.trim() || isTyping}
                className={`transition-all duration-200 active:scale-95 ${
                  input.trim() && !isTyping
                    ? 'opacity-100 cursor-pointer hover:opacity-80'
                    : 'opacity-40 cursor-not-allowed'
                }`}
              >
                <img
                  src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/em0r1ivc_expires_30_days.png"}
                  alt="Send icon" 
                  className={`w-[22px] h-[22px] mt-[9px] mb-2 mx-2.5 object-fill transition-all duration-200 ${
                    input.trim() && !isTyping
                      ? 'filter brightness-110'
                      : 'filter grayscale-[20%]'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// Icon Components

function AndroidIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <g clipPath="url(#clip0_2_108)">
        <path d="M15.24 7.62H14.475V11.43H15.24V7.62Z" fill="#ECECEC"/>
        <path d="M13.715 12.195H14.475V11.43H13.715V7.61996H14.475V6.85996H13.715V5.33496H12.95V6.85996H3.04999V5.33496H2.28499V6.85996H1.52499V7.61996H2.28499V11.43H1.52499V12.195H2.28499V12.955H3.04999V7.61996H12.95V12.955H13.715V12.195Z" fill="#ECECEC"/>
        <path d="M13.715 0H12.95V0.765H13.715V0Z" fill="#ECECEC"/>
        <path d="M12.95 12.955H12.19V13.715H12.95V12.955Z" fill="#ECECEC"/>
        <path d="M12.95 3.81H12.19V5.335H12.95V3.81Z" fill="#ECECEC"/>
        <path d="M12.95 0.765015H12.19V1.52501H12.95V0.765015Z" fill="#ECECEC"/>
        <path d="M12.19 3.04999H11.43V3.80999H12.19V3.04999Z" fill="#ECECEC"/>
        <path d="M12.19 1.52502H11.43V2.29002H12.19V1.52502Z" fill="#ECECEC"/>
        <path d="M10.665 15.24H11.43V14.48H12.19V13.715H10.665V15.24Z" fill="#ECECEC"/>
        <path d="M11.43 2.29004H9.90499V3.05004H11.43V2.29004Z" fill="#ECECEC"/>
        <path d="M10.665 15.24H9.145V16H10.665V15.24Z" fill="#ECECEC"/>
        <path d="M6.855 13.715V15.24H7.62V14.48H8.38V15.24H9.145V13.715H6.855Z" fill="#ECECEC"/>
        <path d="M9.90499 1.52502H6.09499V2.29002H9.90499V1.52502Z" fill="#ECECEC"/>
        <path d="M6.85499 15.24H5.33499V16H6.85499V15.24Z" fill="#ECECEC"/>
        <path d="M11.43 6.095V4.575H10.665V3.81H5.33499V4.575H4.56999V6.095H11.43ZM9.14499 4.575H9.90499V5.335H9.14499V4.575ZM6.09499 4.575H6.85499V5.335H6.09499V4.575Z" fill="#ECECEC"/>
        <path d="M6.09499 2.29004H4.56999V3.05004H6.09499V2.29004Z" fill="#ECECEC"/>
        <path d="M3.81 13.715V14.48H4.57V15.24H5.335V13.715H3.81Z" fill="#ECECEC"/>
        <path d="M4.57 3.04999H3.81V3.80999H4.57V3.04999Z" fill="#ECECEC"/>
        <path d="M4.57 1.52502H3.81V2.29002H4.57V1.52502Z" fill="#ECECEC"/>
        <path d="M3.81 12.955H3.05V13.715H3.81V12.955Z" fill="#ECECEC"/>
        <path d="M3.81 3.81H3.05V5.335H3.81V3.81Z" fill="#ECECEC"/>
        <path d="M3.81 0.765015H3.05V1.52501H3.81V0.765015Z" fill="#ECECEC"/>
        <path d="M3.05 0H2.285V0.765H3.05V0Z" fill="#ECECEC"/>
        <path d="M1.52499 7.62H0.759995V11.43H1.52499V7.62Z" fill="#ECECEC"/>
      </g>
      <defs>
        <clipPath id="clip0_2_108">
          <rect width="16" height="16" fill="white"/>
        </clipPath>
      </defs>
    </svg>
  );
}

function ImageIconInteractive() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg" className="transition-all duration-300">
      <g className="transition-colors duration-300 group-hover:fill-gray-600">
        <path d="M24.5526 1.79193H23.3501V19.7584H24.5526V1.79193Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M5.38365 19.7584V20.953H6.58613V22.1555H7.78075V20.953H10.1779V22.1555H11.3725V20.953H13.7696V22.1555H14.9642V20.953H17.3613V22.1555H18.5638V20.953H19.7584V22.1555H18.5638V23.3501H16.1667V22.1555H14.9642V23.3501H12.575V22.1555H11.3725V23.3501H8.98323V22.1555H7.78075V23.3501H5.38365V22.1555H4.18903V23.3501H1.79193V24.5526H19.7584V23.3501H20.953V20.953H23.3501V19.7584H5.38365Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M20.953 10.1778H18.5638V11.3725H20.953V14.972H22.1555V4.18903H20.953V10.1778Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M18.5638 13.7696H17.3613V14.9721H7.78075V16.1667H20.953V14.9721H18.5638V13.7696Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M19.7584 5.38367H17.3613V7.78077H19.7584V5.38367Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M18.5638 11.3725H17.3613V12.575H18.5638V11.3725Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M17.3613 12.575H16.1667V13.7696H17.3613V12.575Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M16.1667 11.3725H14.9642V12.575H16.1667V11.3725Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M14.9642 10.1779H13.7696V11.3725H14.9642V10.1779Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M13.7696 8.98322H11.3725V10.1778H13.7696V8.98322Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M11.3725 10.1779H10.1778V11.3725H11.3725V10.1779Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M10.1778 11.3725H8.98322V12.575H10.1778V11.3725Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M20.953 2.99438H7.78075V4.18901H20.953V2.99438Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M8.98322 13.7696V12.5749H7.78074V4.18903H6.58612V14.972H7.78074V13.7696H8.98322Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M23.3501 0.59729H5.38364V1.79191H23.3501V0.59729Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M4.18903 20.9531H2.99441V22.1555H4.18903V20.9531Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
        <path d="M2.99441 20.953V19.7584H1.79193V17.3613H2.99441V16.1667H1.79193V13.7696H2.99441V12.575H1.79193V10.1779H2.99441V8.98323H1.79193V6.58613H2.99441V5.38365H4.18903V6.58613H2.99441V7.78075H4.18903V10.1779H2.99441V11.3725H4.18903V13.7696H2.99441V14.9721H4.18903V17.3613H2.99441V18.5638H4.18903V19.7584H5.38365V1.79193H4.18903V4.18903H1.79193V5.38365H0.597305V23.3501H1.79193V20.953H2.99441Z" fill="#999999" className="transition-colors duration-300 group-hover:fill-gray-600"/>
      </g>
    </svg>
  );
}

function UploadIconInteractive({ isActive }: { isActive: boolean }) {
  return (
    <svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg" className="transition-all duration-300">
      <g clipPath="url(#clip0_2_138)">
        <path 
          d="M11.4 18.5L19 10.9L26.6 18.5" 
          stroke={isActive ? "#3B82F6" : "#A1A1A2"} 
          strokeWidth="1.735" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          className="transition-colors duration-300 group-hover:stroke-blue-500"
        />
        <path 
          d="M19 10.9V27.1" 
          stroke={isActive ? "#3B82F6" : "#A1A1A2"} 
          strokeWidth="1.735" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          className="transition-colors duration-300 group-hover:stroke-blue-500"
        />
        <path 
          d="M19 35C27.284 35 34 28.284 34 20C34 11.716 27.284 5 19 5C10.716 5 4 11.716 4 20C4 28.284 10.716 35 19 35Z" 
          stroke={isActive ? "#3B82F6" : "#A1A1A2"} 
          strokeWidth="1.735" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          className="transition-colors duration-300 group-hover:stroke-blue-500"
        />
      </g>
      <defs>
        <clipPath id="clip0_2_138">
          <rect width="38" height="38" fill="white"/>
        </clipPath>
      </defs>
    </svg>
  );
}
