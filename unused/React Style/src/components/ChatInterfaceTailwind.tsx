import React from 'react';

export const ChatInterfaceTailwind: React.FC<{onToggleTheme?: () => void; isDarkMode?: boolean}> = (props) => {
  return (
    <div className="flex flex-col h-screen bg-white">
      <div className="flex-1 bg-white px-5 overflow-y-auto flex flex-col items-center">
        <img
          src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/06qqsua7_expires_30_days.png"
          alt="main icon"
          className="w-[76px] h-[76px] mt-[347px] mb-[286px] object-stretch"
        />
        <div className="bg-white rounded-[5px] py-[11px] mb-[31px] shadow-[0px_0px_6px_rgba(0,0,0,0.25)] w-full max-w-[390px]">
          <button
            className="flex flex-row items-center bg-[#8C57FF] rounded-[2px] py-[5px] px-[9px] mb-[9px] ml-3 shadow-[0px_1px_4px_rgba(0,0,0,0.25)] border-none cursor-pointer w-fit hover:bg-[#7B48E6] active:bg-[#6A3DD4] transition-colors duration-200"
            onClick={() => alert('Pressed!')}
          >
            <img
              src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/swb43i6i_expires_30_days.png"
              alt="rag icon"
              className="w-4 h-4 mr-[5px] object-stretch"
            />
            <span className="text-[#ECECEC] text-[10px] font-bold m-0">
              RAG
            </span>
          </button>
          <p className="text-[#575353] text-xs ml-[14px] m-0">
            Ask, search and I'll answer....
          </p>
          <div className="flex flex-row justify-between items-center mx-[14px]">
            <img
              src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/jp5ykuk4_expires_30_days.png"
              alt="icon 1"
              className="w-[25px] h-[25px] object-stretch"
            />
            <img
              src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/xx8dfl3s_expires_30_days.png"
              alt="icon 2"
              className="w-[41px] h-[41px] object-stretch"
            />
          </div>
        </div>
      </div>
    </div>
  );
};