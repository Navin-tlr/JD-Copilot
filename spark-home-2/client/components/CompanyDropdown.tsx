import { useEffect, useRef, useState } from 'react';
import { buildApiUrl } from '@/lib/api';

interface CompanyDropdownProps {
  onSelect: (company: string) => void;
  onClose: () => void;
  position: { top: number; left: number };
  variant?: 'default' | 'rag' | 'benchmark';
}

interface Company {
  company_name: string;
  role_count?: number;
}

export default function CompanyDropdown({
  onSelect,
  onClose,
  position,
  variant = 'default',
}: CompanyDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const response = await fetch(buildApiUrl('/companies'));
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setCompanies(data.companies || []);
      } catch (err) {
        console.error('Error fetching companies:', err);
        setError('Failed to load companies');
      } finally {
        setLoading(false);
      }
    };

    fetchCompanies();
  }, []);

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

  if (loading) {
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
          padding: '16px',
        }}
      >
        <div className="text-xs font-semibold mb-2 px-2" style={{ color: colors.text, opacity: 0.7 }}>
          Loading companies...
        </div>
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" style={{ color: colors.highlightBg }}></div>
        </div>
      </div>
    );
  }

  if (error) {
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
          padding: '16px',
        }}
      >
        <div className="text-xs font-semibold mb-2 px-2" style={{ color: colors.text, opacity: 0.7 }}>
          Error loading companies
        </div>
        <div className="text-xs px-2" style={{ color: colors.text, opacity: 0.6 }}>
          {error}
        </div>
      </div>
    );
  }

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
          Select Company ({companies.length} available)
        </div>
        {companies.map((company) => (
          <button
            key={company.company_name}
            onClick={() => onSelect(company.company_name)}
            className="w-full text-left px-3 py-2 rounded-md transition-all duration-150 flex items-center justify-between"
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
            <span className="text-sm font-medium">{company.company_name}</span>
            {company.role_count && (
              <span className="text-xs opacity-60">{company.role_count} roles</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}