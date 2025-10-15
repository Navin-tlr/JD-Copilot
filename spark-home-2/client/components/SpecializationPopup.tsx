import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { Target, Users, BarChart3, Settings, DollarSign } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface SpecializationSelection {
  id: string;
  label: string;
  token: string;
  description: string;
  color: string;
  icon: LucideIcon;
}

interface SpecializationPopupProps {
  isOpen: boolean;
  variant?: 'default' | 'rag' | 'benchmark';
  currentSelection: string | null;
  onSelect: (selection: SpecializationSelection) => void;
  onClose: () => void;
}

const SPECIALIZATIONS: SpecializationSelection[] = [
  { 
    id: 'marketing', 
    label: 'Marketing', 
    token: '#marketing',
    description: 'Brand strategy, campaigns, growth',
    color: '#F97316',
    icon: Target
  },
  { 
    id: 'hr', 
    label: 'Human Resources', 
    token: '#hr',
    description: 'Talent, culture, people ops',
    color: '#10B981',
    icon: Users
  },
  { 
    id: 'business-analytics', 
    label: 'Business Analytics', 
    token: '#business-analytics',
    description: 'Data insights, metrics, KPIs',
    color: '#3B82F6',
    icon: BarChart3
  },
  { 
    id: 'operations', 
    label: 'Operations', 
    token: '#operations',
    description: 'Process optimization, logistics',
    color: '#8B5CF6',
    icon: Settings
  },
  { 
    id: 'finance', 
    label: 'Finance', 
    token: '#finance',
    description: 'Financial planning, analysis',
    color: '#EC4899',
    icon: DollarSign
  },
];

export default function SpecializationPopup({
  isOpen,
  variant = 'default',
  currentSelection,
  onSelect,
  onClose,
}: SpecializationPopupProps) {
  const popupRef = useRef<HTMLDivElement>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [focusedIndex, setFocusedIndex] = useState<number>(0);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    const handleArrowKeys = (event: KeyboardEvent) => {
      if (!isOpen) return;
      
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setFocusedIndex((prev) => (prev + 1) % SPECIALIZATIONS.length);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setFocusedIndex((prev) => (prev - 1 + SPECIALIZATIONS.length) % SPECIALIZATIONS.length);
      } else if (event.key === 'Enter') {
        event.preventDefault();
        onSelect(SPECIALIZATIONS[focusedIndex]);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
      document.addEventListener('keydown', handleArrowKeys);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('keydown', handleArrowKeys);
    };
  }, [isOpen, onClose, focusedIndex, onSelect]);

  const getColors = () => {
    switch (variant) {
      case 'rag':
        return {
          bg: 'rgba(30, 30, 30, 0.98)',
          border: 'rgba(255, 255, 255, 0.06)',
          text: '#E8E8E8',
          textSecondary: '#A8A8A8',
          hoverBg: 'rgba(255, 255, 255, 0.05)',
          activeBg: 'rgba(211, 139, 33, 0.1)',
          activeBorder: 'rgba(211, 139, 33, 0.4)',
          activeGlow: 'rgba(211, 139, 33, 0.15)',
        };
      case 'benchmark':
        return {
          bg: 'rgba(252, 252, 252, 0.98)',
          border: 'rgba(0, 0, 0, 0.06)',
          text: '#2D2D2D',
          textSecondary: '#6B6B6B',
          hoverBg: 'rgba(0, 0, 0, 0.025)',
          activeBg: 'rgba(128, 139, 196, 0.08)',
          activeBorder: 'rgba(128, 139, 196, 0.4)',
          activeGlow: 'rgba(128, 139, 196, 0.12)',
        };
      default:
        return {
          bg: 'rgba(30, 30, 30, 0.98)',
          border: 'rgba(255, 255, 255, 0.06)',
          text: '#E8E8E8',
          textSecondary: '#A8A8A8',
          hoverBg: 'rgba(255, 255, 255, 0.05)',
          activeBg: 'rgba(246, 159, 28, 0.1)',
          activeBorder: 'rgba(246, 159, 28, 0.4)',
          activeGlow: 'rgba(246, 159, 28, 0.15)',
        };
    }
  };

  const colors = getColors();

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={popupRef}
          initial={{ opacity: 0, y: 4, filter: 'blur(4px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          exit={{ opacity: 0, y: 2, filter: 'blur(2px)' }}
          transition={{ 
            duration: 0.18,
            ease: [0.16, 1, 0.3, 1]
          }}
          className="absolute bottom-[calc(100%+6px)] left-4 w-[300px] rounded-2xl overflow-hidden backdrop-blur-2xl"
          style={{
            background: colors.bg,
            border: `1px solid ${colors.border}`,
            boxShadow: '0 8px 40px rgba(0, 0, 0, 0.12), 0 0 1px rgba(0, 0, 0, 0.05)',
          }}
        >
          {/* Specializations List - No header, just options */}
          <div className="p-2">
            {SPECIALIZATIONS.map((spec, index) => {
              const isActive = currentSelection === spec.id;
              const isFocused = focusedIndex === index;
              const isHovered = hoveredIndex === index;
              const isInteractive = isHovered || isFocused;
              const Icon = spec.icon;
              
              return (
                <motion.button
                  key={spec.id}
                  onClick={() => onSelect(spec)}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                  onFocus={() => setFocusedIndex(index)}
                  initial={{ opacity: 0, y: 2 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.025, duration: 0.2, ease: 'easeOut' }}
                  className="w-full px-3 py-2.5 rounded-xl flex items-center gap-3 group relative mb-1 last:mb-0"
                  style={{
                    background: isActive 
                      ? colors.activeBg 
                      : isInteractive 
                        ? colors.hoverBg 
                        : 'transparent',
                    border: `1px solid ${isActive ? colors.activeBorder : 'transparent'}`,
                    boxShadow: isActive 
                      ? `0 0 0 1px ${colors.activeGlow}, 0 2px 8px ${colors.activeGlow}` 
                      : 'none',
                    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                  }}
                >
                  {/* Icon with subtle scaling */}
                  <motion.div
                    className="flex items-center justify-center flex-shrink-0"
                    animate={{
                      scale: isInteractive ? 1.05 : 1,
                    }}
                    transition={{ duration: 0.2, ease: 'easeOut' }}
                  >
                    <Icon
                      size={16}
                      strokeWidth={1.5}
                      style={{ 
                        color: variant === 'benchmark' ? '#888888' : '#B8B8B8',
                        opacity: isInteractive || isActive ? 1 : 0.6,
                        transition: 'all 0.2s ease-out',
                      }}
                    />
                  </motion.div>

                  {/* Content */}
                  <div className="flex-1 text-left min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span 
                        className="text-[13px] font-normal"
                        style={{ 
                          color: colors.text,
                          fontWeight: isActive ? '500' : '400',
                        }}
                      >
                        {spec.label}
                      </span>
                      {isActive && (
                        <motion.svg
                          initial={{ scale: 0, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ 
                            type: 'spring', 
                            stiffness: 400, 
                            damping: 20,
                            delay: 0.05
                          }}
                          width="12"
                          height="12"
                          viewBox="0 0 12 12"
                          fill="none"
                          style={{ 
                            color: spec.color,
                            flexShrink: 0,
                          }}
                        >
                          <path
                            d="M10 3L4.5 8.5L2 6"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </motion.svg>
                      )}
                    </div>
                    <motion.p 
                      className="text-[11px] mt-0.5 leading-snug"
                      style={{ color: colors.textSecondary }}
                      animate={{
                        opacity: isInteractive ? 0.9 : 0.65,
                      }}
                      transition={{ duration: 0.2 }}
                    >
                      {spec.description}
                    </motion.p>
                  </div>

                  {/* Token badge - appears on hover */}
                  <motion.code 
                    className="text-[10px] font-mono px-2 py-0.5 rounded-lg"
                    style={{ 
                      background: colors.hoverBg,
                      color: colors.textSecondary,
                    }}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{
                      opacity: isInteractive || isActive ? 1 : 0,
                      scale: isInteractive || isActive ? 1 : 0.95,
                    }}
                    transition={{ duration: 0.2, ease: 'easeOut' }}
                  >
                    {spec.token}
                  </motion.code>
                </motion.button>
              );
            })}
          </div>

          {/* Minimal footer - just keyboard hints */}
          <motion.div
            className="px-3 py-1.5 border-t flex items-center gap-3 justify-center"
            style={{
              borderColor: colors.border,
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15 }}
          >
            <span 
              className="text-[9px] opacity-50"
              style={{ color: colors.textSecondary }}
            >
              ↑↓ navigate · ↵ select · esc close
            </span>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
