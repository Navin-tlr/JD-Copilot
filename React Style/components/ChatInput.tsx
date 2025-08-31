import { useState, KeyboardEvent, useRef } from 'react';
import { Button } from './ui/button';
import { Send, Paperclip, Smile, FileText, CheckSquare, Trophy, Maximize2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
// ModelSelector component not needed for basic functionality
// Placeholder for profile image

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
    <div className="border-t border-border/50 bg-background/80 backdrop-blur-sm">
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
                    <motion.div
                      className="w-12 h-12 md:w-16 md:h-16 rounded-full border-2 border-border/20 shadow-lg bg-white overflow-hidden"
                      whileHover={{ 
                        scale: 1.1,
                        rotate: [0, -5, 5, 0]
                      }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    >
                      <motion.img 
                        src="/assets/Avatar.jpg" 
                        alt="Profile"
                        className="w-full h-full object-cover"
                        animate={{
                          y: [0, -2, 0],
                        }}
                        transition={{
                          duration: 3,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      />
                    </motion.div>
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
            scale: isFocused ? 1.01 : 1,
            boxShadow: isFocused 
              ? "0 8px 25px rgba(0, 0, 0, 0.15)" 
              : "0 4px 12px rgba(0, 0, 0, 0.08)"
          }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
          className={`
            relative bg-card rounded-2xl border transition-colors duration-200
            ${isFocused 
              ? 'border-primary/20 bg-card' 
              : 'border-border/60 bg-card/80'
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
                <div className="text-xs text-muted-foreground px-2 py-1 bg-muted/50 rounded-md">
                  GPT-4
                </div>
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
                  className="h-8 w-8 md:h-9 md:w-9 p-0 text-muted-foreground hover:text-foreground rounded-xl hover:bg-gradient-to-r hover:from-slate-100/70 hover:to-gray-100/70 transition-all duration-300 border border-transparent hover:border-slate-200/50 hover:shadow-sm backdrop-blur-sm group"
                >
                  <Paperclip className="h-3.5 w-3.5 md:h-4 md:w-4 transition-colors duration-300 group-hover:text-slate-600" />
                </Button>
              </motion.div>

              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 md:h-9 md:w-9 p-0 text-muted-foreground hover:text-foreground rounded-xl hover:bg-gradient-to-r hover:from-amber-100/70 hover:to-yellow-100/70 transition-all duration-300 border border-transparent hover:border-amber-200/50 hover:shadow-sm backdrop-blur-sm group"
                >
                  <Smile className="h-3.5 w-3.5 md:h-4 md:w-4 transition-colors duration-300 group-hover:text-amber-600" />
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
                      w-full bg-muted/30 border border-border/30 rounded-lg p-3 
                      outline-none resize-none transition-all duration-200
                      placeholder:text-muted-foreground text-foreground
                      scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent
                      focus:border-primary/30 focus:bg-muted/40 focus:shadow-sm
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
                  onClick={() => {
                    if (!isExpanded) {
                      handleExpand();
                    }
                  }}
                  onBlur={() => {
                    setIsFocused(false);
                    onUserStopTyping?.();
                  }}
                  placeholder="Aim, Shoot, and I deliver.."
                  disabled={disabled}
                  className="
                    w-full bg-transparent border-none outline-none resize-none
                    placeholder:text-muted-foreground text-foreground
                    scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent
                    cursor-text
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
                    h-8 w-8 md:h-9 md:w-9 rounded-full transition-all duration-300 relative overflow-hidden
                    ${message.trim() && !disabled
                      ? 'bg-foreground text-background hover:bg-foreground/90 shadow-lg hover:shadow-xl border border-foreground/10' 
                      : 'bg-muted text-muted-foreground cursor-not-allowed border border-muted'
                    }
                  `}
                >
                  <Send className="h-3.5 w-3.5 md:h-4 md:w-4 relative z-10" />
                  {message.trim() && !disabled && (
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0"
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
                    className="h-9 w-9 p-0 text-muted-foreground hover:text-foreground rounded-xl hover:bg-gradient-to-r hover:from-gray-100/70 hover:to-slate-100/70 transition-all duration-300 border border-transparent hover:border-gray-200/50 hover:shadow-sm backdrop-blur-sm"
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