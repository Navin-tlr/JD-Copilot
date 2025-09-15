import React, { useState, useEffect, useRef } from 'react';
import { Info } from 'lucide-react';

interface CitationIconProps {
  companies: string[];
}

const CitationIcon: React.FC<CitationIconProps> = ({ companies }) => {
  const [isOpen, setIsOpen] = useState(false);
  const popupRef = useRef<HTMLDivElement>(null);

  // Close popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  if (!companies || companies.length === 0) {
    return null;
  }

  return (
    <div className="citation-container" style={{ display: 'inline-block', position: 'relative' }}>
      <Info
        className="citation-icon"
        size={16}
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
      />
      {isOpen && (
        <div ref={popupRef} className="citation-popup">
          <h4 className="citation-title">Cited by:</h4>
          <ul className="citation-list">
            {companies.map((company, index) => (
              <li key={index} className="citation-item">{company}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CitationIcon;
