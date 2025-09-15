import React from 'react';

const CitationIcon = () => {
  return (
    <div className="citation-icon">
      <button className="info-button" aria-label="More Info">
        ℹ️
      </button>
      <div className="popup hidden">
        <p>Additional information about this skill.</p>
      </div>
    </div>
  );
};

export default CitationIcon;