import { Button } from './ui/button';
import { MoreHorizontal, Settings, User } from 'lucide-react';
import { motion } from 'framer-motion';
// Placeholder for avatar image

interface ChatHeaderProps {
  onToggleTheme?: () => void;
  isDarkMode?: boolean;
}

export function ChatHeader({ onToggleTheme, isDarkMode }: ChatHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="
        flex items-center justify-between px-3 py-2 md:px-4 md:py-3 
        border-b border-border bg-background/80 backdrop-blur-md
      "
    >
      <div className="flex items-center gap-2 md:gap-3">
        <motion.div
          className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-white ring-2 ring-primary/10 overflow-hidden"
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
        >
          <img 
            src="/assets/Avatar.jpg" 
            alt="YAKKSSHA"
            className="w-full h-full object-cover"
          />
        </motion.div>
        <div>
          <h2 className="font-medium text-sm md:text-base">YAKKSSHA</h2>
          <p className="text-xs text-muted-foreground">Online</p>
        </div>
      </div>

      <div className="flex items-center gap-0.5 md:gap-1">
        {onToggleTheme && (
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-7 w-7 md:h-8 md:w-8"
            onClick={onToggleTheme}
          >
            {isDarkMode ? (
              <svg className="h-3.5 w-3.5 md:h-4 md:w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="h-3.5 w-3.5 md:h-4 md:w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </Button>
        )}
        <Button variant="ghost" size="icon" className="h-7 w-7 md:h-8 md:w-8">
          <User className="h-3.5 w-3.5 md:h-4 md:w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-7 w-7 md:h-8 md:w-8">
          <Settings className="h-3.5 w-3.5 md:h-4 md:w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-7 w-7 md:h-8 md:w-8">
          <MoreHorizontal className="h-3.5 w-3.5 md:h-4 md:w-4" />
        </Button>
      </div>
    </motion.div>
  );
}