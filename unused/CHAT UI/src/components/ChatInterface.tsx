import { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { ChatHeader } from './ChatHeader';
import { ChatHistory } from './ChatHistory';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from './ui/sheet';

import { AiThinkingFeedback } from './AiThinkingFeedback';
import { ScrollToBottom } from './ScrollToBottom';
import { MascotCharacter } from './MascotCharacter';
import exampleImage from 'figma:asset/786ebf39101d18c428fa4e3c89e6ad75ed54d332.png';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
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
  const [isChatHistoryOpen, setIsChatHistoryOpen] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize current chat ID
  useEffect(() => {
    if (!currentChatId) {
      setCurrentChatId(generateChatId());
    }
  }, []);

  const generateChatId = () => {
    return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  };

  const saveChatSession = (chatMessages: Message[]) => {
    if (chatMessages.length === 0) return;

    const chatSessions = JSON.parse(localStorage.getItem('yakkssha-chat-sessions') || '[]');
    const existingChatIndex = chatSessions.findIndex((chat: any) => chat.id === currentChatId);
    
    const chatTitle = chatMessages[0]?.content.slice(0, 50) || 'New Chat';
    const lastMessage = chatMessages[chatMessages.length - 1]?.content || '';
    
    const chatSession = {
      id: currentChatId,
      title: chatTitle,
      lastMessage,
      timestamp: new Date(),
      messageCount: chatMessages.length,
      messages: chatMessages
    };

    if (existingChatIndex >= 0) {
      chatSessions[existingChatIndex] = chatSession;
    } else {
      chatSessions.push(chatSession);
    }

    localStorage.setItem('yakkssha-chat-sessions', JSON.stringify(chatSessions));
  };

  const handleSendMessage = async (content: string) => {
    // Mark that chat has started to hide particle vortex
    if (!hasStartedChat) {
      setHasStartedChat(true);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date()
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsTyping(true);
    setIsUserTyping(false);
    setMascotState('thinking');

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Thanks for your message! This is a simulated AI response. In a real implementation, this would connect to an actual AI service.',
        sender: 'ai',
        timestamp: new Date()
      };
      const finalMessages = [...newMessages, aiMessage];
      setMessages(finalMessages);
      saveChatSession(finalMessages);
      setIsTyping(false);
      setMascotState('idle');
    }, 1000 + Math.random() * 2000);
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

  const handleOpenChatHistory = () => {
    setIsChatHistoryOpen(true);
  };

  const handleSelectChat = (chatId: string) => {
    const chatSessions = JSON.parse(localStorage.getItem('yakkssha-chat-sessions') || '[]');
    const selectedChat = chatSessions.find((chat: any) => chat.id === chatId);
    
    if (selectedChat) {
      setMessages(selectedChat.messages || []);
      setCurrentChatId(chatId);
      setHasStartedChat(selectedChat.messages?.length > 0);
    }
    
    setIsChatHistoryOpen(false);
  };

  const handleNewChat = () => {
    setMessages([]);
    setCurrentChatId(generateChatId());
    setHasStartedChat(false);
    setMascotState('welcome');
    setIsInputExpanded(false);
    setIsChatHistoryOpen(false);
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
    <div className="flex flex-col h-screen relative overflow-hidden">
      {/* Clean minimal background */}
      <div className="absolute inset-0 bg-background" />
      
      <div className="relative z-10 flex flex-col h-full">
        <ChatHeader onOpenChatHistory={handleOpenChatHistory} />
        
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
            <AiThinkingFeedback isThinking={isTyping} />
            
            <div ref={messagesEndRef} />
          </div>
        </div>
        
        {/* Scroll to bottom button */}
        <ScrollToBottom 
          messagesContainerRef={messagesContainerRef}
          isVisible={messages.length > 0}
        />

        <ChatInput 
          onSendMessage={handleSendMessage} 
          onExpand={handleInputExpand}
          onCollapse={handleInputCollapse}
          onUserStartTyping={handleUserStartTyping}
          onUserStopTyping={handleUserStopTyping}
          disabled={isTyping} 
        />
      </div>

      {/* Chat History Sidebar */}
      <Sheet open={isChatHistoryOpen} onOpenChange={setIsChatHistoryOpen}>
        <SheetContent side="left" className="w-80 p-0 bg-background border-r border-border">
          <SheetHeader className="sr-only">
            <SheetTitle>Chat History</SheetTitle>
            <SheetDescription>
              View and manage your previous chat conversations
            </SheetDescription>
          </SheetHeader>
          <ChatHistory
            onSelectChat={handleSelectChat}
            onNewChat={handleNewChat}
            currentChatId={currentChatId}
          />
        </SheetContent>
      </Sheet>
    </div>
  );
}