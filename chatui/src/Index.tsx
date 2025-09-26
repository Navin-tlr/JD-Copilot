import { useState } from "react";
import ChatComponent from "./components/ChatComponent";
import ToolBox from "./components/ToolBox";
import ChatHistoryArrow from "./components/ChatHistoryArrow";
import RAGWelcome from "./components/RAGWelcome";

type ActiveTool = "none" | "research" | "rag" | "whisper";

export default function Index() {
  const [activeTool, setActiveTool] = useState<ActiveTool>("none");
  const getBackgroundColor = () => (activeTool === "rag" ? "bg-[#F69F1C]/80" : "bg-background"); // already correct, but ensure usage below
  return (
    <div className={`min-h-screen overflow-hidden transition-colors duration-500 ${getBackgroundColor()}`}>
      <div className={`relative w-full h-screen max-w-[390px] mx-auto transition-colors duration-500 ${getBackgroundColor()}`}>
        {/* Figma-accurate vertical stack */}
        <div className="absolute left-0 right-0 top-0 h-full flex flex-col justify-end pb-[39px]">
          {/* Welcome card: absolute, Figma top offset */}
          {activeTool === "rag" && (
            <div className="absolute left-1/2 -translate-x-1/2 top-[90px] z-10 animate-in slide-in-from-top-4 duration-500">
              <RAGWelcome />
            </div>
          )}
          {/* Spacer to push chat and toolbox to bottom */}
          <div className="flex-1" />
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
      {/* Desktop view */}
  <div className={`hidden sm:block fixed inset-0 transition-colors duration-500 ${getBackgroundColor()}`}>
        <div className="flex items-center justify-center h-full">
          <div className={`relative w-[390px] h-[844px] rounded-lg shadow-2xl overflow-hidden transition-colors duration-500 ${getBackgroundColor()}`}>
            <div className="absolute left-0 right-0 top-0 h-full flex flex-col justify-end pb-[39px]">
              {activeTool === "rag" && (
                <div className="absolute left-1/2 -translate-x-1/2 top-[90px] z-10 animate-in slide-in-from-top-4 duration-500">
                  <RAGWelcome />
                </div>
              )}
              <div className="flex-1" />
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
