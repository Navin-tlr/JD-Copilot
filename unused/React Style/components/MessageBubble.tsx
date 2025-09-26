import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  sessionId: string;
}

interface TerminalMessageBubbleProps {
  message: Message;
  index?: number;
}

export function MessageBubble({ message, index = 0 }: TerminalMessageBubbleProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Typewriter effect for AI messages
  useEffect(() => {
    if (message.sender === 'ai') {
      setIsTyping(true);
      let currentIndex = 0;
      const text = message.content;

      const typeInterval = setInterval(() => {
        if (currentIndex <= text.length) {
          setDisplayedText(text.slice(0, currentIndex));
          currentIndex++;
        } else {
          clearInterval(typeInterval);
          setIsTyping(false);
        }
      }, 15);

      return () => clearInterval(typeInterval);
    } else {
      setDisplayedText(message.content);
    }
  }, [message.content, message.sender]);

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getPromptSymbol = () => {
    return message.sender === 'user' ? '$' : '>';
  };

  const getPromptColor = () => {
    return message.sender === 'user'
      ? 'text-green-500 dark:text-green-400'
      : 'text-blue-500 dark:text-blue-400';
  };

  const getTextColor = () => {
    return message.sender === 'user'
      ? 'text-green-700 dark:text-green-300'
      : 'text-blue-700 dark:text-blue-300';
  };

  const getBgColor = () => {
    return message.sender === 'user'
      ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
      : 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.1,
        duration: 0.3,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      className={`mb-4 ${message.sender === 'user' ? 'ml-auto' : 'mr-auto'} max-w-3xl`}
    >
      <div className={`rounded-xl border p-4 font-mono text-sm ${getBgColor()}`}>
        {/* Terminal header with timestamp */}
        <div className="flex items-center justify-between mb-2 pb-2 border-b border-current/10">
          <div className="flex items-center gap-2">
            <span className={`font-bold ${getPromptColor()}`}>
              {getPromptSymbol()}
            </span>
            <span className="text-xs text-muted-foreground">
              {message.sender === 'user' ? 'yakkssha' : 'ai-assistant'}
            </span>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>

        {/* Message content */}
        <div className={`${getTextColor()} whitespace-pre-wrap leading-relaxed`}>
          {displayedText}
          {isTyping && (
            <motion.span
              className={getTextColor()}
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 0.8, repeat: Infinity }}
            >
              ▊
            </motion.span>
          )}
        </div>

        {/* Terminal footer */}
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-current/10">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className={`w-1.5 h-1.5 rounded-full ${message.sender === 'user' ? 'bg-green-500' : 'bg-blue-500'}`} />
            <span>
              {message.sender === 'user' ? 'sent' : 'received'}
            </span>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {message.content.length} chars
          </span>
        </div>
      </div>
    </motion.div>
  );
}