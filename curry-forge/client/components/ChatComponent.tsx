import { useState } from "react";

export default function ChatComponent() {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (message.trim()) {
      // Handle send logic here
      console.log("Sending:", message);
      setMessage("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="w-full max-w-[312px] h-[85px] rounded-[5px] border border-white/25 bg-chat-bg shadow-lg mx-auto">
      <div className="p-[13px] h-full flex flex-col justify-between">
        {/* Input text area */}
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Alright genius, spit out..."
          className="font-hack text-[11px] text-white/60 bg-transparent border-none outline-none resize-none placeholder:text-white/60 flex-1 w-full"
          rows={2}
        />
        
        {/* Bottom row with icons */}
        <div className="flex justify-between items-center mt-2">
          {/* Attachment icon */}
          <button className="p-1 hover:bg-white/10 rounded transition-colors">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path 
                d="M10.75 11.5V3C10.75 2.33696 10.4866 1.70107 10.0178 1.23223C9.54893 0.763392 8.91304 0.5 8.25 0.5H5.75C5.08696 0.5 4.45107 0.763392 3.98223 1.23223C3.51339 1.70107 3.25 2.33696 3.25 3V11.5C3.25 12.0304 3.46071 12.5391 3.83579 12.9142C4.21086 13.2893 4.71957 13.5 5.25 13.5H6.25C6.78043 13.5 7.28914 13.2893 7.66421 12.9142C8.03929 12.5391 8.25 12.0304 8.25 11.5V4C8.25 3.73478 8.14464 3.48043 7.95711 3.29289C7.76957 3.10536 7.51522 3 7.25 3H6.75C6.48478 3 6.23043 3.10536 6.04289 3.29289C5.85536 3.48043 5.75 3.73478 5.75 4V9.5" 
                stroke="#A9A9A9" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </button>

          {/* Send arrow */}
          <button 
            onClick={handleSend}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path 
                d="M6 4L9 7L6 10" 
                stroke="#B5B5B5" 
                strokeOpacity="0.87" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
              <path 
                d="M7 13.5C10.5899 13.5 13.5 10.5899 13.5 7C13.5 3.41015 10.5899 0.5 7 0.5C3.41015 0.5 0.5 3.41015 0.5 7C0.5 10.5899 3.41015 13.5 7 13.5Z" 
                stroke="#B5B5B5" 
                strokeOpacity="0.87" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
