import React from 'react';

export const ChatInterfaceNew: React.FC<{onToggleTheme?: () => void; isDarkMode?: boolean}> = (props) => {
  return (
    <div className="flex flex-col h-screen bg-white">
      <div className="flex-1 bg-white px-5 overflow-y-auto flex flex-col items-center">
        <img
          src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/06qqsua7_expires_30_days.png"}
          alt="main icon"
          className="w-[76px] h-[76px] mt-[347px] mb-[286px] object-fill"
        />
        <div className="flex flex-col items-start self-stretch bg-white py-[11px] mb-[31px] rounded-[5px]"
          style={{
            boxShadow: "0px 0px 6px #00000040"
          }}>
          <button className="flex items-center bg-[#8C57FF] text-left py-[5px] px-[9px] mb-[9px] ml-3 gap-[5px] rounded-sm border-0"
            style={{
              boxShadow: "0px 1px 4px #00000040"
            }}
            onClick={() => alert("Pressed!")}>
            <img
              src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/klyra8z8_expires_30_days.png"}
              alt="rag icon"
              className="w-4 h-4 object-fill"
            />
            <span className="text-[#ECECEC] text-[10px] font-bold">
              {"RAG"}
            </span>
          </button>
          <span className="text-[#575353] text-xs ml-3.5">
            {"Ask, search and I'll answer...."}
          </span>
          <div className="flex justify-between items-center self-stretch mx-3.5">
            <img
              src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/c9tf2e84_expires_30_days.png"}
              alt="icon 1"
              className="w-[25px] h-[25px] object-fill"
            />
            <img
              src={"https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/em0r1ivc_expires_30_days.png"}
              alt="icon 2"
              className="w-[41px] h-[41px] object-fill"
            />
          </div>
        </div>
      </div>
    </div>
  );
};