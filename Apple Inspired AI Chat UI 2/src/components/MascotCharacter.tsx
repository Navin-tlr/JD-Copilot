import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import avatarImage from 'figma:asset/49e1c59c05101ee88132a24fdd051bbf030d2c22.png';

interface MascotCharacterProps {
  state: 'welcome' | 'idle' | 'listening' | 'thinking';
  isVisible: boolean;
  onWelcomeComplete?: () => void;
  onToggleTheme: () => void;
  isDarkMode: boolean;
}

export function MascotCharacter({ 
  state, 
  isVisible, 
  onWelcomeComplete,
  onToggleTheme,
  isDarkMode
}: MascotCharacterProps) {
  const [hasCompletedWelcome, setHasCompletedWelcome] = useState(false);
  const [showWaveGesture, setShowWaveGesture] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isClicked, setIsClicked] = useState(false);

  // Handle welcome animation completion
  useEffect(() => {
    if (state === 'welcome' && !hasCompletedWelcome) {
      const timer = setTimeout(() => {
        setShowWaveGesture(true);
        const completeTimer = setTimeout(() => {
          setHasCompletedWelcome(true);
          onWelcomeComplete?.();
        }, 500); // Additional delay for wave gesture
        
        return () => clearTimeout(completeTimer);
      }, 700); // Welcome animation duration + delay

      return () => clearTimeout(timer);
    }
  }, [state, hasCompletedWelcome, onWelcomeComplete]);

  // Reset welcome state when component becomes invisible
  useEffect(() => {
    if (!isVisible) {
      setHasCompletedWelcome(false);
      setShowWaveGesture(false);
    }
  }, [isVisible]);

  const handleMascotClick = () => {
    setIsClicked(true);
    onToggleTheme();
    
    // Reset click animation after duration
    setTimeout(() => setIsClicked(false), 200);
  };

  const getContainerAnimation = () => {
    const baseAnimation = {
      scale: isHovered ? 1.05 : isClicked ? 0.95 : 1,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 25
      }
    };

    switch (state) {
      case 'welcome':
        return {
          initial: { 
            opacity: 0, 
            scale: 0.8,
            y: 20
          },
          animate: { 
            opacity: 1, 
            scale: isHovered ? 1.05 : 1,
            y: 0
          },
          transition: {
            duration: 0.5,
            delay: 0.2,
            ease: [0.34, 1.56, 0.64, 1] // Spring overshoot curve
          }
        };
      case 'listening':
        return {
          animate: {
            y: [0, -2, 0],
            scale: isHovered ? 1.08 : isClicked ? 0.95 : [1, 1.02, 1]
          },
          transition: {
            duration: 2.5,
            repeat: isHovered || isClicked ? 0 : Infinity,
            ease: "easeInOut",
            type: isHovered || isClicked ? "spring" : "tween",
            stiffness: 400,
            damping: 25
          }
        };
      case 'thinking':
        return {
          animate: {
            y: [0, -3, 0],
            scale: isHovered ? 1.08 : isClicked ? 0.95 : [1, 1.02, 1]
          },
          transition: {
            duration: 2,
            repeat: isHovered || isClicked ? 0 : Infinity,
            ease: "easeInOut",
            type: isHovered || isClicked ? "spring" : "tween",
            stiffness: 400,
            damping: 25
          }
        };
      default: // idle state
        return {
          animate: {
            y: [0, -1, 0],
            scale: isHovered ? 1.05 : isClicked ? 0.95 : 1
          },
          transition: {
            duration: isHovered || isClicked ? 0.2 : 4,
            repeat: isHovered || isClicked ? 0 : Infinity,
            ease: "easeInOut",
            type: isHovered || isClicked ? "spring" : "tween",
            stiffness: 400,
            damping: 25
          }
        };
    }
  };

  const getStatusIndicator = () => {
    switch (state) {
      case 'listening':
        return {
          color: 'bg-emerald-500',
          label: 'Listening',
          pulse: true
        };
      case 'thinking':
        return {
          color: 'bg-blue-500',
          label: 'Thinking',
          pulse: true
        };
      case 'welcome':
        return {
          color: 'bg-violet-500',
          label: 'Ready',
          pulse: false
        };
      default:
        return {
          color: 'bg-gray-400',
          label: 'Ready',
          pulse: false
        };
    }
  };

  if (!isVisible) return null;

  const statusIndicator = getStatusIndicator();

  return (
    <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-20">
      <motion.div
        className="relative pointer-events-auto cursor-pointer group"
        {...getContainerAnimation()}
        onClick={handleMascotClick}
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
      >
        {/* Notion-style card container */}
        <motion.div
          className={`
            relative p-1 rounded-2xl border transition-all duration-300 
            ${isHovered 
              ? 'border-border/80 shadow-lg bg-card/95 backdrop-blur-sm' 
              : 'border-border/40 shadow-sm bg-card/80'
            }
          `}
          style={{
            background: isHovered 
              ? 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(250,250,250,0.95) 100%)'
              : 'rgba(255,255,255,0.8)'
          }}
        >
          {/* Main mascot container */}
          <motion.div
            className="relative w-24 h-24 rounded-xl overflow-hidden"
            animate={{
              scale: isClicked ? 0.98 : 1
            }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
          >
            {/* Avatar image */}
            <motion.img
              src={avatarImage}
              alt="YAKKSSHA Assistant"
              className="w-full h-full object-cover object-center"
              style={{
                objectPosition: 'center 20%',
                transform: 'scale(1.2)',
                transformOrigin: 'center'
              }}
            />
            
            {/* Subtle overlay for state indication */}
            <motion.div
              className="absolute inset-0"
              animate={{
                background: state === 'thinking' 
                  ? 'linear-gradient(45deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1))'
                  : state === 'listening'
                  ? 'linear-gradient(45deg, rgba(16, 185, 129, 0.1), rgba(34, 197, 94, 0.1))'
                  : 'transparent'
              }}
              transition={{ duration: 0.3 }}
            />

            {/* Click ripple effect */}
            <AnimatePresence>
              {isClicked && (
                <motion.div
                  className="absolute inset-0 bg-white/30 rounded-xl"
                  initial={{ scale: 0, opacity: 0.6 }}
                  animate={{ scale: 1, opacity: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                />
              )}
            </AnimatePresence>
          </motion.div>

          {/* Status indicator and label */}
          <motion.div 
            className="absolute -bottom-1 -right-1 flex items-center gap-1.5 bg-background/90 backdrop-blur-sm border border-border/60 rounded-full px-2 py-1 shadow-sm"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, type: "spring", stiffness: 300, damping: 25 }}
          >
            <motion.div
              className={`w-1.5 h-1.5 rounded-full ${statusIndicator.color}`}
              animate={{
                scale: statusIndicator.pulse ? [1, 1.3, 1] : 1,
                opacity: statusIndicator.pulse ? [0.8, 1, 0.8] : 1
              }}
              transition={{
                duration: 1.5,
                repeat: statusIndicator.pulse ? Infinity : 0,
                ease: "easeInOut"
              }}
            />
            <span className="text-xs text-muted-foreground font-medium">
              {statusIndicator.label}
            </span>
          </motion.div>

          {/* Theme toggle hint */}
          <AnimatePresence>
            {isHovered && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.9 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
                className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-background/95 backdrop-blur-sm border border-border/60 rounded-lg px-3 py-1.5 shadow-lg"
              >
                <div className="text-xs text-muted-foreground whitespace-nowrap flex items-center gap-1.5">
                  <span>Click to toggle</span>
                  <div className={`w-2 h-2 rounded-full ${isDarkMode ? 'bg-gray-700' : 'bg-gray-300'}`} />
                  <span>theme</span>
                </div>
                {/* Arrow pointing down */}
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-2 border-r-2 border-t-2 border-transparent border-t-border/60" />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Welcome message */}
        <AnimatePresence>
          {state === 'welcome' && showWaveGesture && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: -10 }}
              transition={{ 
                delay: 0.3, 
                duration: 0.4,
                type: "spring",
                stiffness: 300,
                damping: 25
              }}
              className="absolute -top-20 left-1/2 transform -translate-x-1/2 bg-background/95 backdrop-blur-sm border border-border/60 rounded-xl px-4 py-2 shadow-lg"
            >
              <div className="text-sm text-foreground whitespace-nowrap flex items-center gap-2">
                <span className="text-lg">👋</span>
                <span>Ready to help you today!</span>
              </div>
              {/* Arrow pointing down */}
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-3 border-r-3 border-t-3 border-transparent border-t-border/60" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}