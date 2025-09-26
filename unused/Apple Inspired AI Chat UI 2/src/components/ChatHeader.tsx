import { Button } from './ui/button';
import { MoreHorizontal, Settings, User, Menu } from 'lucide-react';
import { motion } from 'motion/react';
import avatarImage from 'figma:asset/49e1c59c05101ee88132a24fdd051bbf030d2c22.png';

interface ChatHeaderProps {
  onOpenChatHistory: () => void;
}

export function ChatHeader({ onOpenChatHistory }: ChatHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="
        flex items-center justify-between px-3 py-3 md:px-5 md:py-4
        bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl border-b border-white/20 dark:border-gray-800/40
        shadow-sm shadow-black/5 dark:shadow-black/20
      "
    >
      <div className="flex items-center gap-2 md:gap-3">
        {/* Chat History Button */}
        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
          <Button 
            onClick={onOpenChatHistory}
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 md:h-9 md:w-9 rounded-xl bg-white/40 dark:bg-gray-800/40 hover:bg-white/60 dark:hover:bg-gray-700/60 border border-white/20 dark:border-gray-700/40 shadow-sm backdrop-blur-sm transition-all duration-200"
          >
            <Menu className="h-4 w-4 text-gray-700 dark:text-gray-300" />
          </Button>
        </motion.div>

        <motion.div
          className="relative"
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
        >
          <motion.img
            src={avatarImage}
            alt="YAKKSSHA Avatar"
            className="w-9 h-9 md:w-11 md:h-11 rounded-2xl object-cover object-center shadow-lg shadow-black/10 dark:shadow-black/30"
            style={{
              objectPosition: 'center 20%',
              transform: 'scale(1.3)',
              transformOrigin: 'center'
            }}
          />
          {/* Subtle glow effect */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-blue-500/10 to-purple-500/10 blur-sm -z-10" />
          {/* Online status indicator */}
          <motion.div 
            className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-gray-900 shadow-sm"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </motion.div>
        <div>
          <h2 className="font-medium text-sm md:text-base text-gray-900 dark:text-white">YAKKSSHA</h2>
          <motion.span 
            className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1"
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full block" />
            Online
          </motion.span>
        </div>
      </div>

      <div className="flex items-center gap-1 md:gap-2">
        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 md:h-9 md:w-9 rounded-xl bg-white/40 dark:bg-gray-800/40 hover:bg-white/60 dark:hover:bg-gray-700/60 border border-white/20 dark:border-gray-700/40 shadow-sm backdrop-blur-sm transition-all duration-200"
          >
            <User className="h-4 w-4 text-gray-700 dark:text-gray-300" />
          </Button>
        </motion.div>
        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 md:h-9 md:w-9 rounded-xl bg-white/40 dark:bg-gray-800/40 hover:bg-white/60 dark:hover:bg-gray-700/60 border border-white/20 dark:border-gray-700/40 shadow-sm backdrop-blur-sm transition-all duration-200"
          >
            <Settings className="h-4 w-4 text-gray-700 dark:text-gray-300" />
          </Button>
        </motion.div>
        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 md:h-9 md:w-9 rounded-xl bg-white/40 dark:bg-gray-800/40 hover:bg-white/60 dark:hover:bg-gray-700/60 border border-white/20 dark:border-gray-700/40 shadow-sm backdrop-blur-sm transition-all duration-200"
          >
            <MoreHorizontal className="h-4 w-4 text-gray-700 dark:text-gray-300" />
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}