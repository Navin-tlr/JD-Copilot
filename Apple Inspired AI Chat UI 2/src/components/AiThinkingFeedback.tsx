import { motion } from "motion/react";
import avatarImage from "figma:asset/49e1c59c05101ee88132a24fdd051bbf030d2c22.png";

interface AiThinkingFeedbackProps {
  isThinking: boolean;
}

export function AiThinkingFeedback({
  isThinking,
}: AiThinkingFeedbackProps) {
  if (!isThinking) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex items-center gap-3 mr-12 mb-4 px-1"
    >
      {/* Simple thinking indicator */}
      <div className="flex items-center gap-2">
        {/* AI thinking avatar */}
        <motion.div
          className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-medium shadow-sm"
          animate={{
            rotate: [0, 10, -10, 0],
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          y²
        </motion.div>

        {/* Clean thinking text */}
        <motion.span
          className="text-muted-foreground text-sm"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          y² is thinking...
        </motion.span>

        {/* Minimal thinking dots */}
        <div className="flex gap-1 ml-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-1 h-1 bg-muted-foreground/40 rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.8, 0.3],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: i * 0.15,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}