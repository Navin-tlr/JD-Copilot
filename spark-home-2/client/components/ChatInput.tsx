import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import SpecializationPopup, { SpecializationSelection } from './SpecializationPopup';

interface ChatInputProps {
  variant?: 'default' | 'rag' | 'benchmark';
  onSend?: (value: string) => void;
}

export default function ChatInput({ variant = 'default', onSend }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [isSpecializationPopupOpen, setIsSpecializationPopupOpen] = useState(false);
  const [specializationTriggerIndex, setSpecializationTriggerIndex] = useState<number | null>(null);
  const [lastHashHandled, setLastHashHandled] = useState<number | null>(null);
  const [selectedSpecialization, setSelectedSpecialization] = useState<SpecializationSelection | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const location = useLocation();

  const getRagMode = () => location.pathname === '/rag';
  const ragMode = getRagMode();

  const getColors = () => {
    switch (variant) {
      case 'rag':
        return {
          bg: '#464646',
          border: 'rgba(200, 200, 200, 0.25)',
          text: '#FFFFFF',
          icon: '#C1C1C1',
          placeholder: 'rgba(255, 255, 255, 0.6)',
          toolBg: '#393939',
          toolItemBg: '#4A4A4A',
          ragActiveBg: '#EEA437',
          ragActiveStroke: '#464646',
        };
      case 'benchmark':
        return {
          bg: '#D2D2D2',
          border: 'rgba(200, 200, 200, 0.25)',
          text: '#B729C1',
          icon: '#4A4A4A',
          placeholder: 'rgba(183, 41, 193, 0.6)',
          toolBg: '#D2D2D2',
          toolItemBg: '#DDD',
          ragActiveBg: '',
          ragActiveStroke: '',
        };
      default:
        return {
          bg: '#464646',
          border: 'rgba(200, 200, 200, 0.25)',
          text: '#FFFFFF',
          icon: '#A9A9A9',
          placeholder: 'rgba(255, 255, 255, 0.6)',
          toolBg: '#393939',
          toolItemBg: '#4A4A4A',
          ragActiveBg: '',
          ragActiveStroke: '',
        };
    }
  };

  const colors = getColors();
  const active = input.trim().length > 0;

  useEffect(() => {
    if (!selectedSpecialization) {
      return;
    }

    const token = selectedSpecialization.token.toLowerCase();
    if (!input.toLowerCase().includes(token)) {
      setSelectedSpecialization(null);
    }
  }, [input, selectedSpecialization]);

  const handleRagClick = () => {
    navigate('/rag');
  };

  const handleDeepResearchClick = () => {
    navigate('/benchmark');
  };

  const handleWhisperClick = () => {
    // Handle whisper mode
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInput(value);

    const lastHashIndex = value.lastIndexOf('#');

    if (lastHashIndex !== -1) {
      setSpecializationTriggerIndex(lastHashIndex);
      if (lastHashHandled !== lastHashIndex) {
        setIsSpecializationPopupOpen(true);
        setLastHashHandled(lastHashIndex);
      }
    } else {
      if (isSpecializationPopupOpen) {
        setIsSpecializationPopupOpen(false);
      }
      if (specializationTriggerIndex !== null) {
        setSpecializationTriggerIndex(null);
      }
      if (lastHashHandled !== null) {
        setLastHashHandled(null);
      }
    }
  };

  const handleSpecializationSelect = (selection: SpecializationSelection) => {
    const triggerIndex =
      specializationTriggerIndex !== null ? specializationTriggerIndex : input.lastIndexOf('#');

    if (triggerIndex === -1) {
      setIsSpecializationPopupOpen(false);
      setSpecializationTriggerIndex(null);
      setLastHashHandled(null);
      return;
    }

    const before = input.slice(0, triggerIndex);
    const after = input.slice(triggerIndex + 1);
    const baseToken = selection.token.toLowerCase();
    const needsLeadingSpace = before.length > 0 && !/\s$/.test(before);
    const needsTrailingSpace = after.length > 0 && !/^\s/.test(after);
    const tokenWithSpacing = `${needsLeadingSpace ? ' ' : ''}${baseToken}${needsTrailingSpace ? ' ' : ''}`;
    const nextValue = `${before}${tokenWithSpacing}${after}`;

    setInput(nextValue);
    setSelectedSpecialization(selection);
    setIsSpecializationPopupOpen(false);
    setSpecializationTriggerIndex(null);
    setLastHashHandled(null);

    requestAnimationFrame(() => {
      if (inputRef.current) {
        const caretPosition = before.length + tokenWithSpacing.length;
        inputRef.current.focus();
        inputRef.current.setSelectionRange(caretPosition, caretPosition);
      }
    });
  };

  const handleSend = () => {
    if (!active) return;
    onSend?.(input.trim());
    setInput('');
    setSelectedSpecialization(null);
    setSpecializationTriggerIndex(null);
    setLastHashHandled(null);
    setIsSpecializationPopupOpen(false);
  };

  return (
    <div
      className="w-full max-w-[914px] h-[116px] rounded-[5px] shadow-lg relative transition-all duration-300"
      style={{
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        boxShadow: '0 4px 4px 0 rgba(0, 0, 0, 0.10)',
      }}
    >
      {/* Attachment Icon */}
      <svg
        className="absolute left-5 top-[15px] w-[21px] h-[21px] cursor-pointer transition-opacity hover:opacity-80"
        viewBox="0 0 21 21"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M16.125 17.25V4.5C16.125 3.50544 15.7299 2.55161 15.0267 1.84835C14.3234 1.14509 13.3696 0.75 12.375 0.75H8.625C7.63044 0.75 6.67661 1.14509 5.97335 1.84835C5.27009 2.55161 4.875 3.50544 4.875 4.5V17.25C4.875 18.0456 5.19107 18.8087 5.75368 19.3713C6.31629 19.9339 7.07935 20.25 7.875 20.25H9.375C10.1706 20.25 10.9337 19.9339 11.4963 19.3713C12.0589 18.8087 12.375 18.0456 12.375 17.25V6C12.375 5.60218 12.217 5.22064 11.9357 4.93934C11.6544 4.65804 11.2728 4.5 10.875 4.5H10.125C9.72718 4.5 9.34564 4.65804 9.06434 4.93934C8.78304 5.22064 8.625 5.60218 8.625 6V14.25"
          stroke={colors.icon}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>

      {/* Input Text */}
      <input
        ref={inputRef}
        type="text"
        value={input}
        onChange={handleInputChange}
        onKeyDown={(e) => {
          if (e.key === 'Enter') handleSend();
        }}
  placeholder={variant === 'benchmark' ? 'Alright genius, spit out...' : 'Type # to select specialization...'}
        className="absolute left-[60px] top-[17px] bg-transparent outline-none text-[14px] font-normal w-[calc(100%-120px)]"
        style={{ color: colors.text, opacity: input ? 1 : 0.6 }}
      />

      {/* Send Arrow - Figma: left:873px;top:76px;width:23px;height:23px */}
      <div className="absolute left-[873px] top-[76px] w-[23px] h-[23px]">
        <div className="relative group w-full h-full">
          {/* orange hint / shadow beneath icon on hover */}
          <div
            className={`absolute left-1/2 transform -translate-x-1/2 -bottom-1 w-6 h-1.5 rounded-full opacity-0 transition-opacity duration-200 pointer-events-none group-hover:opacity-100`}
            style={{ background: 'rgba(246,159,28,0.3)', filter: 'blur(4px)' }}
          />

          <button
            onClick={handleSend}
            disabled={!active}
            className={`relative w-full h-full flex items-center justify-center transition-transform duration-200 ease-out ${
              active ? 'cursor-pointer' : 'cursor-default'
            } group-hover:-translate-y-0.5 active:scale-95`}
            aria-label="Send"
            style={{
              background: 'transparent',
              border: 'none',
            }}
          >
            <svg
              width="23"
              height="23"
              viewBox="0 0 25 25"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M10.7307 7.19226L16.0384 12.5L10.7307 17.8076"
                stroke={active ? 'rgb(246,159,28)' : (variant === 'benchmark' ? '#4A4A4A' : '#B5B5B5')}
                strokeOpacity={active ? '1' : (variant === 'benchmark' ? '1' : '0.87')}
                strokeWidth="1.76923"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M12.5 24C18.8513 24 24 18.8513 24 12.5C24 6.14873 18.8513 1 12.5 1C6.14873 1 1 6.14873 1 12.5C1 18.8513 6.14873 24 12.5 24Z"
                stroke={active ? 'rgb(246,159,28)' : (variant === 'benchmark' ? '#4A4A4A' : '#B5B5B5')}
                strokeOpacity={active ? '1' : (variant === 'benchmark' ? '1' : '0.87')}
                strokeWidth="1.76923"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Tool Box */}
      <div
        className="absolute left-5 top-[63px] w-[155px] h-10 rounded-[5px] flex items-center gap-1 px-2"
        style={{
          background: colors.toolBg,
          boxShadow: '0px 1px 4px 0px rgba(0, 0, 0, 0.1)',
        }}
      >
        {/* Deep Research Icon */}
        <button
          disabled
          className="w-[38px] h-[31px] rounded-[6px] flex items-center justify-center transition-all duration-200 ease-out active:scale-95 opacity-50 cursor-not-allowed"
          style={{
            background: colors.toolItemBg,
            boxShadow: '0px 0px 4px 0px rgba(0, 0, 0, 0.15)',
          }}
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 22 22"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_93_43)">
              <path
                d="M7.07143 20.4286C10.5429 20.4286 13.3571 17.6144 13.3571 14.1429C13.3571 10.6714 10.5429 7.85718 7.07143 7.85718C3.59993 7.85718 0.785721 10.6714 0.785721 14.1429C0.785721 17.6144 3.59993 20.4286 7.07143 20.4286Z"
                stroke={variant === 'benchmark' ? 'url(#paint0_linear_bench)' : '#C1C1C1'}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M14.9286 20.4286C18.4001 20.4286 21.2143 17.6144 21.2143 14.1429C21.2143 10.6714 18.4001 7.85718 14.9286 7.85718C11.4571 7.85718 8.64287 10.6714 8.64287 14.1429C8.64287 17.6144 11.4571 20.4286 14.9286 20.4286Z"
                stroke={variant === 'benchmark' ? 'url(#paint1_linear_bench)' : '#C1C1C1'}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M11 14.1428C14.4715 14.1428 17.2857 11.3286 17.2857 7.85713C17.2857 4.38562 14.4715 1.57141 11 1.57141C7.5285 1.57141 4.71429 4.38562 4.71429 7.85713C4.71429 11.3286 7.5285 14.1428 11 14.1428Z"
                stroke={variant === 'benchmark' ? 'url(#paint2_linear_bench)' : '#C1C1C1'}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <linearGradient id="paint0_linear_bench" x1="7.07143" y1="7.85718" x2="7.07143" y2="20.4286" gradientUnits="userSpaceOnUse">
                <stop stopColor="#808BC4"/>
                <stop offset="1" stopColor="#4D659C"/>
              </linearGradient>
              <linearGradient id="paint1_linear_bench" x1="14.9286" y1="7.85718" x2="14.9286" y2="20.4286" gradientUnits="userSpaceOnUse">
                <stop stopColor="#808BC4"/>
                <stop offset="1" stopColor="#4D659C"/>
              </linearGradient>
              <linearGradient id="paint2_linear_bench" x1="11" y1="1.57141" x2="11" y2="14.1428" gradientUnits="userSpaceOnUse">
                <stop stopColor="#808BC4"/>
                <stop offset="1" stopColor="#4D659C"/>
              </linearGradient>
              <clipPath id="clip0_93_43">
                <rect width="22" height="22" fill="white"/>
              </clipPath>
            </defs>
          </svg>
        </button>

        {/* RAG Icon */}
        <button
          onClick={handleRagClick}
          className="w-[38px] h-[31px] rounded-[6px] flex items-center justify-center transition-all duration-200 ease-out active:scale-95"
          style={{
            background: ragMode && variant === 'rag' ? colors.ragActiveBg : colors.toolItemBg,
            boxShadow: '0px 0px 4px 0px rgba(0, 0, 0, 0.15)',
          }}
        >
          {/* svg omitted for brevity - unchanged */}
          <svg
            width="22"
            height="22"
            viewBox="0 0 22 22"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_140_25)">
              <path
                d="M5.49999 15.7144H1.57142C1.13748 15.7144 0.785706 16.0661 0.785706 16.5001V20.4286C0.785706 20.8626 1.13748 21.2144 1.57142 21.2144H5.49999C5.93393 21.2144 6.28571 20.8626 6.28571 20.4286V16.5001C6.28571 16.0661 5.93393 15.7144 5.49999 15.7144Z"
                stroke={ragMode && variant === 'rag' ? colors.ragActiveStroke : (variant === 'benchmark' ? 'url(#paint0_linear_140_25)' : 'url(#paint0_linear_140_25)')}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M20.4285 15.7144H16.5C16.066 15.7144 15.7143 16.0661 15.7143 16.5001V20.4286C15.7143 20.8626 16.066 21.2144 16.5 21.2144H20.4285C20.8625 21.2144 21.2143 20.8626 21.2143 20.4286V16.5001C21.2143 16.0661 20.8625 15.7144 20.4285 15.7144Z"
                stroke={ragMode && variant === 'rag' ? colors.ragActiveStroke : (variant === 'benchmark' ? 'url(#paint1_linear_140_25)' : 'url(#paint1_linear_140_25)')}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M13.3571 0.785767H8.64283C8.20889 0.785767 7.85712 1.13754 7.85712 1.57148V6.28577C7.85712 6.7197 8.20889 7.07148 8.64283 7.07148H13.3571C13.7911 7.07148 14.1428 6.7197 14.1428 6.28577V1.57148C14.1428 1.13754 13.7911 0.785767 13.3571 0.785767Z"
                stroke={ragMode && variant === 'rag' ? colors.ragActiveStroke : (variant === 'benchmark' ? 'url(#paint2_linear_140_25)' : 'url(#paint2_linear_140_25)')}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M6.28571 18.8572H15.7143"
                stroke={ragMode && variant === 'rag' ? colors.ragActiveStroke : (variant === 'benchmark' ? 'url(#paint3_linear_140_25)' : 'url(#paint3_linear_140_25)')}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M7.99856 6.74146L3.92856 15.7143"
                stroke={ragMode && variant === 'rag' ? colors.ragActiveStroke : (variant === 'benchmark' ? 'url(#paint4_linear_140_25)' : 'url(#paint4_linear_140_25)')}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M14.0014 6.74146L18.0714 15.7143"
                stroke={ragMode && variant === 'rag' ? colors.ragActiveStroke : (variant === 'benchmark' ? 'url(#paint5_linear_140_25)' : 'url(#paint5_linear_140_25)')}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <linearGradient id="paint0_linear_140_25" x1="3.53571" y1="15.7144" x2="3.53571" y2="21.2144" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint1_linear_140_25" x1="18.4643" y1="15.7144" x2="18.4643" y2="21.2144" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint2_linear_140_25" x1="11" y1="0.785767" x2="11" y2="7.07148" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint3_linear_140_25" x1="11" y1="18.8572" x2="11" y2="19.8572" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint4_linear_140_25" x1="5.96356" y1="6.74146" x2="5.96356" y2="15.7143" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <linearGradient id="paint5_linear_140_25" x1="16.0364" y1="6.74146" x2="16.0364" y2="15.7143" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F68E51"/>
                <stop offset="1" stopColor="#F68D51"/>
              </linearGradient>
              <clipPath id="clip0_140_25">
                <rect width="22" height="22" fill="white"/>
              </clipPath>
            </defs>
          </svg>
        </button>

        {/* Whisper Icon */}
        <button
          disabled
          className="w-[38px] h-[31px] rounded-[6px] flex items-center justify-center transition-all duration-200 ease-out active:scale-95 opacity-50 cursor-not-allowed"
          style={{
            background: colors.toolItemBg,
            boxShadow: '0px 0px 4px 0px rgba(0, 0, 0, 0.15)',
          }}
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 22 22"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_93_48)">
              <path
                d="M11 14.143C12.9527 14.143 14.5357 12.56 14.5357 10.6072C14.5357 8.65453 12.9527 7.07153 11 7.07153C9.04729 7.07153 7.46429 8.65453 7.46429 10.6072C7.46429 12.56 9.04729 14.143 11 14.143Z"
                stroke={variant === 'benchmark' ? '#504640' : '#C1C1C1'}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M17.2857 21.2144C16.6908 20.0601 15.7896 19.092 14.6808 18.4161C13.572 17.7401 12.2986 17.3826 11 17.3826C9.70146 17.3826 8.42798 17.7401 7.31921 18.4161C6.21044 19.092 5.30919 20.0601 4.71429 21.2144"
                stroke={variant === 'benchmark' ? '#504640' : '#C1C1C1'}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M18.8571 16.5943C19.9723 15.1398 20.6582 13.4023 20.8373 11.5782C21.0164 9.75422 20.6815 7.91648 19.8705 6.27286C19.0596 4.62924 17.8049 3.24533 16.2484 2.27764C14.6919 1.30996 12.8957 0.797119 11.0629 0.797119C9.23006 0.797119 7.43383 1.30996 5.87732 2.27764C4.32081 3.24533 3.06612 4.62924 2.25517 6.27286C1.44421 7.91648 1.10934 9.75422 1.28843 11.5782C1.46752 13.4023 2.15343 15.1398 3.26857 16.5943"
                stroke={variant === 'benchmark' ? '#504640' : '#C1C1C1'}
                strokeWidth="1.57143"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <clipPath id="clip0_93_48">
                <rect width="22" height="22" fill="white"/>
              </clipPath>
            </defs>
          </svg>
        </button>
      </div>

      {/* RAG Mode Indicator - Only show in RAG screen */}
      {variant === 'rag' && (
        <svg
          className="absolute left-[186px] top-[72px] w-[26px] h-[26px] animate-fade-in"
          viewBox="0 0 26 26"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g clipPath="url(#clip0_93_203)">
            <path
              d="M13 25.0714V15.3214C13 14.7057 13.2446 14.1153 13.6799 13.6799C14.1153 13.2446 14.7057 13 15.3214 13V13C15.9371 13 16.5276 13.2446 16.9629 13.6799C17.3983 14.1153 17.6429 14.7057 17.6429 15.3214V20.4286H21.3571C22.3422 20.4286 23.287 20.8199 23.9835 21.5165C24.6801 22.213 25.0714 23.1578 25.0714 24.1429V25.0714"
              stroke="#C1C1C1"
              strokeWidth="1.85714"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M1.85716 2.78573C2.37 2.78573 2.78573 2.37 2.78573 1.85716C2.78573 1.34432 2.37 0.928589 1.85716 0.928589C1.34432 0.928589 0.928589 1.34432 0.928589 1.85716C0.928589 2.37 1.34432 2.78573 1.85716 2.78573Z"
              stroke="#C1C1C1"
              strokeWidth="1.85714"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M9.28575 2.78573C9.79858 2.78573 10.2143 2.37 10.2143 1.85716C10.2143 1.34432 9.79858 0.928589 9.28575 0.928589C8.77291 0.928589 8.35718 1.34432 8.35718 1.85716C8.35718 2.37 8.77291 2.78573 9.28575 2.78573Z"
              stroke="#C1C1C1"
              strokeWidth="1.85714"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M16.7143 2.78573C17.2272 2.78573 17.6429 2.37 17.6429 1.85716C17.6429 1.34432 17.2272 0.928589 16.7143 0.928589C16.2015 0.928589 15.7858 1.34432 15.7858 1.85716C15.7858 2.37 16.2015 2.78573 16.7143 2.78573Z"
              stroke="#C1C1C1"
              strokeWidth="1.85714"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M1.85716 9.28573C2.37 9.28573 2.78573 8.87 2.78573 8.35716C2.78573 7.84432 2.37 7.42859 1.85716 7.42859C1.34432 7.42859 0.928589 7.84432 0.928589 8.35716C0.928589 8.87 1.34432 9.28573 1.85716 9.28573Z"
              stroke="#C1C1C1"
              strokeWidth="1.85714"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M9.28575 9.28573C9.79858 9.28573 10.2143 8.87 10.2143 8.35716C10.2143 7.84432 9.79858 7.42859 9.28575 7.42859C8.77291 7.42859 8.35718 7.84432 8.35718 8.35716C8.35718 8.87 8.77291 9.28573 9.28575 9.28573Z"
              stroke="#C1C1C1"
              strokeWidth="1.85714"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M16.7143 9.28573C17.2272 9.28573 17.6429 8.87 17.6429 8.35716C17.6429 7.84432 17.2272 7.42859 16.7143 7.42859C16.2015 7.42859 15.7858 7.84432 15.7858 8.35716C15.7858 8.87 16.2015 9.28573 16.7143 9.28573Z"
              stroke="#C1C1C1"
              strokeWidth="1.85714"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </g>
          <defs>
            <clipPath id="clip0_93_203">
              <rect width="26" height="26" fill="white"/>
            </clipPath>
          </defs>
        </svg>
      )}

      <SpecializationPopup
        isOpen={isSpecializationPopupOpen}
        variant={variant}
        currentSelection={selectedSpecialization?.id ?? null}
        onSelect={handleSpecializationSelect}
        onClose={() => {
          setIsSpecializationPopupOpen(false);
          if (specializationTriggerIndex !== null) {
            setLastHashHandled(specializationTriggerIndex);
          }
        }}
      />
    </div>
  );
}
