import { useState, KeyboardEvent, useRef } from 'react';
import { Button } from './ui/button';
import { Send, Paperclip, Smile, FileText, CheckSquare, Trophy, Maximize2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { ModelSelector } from './ModelSelector';
import profileImage from 'figma:asset/49e1c59c05101ee88132a24fdd051bbf030d2c22.png';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onExpand?: () => void;
  onCollapse?: () => void;
  onUserStartTyping?: () => void;
  onUserStopTyping?: () => void;
  disabled?: boolean;
}

export function ChatInput({ 
  onSendMessage, 
  onExpand, 
  onCollapse, 
  onUserStartTyping,
  onUserStopTyping,
  disabled = false 
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [textareaHeight, setTextareaHeight] = useState('200px');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Trigger typing event on any key press (except Enter for send)
    if (e.key !== 'Enter') {
      onUserStartTyping?.();
    }
    
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleMessageChange = (value: string) => {
    setMessage(value);
    if (value.trim()) {
      onUserStartTyping?.();
    } else {
      onUserStopTyping?.();
    }
  };

  const handleExpand = () => {
    setIsExpanded(true);
    onExpand?.();
  };

  const handleCollapse = () => {
    setIsExpanded(false);
    onCollapse?.();
  };

  return (
    <div className="bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border-t border-white/20 dark:border-gray-800/40 shadow-lg shadow-black/5 dark:shadow-black/20">
      <motion.div 
        className="max-w-4xl mx-auto p-3 md:p-4"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
      >
        {/* Expanded mode with image and toolbar */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="mb-4 overflow-hidden"
            >
              {/* Profile Image Section */}
              <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1, type: "spring", stiffness: 300 }}
                className="flex justify-center mb-4 md:mb-6"
              >
                <div className="relative">
                  <motion.div
                    className="relative"
                    animate={{
                      y: [0, -2, 0],
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  >
                    <motion.img
                      src={profileImage}
                      alt="Profile"
                      className="w-12 h-12 md:w-16 md:h-16 rounded-3xl border-2 border-white/30 dark:border-gray-700/30 shadow-2xl bg-white dark:bg-gray-800"
                      whileHover={{ 
                        scale: 1.1,
                        rotate: [0, -5, 5, 0]
                      }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    />
                    <motion.div
                      className="absolute inset-0 rounded-full border-2 border-primary/20"
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0, 0.3, 0]
                      }}
                      transition={{
                        duration: 2.5,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    />
                  </motion.div>
                  
                  {/* Subtle glow effect */}
                  <motion.div
                    className="absolute -inset-2 rounded-full bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 blur-md -z-10"
                    animate={{
                      opacity: [0.3, 0.6, 0.3],
                    }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                  />
                </div>
              </motion.div>

              {/* Toolbar */}
              <motion.div
                className="flex items-center gap-1.5 md:gap-2 flex-wrap"
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                <motion.div
                  whileHover={{ 
                    scale: 1.02,
                    y: -2
                  }}
                  whileTap={{ scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 md:h-8 gap-1.5 md:gap-2 px-2.5 md:px-3 py-1 md:py-1.5 bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/50 dark:hover:bg-blue-950/70 text-blue-700 dark:text-blue-300 hover:text-blue-800 dark:hover:text-blue-200 border border-blue-200/50 dark:border-blue-800/50 hover:border-blue-300/70 dark:hover:border-blue-700/70 rounded-full transition-all duration-200"
                  >
                    <FileText className="h-3 w-3 md:h-3.5 md:w-3.5" />
                    <span className="text-xs font-medium">Y-Res</span>
                  </Button>
                </motion.div>
                
                <motion.div
                  whileHover={{ 
                    scale: 1.02,
                    y: -2
                  }}
                  whileTap={{ scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 md:h-8 gap-1.5 md:gap-2 px-2.5 md:px-3 py-1 md:py-1.5 bg-green-50 hover:bg-green-100 dark:bg-green-950/50 dark:hover:bg-green-950/70 text-green-700 dark:text-green-300 hover:text-green-800 dark:hover:text-green-200 border border-green-200/50 dark:border-green-800/50 hover:border-green-300/70 dark:hover:border-green-700/70 rounded-full transition-all duration-200"
                  >
                    <CheckSquare className="h-3 w-3 md:h-3.5 md:w-3.5" />
                    <span className="text-xs font-medium">Tasks</span>
                  </Button>
                </motion.div>
                
                <motion.div
                  whileHover={{ 
                    scale: 1.02,
                    y: -2
                  }}
                  whileTap={{ scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 md:h-8 gap-1.5 md:gap-2 px-2.5 md:px-3 py-1 md:py-1.5 bg-orange-50 hover:bg-orange-100 dark:bg-orange-950/50 dark:hover:bg-orange-950/70 text-orange-700 dark:text-orange-300 hover:text-orange-800 dark:hover:text-orange-200 border border-orange-200/50 dark:border-orange-800/50 hover:border-orange-300/70 dark:hover:border-orange-700/70 rounded-full transition-all duration-200"
                  >
                    <Trophy className="h-3 w-3 md:h-3.5 md:w-3.5" />
                    <span className="text-xs font-medium">Grill-Max</span>
                  </Button>
                </motion.div>
                
                <div className="flex-1" />
                
                <motion.div
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.25 }}
                  whileHover={{ 
                    scale: 1.05,
                    rotate: 5
                  }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCollapse}
                    className="h-8 w-8 md:h-9 md:w-9 p-0 text-muted-foreground hover:text-foreground rounded-xl hover:bg-gradient-to-r hover:from-gray-100/70 hover:to-slate-100/70 transition-all duration-300 border border-transparent hover:border-gray-200/50 hover:shadow-sm backdrop-blur-sm"
                  >
                    <Maximize2 className="h-3 w-3 md:h-3.5 md:w-3.5 rotate-180" />
                  </Button>
                </motion.div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main input container */}
        <motion.div
          animate={{
            scale: isFocused ? 1.02 : 1,
            boxShadow: isFocused 
              ? "0 20px 40px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(59, 130, 246, 0.2)" 
              : "0 8px 25px rgba(0, 0, 0, 0.06)"
          }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
          className={`
            relative backdrop-blur-xl rounded-3xl border transition-all duration-300
            ${isFocused 
              ? 'border-blue-200/50 dark:border-blue-700/50 bg-white/80 dark:bg-gray-800/80' 
              : 'border-white/30 dark:border-gray-700/30 bg-white/70 dark:bg-gray-800/70'
            }
          `}
        >


          {/* Main input area */}
          <div className={`flex ${isExpanded ? 'items-start' : 'items-end'} gap-2 md:gap-3 p-3 md:p-4 ${isExpanded ? 'pt-2' : 'pt-3'}`}>
            {/* Left side controls */}
            <div className={`flex items-center gap-1.5 md:gap-2 ${isExpanded ? 'pt-2' : ''}`}>
              {/* Model selector - positioned on the left */}
              <motion.div 
                className="flex items-center"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1, type: "spring", stiffness: 300, damping: 25 }}
              >
                <ModelSelector />
              </motion.div>

              {/* Subtle separator */}
              <div className="h-4 w-px bg-border/50" />

              {/* Action buttons */}
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 md:h-9 md:w-9 p-0 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-2xl hover:bg-white/60 dark:hover:bg-gray-700/60 transition-all duration-300 border border-white/20 dark:border-gray-600/20 hover:border-gray-200/50 dark:hover:border-gray-600/50 hover:shadow-lg backdrop-blur-sm group"
                >
                  <Paperclip className="h-3.5 w-3.5 md:h-4 md:w-4 transition-colors duration-300" />
                </Button>
              </motion.div>

              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 md:h-9 md:w-9 p-0 text-amber-500 dark:text-amber-400 hover:text-amber-600 dark:hover:text-amber-300 rounded-2xl hover:bg-amber-50/80 dark:hover:bg-amber-900/30 transition-all duration-300 border border-amber-200/30 dark:border-amber-700/30 hover:border-amber-300/50 dark:hover:border-amber-600/50 hover:shadow-lg backdrop-blur-sm group"
                >
                  <Smile className="h-3.5 w-3.5 md:h-4 md:w-4 transition-colors duration-300" />
                </Button>
              </motion.div>
            </div>
            
            {/* Text input */}
            <div className="flex-1">
              {isExpanded ? (
                <div className="relative">
                  <textarea
                    ref={textareaRef}
                    value={message}
                    onChange={(e) => handleMessageChange(e.target.value)}
                    onKeyDown={handleKeyPress}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => {
                      setIsFocused(false);
                      onUserStopTyping?.();
                    }}
                    placeholder="Aim, Shoot, and I deliver.."
                    disabled={disabled}
                    className="
                      w-full bg-white/50 dark:bg-gray-800/50 border border-gray-200/40 dark:border-gray-700/40 rounded-2xl p-4 
                      outline-none resize-none transition-all duration-300 backdrop-blur-sm
                      placeholder:text-gray-500 dark:placeholder:text-gray-400 text-gray-900 dark:text-gray-100
                      scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent
                      focus:border-blue-400/50 dark:focus:border-blue-600/50 focus:bg-white/70 dark:focus:bg-gray-800/70 focus:shadow-lg
                    "
                    rows={4}
                    style={{
                      minHeight: '80px',
                      maxHeight: textareaHeight
                    }}
                  />
                  {/* Expand button for textarea */}
                  <motion.button
                    className="absolute bottom-2 right-2 p-1.5 rounded-md hover:bg-accent/60 text-muted-foreground hover:text-foreground transition-all duration-200 hover:shadow-sm border border-transparent hover:border-border/20"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      const newHeight = textareaHeight === '200px' ? '300px' : '200px';
                      setTextareaHeight(newHeight);
                    }}
                  >
                    <Maximize2 className="h-3 w-3" />
                  </motion.button>
                </div>
              ) : (
                <textarea
                  value={message}
                  onChange={(e) => handleMessageChange(e.target.value)}
                  onKeyDown={handleKeyPress}
                  onFocus={() => {
                    setIsFocused(true);
                    handleExpand();
                  }}
                  onBlur={() => {
                    setIsFocused(false);
                    onUserStopTyping?.();
                  }}
                  placeholder="Aim, Shoot, and I deliver.."
                  disabled={disabled}
                  className="
                    w-full bg-transparent border-none outline-none resize-none
                    placeholder:text-gray-500 dark:placeholder:text-gray-400 text-gray-900 dark:text-gray-100
                    scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent
                  "
                  rows={1}
                  style={{
                    height: 'auto',
                    minHeight: '20px',
                    maxHeight: '32px',
                    overflowY: 'hidden'
                  }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = 'auto';
                    target.style.height = Math.min(target.scrollHeight, 32) + 'px';
                  }}
                />
              )}
            </div>
            
            {/* Right side controls */}
            <div className={`flex items-center gap-1.5 md:gap-2 ${isExpanded ? 'pt-2' : ''}`}>
              {/* Send button */}
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  onClick={handleSend}
                  disabled={!message.trim() || disabled}
                  size="icon"
                  className={`
                    h-9 w-9 md:h-10 md:w-10 rounded-2xl transition-all duration-300 relative overflow-hidden shadow-lg
                    ${message.trim() && !disabled
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 shadow-blue-500/25 hover:shadow-blue-500/40 hover:shadow-xl border border-blue-400/20' 
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed border border-gray-300 dark:border-gray-600'
                    }
                  `}
                >
                  <Send className="h-4 w-4 md:h-4.5 md:w-4.5 relative z-10" />
                  {message.trim() && !disabled && (
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0"
                      animate={{
                        x: ['-100%', '100%']
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "linear"
                      }}
                    />
                  )}
                </Button>
              </motion.div>

              {/* Expand button - only visible when not expanded */}
              {!isExpanded && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleExpand}
                    className="h-9 w-9 p-0 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-2xl hover:bg-white/60 dark:hover:bg-gray-700/60 transition-all duration-300 border border-white/20 dark:border-gray-600/20 hover:border-gray-200/50 dark:hover:border-gray-600/50 hover:shadow-lg backdrop-blur-sm"
                  >
                    <Maximize2 className="h-3.5 w-3.5" />
                  </Button>
                </motion.div>
              )}
            </div>
          </div>

          {/* Expanded mode footer */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2, delay: 0.1 }}
                className="flex items-center justify-between px-4 pb-4 pt-3 border-t border-border/20"
              >
                <motion.div
                  className="flex items-center gap-4 text-xs text-muted-foreground"
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <span>Press ⏎ to send, ⇧⏎ for new line</span>
                  <span className="text-xs text-muted-foreground/60">•</span>
                  <span>Click expand icon to resize text area</span>
                </motion.div>
                
                <motion.div
                  className="flex items-center gap-2"
                  initial={{ x: 10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.25 }}
                >
                  <span className={`text-xs transition-colors ${
                    message.length > 3800 ? 'text-destructive' : 
                    message.length > 3000 ? 'text-yellow-500' : 
                    'text-muted-foreground'
                  }`}>
                    {message.length}/4000
                  </span>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </div>
  );
}