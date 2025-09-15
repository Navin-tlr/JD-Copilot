import { motion } from 'framer-motion';
import { NotionStyleResponse } from './NotionStyleResponse';
import CitationIcon from '../src/components/CitationIcon';
// Placeholder for avatar image

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  sessionId: string;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.sender === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        type: "spring",
        stiffness: 400,
        damping: 25,
        duration: 0.4 
      }}
      className={`group relative ${isUser ? 'ml-6 md:ml-12' : 'mr-6 md:mr-12'} mb-4 md:mb-6 flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-2 md:gap-3`}
    >
      {/* Avatar */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: "spring", stiffness: 400, damping: 25 }}
        className="flex-shrink-0"
      >
        {isUser ? (
          <motion.div
            className="w-7 h-7 md:w-8 md:h-8 rounded-full bg-white shadow-sm ring-2 ring-primary/10 overflow-hidden"
            whileHover={{ scale: 1.1 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            <img 
              src="/assets/Avatar.jpg" 
              alt="User Avatar"
              className="w-full h-full object-cover"
            />
          </motion.div>
        ) : (
          <motion.div
            className="w-7 h-7 md:w-8 md:h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-medium shadow-sm"
            whileHover={{ scale: 1.1 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            y²
          </motion.div>
        )}
      </motion.div>

      {/* Message container */}
      <div
        className={`
          relative px-3 py-3 md:px-5 md:py-4 rounded-lg transition-all duration-200 flex-1
          ${isUser 
            ? 'bg-accent/40 border border-accent/60 max-w-[85%] md:max-w-[80%]' 
            : 'bg-background/50 border border-border/40 backdrop-blur-sm max-w-[90%] md:max-w-[85%]'
          }
          hover:shadow-sm hover:border-border/60
        `}
      >
        {/* Sender indicator */}
        <div className={`flex items-center gap-2 mb-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span className={`text-xs font-medium tracking-wide ${
            isUser 
              ? 'text-muted-foreground/70' 
              : 'text-muted-foreground/80'
          }`}>
            {isUser ? 'You' : 'y²'}
          </span>
          {!isUser && <CitationIcon companies={['Google', 'Meta', 'Amazon']} />}
          <div className={`w-1.5 h-1.5 rounded-full ${
            isUser 
              ? 'bg-foreground/60' 
              : 'bg-foreground/50'
          }`} />
        </div>
        
        {/* Message content */}
        <div className={`${isUser ? 'text-right' : 'text-left'}`}>
          {isUser ? (
            <p className="whitespace-pre-wrap break-words leading-relaxed text-sm md:text-[15px]">
              {message.content}
            </p>
          ) : (
            <NotionStyleResponse content={message.content} />
          )}
        </div>
        
        {/* Timestamp on hover */}
        <motion.div
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 1 }}
          className={`
            absolute -bottom-6 text-xs text-muted-foreground/60 pointer-events-none
            ${isUser ? 'right-2' : 'left-2'}
          `}
        >
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </motion.div>
      </div>
    </motion.div>
  );
}