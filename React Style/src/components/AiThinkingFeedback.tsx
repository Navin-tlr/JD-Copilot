import { motion } from "motion/react";
import avatarImage from "figma:asset/49e1c59c05101ee88132a24fdd051bbf030d2c22.png";

interface AiThinkingFeedbackProps {
  isThinking: boolean;
  onCancel?: () => void;
}

export function AiThinkingFeedback({
  isThinking,
  onCancel,
}: AiThinkingFeedbackProps) {
  if (!isThinking) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="flex items-center gap-3 mr-12 mb-4 px-2"
    >
      <div className="flex items-center gap-3 bg-white/80 dark:bg-gray-800/70 border border-white/20 dark:border-gray-700/30 rounded-full px-3 py-2 shadow-sm">
        {/* simple pulsing avatar */}
        <motion.div
          className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-white text-xs font-semibold"
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
        >
          y²
        </motion.div>

        {/* short label */}
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-800 dark:text-gray-100">Generating response</span>
          <div className="w-48 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mt-1">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-400 via-violet-400 to-pink-400"
              animate={{ x: ['-30%', '100%'] }}
              transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
              style={{ width: '40%' }}
            />
          </div>
        </div>

        {/* interactive cancel */}
        <div className="ml-2">
          <button
            onClick={() => onCancel && onCancel()}
            className="text-xs text-gray-600 dark:text-gray-300 bg-white/0 hover:bg-gray-100 dark:hover:bg-gray-700 px-3 py-1 rounded-full border border-transparent hover:border-gray-200 transition-colors"
          >
            Stop
          </button>
        </div>
      </div>
    </motion.div>
  );
}