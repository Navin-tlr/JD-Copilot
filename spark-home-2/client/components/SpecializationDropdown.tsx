import { useEffect, useRef } from 'react';

interface SpecializationDropdownProps {
  onSelectSpecialization: (specialization: string) => void;
  onClose: () => void;
  position: { top: number; left: number };
  variant?: 'default' | 'rag' | 'benchmark';
}

const SPECIALIZATIONS = [
  { value: 'marketing', label: 'Marketing', icon: '📢' },
  { value: 'finance', label: 'Finance', icon: '💰' },
  { value: 'hr', label: 'HR', icon: '👥' },
  { value: 'operations', label: 'Operations', icon: '⚙️' },
  { value: 'analytics', label: 'Analytics', icon: '📊' },
  { value: 'it', label: 'IT', icon: '💻' },
  { value: 'strategy', label: 'Strategy', icon: '🎯' },
];

export default function SpecializationDropdown({
  onSelectSpecialization,
  onClose,
  position,
  variant = 'default',
}: SpecializationDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const getColors = () => {
    switch (variant) {
      case 'rag':
        return {
          bg: '#393939',
          border: 'rgba(200, 200, 200, 0.25)',
          text: '#FFFFFF',
          itemBg: '#4A4A4A',
          itemHoverBg: '#555555',
          highlightBg: '#D38B21',
        };
      case 'benchmark':
        return {
          bg: '#D2D2D2',
          border: 'rgba(200, 200, 200, 0.25)',
          text: '#B729C1',
          itemBg: '#DDD',
          itemHoverBg: '#E8E8E8',
          highlightBg: '#808BC4',
        };
      default:
        return {
          bg: '#393939',
          border: 'rgba(200, 200, 200, 0.25)',
          text: '#FFFFFF',
          itemBg: '#4A4A4A',
          itemHoverBg: '#555555',
          highlightBg: '#F69F1C',
        };
    }
  };

  const colors = getColors();

  return (
    <div
      ref={dropdownRef}
      className="fixed z-50 rounded-lg shadow-xl animate-fade-in"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        background: colors.bg,
        border: `1px solid ${colors.border}`,
        minWidth: '200px',
        maxHeight: '300px',
        overflowY: 'auto',
      }}
    >
      <div className="p-2">
        <div className="text-xs font-semibold mb-2 px-2" style={{ color: colors.text, opacity: 0.7 }}>
          Select Specialization
        </div>
        {SPECIALIZATIONS.map((spec) => (
          <button
            key={spec.value}
            onClick={() => onSelectSpecialization(spec.value)}
            className="w-full text-left px-3 py-2 rounded-md transition-all duration-150 flex items-center gap-2"
            style={{
              color: colors.text,
              background: colors.itemBg,
              marginBottom: '4px',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = colors.itemHoverBg;
              e.currentTarget.style.transform = 'translateX(4px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = colors.itemBg;
              e.currentTarget.style.transform = 'translateX(0)';
            }}
          >
            <span className="text-base">{spec.icon}</span>
            <span className="text-sm font-medium">{spec.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
