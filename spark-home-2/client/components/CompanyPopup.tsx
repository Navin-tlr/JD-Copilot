import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { Building } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { buildApiUrl } from '@/lib/api';

export interface CompanySelection {
  id: string;
  name: string;
  token: string;
}

interface CompanyPopupProps {
  isOpen: boolean;
  variant?: 'default' | 'rag' | 'benchmark';
  currentSelection: string | null;
  filterText: string;
  onSelect: (selection: CompanySelection) => void;
  onClose: () => void;
}

const CompanyPopup: React.FC<CompanyPopupProps> = ({
  isOpen,
  variant = 'default',
  currentSelection,
  filterText,
  onSelect,
  onClose,
}) => {
  const popupRef = useRef<HTMLDivElement>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [focusedIndex, setFocusedIndex] = useState<number>(0);
  const [companies, setCompanies] = useState<CompanySelection[]>([]);

  // Mock companies for immediate functionality, mirroring SpecializationPopup's hardcoded approach
  const MOCK_COMPANIES: CompanySelection[] = [
    { id: 'google', name: 'Google', token: '@Google' },
    { id: 'microsoft', name: 'Microsoft', token: '@Microsoft' },
    { id: 'amazon', name: 'Amazon', token: '@Amazon' },
    { id: 'apple', name: 'Apple', token: '@Apple' },
    { id: 'meta', name: 'Meta', token: '@Meta' },
    { id: 'tesla', name: 'Tesla', token: '@Tesla' },
    { id: 'nvidia', name: 'NVIDIA', token: '@NVIDIA' },
    { id: 'ibm', name: 'IBM', token: '@IBM' },
    { id: 'oracle', name: 'Oracle', token: '@Oracle' },
    { id: 'salesforce', name: 'Salesforce', token: '@Salesforce' },
  ];

  useEffect(() => {
    if (isOpen) {
      console.log('DEBUG: CompanyPopup opened - isOpen:', isOpen);
    } else {
      console.log('DEBUG: CompanyPopup closed - isOpen:', isOpen);
    }
  }, [isOpen]);

  useEffect(() => {
    const fetchCompanies = async () => {
      console.log('DEBUG: CompanyPopup: Fetching companies from /companies?limit=100');
      try {
        const response = await fetch(buildApiUrl('/companies?limit=100'));
        console.log('DEBUG: CompanyPopup: Fetch response status:', response.status, 'ok:', response.ok);
        if (response.ok) {
          const data = await response.json();
          console.log('DEBUG: CompanyPopup: Fetched companies data:', data);
          const companyList = data.companies || [];
          const mappedCompanies = companyList.map(c => ({
            id: c.id || c.company_name,
            name: c.company_name,
            token: `@${c.company_name}`
          }));
          setCompanies(mappedCompanies);
          console.log('DEBUG: CompanyPopup: Set companies state to length:', mappedCompanies.length);
        } else {
          console.error('DEBUG: CompanyPopup: Fetch failed with status:', response.status, 'response:', await response.text());
          // Fallback to mock data if fetch fails
          setCompanies(MOCK_COMPANIES);
          console.log('DEBUG: CompanyPopup: Fallback to mock companies, length:', MOCK_COMPANIES.length);
        }
      } catch (error) {
        console.error('DEBUG: CompanyPopup: Fetch error:', error);
        // Fallback to mock data on error
        setCompanies(MOCK_COMPANIES);
        console.log('DEBUG: CompanyPopup: Fallback to mock companies on error, length:', MOCK_COMPANIES.length);
      }
    };

    if (isOpen) {
      fetchCompanies();
    }
  }, [isOpen]);

  const filteredCompanies = companies.filter(company =>
    company.name.toLowerCase().includes(filterText.toLowerCase().trim()) // Changed to includes for better matching, like fuzzy search
  ).slice(0, 10); // Limit to top 10 for performance

  useEffect(() => {
    console.log('DEBUG: CompanyPopup: Filter text changed to:', filterText, 'Total companies:', companies.length, 'Filtered companies:', filteredCompanies.length);
    console.log('DEBUG: CompanyPopup: First few filtered companies:', filteredCompanies.slice(0, 3));
    setFocusedIndex(0);
  }, [filterText, filteredCompanies.length, companies.length]);

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
        setFocusedIndex((prev) => (prev + 1) % filteredCompanies.length);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setFocusedIndex((prev) => (prev - 1 + filteredCompanies.length) % filteredCompanies.length);
      } else if (event.key === 'Enter' || event.key === 'Tab') {
        event.preventDefault();
        const selectIndex = event.key === 'Tab' ? 0 : focusedIndex;
        if (filteredCompanies[selectIndex]) {
          onSelect(filteredCompanies[selectIndex]);
        }
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
  }, [isOpen, onClose, focusedIndex, onSelect, filteredCompanies]);

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

  // Always render if open, even if empty (show loading or no results), but for initial empty filter, use mocks if needed
  console.log('DEBUG: CompanyPopup: Rendering popup with', filteredCompanies.length, 'filtered companies for filter:', filterText);

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
          className="absolute bottom-[calc(100%+6px)] left-4 w-[300px] rounded-2xl overflow-hidden backdrop-blur-2xl max-h-[300px] overflow-y-auto z-50"
          style={{
            background: colors.bg,
            border: `1px solid ${colors.border}`,
            boxShadow: '0 8px 40px rgba(0, 0, 0, 0.12), 0 0 1px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div className="p-2">
            {filteredCompanies.length === 0 ? (
              <div className="p-4 text-center">
                <p style={{ color: colors.textSecondary, fontSize: '14px' }}>No companies found</p>
                <p style={{ color: colors.textSecondary, fontSize: '12px', opacity: 0.7 }}>Try a different search</p>
              </div>
            ) : (
              filteredCompanies.map((company, index) => {
                const isActive = currentSelection === company.id;
                const isFocused = focusedIndex === index;
                const isHovered = hoveredIndex === index;
                const isInteractive = isHovered || isFocused;
                const Icon = Building;
                
                return (
                  <motion.button
                    key={company.id}
                    onClick={() => {
                      console.log('DEBUG: CompanyPopup: Select event for company:', company.name, 'ID:', company.id);
                      onSelect(company);
                    }}
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

                    <div className="flex-1 text-left min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="text-[13px] font-normal"
                          style={{
                            color: colors.text,
                            fontWeight: isActive ? '500' : '400',
                          }}
                        >
                          {company.name}
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
                              color: '#10B981',
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
                    </div>

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
                      {company.token}
                    </motion.code>
                  </motion.button>
                );
              })
            )}
          </div>

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
};

export default CompanyPopup;