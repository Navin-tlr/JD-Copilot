import { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { ChatHeader } from './ChatHeader';
import { AiThinkingFeedback } from './AiThinkingFeedback';
import { ScrollToBottom } from './ScrollToBottom';
import { MascotCharacter } from './MascotCharacter';
import { ParticleVortex } from './ParticleVortex';

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
  const [isTyping, setIsTyping] = useState(false);
  const [hasStartedChat, setHasStartedChat] = useState(false);
  const [isInputExpanded, setIsInputExpanded] = useState(false);
  const [isUserTyping, setIsUserTyping] = useState(false);
  const [mascotState, setMascotState] = useState<'welcome' | 'idle' | 'listening' | 'thinking'>('welcome');
  const [backendStatus, setBackendStatus] = useState<string>('');
  const [backendLogs, setBackendLogs] = useState<string[]>([]);
  const [estimatedTime, setEstimatedTime] = useState<number>(0);
  const [sessionId] = useState(`session_${Date.now()}_user`);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const generateDynamicLogs = (query: string): string[] => {
    const queryLower = query.toLowerCase();
    
    // Different log patterns based on query type
    if (queryLower.includes('how many') || queryLower.includes('count') || queryLower.includes('companies')) {
      return [
        '🔍 Routing decision: STRUCTURED',
        `🔍 Executing structured query for: "${query}"`,
        '🔧 Schema Helper: Analyzing placement data structure',
        '📊 Query: SELECT COUNT(DISTINCT company_id) FROM placements',
        '🔍 Retrieving company placement statistics...',
        '📈 Processing aggregation results...'
      ];
    } else if (queryLower.includes('jd') || queryLower.includes('job') || queryLower.includes('description')) {
      return [
        '🔍 Routing decision: HYBRID',
        `🔍 Analyzing job description query: "${query}"`,
        '🔍 Searching vector database for relevant JDs...',
        '📄 Found 5+ relevant job descriptions',
        '🔧 Schema Helper: Joining companies with roles table',
        '📋 Synthesizing comprehensive JD response...'
      ];
    } else if (queryLower.includes('salary') || queryLower.includes('package') || queryLower.includes('compensation')) {
      return [
        '🔍 Routing decision: STRUCTURED',
        `🔍 Querying compensation data for: "${query}"`,
        '💰 Accessing salary database...',
        '📊 Analyzing compensation trends...',
        '🔧 Schema Helper: Processing salary aggregations',
        '📈 Generating salary insights...'
      ];
    } else if (queryLower.includes('advice') || queryLower.includes('tips') || queryLower.includes('help')) {
      return [
        '🔍 Routing decision: UNSTRUCTURED',
        `🔍 Processing advice request: "${query}"`,
        '📚 Searching knowledge base for guidance...',
        '🧠 Analyzing context and user intent...',
        '💡 Retrieving relevant advice patterns...',
        '📝 Synthesizing personalized recommendations...'
      ];
    } else {
      // Default pattern for other queries
      return [
        '🔍 Routing decision: INTELLIGENT',
        `🔍 Processing query: "${query}"`,
        '🧠 Analyzing query intent and complexity...',
        '🔍 Determining optimal search strategy...',
        '📊 Executing multi-modal search approach...',
        '📝 Generating comprehensive response...'
      ];
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    // Mark that chat has started to hide particle vortex
    if (!hasStartedChat) {
      setHasStartedChat(true);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
      sessionId
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    setIsUserTyping(false);
    
    // Start real-time backend process tracking
    const startTime = Date.now();
    setMascotState('thinking');
    setBackendStatus('searching_vector_db');
    
    // Clear previous logs and start real timer
    setBackendLogs([]);
    setEstimatedTime(0);
    
    // Real-time progress tracking with micro-interactions
    const progressInterval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      setEstimatedTime(elapsed);
    }, 100); // Update every 100ms for smooth animation
    
    // Generate dynamic backend logs based on query content
    const logs = generateDynamicLogs(content);
    let logIndex = 0;
    
    // Real backend process progression with actual timing
    const logInterval = setInterval(() => {
      if (logIndex < logs.length) {
        setBackendLogs(prev => [...prev, logs[logIndex]]);
        logIndex++;
        
        // Update status based on log progress
        if (logIndex === 1) setBackendStatus('analyzing_query');
        else if (logIndex === 3) setBackendStatus('retrieving_documents');
        else if (logIndex === 5) setBackendStatus('generating_response');
      } else {
        clearInterval(logInterval);
      }
    }, 600); // Real log progression timing

    try {
      // Send message to Python backend
      console.log('🚀 Sending query to backend:', content);
      const response = await fetch('http://localhost:8000/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          content: content,
          user_id: 'user'
        }),
      });

      if (response.ok) {
        // Handle streaming response
        const reader = response.body?.getReader();
        if (reader) {
          let aiMessage: Message | null = null;
          
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              const chunk = new TextDecoder().decode(value);
              console.log('🔍 Received chunk:', chunk); // Debug log
              
              const lines = chunk.split('\n');
              
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.substring(6));
                    console.log('📊 Parsed data:', data); // Debug log
                    
                    if (data.type === 'ai_message_chunk') {
                      if (!aiMessage) {
                        aiMessage = {
                          id: data.message_id || Date.now().toString(),
                          content: data.content || '',
                          sender: 'ai',
                          timestamp: new Date(data.timestamp || Date.now()),
                          sessionId
                        };
                        setMessages(prev => [...prev, aiMessage!]);
                      } else {
                        // Update existing AI message
                        setMessages(prev => prev.map(msg => 
                          msg.id === aiMessage!.id 
                            ? { ...msg, content: msg.content + (data.content || '') }
                            : msg
                        ));
                      }
                    }
                  } catch (e) {
                    console.error('Error parsing chunk:', e);
                  }
                }
              }
            }
          } catch (error) {
            console.error('Error reading stream:', error);
          }
        }
      } else {
        // Fallback to simulated response if backend fails
        setTimeout(() => {
          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: 'Thanks for your message! This is a simulated AI response. The backend server responded with an error, so I\'m providing a fallback response.',
            sender: 'ai',
            timestamp: new Date(),
            sessionId
          };
          setMessages(prev => [...prev, aiMessage]);
          setIsTyping(false);
          setMascotState('idle');
        }, 1000 + Math.random() * 2000);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Fallback to simulated response when backend is not available
      setTimeout(() => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: 'Hello! I\'m your AI assistant. Since the backend server isn\'t running, I\'m providing a simulated response. To get real AI responses, please start the Python backend server.',
          sender: 'ai',
          timestamp: new Date(),
          sessionId
        };
        setMessages(prev => [...prev, aiMessage]);
        setIsTyping(false);
        setMascotState('idle');
      }, 1000);
    } finally {
      // Clean up intervals
      if (typeof progressInterval !== 'undefined') clearInterval(progressInterval);
      if (typeof logInterval !== 'undefined') clearInterval(logInterval);
      
      setIsTyping(false);
      setMascotState('idle');
      setBackendStatus('');
      setBackendLogs([]);
      setEstimatedTime(0);
    }
  };

  const handleInputExpand = () => {
    setIsInputExpanded(true);
    if (!hasStartedChat) {
      setHasStartedChat(true);
    }
  };

  const handleInputCollapse = () => {
    setIsInputExpanded(false);
  };

  const handleUserStartTyping = () => {
    setIsUserTyping(true);
    if (mascotState !== 'thinking') {
      setMascotState('listening');
    }
    
    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Set timeout to return to idle state after user stops typing
    typingTimeoutRef.current = setTimeout(() => {
      setIsUserTyping(false);
      if (mascotState !== 'thinking') {
        setMascotState('idle');
      }
    }, 2000);
  };

  const handleUserStopTyping = () => {
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    typingTimeoutRef.current = setTimeout(() => {
      setIsUserTyping(false);
      if (mascotState !== 'thinking') {
        setMascotState('idle');
      }
    }, 1000);
  };

  const handleMascotWelcomeComplete = () => {
    setMascotState('idle');
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-screen bg-background relative overflow-hidden">
      <ChatHeader onToggleTheme={onToggleTheme} isDarkMode={isDarkMode} />
      
      {/* Mascot Character - shown when no messages exist */}
      <MascotCharacter 
        state={mascotState}
        isVisible={messages.length === 0 && !isInputExpanded}
        onWelcomeComplete={handleMascotWelcomeComplete}
        onToggleTheme={onToggleTheme}
        isDarkMode={isDarkMode}
      />
      
      <div className="flex-1 overflow-hidden">
        <div 
          ref={messagesContainerRef}
          className="h-full overflow-y-auto px-3 py-4 md:px-6 md:py-8 scroll-smooth"
        >
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {/* AI Thinking Feedback - replaces simple typing indicator */}
          <AiThinkingFeedback 
            isThinking={isTyping} 
            backendStatus={backendStatus} 
            backendLogs={backendLogs}
            estimatedTime={estimatedTime}
          />
          
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Scroll to bottom button */}
      <ScrollToBottom 
        messagesContainerRef={messagesContainerRef}
        isVisible={messages.length > 0}
      />

      {/* Particle Vortex - shown before chat starts */}
      {!hasStartedChat && messages.length === 0 && (
        <div className="absolute inset-0 pointer-events-none">
          <ParticleVortex />
        </div>
      )}

      <ChatInput 
        onSendMessage={handleSendMessage} 
        onExpand={handleInputExpand}
        onCollapse={handleInputCollapse}
        onUserStartTyping={handleUserStartTyping}
        onUserStopTyping={handleUserStopTyping}
        disabled={isTyping} 
      />
    </div>
  );
}