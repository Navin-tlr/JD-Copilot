import { motion } from 'motion/react';
import avatarImage from 'figma:asset/49e1c59c05101ee88132a24fdd051bbf030d2c22.png';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
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
          <motion.img
            src={avatarImage}
            alt="User Avatar"
            className="w-7 h-7 md:w-8 md:h-8 rounded-2xl object-cover object-center shadow-lg shadow-black/10 dark:shadow-black/30"
            style={{
              objectPosition: 'center 20%',
              transform: 'scale(1.2)',
              transformOrigin: 'center'
            }}
            whileHover={{ scale: 1.1 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          />
        ) : (
          <motion.div
            className="w-7 h-7 md:w-8 md:h-8 rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-blue-500 flex items-center justify-center text-white text-xs font-medium shadow-lg shadow-violet-500/20"
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
          relative px-4 py-4 md:px-6 md:py-5 transition-all duration-300 flex-1 backdrop-blur-xl
          ${isUser 
            ? 'bg-gradient-to-br from-blue-500/10 to-indigo-500/5 border border-blue-200/30 dark:border-blue-800/30 rounded-2xl max-w-[85%] md:max-w-[80%] shadow-lg shadow-blue-500/5' 
            : 'bg-white/70 dark:bg-gray-800/70 border border-white/30 dark:border-gray-700/40 rounded-2xl max-w-[85%] md:max-w-[80%] shadow-lg shadow-black/5 dark:shadow-black/20'
          }
          hover:shadow-xl hover:scale-[1.02] hover:border-opacity-50
        `}
      >
        {/* Sender indicator */}
        <div className={`flex items-center gap-2 mb-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span className={`text-xs font-semibold tracking-wide ${
            isUser 
              ? 'text-blue-600 dark:text-blue-400' 
              : 'text-violet-600 dark:text-violet-400'
          }`}>
            {isUser ? 'You' : 'y²'}
          </span>
          <div className={`w-2 h-2 rounded-full ${
            isUser 
              ? 'bg-blue-500 shadow-sm' 
              : 'bg-violet-500 shadow-sm'
          }`} />
        </div>
        
        {/* Message content */}
        <div className={`${isUser ? 'text-right' : 'text-left'}`}>
          <p className="whitespace-pre-wrap break-words leading-relaxed text-sm md:text-[15px] text-gray-800 dark:text-gray-100">
            {message.content}
          </p>
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