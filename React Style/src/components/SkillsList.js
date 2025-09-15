import React from 'react';
import SkillItem from './SkillItem';

interface Skill {
  skill?: string;
  name?: string;
  companies?: string[];
  cited_by?: string[];
  specializations?: string[];
  why_matters?: string;
  whyMatters?: string;
  recommendations?: string;
}

interface SkillsListProps {
  skills: Skill[];
  title?: string;
}

const SkillsList: React.FC<SkillsListProps> = ({ skills, title = "Skills Analysis" }) => {
  if (!skills || skills.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        No skills data available
      </div>
    );
  }

  return (
    <div className="skills-list max-w-4xl mx-auto p-4">
      <h2 className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-6 text-center">
        🎯 {title}
      </h2>

      <div className="space-y-4">
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
      </div>

      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-blue-800 dark:text-blue-200 m-0">
          <span className="font-semibold">💡 Tip:</span> Click the ℹ️ icon next to each skill to see which companies cited it as a requirement.
        </p>
      </div>
    </div>
  );
};

export default SkillsList;
