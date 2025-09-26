import { useState } from "react";
import ChatComponent from "../components/ChatComponent";
import ToolBox from "../components/ToolBox";
import ChatHistoryArrow from "../components/ChatHistoryArrow";
import RAGWelcome from "../components/RAGWelcome";

type ActiveTool = "none" | "research" | "rag" | "whisper";

export default function Index() {
  const [activeTool, setActiveTool] = useState<ActiveTool>("none");

  // Determine background color based on active tool
  const getBackgroundColor = () => {
    switch (activeTool) {
      case "rag":
        return "bg-[#F69F1C]/80"; // Orange background from Figma
      default:
        return "bg-background"; // Default dark background
    }
  };

  return (
    <div className={`min-h-screen overflow-hidden transition-colors duration-500 ${getBackgroundColor()}`}>
      {/* Main container with mobile-first design */}
      <div className={`relative w-full h-screen max-w-[390px] mx-auto transition-colors duration-500 ${getBackgroundColor()}`}>
        {/* Main content area - flex to push chat components to bottom */}
        <div className="flex flex-col h-full justify-end pb-[39px]">
          {/* RAG Welcome message - only show when RAG tool is active */}
          {activeTool === "rag" && (
            <div className="px-[39px] mb-8 animate-in slide-in-from-top-4 duration-500">
              <RAGWelcome />
            </div>
          )}

          {/* Chat component positioned from bottom */}
          <div className="px-[39px] mb-[12px]">
            <ChatComponent />
          </div>

          {/* Bottom row with toolbox and history arrow */}
          <div className="flex items-center justify-between px-[39px]">
            {/* Tool box centered */}
            <div className="flex-1 flex justify-center">
              <ToolBox activeTool={activeTool} onToolChange={setActiveTool} />
            </div>

            {/* Chat history arrow positioned to the right */}
            <div className="ml-[43px]">
              <ChatHistoryArrow isOrangeTheme={activeTool === "rag"} />
            </div>
          </div>
        </div>
      </div>

      {/* Responsive layout for larger screens */}
      <div className={`hidden sm:block fixed inset-0 transition-colors duration-500 ${getBackgroundColor()}`}>
        <div className="flex items-center justify-center h-full">
          <div className={`relative w-[390px] h-[844px] rounded-lg shadow-2xl overflow-hidden transition-colors duration-500 ${getBackgroundColor()}`}>
            {/* Mobile design preview for larger screens */}
            <div className="flex flex-col h-full justify-end pb-[39px]">
              {/* RAG Welcome message for desktop */}
              {activeTool === "rag" && (
                <div className="px-[39px] mb-8 animate-in slide-in-from-top-4 duration-500">
                  <RAGWelcome />
                </div>
              )}

              <div className="px-[39px] mb-[12px]">
                <ChatComponent />
              </div>

              <div className="flex items-center justify-between px-[39px]">
                <div className="flex-1 flex justify-center">
                  <ToolBox activeTool={activeTool} onToolChange={setActiveTool} />
                </div>
                <div className="ml-[43px]">
                  <ChatHistoryArrow isOrangeTheme={activeTool === "rag"} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
