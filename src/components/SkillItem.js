import React from 'react';
import CitationIcon from './CitationIcon';

const SkillItem = ({ skill, companies, specializations, whyMatters, recommendations }) => {
  return (
    <div className="skill-item" style={{ marginBottom: '16px', padding: '12px', border: '1px solid #e0e0e0', borderRadius: '8px' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
        <h3 style={{ margin: '0', fontSize: '18px', fontWeight: 'bold' }}>
          {skill}
        </h3>
        <CitationIcon companies={companies} />
      </div>

      {specializations && specializations.length > 0 && (
        <p style={{ margin: '4px 0', color: '#666', fontSize: '14px' }}>
          <strong>Relevant Specializations:</strong> {specializations.join(', ')}
        </p>
      )}

      {whyMatters && (
        <p style={{ margin: '4px 0', color: '#555', fontSize: '14px' }}>
          <strong>Why It Matters:</strong> {whyMatters}
        </p>
      )}

      {recommendations && (
        <p style={{ margin: '4px 0', color: '#555', fontSize: '14px' }}>
          <strong>Recommendations:</strong> {recommendations}
        </p>
      )}
    </div>
  );
};

export default SkillItem;