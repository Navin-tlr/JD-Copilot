import React from 'react';
import SkillItem from './SkillItem';

const SkillsList = ({ skills, title = "Skills Analysis" }) => {
  if (!skills || skills.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No skills data available
      </div>
    );
  }

  return (
    <div className="skills-list" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2 style={{ color: '#1f77b4', marginBottom: '20px', textAlign: 'center' }}>
        🎯 {title}
      </h2>

      {skills.map((skill, index) => (
        <SkillItem
          key={index}
          skill={skill.skill || skill.name || `Skill ${index + 1}`}
          companies={skill.companies || skill.cited_by || []}
          specializations={skill.specializations || []}
          whyMatters={skill.why_matters || skill.whyMatters}
          recommendations={skill.recommendations}
        />
      ))}

      <div style={{ marginTop: '20px', padding: '12px', backgroundColor: '#f0f8ff', borderRadius: '8px', border: '1px solid #b3d9ff' }}>
        <p style={{ margin: '0', fontSize: '14px', color: '#333' }}>
          <strong>💡 Tip:</strong> Click the ℹ️ icon next to each skill to see which companies cited it as a requirement.
        </p>
      </div>
    </div>
  );
};

export default SkillsList;