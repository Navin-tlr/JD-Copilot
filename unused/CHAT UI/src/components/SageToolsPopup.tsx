import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { 
  Search, 
  FileText, 
  MessageSquare, 
  CheckSquare, 
  TrendingUp, 
  Users, 
  BarChart,
  Plus,
  Sparkles 
} from 'lucide-react';

interface SageToolsPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onToolSelect: (tool: string) => void;
}

interface Tool {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  bgColor: string;
  iconColor: string;
}

const tools: Tool[] = [
  {
    id: 'resume-strategist',
    name: 'Resume Strategist',
    description: 'AI-powered resume optimization and career strategy guidance',
    icon: <FileText className="h-5 w-5" />,
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    iconColor: 'text-blue-600 dark:text-blue-400'
  },
  {
    id: 'researcher',
    name: 'Researcher',
    description: 'Advanced research and data analysis capabilities',
    icon: <Search className="h-5 w-5" />,
    bgColor: 'bg-green-50 dark:bg-green-950/30',
    iconColor: 'text-green-600 dark:text-green-400'
  },
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Data visualization and performance metrics analysis',
    icon: <BarChart className="h-5 w-5" />,
    bgColor: 'bg-purple-50 dark:bg-purple-950/30',
    iconColor: 'text-purple-600 dark:text-purple-400'
  },
  {
    id: 'grill',
    name: 'Grill',
    description: 'Deep analysis and critical questioning techniques',
    icon: <MessageSquare className="h-5 w-5" />,
    bgColor: 'bg-orange-50 dark:bg-orange-950/30',
    iconColor: 'text-orange-600 dark:text-orange-400'
  },
  {
    id: 'tasks',
    name: 'Tasks',
    description: 'Task management and intelligent planning workflows',
    icon: <CheckSquare className="h-5 w-5" />,
    bgColor: 'bg-cyan-50 dark:bg-cyan-950/30',
    iconColor: 'text-cyan-600 dark:text-cyan-400'
  },
  {
    id: 'radar',
    name: 'Radar',
    description: 'Trend detection and market intelligence monitoring',
    icon: <TrendingUp className="h-5 w-5" />,
    bgColor: 'bg-indigo-50 dark:bg-indigo-950/30',
    iconColor: 'text-indigo-600 dark:text-indigo-400'
  },
  {
    id: 'inner-circle',
    name: 'Inner Circle',
    description: 'Exclusive insights and collaborative intelligence',
    icon: <Users className="h-5 w-5" />,
    bgColor: 'bg-pink-50 dark:bg-pink-950/30',
    iconColor: 'text-pink-600 dark:text-pink-400'
  }
];

export function SageToolsPopup({ isOpen, onClose, onToolSelect }: SageToolsPopupProps) {
  const handleToolClick = (toolId: string) => {
    onToolSelect(toolId);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <Dialog open={isOpen} onOpenChange={onClose}>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/80"
          />
          <DialogContent className="w-[92vw] max-w-md mx-auto bg-background border border-border/50 shadow-2xl max-h-[85vh] rounded-2xl p-0 overflow-hidden">
            <DialogHeader className="p-6 pb-4 text-center border-b border-border/30">
              <DialogTitle className="flex items-center justify-center gap-2 mb-2 text-lg font-medium text-foreground">
                <Sparkles className="h-4 w-4 text-muted-foreground" />
                Sage Tools
              </DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground">
                Choose a specialized tool to enhance your conversation
              </DialogDescription>
            </DialogHeader>
            
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              transition={{ 
                type: "spring", 
                damping: 25, 
                stiffness: 300,
                duration: 0.3 
              }}
              className="w-full h-full"
            >

              {/* Tools Grid - Scrollable */}
              <div className="overflow-y-auto max-h-[calc(85vh-180px)] p-6 pt-4">
                <div className="grid grid-cols-2 gap-3">
                  {tools.map((tool, index) => (
                    <motion.div
                      key={tool.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05, duration: 0.2 }}
                    >
                      <Button
                        variant="ghost"
                        onClick={() => handleToolClick(tool.id)}
                        className={`
                          w-full h-[120px] p-4 flex flex-col items-start text-left rounded-2xl 
                          border border-border/30 ${tool.bgColor} 
                          hover:border-border/60 hover:shadow-sm hover:scale-[1.02]
                          transition-all duration-200 group relative overflow-hidden
                        `}
                      >
                        {/* Icon */}
                        <div className={`${tool.iconColor} mb-3`}>
                          {tool.icon}
                        </div>
                        
                        {/* Content */}
                        <div className="flex-1 w-full">
                          <div className="font-medium text-foreground text-sm mb-1 leading-tight">
                            {tool.name}
                          </div>
                          <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                            {tool.description}
                          </p>
                        </div>
                        
                        {/* Plus icon */}
                        <div className="absolute top-4 right-4 opacity-40 group-hover:opacity-60 transition-opacity">
                          <Plus className="h-4 w-4" />
                        </div>
                      </Button>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className="p-6 pt-4 border-t border-border/30">
                <Button
                  variant="ghost"
                  onClick={onClose}
                  className="w-full text-muted-foreground hover:text-foreground py-3 text-sm rounded-xl
                           hover:bg-muted/50 transition-all duration-200"
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </DialogContent>
        </Dialog>
      )}
    </AnimatePresence>
  );
}