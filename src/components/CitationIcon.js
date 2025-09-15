import React, { useState } from 'react';
import { FaInfoCircle } from 'react-icons/fa';
import './CitationIcon.css';

const CitationIcon = ({ companies }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="citation-container" style={{ display: 'inline-block', position: 'relative' }}>
      <FaInfoCircle 
        className="citation-icon" 
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
      />
      {isOpen && (
        <div className="citation-popup">
          <h4>Cited by:</h4>
          <ul>
            {companies.map((company, index) => (
              <li key={index}>{company}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CitationIcon;
