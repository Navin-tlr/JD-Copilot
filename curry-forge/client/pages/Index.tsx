import React, { useState, useEffect, useRef, useCallback } from 'react';

import { cn } from '@/lib/utils';

type AppMode = 'default' | 'rag' | 'deep-research';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const DEFAULT_USER_ID = 'anonymous';
const HISTORY_STORAGE_KEY = 'jd_chat_history';
const SESSION_STORAGE_KEY = 'jd_chat_session_id';

const sessionStorageKey = (sessionId: string) => `${HISTORY_STORAGE_KEY}:${sessionId}`;

type TranscriptEntry = {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
  timestamp?: string;
};

type SessionSummary = {
  session_id: string;
  title?: string | null;
  updated_at?: string | null;
  message_count?: number | null;
  last_message_preview?: string | null;
};

const createSessionId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `session-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
};

const formatTimestamp = (iso?: string | null) => {
  if (!iso) return '';
  try {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return '';
  }
};

const RagIcon = ({ isActive, className }: { isActive?: boolean; className?: string }) => (
  <svg
    width="22"
    height="22"
    viewBox="0 0 22 22"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <g clipPath="url(#clip0_rag)">
      <path d="M5.50001 15.7143H1.57144C1.1375 15.7143 0.785721 16.0661 0.785721 16.5V20.4286C0.785721 20.8625 1.1375 21.2143 1.57144 21.2143H5.50001C5.93394 21.2143 6.28572 20.8625 6.28572 20.4286V16.5C6.28572 16.0661 5.93394 15.7143 5.50001 15.7143Z" stroke={isActive ? '#191818' : 'url(#paint0_linear_rag)'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20.4286 15.7143H16.5C16.0661 15.7143 15.7143 16.0661 15.7143 16.5V20.4286C15.7143 20.8625 16.0661 21.2143 16.5 21.2143H20.4286C20.8625 21.2143 21.2143 20.8625 21.2143 20.4286V16.5C21.2143 16.0661 20.8625 15.7143 20.4286 15.7143Z" stroke={isActive ? '#191818' : 'url(#paint1_linear_rag)'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M13.3571 0.785706H8.64286C8.20892 0.785706 7.85715 1.13748 7.85715 1.57142V6.28571C7.85715 6.71964 8.20892 7.07142 8.64286 7.07142H13.3571C13.7911 7.07142 14.1429 6.71964 14.1429 6.28571V1.57142C14.1429 1.13748 13.7911 0.785706 13.3571 0.785706Z" stroke={isActive ? '#191818' : 'url(#paint2_linear_rag)'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6.28572 18.8571H15.7143" stroke={isActive ? '#191818' : 'url(#paint3_linear_rag)'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7.99857 6.74139L3.92857 15.7143" stroke={isActive ? '#191818' : 'url(#paint4_linear_rag)'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14.0014 6.74139L18.0714 15.7143" stroke={isActive ? '#191818' : 'url(#paint5_linear_rag)'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
    </g>
    <defs>
      <linearGradient id="paint0_linear_rag" x1="3.53572" y1="15.7143" x2="3.53572" y2="21.2143" gradientUnits="userSpaceOnUse"><stop stopColor="#F68E51" /><stop offset="0.677885" stopColor="#F68D51" /><stop offset="1" stopColor="#F68D51" /></linearGradient>
      <linearGradient id="paint1_linear_rag" x1="18.4643" y1="15.7143" x2="18.4643" y2="21.2143" gradientUnits="userSpaceOnUse"><stop stopColor="#F68E51" /><stop offset="0.677885" stopColor="#F68D51" /><stop offset="1" stopColor="#F68D51" /></linearGradient>
      <linearGradient id="paint2_linear_rag" x1="11" y1="0.785706" x2="11" y2="7.07142" gradientUnits="userSpaceOnUse"><stop stopColor="#F68E51" /><stop offset="0.677885" stopColor="#F68D51" /><stop offset="1" stopColor="#F68D51" /></linearGradient>
      <linearGradient id="paint3_linear_rag" x1="11" y1="18.8571" x2="11" y2="19.8571" gradientUnits="userSpaceOnUse"><stop stopColor="#F68E51" /><stop offset="0.677885" stopColor="#F68D51" /><stop offset="1" stopColor="#F68D51" /></linearGradient>
      <linearGradient id="paint4_linear_rag" x1="5.96357" y1="6.74139" x2="5.96357" y2="15.7143" gradientUnits="userSpaceOnUse"><stop stopColor="#F68E51" /><stop offset="0.677885" stopColor="#F68D51" /><stop offset="1" stopColor="#F68D51" /></linearGradient>
      <linearGradient id="paint5_linear_rag" x1="16.0364" y1="6.74139" x2="16.0364" y2="15.7143" gradientUnits="userSpaceOnUse"><stop stopColor="#F68E51" /><stop offset="0.677885" stopColor="#F68D51" /><stop offset="1" stopColor="#F68D51" /></linearGradient>
      <clipPath id="clip0_rag"><rect width="22" height="22" fill="white" /></clipPath>
    </defs>
  </svg>
);

// Updated DeepResearchIcon: white by default, blue gradient only when active
const DeepResearchIcon = ({ isActive, className }: { isActive?: boolean; className?: string }) => (
  <svg
    width="22"
    height="22"
    viewBox="0 0 22 22"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <g clipPath="url(#clip0_deep_new)">
  <path d="M7.07142 20.4285C10.5429 20.4285 13.3571 17.6143 13.3571 14.1428C13.3571 10.6713 10.5429 7.85712 7.07142 7.85712C3.59992 7.85712 0.785706 10.6713 0.785706 14.1428C0.785706 17.6143 3.59992 20.4285 7.07142 20.4285Z" stroke={isActive ? 'url(#paint0_linear_deep_new)' : '#C1C1C1'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
  <path d="M14.9285 20.4285C18.4 20.4285 21.2143 17.6143 21.2143 14.1428C21.2143 10.6713 18.4 7.85712 14.9285 7.85712C11.457 7.85712 8.64282 10.6713 8.64282 14.1428C8.64282 17.6143 11.457 20.4285 14.9285 20.4285Z" stroke={isActive ? 'url(#paint1_linear_deep_new)' : '#C1C1C1'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
  <path d="M11 14.1428C14.4715 14.1428 17.2857 11.3286 17.2857 7.85713C17.2857 4.38562 14.4715 1.57141 11 1.57141C7.5285 1.57141 4.71429 4.38562 4.71429 7.85713C4.71429 11.3286 7.5285 14.1428 11 14.1428Z" stroke={isActive ? 'url(#paint2_linear_deep_new)' : '#C1C1C1'} strokeWidth="1.57143" strokeLinecap="round" strokeLinejoin="round" />
    </g>
    <defs>
      <linearGradient id="paint0_linear_deep_new" x1="7.07142" y1="7.85712" x2="7.07142" y2="20.4285" gradientUnits="userSpaceOnUse">
        <stop stopColor="#7D94C5" />
        <stop offset="0.461538" stopColor="#8483C3" />
        <stop offset="1" stopColor="#4B649A" />
      </linearGradient>
      <linearGradient id="paint1_linear_deep_new" x1="14.9285" y1="7.85712" x2="14.9285" y2="20.4285" gradientUnits="userSpaceOnUse">
        <stop stopColor="#7D94C5" />
        <stop offset="0.461538" stopColor="#8483C3" />
        <stop offset="1" stopColor="#4B649A" />
      </linearGradient>
      <linearGradient id="paint2_linear_deep_new" x1="11" y1="1.57141" x2="11" y2="14.1428" gradientUnits="userSpaceOnUse">
        <stop stopColor="#7D94C5" />
        <stop offset="0.461538" stopColor="#8483C3" />
        <stop offset="1" stopColor="#4B649A" />
      </linearGradient>
      <clipPath id="clip0_deep_new">
        <rect width="22" height="22" fill="white" />
      </clipPath>
    </defs>
  </svg>
);

const WhisperIcon = ({ className }: { className?: string }) => (
  <svg 
    width="22" 
    height="22" 
    viewBox="0 0 22 22" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <g clipPath="url(#clip0_whisper)">
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
      <clipPath id="clip0_whisper">
        <rect width="22" height="22" fill="white"/>
      </clipPath>
    </defs>
  </svg>
);

const SendArrowIcon = ({ mode, onClick, disabled }: { mode: AppMode; onClick?: () => void; disabled?: boolean }) => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 14 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    onClick={() => !disabled && onClick?.()}
    role="button"
    aria-label="Send message"
    className={cn(disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer select-none')}
  >
    <path
      d="M6 4L9 7L6 10"
      stroke={mode === 'deep-research' ? '#3D3A3A' : '#B5B5B5'}
      strokeOpacity="0.87"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M7 13.5C10.5899 13.5 13.5 10.5899 13.5 7C13.5 3.41015 10.5899 0.5 7 0.5C3.41015 0.5 0.5 3.41015 0.5 7C0.5 10.5899 3.41015 13.5 7 13.5Z"
      stroke={mode === 'deep-research' ? '#3D3A3A' : '#B5B5B5'}
      strokeOpacity="0.87"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const StopIcon = ({ onClick }: { onClick?: () => void }) => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 14 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    role="button"
    aria-label="Stop generation"
    onClick={() => onClick?.()}
    className="cursor-pointer select-none"
  >
    <rect x="2.5" y="2.5" width="9" height="9" rx="1" stroke="#FFFFFF" strokeOpacity="0.85" />
    <circle cx="7" cy="7" r="6.25" stroke="#FFFFFF" strokeOpacity="0.35" />
  </svg>
);

const AttachmentIcon = ({ mode }: { mode: AppMode }) => (
  <svg 
    width="14" 
    height="14" 
    viewBox="0 0 14 14" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <path 
      d="M10.75 11.5V3C10.75 2.33696 10.4866 1.70107 10.0178 1.23223C9.54893 0.763392 8.91304 0.5 8.25 0.5H5.75C5.08696 0.5 4.45107 0.763392 3.98223 1.23223C3.51339 1.70107 3.25 2.33696 3.25 3V11.5C3.25 12.0304 3.46071 12.5391 3.83579 12.9142C4.21086 13.2893 4.71957 13.5 5.25 13.5H6.25C6.78043 13.5 7.28914 13.2893 7.66421 12.9142C8.03929 12.5391 8.25 12.0304 8.25 11.5V4C8.25 3.73478 8.14464 3.48043 7.95711 3.29289C7.76957 3.10536 7.51522 3 7.25 3H6.75C6.48478 3 6.23043 3.10536 6.04289 3.29289C5.85536 3.48043 5.75 3.73478 5.75 4V9.5" 
      stroke={mode === 'deep-research' ? "#494747" : "#A9A9A9"} 
      strokeLinecap="round" 
      strokeLinejoin="round"
    />
  </svg>
);

const ChatHistoryIcon = ({ mode }: { mode: AppMode }) => (
  <svg 
    width="21" 
    height="21" 
    viewBox="0 0 21 21" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <g clipPath="url(#clip0_history)">
      <path 
        d="M0.75 9V2.25C0.75 1.85218 0.908035 1.47064 1.18934 1.18934C1.47064 0.908035 1.85218 0.75 2.25 0.75H18.75C19.1478 0.75 19.5294 0.908035 19.8107 1.18934C20.092 1.47064 20.25 1.85218 20.25 2.25V18.75C20.25 19.1478 20.092 19.5294 19.8107 19.8107C19.5294 20.092 19.1478 20.25 18.75 20.25H12" 
        stroke={mode === 'deep-research' ? "#525151" : mode === 'rag' ? "#464646" : "#C1C1C1"} 
        strokeWidth="1.5" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <path 
        d="M6 20.25H0.75V15" 
        stroke={mode === 'deep-research' ? "#525151" : mode === 'rag' ? "#464646" : "#C1C1C1"} 
        strokeWidth="1.5" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
      <path 
        d="M0.75 20.25L10.5 10.5" 
        stroke={mode === 'deep-research' ? "#525151" : mode === 'rag' ? "#464646" : "#C1C1C1"} 
        strokeWidth="1.5" 
        strokeLinecap="round" 
        strokeLinejoin="round"
      />
    </g>
    <defs>
      <clipPath id="clip0_history">
        <rect width="21" height="21" fill="white"/>
      </clipPath>
    </defs>
  </svg>
);

// Icon used to prefix assistant answers (lightbulb / idea symbol)
const AnswerIcon = ({ className }: { className?: string }) => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 14 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <g clipPath="url(#clip0_answer)" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.5 8.00001C10.5023 7.37594 10.3377 6.76259 10.0233 6.22351C9.70888 5.68443 9.25603 5.23922 8.71168 4.93402C8.16732 4.62881 7.55126 4.4747 6.92732 4.48766C6.30338 4.50062 5.69425 4.68018 5.16303 5.00772C4.63182 5.33527 4.19785 5.79889 3.90607 6.35057C3.6143 6.90224 3.47534 7.52189 3.50359 8.14533C3.53184 8.76877 3.72626 9.37331 4.06673 9.89634C4.4072 10.4194 4.88132 10.8418 5.43998 11.12V12.84C5.44258 12.9417 5.48482 13.0383 5.55768 13.1093C5.63054 13.1803 5.72825 13.22 5.82998 13.22H8.16998C8.2717 13.22 8.36941 13.1803 8.44227 13.1093C8.51513 13.0383 8.55737 12.9417 8.55998 12.84V11.09C9.13622 10.8032 9.62219 10.3629 9.96446 9.81779C10.3067 9.27264 10.492 8.64365 10.5 8.00001V8.00001Z" />
      <path d="M7 0.809998V2.31" />
      <path d="M10.9999 2.23999L9.93994 3.30999" />
      <path d="M13.28 5.34H11.78" />
      <path d="M3 2.23999L4.06 3.30999" />
      <path d="M0.719971 5.34H2.21997" />
    </g>
    <defs>
      <clipPath id="clip0_answer"><rect width="14" height="14" fill="white" /></clipPath>
    </defs>
  </svg>
);


// Exact Figma welcome card recreation
const WelcomeCardContent = () => (
  <div className="w-full max-w-sm flex justify-center">
    <svg
      width="308"
      height="149"
      viewBox="0 0 334 163"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="flex-shrink-0"
    >
      <g filter="url(#filter0_d_welcome)">
        <rect x="13" y="20" width="308" height="129" rx="6" fill="#424242"/>
      </g>
      <path
        d="M55.4586 17.0468C61.2888 14.2312 67.0447 12.6872 71.6338 12.4617C73.9287 12.3489 75.9249 12.5661 77.4903 13.1135C79.0546 13.6606 80.179 14.5334 80.755 15.7261C81.3309 16.9188 81.315 18.3416 80.7709 19.9067C80.2264 21.473 79.1553 23.1716 77.6401 24.8988C74.6101 28.3528 69.822 31.9007 63.9918 34.7163C58.1616 37.5319 52.4058 39.076 47.8166 39.3015C45.5218 39.4143 43.5255 39.1971 41.9602 38.6497C40.3961 38.1027 39.2718 37.2304 38.6958 36.0379C38.1198 34.8452 38.1353 33.4218 38.6795 31.8565C39.224 30.2902 40.2951 28.5916 41.8103 26.8644C44.8403 23.4104 49.6284 19.8624 55.4586 17.0468Z"
        fill="#51DA7F"
        stroke="black"
        strokeWidth="0.293442"
      />
      <circle
        cx="60.7438"
        cy="25.2427"
        r="8.88153"
        transform="rotate(-25.7774 60.7438 25.2427)"
        fill="#F8CEEE"
        stroke="black"
        strokeWidth="0.293442"
      />
      <circle
        cx="61.5183"
        cy="20.7399"
        r="2.65537"
        transform="rotate(-25.7774 61.5183 20.7399)"
        fill="black"
      />
      <path
        d="M38.6311 35.9211C36.7111 33.1553 33.9795 25.9259 38.4128 19.1353C43.9545 10.647 64.6378 6.65202 61.6559 18.2631"
        stroke="black"
        strokeWidth="0.293442"
      />
      <text
        fill="#BDB6B6"
        xmlSpace="preserve"
        style={{ whiteSpace: 'pre' }}
        fontFamily="Hack"
        fontSize="11"
        fontWeight="bold"
      >
        <tspan x="35" y="62.8081">Welcome to RAG. </tspan>
      </text>
      <text
        fill="#BDB6B6"
        xmlSpace="preserve"
        style={{ whiteSpace: 'pre' }}
        fontFamily="Hack"
        fontSize="11"
      >
        <tspan x="35" y="94.8081">It digs through job descriptions so </tspan>
        <tspan x="35" y="110.808">you don't have to. Ask a sharp question, </tspan>
        <tspan x="35" y="126.808">or don't bother</tspan>
      </text>
      <defs>
        <filter
          id="filter0_d_welcome"
          x="0"
          y="8"
          width="334"
          height="155"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feFlood floodOpacity="0" result="BackgroundImageFix"/>
          <feColorMatrix
            in="SourceAlpha"
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
            result="hardAlpha"
          />
          <feOffset dy="1"/>
          <feGaussianBlur stdDeviation="6.5"/>
          <feComposite in2="hardAlpha" operator="out"/>
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0"
          />
          <feBlend
            mode="normal"
            in2="BackgroundImageFix"
            result="effect1_dropShadow_welcome"
          />
          <feBlend
            mode="normal"
            in="SourceGraphic"
            in2="effect1_dropShadow_welcome"
            result="shape"
          />
        </filter>
      </defs>
    </svg>
  </div>
);

const ToolBox = ({ mode, onModeChange, onToggleRag }: { mode: AppMode; onModeChange: (mode: AppMode) => void; onToggleRag: () => void }) => {
  const getToolboxBg = () => {
    switch (mode) {
      case 'rag': return 'bg-rag-toolbox-dark';
      case 'deep-research': return 'bg-rag-toolbox-light';
      default: return 'bg-rag-toolbox-dark';
    }
  };

  const getButtonBg = (buttonMode: AppMode | 'welcome') => {
    const isActive = (buttonMode === 'welcome') ? false : mode === buttonMode;
    if (mode === 'rag') {
      if (isActive) return 'bg-gradient-to-b from-orange-400/80 via-orange-400/80 to-orange-400/80';
      return 'bg-rag-button-dark';
    }
    if (mode === 'deep-research') {
      return isActive ? 'bg-rag-button-light' : 'bg-rag-button-light';
    }
    return 'bg-rag-button-dark';
  };

  return (
    <div className={cn(
      "w-40 h-10 rounded-md shadow-sm flex items-center p-1",
      getToolboxBg()
    )}>
      {/* Deep Research (LEFT) - toggles light mode */}
      <button
        onClick={() => {
          if (mode === 'deep-research') onModeChange('default');
          else onModeChange('deep-research');
        }}
        aria-label="Deep Research"
        className={cn(
          "w-10 h-8 rounded-md flex items-center justify-center shadow-sm transition-all duration-200",
          getButtonBg('deep-research')
        )}
      >
        <DeepResearchIcon isActive={mode === 'deep-research'} />
      </button>

      {/* RAG Icon (CENTER) - toggles rag mode (shows inline welcome if not dismissed) */}
      <button
        onClick={() => onToggleRag()}
        aria-label="RAG Welcome"
        className={cn(
          "w-10 h-8 rounded-md flex items-center justify-center shadow-sm transition-all duration-200 ml-1.5",
          getButtonBg('rag')
        )}
      >
        <RagIcon isActive={mode === 'rag'} />
      </button>

      {/* Whisper / Default (RIGHT) - returns to default */}
      <button
        onClick={() => onModeChange('default')}
        aria-label="Whisper"
        className={cn(
          "w-10 h-8 rounded-md flex items-center justify-center shadow-sm transition-all duration-200 ml-1.5",
          getButtonBg('default')
        )}
      >
        <WhisperIcon />
      </button>
    </div>
  );
};
// ...existing code...

export default function Index() {
  const [mode, setMode] = useState<AppMode>('default');
  // showWelcome inline (no modal); fades away on first user interaction with input
  const [showWelcome, setShowWelcome] = useState(true);
  const [welcomeFaded, setWelcomeFaded] = useState(false);
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState<TranscriptEntry[]>([]);
  const convoRef = useRef<HTMLDivElement | null>(null);
  const userIdRef = useRef(DEFAULT_USER_ID);
  const [sessionId, setSessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = window.localStorage.getItem(SESSION_STORAGE_KEY);
        if (stored) {
          return stored;
        }
      } catch {/* ignore */}
    }
    return createSessionId();
  });
  const sessionIdRef = useRef(sessionId);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  // Company slash palette state
  const [companies, setCompanies] = useState<string[]>([]);
  const [showCompanyPalette, setShowCompanyPalette] = useState(false);
  const [companyQuery, setCompanyQuery] = useState("");
  
  // Role type selector state (triggered by ">")
  const [roleTypes, setRoleTypes] = useState<string[]>([]);
  const [showRoleTypePalette, setShowRoleTypePalette] = useState(false);
  const [roleTypeQuery, setRoleTypeQuery] = useState("");
  const paletteRef = useRef<HTMLDivElement | null>(null);
  const currentFrameRef = useRef<number | null>(null);
  const abortStreamingRef = useRef<{aborted:boolean}>({aborted:false});
  const abortControllerRef = useRef<AbortController | null>(null);
  const placeholderAssistantIdRef = useRef<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [pendingVectorApproval, setPendingVectorApproval] = useState<{question:string; reason?:string} | null>(null);

  const refreshSessions = useCallback(async () => {
    const normalizedUser = (userIdRef.current || DEFAULT_USER_ID).trim() || DEFAULT_USER_ID;
    try {
      setHistoryLoading(true);
      setHistoryError(null);
      const res = await fetch(`${API_BASE}/chat/history/sessions?user_id=${encodeURIComponent(normalizedUser)}`);
      if (!res.ok) {
        if (res.status === 404) {
          setSessions([]);
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      const list = Array.isArray(data.sessions) ? data.sessions : [];
      setSessions(list);
    } catch {
      setHistoryError('Unable to load history.');
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const beginNewSession = useCallback(() => {
    const next = createSessionId();
    setSessionId(next);
    sessionIdRef.current = next;
    setMessages([]);
    setPendingVectorApproval(null);
    setShowHistory(false);
    setShowWelcome(true);
    setWelcomeFaded(false);
    refreshSessions();
  }, [refreshSessions]);

  const deleteSession = useCallback(async (targetId: string) => {
    const normalizedUser = (userIdRef.current || DEFAULT_USER_ID).trim() || DEFAULT_USER_ID;
    try {
      await fetch(`${API_BASE}/chat/clear?session_id=${encodeURIComponent(targetId)}&user_id=${encodeURIComponent(normalizedUser)}`, {
        method: 'POST'
      });
    } catch {/* ignore */}
    try { localStorage.removeItem(sessionStorageKey(targetId)); } catch {/* ignore */}

    if (sessionIdRef.current === targetId) {
      beginNewSession();
    } else {
      refreshSessions();
    }
  }, [beginNewSession, refreshSessions]);

  const loadTranscript = useCallback(async (targetSessionId: string) => {
    const normalizedUser = (userIdRef.current || DEFAULT_USER_ID).trim() || DEFAULT_USER_ID;
    try {
      const res = await fetch(`${API_BASE}/chat/history/${encodeURIComponent(targetSessionId)}/transcript?user_id=${encodeURIComponent(normalizedUser)}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.messages)) {
          sessionIdRef.current = targetSessionId;
          setSessionId(targetSessionId);
          setMessages(data.messages as TranscriptEntry[]);
          setShowHistory(false);
          setPendingVectorApproval(null);
          if (data.messages.length) {
            setShowWelcome(false);
            setWelcomeFaded(true);
          }
          await refreshSessions();
          return;
        }
      } else if (res.status === 404) {
        sessionIdRef.current = targetSessionId;
        setSessionId(targetSessionId);
        setMessages([]);
        setShowHistory(false);
        setPendingVectorApproval(null);
        await refreshSessions();
        return;
      }
    } catch {/* ignore */}

    sessionIdRef.current = targetSessionId;
    setSessionId(targetSessionId);
    setShowHistory(false);
    setPendingVectorApproval(null);
  }, [refreshSessions]);

  const clearHistory = useCallback(async () => {
    await deleteSession(sessionIdRef.current);
  }, [deleteSession]);

  useEffect(() => {
    let active = true;
    const hydrate = async () => {
      const key = sessionStorageKey(sessionId);
      let fallback: TranscriptEntry[] = [];
      try {
        const raw = localStorage.getItem(key);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) fallback = parsed as TranscriptEntry[];
        }
      } catch {/* ignore */}

      const normalizedUser = (userIdRef.current || DEFAULT_USER_ID).trim() || DEFAULT_USER_ID;
      try {
        const res = await fetch(`${API_BASE}/chat/history/${encodeURIComponent(sessionId)}/transcript?user_id=${encodeURIComponent(normalizedUser)}`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data.messages)) {
            if (!active) return;
            setMessages(data.messages as TranscriptEntry[]);
            if (data.messages.length) {
              setShowWelcome(false);
              setWelcomeFaded(true);
            }
            return;
          }
        }
      } catch {/* ignore */}

      if (!active) return;
      setMessages(fallback);
      if (fallback.length) {
        setShowWelcome(false);
        setWelcomeFaded(true);
      }
    };

    hydrate();
    return () => { active = false; };
  }, [sessionId]);

  useEffect(() => {
    sessionIdRef.current = sessionId;
    try { localStorage.setItem(SESSION_STORAGE_KEY, sessionId); } catch {/* ignore */}
  }, [sessionId]);

  useEffect(() => {
    const key = sessionStorageKey(sessionIdRef.current);
    try { localStorage.setItem(key, JSON.stringify(messages)); } catch {/* ignore */}
  }, [messages, sessionId]);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    if (showHistory) {
      refreshSessions();
    }
  }, [showHistory, refreshSessions]);

  // Fetch companies and role types once
  useEffect(() => {
    (async () => {
      try {
        // Fetch companies
  const companiesRes = await fetch(`${API_BASE}/companies`);
        if (companiesRes.ok) {
          const companiesData = await companiesRes.json();
          const names: string[] = (companiesData.companies || []).map((c: any) => c.company_name).filter(Boolean);
          setCompanies(names.sort((a,b) => a.localeCompare(b)));
        }
        
        // Fetch role types
  const roleTypesRes = await fetch(`${API_BASE}/role-types`);
        if (roleTypesRes.ok) {
          const roleTypesData = await roleTypesRes.json();
          const types: string[] = (roleTypesData.role_types || []).filter(Boolean);
          setRoleTypes(types);
        }
      } catch {/* ignore network errors silently */}
    })();
  }, []);

  // Close palettes on outside click
  useEffect(() => {
    if (!showCompanyPalette && !showRoleTypePalette) return;
    const handler = (e: MouseEvent) => {
      if (paletteRef.current && !paletteRef.current.contains(e.target as Node)) {
        setShowCompanyPalette(false);
        setShowRoleTypePalette(false);
      }
    };
    window.addEventListener('mousedown', handler);
    return () => window.removeEventListener('mousedown', handler);
  }, [showCompanyPalette, showRoleTypePalette]);

  // Auto scroll
  useEffect(() => {
    if (convoRef.current) {
      convoRef.current.scrollTop = convoRef.current.scrollHeight;
    }
  }, [messages]);

  // Typing indicator (Perplexity-style pulsing dots) component
  const TypingIndicator = () => (
    <div className="h-6 w-6 select-none" aria-label="Thinking">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="ti_orbit_white" x1="12" y1="0" x2="12" y2="24" gradientUnits="userSpaceOnUse">
            <stop stopColor="#FFFFFF" stopOpacity="0.9" />
            <stop offset="1" stopColor="#FFFFFF" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <circle cx="12" cy="12" r="9" stroke="#FFFFFF" strokeOpacity="0.22" strokeWidth="1.25" />
        <circle cx="12" cy="12" r="9" stroke="url(#ti_orbit_white)" strokeWidth="1.5" strokeDasharray="40 22" strokeLinecap="round">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1.05s" repeatCount="indefinite" />
        </circle>
        <circle cx="12" cy="12" r="3.2" fill="#FFFFFF" fillOpacity="0.65">
          <animate attributeName="r" values="3.2;4.2;3.2" dur="1.3s" repeatCount="indefinite" />
          <animate attributeName="fill-opacity" values="0.65;1;0.65" dur="1.3s" repeatCount="indefinite" />
        </circle>
        <circle cx="20" cy="12" r="2" fill="#FFFFFF" fillOpacity="0.85">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1.05s" repeatCount="indefinite" />
          <animate attributeName="fill-opacity" values="0.3;0.85;0.3" dur="1.05s" repeatCount="indefinite" />
        </circle>
      </svg>
    </div>
  );

  // Toggle rag mode; when entering rag show welcome (unless dismissed)
  const toggleRag = () => {
    if (mode === 'rag') {
      setMode('default');
    } else {
      setMode('rag');
      if (!welcomeFaded) setShowWelcome(true);
    }
  };

  // Unified mode change handler that also closes modal if switching away
  const handleModeChange = (nextMode: AppMode) => {
    if (mode === nextMode) {
      setMode('default');
    } else {
      setMode(nextMode);
    }
  // Leaving explicit mode hides welcome
  if (nextMode !== 'rag') setShowWelcome(false);
  };

  const getBackgroundClass = () => {
    switch (mode) {
  case 'rag': return 'bg-[#F69F1C]/80'; // #F69F1C at 80% opacity
      case 'deep-research': return 'bg-rag-light/80';
      default: return 'bg-rag-dark';
    }
  };

  // Send current message to backend real chat endpoint
  const sendMessage = async () => {
    if (mode !== 'rag') return; // Only active in RAG mode
    const text = message.trim();
    if (!text || isSending || generating) return;

    const normalizedUser = (userIdRef.current || DEFAULT_USER_ID).trim() || DEFAULT_USER_ID;
    const activeSessionId = sessionIdRef.current;
    const now = new Date().toISOString();

    setIsSending(true);
    setGenerating(true);
    setShowWelcome(false);
    setWelcomeFaded(true);

    const userEntry: TranscriptEntry = { id: crypto.randomUUID(), role: 'user', content: text, timestamp: now };
    setMessages((m) => [...m, userEntry]);

    abortStreamingRef.current.aborted = false;
    const placeholderId = crypto.randomUUID();
    const placeholderTimestamp = new Date().toISOString();
    placeholderAssistantIdRef.current = placeholderId;
    setMessages((m) => [...m, { id: placeholderId, role: 'assistant', content: '', streaming: true, timestamp: placeholderTimestamp }]);
    setMessage("");

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const finish = () => {
      setIsSending(false);
      setGenerating(false);
      refreshSessions();
    };

    let answer = '';
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: text,
          session_id: activeSessionId,
          user_id: normalizedUser
        }),
        signal: controller.signal
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      answer = typeof data.answer === 'string' ? data.answer : '';
      const offerDeepDive = Boolean(data.needs_vector_approval || data.deep_dive_consent_needed);
      if (offerDeepDive) {
        setPendingVectorApproval({
          question: text,
          reason: data.vector_reason || 'Structured DB returned no rows. Run Deep-Dive over unstructured job descriptions?'
        });
      } else {
        setPendingVectorApproval(null);
      }
    } catch (err) {
      if ((err as any).name === 'AbortError' || abortStreamingRef.current.aborted) {
        setMessages(m => m.map(msg => msg.id === placeholderId ? { ...msg, streaming: false, content: msg.content || '(stopped)' } : msg));
        finish();
        return;
      }
      setMessages(m => m.map(msg => msg.id === placeholderId ? { ...msg, streaming: false, content: 'Error processing your request.', timestamp: msg.timestamp ?? new Date().toISOString() } : msg));
      finish();
      return;
    }

    if (abortStreamingRef.current.aborted) {
      setMessages(m => m.map(msg => msg.id === placeholderId ? { ...msg, streaming: false, content: msg.content || '(stopped)' } : msg));
      finish();
      return;
    }

    const chars = Array.from(answer ?? '');
    let idx = 0;

    const step = () => {
      if (abortStreamingRef.current.aborted) {
        setMessages(m => m.map(msg => msg.id === placeholderId ? { ...msg, streaming: false, content: msg.content || '(stopped)' } : msg));
        currentFrameRef.current = null;
        finish();
        return;
      }
      idx = Math.min(idx + 1, chars.length);
      const done = idx >= chars.length;
      setMessages(m => m.map(msg => msg.id === placeholderId ? {
        ...msg,
        content: chars.slice(0, idx).join(''),
        streaming: !done,
        timestamp: msg.timestamp ?? new Date().toISOString()
      } : msg));
      if (!done) {
        currentFrameRef.current = requestAnimationFrame(step);
      } else {
        currentFrameRef.current = null;
        finish();
      }
    };

    currentFrameRef.current = requestAnimationFrame(step);
  };
  // Removed explicit reset button per request; keeping helper for potential internal uses


  const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInputEngagement = () => {
    if (showWelcome) {
      // trigger fade
      setWelcomeFaded(true);
      // remove after animation (500ms)
      setTimeout(() => setShowWelcome(false), 500);
    }
  };

  const handleInputChange: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const val = e.target.value;
    setMessage(val);
    handleInputEngagement();
    
    // Check for company selector trigger "/"
    const lastSlash = val.lastIndexOf('/');
    if (lastSlash !== -1) {
      const fragment = val.slice(lastSlash + 1).trim();
      setCompanyQuery(fragment.toLowerCase());
      setShowCompanyPalette(true);
      setShowRoleTypePalette(false); // Close role palette
      return;
    }
    
    // Check for role type selector trigger ">"
    const lastGreater = val.lastIndexOf('>');
    if (lastGreater !== -1) {
      const fragment = val.slice(lastGreater + 1).trim();
      setRoleTypeQuery(fragment.toLowerCase());
      setShowRoleTypePalette(true);
      setShowCompanyPalette(false); // Close company palette
      return;
    }
    
    // Close both palettes if no triggers found
    if (showCompanyPalette) setShowCompanyPalette(false);
    if (showRoleTypePalette) setShowRoleTypePalette(false);
  };

  const filteredCompanies = showCompanyPalette ? companies.filter(c => {
    if (!companyQuery) return true;
    return c.toLowerCase().includes(companyQuery);
  }).slice(0, 30) : [];

  const filteredRoleTypes = showRoleTypePalette ? roleTypes.filter(rt => {
    if (!roleTypeQuery) return true;
    return rt.toLowerCase().includes(roleTypeQuery);
  }).slice(0, 30) : [];

  const insertCompany = (name: string) => {
    const val = message;
    const lastSlash = val.lastIndexOf('/');
    if (lastSlash === -1) return;
    const before = val.slice(0, lastSlash).trimEnd();
    const newVal = (before ? before + ' ' : '') + name + ' ';
    setMessage(newVal);
    setShowCompanyPalette(false);
  };

  const insertRoleType = (roleType: string) => {
    const val = message;
    const lastGreater = val.lastIndexOf('>');
    if (lastGreater === -1) return;
    const before = val.slice(0, lastGreater).trimEnd();
    const newVal = (before ? before + ' ' : '') + roleType + ' ';
    setMessage(newVal);
    setShowRoleTypePalette(false);
  };

  // Formatting utilities for assistant answers
  const cleanMarkdown = (text: string) => text.replace(/\*\*(.*?)\*\*/g, '$1');
  const formatBlocks = (text: string) => {
    const lines = cleanMarkdown(text).split(/\r?\n/);
    return lines.map((ln, i) => {
      const t = ln.trim();
      if (!t) return <div key={i} className="h-1"/>; // spacer
      // Heading heuristic: all caps words or ends with ':' and short
      if ((/^[-A-Z0-9 &()\/]{3,40}:?$/.test(t) && t.split(' ').length <= 8 && /[A-Z]/.test(t)) || /^#{1,3}\s/.test(t)) {
        return <div key={i} className="font-hack font-bold text-[11px] tracking-wide text-white/90 mt-2 first:mt-0">{t.replace(/^#{1,3}\s/, '')}</div>;
      }
      // Bullet list
      if (/^[-*•]\s+/.test(t)) {
        return <div key={i} className="pl-3 relative font-hack text-[11px] text-white/75 leading-snug"><span className="absolute left-0 text-white/50">•</span>{t.replace(/^[-*•]\s+/, '')}</div>;
      }
      // Numbered list
      if (/^\d+\./.test(t)) {
        return <div key={i} className="pl-4 font-hack text-[11px] text-white/75 leading-snug">{t}</div>;
      }
      // Body paragraph
      return <div key={i} className="font-hack text-[11px] text-white/70 leading-relaxed">{t}</div>;
    });
  };

  const MessageBubble = ({ msg }: { msg: { id: string; role: 'user' | 'assistant'; content: string; streaming?: boolean } }) => {
    const base = 'font-hack text-[11px] whitespace-pre-wrap rounded-[5px] px-3 py-1.5 transition-colors';
    if (msg.role === 'user') {
      return (
        <div className={cn(base, 'bg-[#3f3f3f] border border-[#F69F1C]/15 text-rag-text-primary/85')}>{msg.content}</div>
      );
    }
    return (
      <div className={cn(base, 'bg-[#3a3a3a] border border-[#F69F1C]/40 text-rag-text-primary/75 shadow-sm')}>
        <div className="flex items-start gap-2">
          <AnswerIcon className="mt-0.5 text-white/80 flex-shrink-0" />
          <div className="flex-1 space-y-0.5">
            {msg.streaming && !msg.content ? <span className="opacity-60">...</span> : formatBlocks(msg.content)}
          </div>
        </div>
      </div>
    );
  };

  // Inline deep dive consent prompt (replaces prior full-screen modal)
  const DeepDivePrompt = ({ question, reason }: { question: string; reason?: string }) => {
    return (
      <div className="w-full bg-[#3a3a3a] border border-[#F69F1C]/45 rounded-[5px] px-3 py-2 flex flex-col gap-2 shadow-sm">
        <div className="font-hack text-[11px] text-[#F69F1C] tracking-wide">Deep-Dive Mode Available</div>
        <div className="font-hack text-[10px] text-rag-text-primary/70 leading-snug">{reason || 'Run deeper unstructured search?'}</div>
        <div className="font-hack text-[9px] text-rag-text-primary/40">Query: <span className="text-rag-text-primary/60">{question}</span></div>
        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            onClick={() => setPendingVectorApproval(null)}
            className="font-hack text-[10px] px-2 py-1 rounded-sm bg-transparent text-rag-text-primary/55 hover:text-rag-text-primary/85"
          >dismiss</button>
          <button
            onClick={async () => {
              // Fire vector endpoint directly; append new assistant message with deep dive answer
              const q = question;
              setPendingVectorApproval(null);
              const normalizedUser = (userIdRef.current || DEFAULT_USER_ID).trim() || DEFAULT_USER_ID;
              const targetSession = sessionIdRef.current;
              try {
                const resp = await fetch(`${API_BASE}/chat/vector`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ question: q, session_id: targetSession, user_id: normalizedUser })
                });
                if (resp.ok) {
                  const data = await resp.json();
                  const vecAnswer = data.answer || '(no deep-dive answer)';
                  const timestamp = new Date().toISOString();
                  setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', content: vecAnswer, timestamp }]);
                  refreshSessions();
                } else {
                  const timestamp = new Date().toISOString();
                  setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', content: 'Deep-dive failed (network).', timestamp }]);
                }
              } catch {
                const timestamp = new Date().toISOString();
                setMessages(m => [...m, { id: crypto.randomUUID(), role: 'assistant', content: 'Deep-dive error.', timestamp }]);
              }
            }}
            className="font-hack text-[10px] px-3 py-1 rounded-sm bg-[#F69F1C]/25 border border-[#F69F1C]/40 text-[#F69F1C] hover:bg-[#F69F1C]/35"
          >Run Deep-Dive</button>
        </div>
      </div>
    );
  };

  return (
    <div className={cn(
      "h-screen flex flex-col items-center p-4 transition-all duration-500 relative overflow-hidden",
      getBackgroundClass()
    )}>
      <div className="w-full max-w-sm flex flex-col h-full">
        <div ref={convoRef} className="flex-1 flex flex-col items-center relative w-full pt-6 overflow-y-auto min-h-0">
        {mode === 'rag' && showWelcome && (
          <div
            className={cn(
              'transition-opacity duration-500 mb-6',
              welcomeFaded ? 'opacity-0' : 'opacity-100'
            )}
          >
            <WelcomeCardContent />
          </div>
        )}
        {mode === 'rag' && (
          <div className="w-full flex flex-col gap-2 pb-4">
            {messages.map((m, idx) => {
              const fallbackId = `${m.role}-${idx}-${m.timestamp ?? "local"}`;
              const bubbleMessage = {
                id: m.id ?? fallbackId,
                role: m.role,
                content: m.content,
                streaming: m.streaming,
              } as const;
              return <MessageBubble key={bubbleMessage.id} msg={bubbleMessage} />;
            })}
            {pendingVectorApproval && mode === 'rag' && (
              <DeepDivePrompt question={pendingVectorApproval.question} reason={pendingVectorApproval.reason} />
            )}
            {mode === 'rag' && isSending && !messages.some(m => m.streaming) && (
              <div className="px-1 py-1">
                <TypingIndicator />
              </div>
            )}
          </div>
        )}
      </div>
      <div className="w-full space-y-4 flex flex-col items-center z-10 flex-shrink-0">
        {/* Original ChatComponent before backend connection */}
        <div className={cn(
          'w-full max-w-sm h-20 rounded-md border shadow-sm flex flex-col justify-between p-3 relative',
          mode === 'deep-research' ? 'bg-rag-chat-light border-gray-300' : 'bg-rag-chat-dark border-gray-500/25'
        )}>
          <input
            aria-label="Message input"
            placeholder="Alright genius, spit out..."
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleInputEngagement}
            onInput={handleInputEngagement}
            // Allow input in all modes so '/' trigger + stop icon can be tested universally
            disabled={isSending}
            className={cn(
              'bg-transparent outline-none border-none p-0 m-0 font-hack text-xs w-full',
              mode !== 'rag' ? 'opacity-30 cursor-not-allowed text-rag-text-primary/40 placeholder:text-rag-text-primary/30' : 'opacity-70 text-rag-text-primary placeholder:text-rag-text-primary'
            )}
          />
          <div className="flex items-center justify-between">
            <AttachmentIcon mode={mode} />
            {(messages.some(m => m.streaming) || generating) ? (
              <StopIcon onClick={() => {
                // Abort streaming and finalize current assistant message
                abortStreamingRef.current.aborted = true;
                if (currentFrameRef.current) cancelAnimationFrame(currentFrameRef.current);
                if (abortControllerRef.current) {
                  try { abortControllerRef.current.abort(); } catch {/* ignore */}
                }
                // Mark any streaming assistant message as complete (unless already filled)
                setMessages(m => m.map(msg => msg.streaming ? { ...msg, streaming: false, content: msg.content || '(stopped)' } : msg));
                setIsSending(false); setGenerating(false);
              }} />
            ) : (
              <SendArrowIcon mode={mode} onClick={sendMessage} disabled={!message.trim() || isSending} />
            )}
          </div>
          {showCompanyPalette && (
            <div
              ref={paletteRef}
              className="absolute bottom-full mb-2 left-0 w-full bg-rag-chat-dark border border-[#F69F1C]/30 rounded-md shadow-lg max-h-60 overflow-y-auto z-50"
            >
              <div className="px-3 py-1 border-b border-[#F69F1C]/20 flex items-center justify-between">
                <span className="font-hack text-[10px] tracking-wide text-[#F69F1C]">Companies</span>
                <span className="font-hack text-[9px] text-rag-text-primary/50">{filteredCompanies.length}</span>
              </div>
              <ul className="py-1">
                {filteredCompanies.length === 0 && (
                  <li className="px-3 py-1 font-hack text-[10px] text-rag-text-primary/40">No matches</li>
                )}
                {filteredCompanies.map(c => (
                  <li
                    key={c}
                    onClick={() => insertCompany(c)}
                    className="px-3 py-1 font-hack text-[11px] text-rag-text-primary/80 hover:bg-[#F69F1C]/10 cursor-pointer select-none"
                  >{c}</li>
                ))}
              </ul>
              <div className="px-3 py-1 border-t border-[#F69F1C]/15">
                <span className="font-hack text-[9px] text-rag-text-primary/40">Type '/' then letters to filter • Enter to send</span>
              </div>
            </div>
          )}
          {showRoleTypePalette && (
            <div
              ref={paletteRef}
              className="absolute bottom-full mb-2 left-0 w-full bg-rag-chat-dark border border-[#F69F1C]/30 rounded-md shadow-lg max-h-60 overflow-y-auto z-50"
            >
              <div className="px-3 py-1 border-b border-[#F69F1C]/20 flex items-center justify-between">
                <span className="font-hack text-[10px] tracking-wide text-[#F69F1C]">Role Types</span>
                <span className="font-hack text-[9px] text-rag-text-primary/50">{filteredRoleTypes.length}</span>
              </div>
              <ul className="py-1">
                {filteredRoleTypes.length === 0 && (
                  <li className="px-3 py-1 font-hack text-[10px] text-rag-text-primary/40">No matches</li>
                )}
                {filteredRoleTypes.map(rt => (
                  <li
                    key={rt}
                    onClick={() => insertRoleType(rt)}
                    className="px-3 py-1 font-hack text-[11px] text-rag-text-primary/80 hover:bg-[#F69F1C]/10 cursor-pointer select-none"
                  >{rt}</li>
                ))}
              </ul>
              <div className="px-3 py-1 border-t border-[#F69F1C]/15">
                <span className="font-hack text-[9px] text-rag-text-primary/40">Type {'>'} then letters to filter • Enter to send</span>
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center justify-between w-full">
          <ToolBox mode={mode} onModeChange={handleModeChange} onToggleRag={toggleRag} />
          <button onClick={() => mode === 'rag' && setShowHistory(true)} aria-label="Open chat history" className={cn('p-0 m-0 bg-transparent', mode !== 'rag' && 'opacity-40 cursor-not-allowed') }>
            <ChatHistoryIcon mode={mode} />
          </button>
        </div>
  </div>
      {showHistory && mode === 'rag' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowHistory(false)} aria-hidden />
          <div className="relative w-full max-w-md h-[70vh] bg-rag-chat-dark border border-[#F69F1C]/30 rounded-md shadow-lg flex flex-col">
            <div className="px-4 py-2 border-b border-[#F69F1C]/20 flex items-center justify-between">
              <span className="font-hack text-[11px] tracking-wide text-[#F69F1C]">History</span>
              <button onClick={() => setShowHistory(false)} className="font-hack text-[10px] text-rag-text-primary/60 hover:text-rag-text-primary/90">close</button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <div className="space-y-2">
                <div className="font-hack text-[10px] uppercase tracking-[0.2em] text-rag-text-primary/50">Sessions</div>
                {historyLoading && (
                  <div className="font-hack text-xs text-rag-text-primary/40">Loading…</div>
                )}
                {historyError && (
                  <div className="font-hack text-xs text-[#F69F1C]">{historyError}</div>
                )}
                {!historyLoading && !historyError && sessions.length === 0 && (
                  <div className="font-hack text-xs text-rag-text-primary/40">No saved sessions yet.</div>
                )}
                {sessions.map((session) => {
                  const isActive = session.session_id === sessionId;
                  return (
                    <div
                      key={session.session_id}
                      role="button"
                      tabIndex={0}
                      onClick={() => loadTranscript(session.session_id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          loadTranscript(session.session_id);
                        }
                      }}
                      className={cn(
                        'rounded-md border px-3 py-2 bg-[#3a3a3a] text-left cursor-pointer select-none focus:outline-none focus:ring-1 focus:ring-[#F69F1C]/60',
                        isActive ? 'border-[#F69F1C]/60 shadow-sm' : 'border-[#F69F1C]/20 hover:border-[#F69F1C]/40'
                      )}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-hack text-[11px] text-rag-text-primary/80 truncate">{session.title || 'Conversation'}</span>
                        <span className="font-hack text-[9px] text-rag-text-primary/45 whitespace-nowrap">{formatTimestamp(session.updated_at)}</span>
                      </div>
                      {session.last_message_preview ? (
                        <div className="font-hack text-[10px] text-rag-text-primary/55 mt-1 overflow-hidden whitespace-nowrap text-ellipsis">{session.last_message_preview}</div>
                      ) : (
                        <div className="font-hack text-[10px] text-rag-text-primary/40 mt-1">No messages yet.</div>
                      )}
                      <div className="mt-2 flex items-center justify-between text-[9px] font-hack text-rag-text-primary/40">
                        <span>{session.message_count ?? 0} messages</span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteSession(session.session_id);
                          }}
                          className="text-rag-text-primary/45 hover:text-[#F69F1C]"
                        >
                          delete
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="border-t border-[#F69F1C]/20 pt-3 space-y-2">
                <div className="font-hack text-[10px] uppercase tracking-[0.2em] text-rag-text-primary/50">Current transcript</div>
                {messages.length === 0 ? (
                  <div className="font-hack text-xs text-rag-text-primary/40">No messages yet.</div>
                ) : (
                  <div className="space-y-2">
                    {messages.map((m, idx) => {
                      const fallbackId = `${m.role}-${idx}-${m.timestamp ?? 'local'}`;
                      const key = m.id ?? fallbackId;
                      return (
                        <div
                          key={key}
                          className={cn(
                            'font-hack text-xs leading-relaxed whitespace-pre-wrap rounded-md px-2 py-1',
                            m.role === 'assistant' ? 'border border-[#F69F1C]/35 text-rag-text-primary/70' : 'text-rag-text-primary/80'
                          )}
                        >
                          {m.content}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
            <div className="px-4 py-2 border-t border-[#F69F1C]/20 flex items-center justify-between">
              <button onClick={beginNewSession} className="font-hack text-[10px] text-rag-text-primary/55 hover:text-rag-text-primary/80">new session</button>
              <div className="flex items-center gap-4">
                <button onClick={() => { clearHistory(); }} className="font-hack text-[10px] text-rag-text-primary/50 hover:text-[#F69F1C]">delete current</button>
                <button onClick={() => setShowHistory(false)} className="font-hack text-[10px] text-rag-text-primary/60 hover:text-rag-text-primary/90">done</button>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
