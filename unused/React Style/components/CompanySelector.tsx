import { useState, useEffect, KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Company {
  company_name: string;
  company_type?: string;
  industry?: string;
  location?: string;
  role_count?: number;
}

interface CompanySelectorProps {
  isVisible: boolean;
  searchQuery: string;
  onSelectCompany: (companyName: string) => void;
  onClose: () => void;
  onKeyDown?: (e: KeyboardEvent<Element>) => void;
}

export function CompanySelector({ isVisible, searchQuery, onSelectCompany, onClose, onKeyDown }: CompanySelectorProps) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [filteredCompanies, setFilteredCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Fetch companies from backend
  useEffect(() => {
    if (isVisible) {
      fetchCompanies();
    }
  }, [isVisible]);

  // Filter companies based on search query
  useEffect(() => {
    if (searchQuery.trim()) {
      const filtered = companies.filter(company =>
        company.company_name.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredCompanies(filtered);
      setSelectedIndex(0);
    } else {
      setFilteredCompanies(companies.slice(0, 10)); // Show first 10 companies
      setSelectedIndex(0);
    }
  }, [searchQuery, companies]);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/companies');
      if (response.ok) {
        const data = await response.json();
        setCompanies(data.companies || []);
      } else {
        console.error('Failed to fetch companies');
        setCompanies([]);
      }
    } catch (error) {
      console.error('Error fetching companies:', error);
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<Element>) => {
    if (onKeyDown) {
      onKeyDown(e);
    } else {
      // Default behavior
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, filteredCompanies.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCompanies[selectedIndex]) {
            onSelectCompany(filteredCompanies[selectedIndex].company_name);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    }
  };

  // Remove keyboard event listener - let parent handle it
  // useEffect(() => {
  //   if (isVisible) {
  //     document.addEventListener('keydown', handleKeyDown);
  //     return () => document.removeEventListener('keydown', handleKeyDown);
  //   }
  // }, [isVisible, selectedIndex, filteredCompanies]);

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -8, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -8, scale: 0.96 }}
        transition={{
          type: "tween",
          ease: [0.25, 0.1, 0.25, 1],
          duration: 0.15
        }}
        className="absolute bottom-full left-0 right-0 mb-2 z-50"
      >
        <div className="bg-card/95 backdrop-blur-md border border-border/50 rounded-lg shadow-lg overflow-hidden max-h-48">
          {/* Minimal Header */}
          <div className="px-3 py-2 border-b border-border/30 bg-muted/20">
            <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
              <span className="text-emerald-500">$</span>
              <span>company</span>
              {searchQuery && <span className="text-blue-400">"{searchQuery}"</span>}
              {loading && (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-3 h-3 border border-emerald-500 border-t-transparent rounded-full"
                />
              )}
            </div>
          </div>

          {/* Compact Results */}
          <div className="max-h-32 overflow-y-auto scrollbar-thin scrollbar-thumb-border/30">
            {loading ? (
              <div className="p-3 text-center text-xs text-muted-foreground">
                Loading...
              </div>
            ) : filteredCompanies.length === 0 ? (
              <div className="p-3 text-center text-xs text-muted-foreground">
                No companies found
              </div>
            ) : (
              filteredCompanies.slice(0, 6).map((company, index) => (
                <motion.div
                  key={company.company_name}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.01 }}
                  className={`
                    px-3 py-2 cursor-pointer text-sm transition-colors duration-100
                    ${index === selectedIndex 
                      ? 'bg-accent text-accent-foreground' 
                      : 'hover:bg-muted/50'
                    }
                  `}
                  onClick={() => onSelectCompany(company.company_name)}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                      {index === selectedIndex && (
                        <span className="text-blue-500 text-xs">▶</span>
                      )}
                      <span className="font-medium truncate">
                        {company.company_name}
                      </span>
                    </div>
                    {company.role_count && company.role_count > 0 && (
                      <span className="text-xs text-muted-foreground ml-2 shrink-0">
                        {company.role_count}
                      </span>
                    )}
                  </div>
                  {(company.industry || company.location) && (
                    <div className="text-xs text-muted-foreground mt-1 truncate">
                      {company.industry}
                      {company.industry && company.location && ' • '}
                      {company.location}
                    </div>
                  )}
                </motion.div>
              ))
            )}
          </div>

          {/* Minimal Footer */}
          {filteredCompanies.length > 0 && (
            <div className="px-3 py-1.5 border-t border-border/30 bg-muted/10">
              <div className="flex justify-between items-center text-xs text-muted-foreground">
                <span>↑↓ navigate • ↵ select</span>
                <span>{Math.min(filteredCompanies.length, 6)}{filteredCompanies.length > 6 ? '+' : ''}</span>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
