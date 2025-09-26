import { useState } from 'react';
import { Button } from './ui/button';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Check, ChevronDown, Zap, Brain } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface ModelOption {
  id: string;
  name: string;
  description: string;
  speed: number; // 1-5 scale
  capability: number; // 1-5 scale
  icon: 'zap' | 'brain';
}

const models: ModelOption[] = [
  {
    id: 'y-fast',
    name: 'Y-Fast',
    description: 'Lightning quick responses',
    speed: 5,
    capability: 3,
    icon: 'zap'
  },
  {
    id: 'y-smart',
    name: 'Y-Smart',
    description: 'Advanced reasoning and analysis',
    speed: 3,
    capability: 5,
    icon: 'brain'
  }
];

export function ModelSelector() {
  const [selectedModel, setSelectedModel] = useState<ModelOption>(models[0]);
  const [isOpen, setIsOpen] = useState(false);
  const [isClicked, setIsClicked] = useState(false);

  const SpeedIndicator = ({ speed }: { speed: number }) => (
    <div className="flex items-center gap-1">
      <span className="text-xs text-muted-foreground">Speed</span>
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((level) => (
          <div
            key={level}
            className={`w-1 h-3 rounded-sm ${
              level <= speed 
                ? 'bg-green-500' 
                : 'bg-muted'
            }`}
          />
        ))}
      </div>
    </div>
  );

  const CapabilityIndicator = ({ capability }: { capability: number }) => (
    <div className="flex items-center gap-1">
      <span className="text-xs text-muted-foreground">Smart</span>
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((level) => (
          <div
            key={level}
            className={`w-1 h-3 rounded-sm ${
              level <= capability 
                ? 'bg-blue-500' 
                : 'bg-muted'
            }`}
          />
        ))}
      </div>
    </div>
  );

  const handleClick = () => {
    setIsClicked(true);
    setTimeout(() => setIsClicked(false), 200);
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <motion.div
          animate={{
            scale: isClicked ? 0.95 : 1,
            rotateX: isClicked ? 5 : 0,
          }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
          whileHover={{ 
            scale: 1.02, 
            y: -1,
          }}
          whileTap={{ scale: 0.98 }}
        >
          <Button
            variant="ghost"
            className="h-8 px-3 gap-2 text-sm bg-white/50 dark:bg-gray-800/50 hover:bg-white/70 dark:hover:bg-gray-700/70 transition-all duration-300 border border-white/30 dark:border-gray-600/30 hover:border-gray-200/50 dark:hover:border-gray-600/50 rounded-2xl shadow-sm hover:shadow-lg backdrop-blur-sm"
            onClick={handleClick}
          >
            <div className="flex items-center gap-2">
              <motion.div
                animate={{
                  rotate: isOpen ? 90 : 0,
                  scale: isClicked ? 1.1 : 1
                }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                {selectedModel.icon === 'zap' ? (
                  <Zap className="h-3.5 w-3.5 text-yellow-500" />
                ) : (
                  <Brain className="h-3.5 w-3.5 text-purple-500" />
                )}
              </motion.div>
              <span className="font-medium text-gray-700 dark:text-gray-200">{selectedModel.name}</span>
            </div>
            <motion.div
              animate={{ rotate: isOpen ? 180 : 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
            >
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
            </motion.div>
          </Button>
        </motion.div>
      </PopoverTrigger>
      
      <PopoverContent className="w-72 p-0" align="start">
        <motion.div
          initial={{ opacity: 0, y: -10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.95 }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
          className="p-2"
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-sm font-medium text-muted-foreground mb-2 px-2"
          >
            Select Model
          </motion.div>
          
          <div className="space-y-1">
            {models.map((model, index) => (
              <motion.button
                key={model.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + (index * 0.05) }}
                onClick={() => {
                  setSelectedModel(model);
                  setIsOpen(false);
                  setIsClicked(true);
                  setTimeout(() => setIsClicked(false), 300);
                }}
                className="w-full text-left p-3 rounded-lg hover:bg-accent/50 transition-all duration-200 border border-transparent hover:border-border/50 hover:shadow-sm group"
                whileHover={{ 
                  scale: 1.01,
                  x: 2,
                  transition: { type: "spring", stiffness: 400, damping: 25 }
                }}
                whileTap={{ 
                  scale: 0.98,
                  transition: { type: "spring", stiffness: 500, damping: 30 }
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <motion.div 
                      className="mt-0.5"
                      whileHover={{ 
                        rotate: 360, 
                        scale: 1.1,
                        transition: { duration: 0.3 }
                      }}
                    >
                      {model.icon === 'zap' ? (
                        <Zap className="h-4 w-4 text-yellow-500" />
                      ) : (
                        <Brain className="h-4 w-4 text-purple-500" />
                      )}
                    </motion.div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm group-hover:text-foreground transition-colors">
                          {model.name}
                        </span>
                        {selectedModel.id === model.id && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: "spring", stiffness: 500, damping: 25 }}
                          >
                            <Check className="h-3.5 w-3.5 text-primary" />
                          </motion.div>
                        )}
                      </div>
                      
                      <p className="text-xs text-muted-foreground mb-2 group-hover:text-muted-foreground/80 transition-colors">
                        {model.description}
                      </p>
                      
                      <div className="flex items-center gap-4">
                        <SpeedIndicator speed={model.speed} />
                        <CapabilityIndicator capability={model.capability} />
                      </div>
                    </div>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
          
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-3 pt-2 border-t border-border"
          >
            <p className="text-xs text-muted-foreground px-2">
              Choose based on your needs: Y-Fast for quick responses, Y-Smart for complex tasks.
            </p>
          </motion.div>
        </motion.div>
      </PopoverContent>
    </Popover>
  );
}