import { motion } from 'framer-motion';

// Function to get user-friendly status messages
function getStatusMessage(status: string): string {
  switch (status) {
    case 'searching_vector_db':
      return 'Searching vector database...';
    case 'analyzing_query':
      return 'Analyzing your query...';
    case 'retrieving_documents':
      return 'Retrieving relevant documents...';
    case 'generating_response':
      return 'Generating intelligent response...';
    default:
      return 'y² is thinking...';
  }
}

interface AiThinkingFeedbackProps {
  isThinking: boolean;
  backendStatus?: string;
  backendLogs?: string[];
  estimatedTime?: number;
}

export function AiThinkingFeedback({ isThinking, backendStatus, backendLogs, estimatedTime }: AiThinkingFeedbackProps) {
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
            scale: [1, 1.05, 1]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        >
          y²
        </motion.div>
        
        {/* Backend process status */}
        <motion.span 
          className="text-muted-foreground text-sm"
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity, 
            ease: "easeInOut" 
          }}
        >
          {backendStatus ? getStatusMessage(backendStatus) : 'y² is thinking...'}
        </motion.span>
        
        {/* Minimal thinking dots */}
        <div className="flex gap-1 ml-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-1 h-1 bg-muted-foreground/40 rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.3, 0.8, 0.3]
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: i * 0.15,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </div>
      
      {/* Backend Logs Display */}
      {backendLogs && backendLogs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-3 p-3 bg-muted/30 rounded-lg border border-border/20"
        >
          <div className="text-xs text-muted-foreground mb-2 font-medium">Backend Process Logs:</div>
          <div className="space-y-1">
            {backendLogs.map((log, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-xs font-mono text-muted-foreground/80"
              >
                {log}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
      
      {/* Real-Time Elapsed Time */}
      {estimatedTime && estimatedTime > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-2 flex items-center gap-2"
        >
          <motion.div 
            className="text-xs text-muted-foreground"
            animate={{ opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            Processing time:
          </motion.div>
          <motion.div 
            className="text-xs font-medium text-primary"
            animate={{ 
              scale: [1, 1.05, 1],
              color: ['#3b82f6', '#8b5cf6', '#3b82f6']
            }}
            transition={{ duration: 0.8, repeat: Infinity }}
          >
            {estimatedTime.toFixed(1)}s
          </motion.div>
          
          {/* Real-time progress indicator */}
          <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min((estimatedTime / 5) * 100, 100)}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
          
          {/* Micro-interaction: Pulsing dot */}
          <motion.div
            className="w-1.5 h-1.5 bg-primary rounded-full"
            animate={{ 
              scale: [1, 1.5, 1],
              opacity: [0.5, 1, 0.5]
            }}
            transition={{ duration: 0.6, repeat: Infinity }}
          />
        </motion.div>
      )}
    </motion.div>
  );
}