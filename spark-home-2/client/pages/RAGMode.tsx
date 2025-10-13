import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DeepDiveConsentCard from '@/components/DeepDiveConsentCard';
import ModalPortal from '@/components/ModalPortal';
import SapientLogo from '@/components/SapientLogo';
import ChatInput from '@/components/ChatInput';
import ChatHistory from '@/components/ChatHistory';
import { buildApiUrl, BACKEND_BASE_URL } from '@/lib/api';
import ThinkingIndicator from '@/components/ThinkingIndicator';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

export default function RAGMode() {
  const navigate = useNavigate();
  const [welcomeVisible, setWelcomeVisible] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pendingDeepDive, setPendingDeepDive] = useState<{ question: string; reason?: string } | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [userId] = useState('student-123'); // Replace with actual user ID from auth
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const handleSend = async (value: string) => {
    // fade the welcome message
    setWelcomeVisible(false);
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: value }]);
    setIsLoading(true);

    try {
      const response = await fetch(buildApiUrl('/chat'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: value,
          session_id: sessionId || 'rag-session',
          user_id: userId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Append assistant message
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);

      // If backend signals no structured data and suggests deep‑dive, show consent modal
      if (data?.deep_dive_consent_needed || data?.needs_vector_approval) {
        setPendingDeepDive({ question: value, reason: data?.vector_reason });
      } else {
        // Frontend fallback: parse answer for common no-data patterns and open consent
        // Skip if answer contains phrases like "MBA Placement Cell Briefing" (indicates structured summary)
        const lower = (data?.answer || '').toLowerCase();
        const hasStructuredSummary = (
          lower.includes('placement cell briefing') ||
          lower.includes('market snapshot') ||
          lower.includes('verified company count')
        );
        
        const looksNoData = (
          /\b0\b[^\n\r.!?]{0,60}\b(companies|roles|placements|offers)\b/.test(lower) ||
          /\bno\b[^\n\r.!?]{0,60}\b(companies|roles|placements|offers)\b/.test(lower) ||
          lower.includes('no results') ||
          lower.includes('no data available') ||
          lower.includes("couldn't find") ||
          lower.includes('could not find')
        );
        
        // Only show modal if no data AND no structured summary
        if (looksNoData && !hasStructuredSummary) {
          setPendingDeepDive({
            question: value,
            reason: data?.vector_reason || 'Query returned no results. Offer deep-dive search of unstructured job descriptions.'
          });
        }
      }
    } catch (error) {
      console.error('Error calling backend:', error);
  const backendHint = BACKEND_BASE_URL || 'the configured backend server';
  const errorMessage = `<p style="color: #ff6b6b;">Sorry, I encountered an error while processing your query. Please make sure the backend server is reachable at ${backendHint}.</p><p>Error: ${error instanceof Error ? error.message : 'Unknown error'}</p>`;
      setMessages(prev => [...prev, { role: 'assistant', content: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setSessionId(''); // Clear session to create new one
    setMessages([]);
    setWelcomeVisible(true);
  };

  const handleSessionSelect = async (newSessionId: string) => {
    setSessionId(newSessionId);
    setWelcomeVisible(false);
    // Fetch messages for this session
    try {
      const response = await fetch(buildApiUrl(`/sessions/${newSessionId}/messages`));
      const data = await response.json();
      const formatted = data.messages.map((msg: any) => ({
        role: msg.sender,
        content: msg.content
      }));
      setMessages(formatted);
    } catch (error) {
      console.error('Failed to fetch session messages:', error);
      setMessages([]);
    }
  };

  return (
    <div className="min-h-screen bg-[#313131] flex flex-col items-center py-12 px-4 relative animate-fade-in">
      <ThinkingIndicator active={isLoading} message="Working on that for you" />
      {/* Chat History Sidebar */}
      <ChatHistory
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        currentSessionId={sessionId}
        userId={userId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChat}
        variant="rag"
      />

      {/* Header */}
      <div className="w-full max-w-[1280px] flex items-center justify-between">
        <div className="pl-4">
          <SapientLogo variant="rag" />
        </div>

        {/* Chat History Arrow */}
        <button
          onClick={() => setIsHistoryOpen(true)}
          className="pr-4 transition-transform hover:scale-110"
        >
          <svg
            width="21"
            height="21"
            viewBox="0 0 21 21"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g clipPath="url(#clip0_93_188)">
              <path
                d="M0.75 9V2.25C0.75 1.85218 0.908035 1.47064 1.18934 1.18934C1.47064 0.908035 1.85218 0.75 2.25 0.75H18.75C19.1478 0.75 19.5294 0.908035 19.8107 1.18934C20.092 1.47064 20.25 1.85218 20.25 2.25V18.75C20.25 19.1478 20.092 19.5294 19.8107 19.8107C19.5294 20.092 19.1478 20.25 18.75 20.25H12"
                stroke="#C1C1C1"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M6 20.25H0.75V15"
                stroke="#C1C1C1"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M0.75 20.25L10.5 10.5"
                stroke="#C1C1C1"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </g>
            <defs>
              <clipPath id="clip0_93_188">
                <rect width="21" height="21" fill="white" />
              </clipPath>
            </defs>
          </svg>
        </button>
      </div>

      {/* Content Area - Messages or RAG Icon and Description */}
      <div className={`flex-1 w-full max-w-[1280px] flex ${messages.length > 0 ? 'justify-start pt-4' : 'justify-center items-center'}`}>
        {messages.length > 0 ? (
          <div className="w-full max-w-[900px] mx-auto flex flex-col gap-8 px-6" style={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto' }}>
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} w-full animate-fade-in`}>
                {msg.role === 'user' ? (
                  <div className="max-w-[85%] bg-[#3D3D3D] text-[#FFFFFF] px-5 py-3.5 rounded-2xl text-[14px] leading-[1.6] shadow-md">
                    {msg.content}
                  </div>
                ) : (
                  <div className="w-full">
                    {/* Assistant label */}
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-6 h-6 rounded-full bg-[#D38B21] flex items-center justify-center">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M3.5 9.625H1C0.72386 9.625 0.5 9.84886 0.5 10.125V13C0.5 13.2761 0.72386 13.5 1 13.5H3.5C3.77614 13.5 4 13.2761 4 13V10.125C4 9.84886 3.77614 9.625 3.5 9.625Z" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M13 9.625H10.5C10.2239 9.625 10 9.84886 10 10.125V13C10 13.2761 10.2239 13.5 10.5 13.5H13C13.2761 13.5 13.5 13.2761 13.5 13V10.125C13.5 9.84886 13.2761 9.625 13 9.625Z" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M8.5 0.5H5.5C5.22386 0.5 5 0.72386 5 1V4C5 4.27614 5.22386 4.5 5.5 4.5H8.5C8.77614 4.5 9 4.27614 9 4V1C9 0.72386 8.77614 0.5 8.5 0.5Z" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M4 11.875H10" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M5.09375 4.28125L2.34375 9.625" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M8.90625 4.28125L11.6562 9.625" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      <span className="text-[12px] text-[#C8C6C4] font-semibold">Analyst</span>
                    </div>
                    {/* Assistant content */}
                    <div className="max-w-[95%] bg-[#2f2f2f] text-[#E0E0E0] px-5 py-4 rounded-2xl text-[14px] leading-[1.8] shadow rag-response prose prose-invert max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex flex-col items-start w-full animate-fade-in">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-full bg-[#D38B21] flex items-center justify-center">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3.5 9.625H1C0.72386 9.625 0.5 9.84886 0.5 10.125V13C0.5 13.2761 0.72386 13.5 1 13.5H3.5C3.77614 13.5 4 13.2761 4 13V10.125C4 9.84886 3.77614 9.625 3.5 9.625Z" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M13 9.625H10.5C10.2239 9.625 10 9.84886 10 10.125V13C10 13.2761 10.2239 13.5 10.5 13.5H13C13.2761 13.5 13.5 13.2761 13.5 13V10.125C13.5 9.84886 13.2761 9.625 13 9.625Z" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8.5 0.5H5.5C5.22386 0.5 5 0.72386 5 1V4C5 4.27614 5.22386 4.5 5.5 4.5H8.5C8.77614 4.5 9 4.27614 9 4V1C9 0.72386 8.77614 0.5 8.5 0.5Z" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M4 11.875H10" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M5.09375 4.28125L2.34375 9.625" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M8.90625 4.28125L11.6562 9.625" stroke="#464646" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <span className="text-[12px] text-[#C8C6C4] font-semibold">Analyst</span>
                </div>
                <div className="text-[#D0D0D0] text-[13px] leading-[1.7] italic">
                  Gathering context for the best possible answer…
                </div>
              </div>
            )}
          </div>
        ) : (
          welcomeVisible && (
            <div className="flex flex-col items-center gap-[47px] mx-auto">
              {/* Large RAG Icon */}
              <svg
                className="w-[155px] h-[155px] animate-fade-in"
                viewBox="0 0 155 155"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <g clipPath="url(#clip0_93_158)">
                  <path
                    d="M38.7499 110.714H11.0714C8.01407 110.714 5.53564 113.193 5.53564 116.25V143.929C5.53564 146.986 8.01407 149.464 11.0714 149.464H38.7499C41.8072 149.464 44.2856 146.986 44.2856 143.929V116.25C44.2856 113.193 41.8072 110.714 38.7499 110.714Z"
                    stroke="url(#paint0_linear_93_158)"
                    strokeWidth="11.0714"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M143.929 110.714H116.25C113.193 110.714 110.714 113.193 110.714 116.25V143.929C110.714 146.986 113.193 149.464 116.25 149.464H143.929C146.986 149.464 149.464 146.986 149.464 143.929V116.25C149.464 113.193 146.986 110.714 143.929 110.714Z"
                    stroke="url(#paint1_linear_93_158)"
                    strokeWidth="11.0714"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M94.1069 5.53589H60.8926C57.8354 5.53589 55.3569 8.01431 55.3569 11.0716V44.2859C55.3569 47.3432 57.8354 49.8216 60.8926 49.8216H94.1069C97.1642 49.8216 99.6426 47.3432 99.6426 44.2859V11.0716C99.6426 8.01431 97.1642 5.53589 94.1069 5.53589Z"
                    stroke="url(#paint2_linear_93_158)"
                    strokeWidth="11.0714"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M44.2856 132.857H110.714"
                    stroke="url(#paint3_linear_93_158)"
                    strokeWidth="11.0714"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M56.3532 47.4962L27.6782 110.714"
                    stroke="url(#paint4_linear_93_158)"
                    strokeWidth="11.0714"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M98.6462 47.4962L127.321 110.714"
                    stroke="url(#paint5_linear_93_158)"
                    strokeWidth="11.0714"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </g>
                <defs>
                  <linearGradient id="paint0_linear_93_158" x1="24.9106" y1="110.714" x2="24.9106" y2="149.464" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#C8C6C4" />
                    <stop offset="1" stopColor="#7F7B79" />
                  </linearGradient>
                  <linearGradient id="paint1_linear_93_158" x1="130.089" y1="110.714" x2="130.089" y2="149.464" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#C8C6C4" />
                    <stop offset="1" stopColor="#7F7B79" />
                  </linearGradient>
                  <linearGradient id="paint2_linear_93_158" x1="77.4998" y1="5.53589" x2="77.4998" y2="49.8216" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#C8C6C4" />
                    <stop offset="1" stopColor="#7F7B79" />
                  </linearGradient>
                  <linearGradient id="paint3_linear_93_158" x1="77.4999" y1="132.857" x2="77.4999" y2="133.857" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#C8C6C4" />
                    <stop offset="1" stopColor="#7F7B79" />
                  </linearGradient>
                  <linearGradient id="paint4_linear_93_158" x1="42.0157" y1="47.4962" x2="42.0157" y2="110.714" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#C8C6C4" />
                    <stop offset="1" stopColor="#7F7B79" />
                  </linearGradient>
                  <linearGradient id="paint5_linear_93_158" x1="112.984" y1="47.4962" x2="112.984" y2="110.714" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#C8C6C4" />
                    <stop offset="1" stopColor="#7F7B79" />
                  </linearGradient>
                  <clipPath id="clip0_93_158">
                    <rect width="155" height="155" fill="white" />
                  </clipPath>
                </defs>
              </svg>

              {/* Description */}
              <div className="flex items-start gap-2 max-w-[247px]">
                <svg
                  className="w-[13px] h-2 mt-[3px] flex-shrink-0"
                  viewBox="0 0 13 8"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <g clipPath="url(#clip0_140_92)">
                    <path
                      d="M3.64573 7.5L0.455688 4L3.64573 0.5"
                      stroke="#DCDCE8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M9.11438 7.5L12.3044 4L9.11438 0.5"
                      stroke="#DCDCE8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </g>
                  <defs>
                    <clipPath id="clip0_140_92">
                      <rect width="12.7601" height="8" fill="white" />
                    </clipPath>
                  </defs>
                </svg>
                <p className="text-[11px] leading-[15px] text-[#D7D2CF] mb-0">
                  This is the <span className="font-bold">RAG Function</span>, you can
                  use this function to query any information regarding the <span className="font-bold">Job descriptions.</span>
                </p>
              </div>
            </div>
          )
        )}
      </div>

      {/* Chat Input - sticky at bottom */}
      <div className="w-full flex justify-center sticky bottom-0 bg-[#313131]/80 backdrop-blur supports-[backdrop-filter]:bg-[#313131]/60 pt-4">
        <div className="w-full max-w-[1280px] flex justify-center">
          <ChatInput variant="rag" onSend={handleSend} />
        </div>
      </div>

      {/* Deep‑Dive Consent Modal */}
      {pendingDeepDive && (
        <ModalPortal>
          <div className="fixed inset-0 z-[999] flex items-center justify-center">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-[2px]"
              onClick={() => setPendingDeepDive(null)}
            />
            {/* Panel */}
            <div className="relative w-[560px] max-w-[92vw] modal-appear">
              <DeepDiveConsentCard
                description={pendingDeepDive.reason || 'No structured data matched this query. Deep‑Dive analyzes unstructured documents to generate guidance.'}
                onCancel={() => setPendingDeepDive(null)}
                onActivate={async () => {
                  const q = pendingDeepDive.question;
                  setPendingDeepDive(null);
                  setMessages(prev => [...prev, { role: 'assistant', content: '🔎 Deep‑Dive activated. Analyzing unstructured documents…' }]);
                  try {
                    const vecResp = await fetch(buildApiUrl('/chat/vector'), {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        question: q,
                        session_id: 'rag-session',
                        user_id: 'frontend-user'
                      }),
                    });
                    if (!vecResp.ok) throw new Error(`HTTP ${vecResp.status}`);
                    const vecData = await vecResp.json();
                    setMessages(prev => [...prev, { role: 'assistant', content: vecData.answer }]);
                  } catch (e: any) {
                    setMessages(prev => [...prev, { role: 'assistant', content: `Deep‑Dive failed: ${e?.message || 'Unknown error'}` }]);
                  }
                }}
              />
            </div>
          </div>
        </ModalPortal>
      )}
    </div>
  );
}
