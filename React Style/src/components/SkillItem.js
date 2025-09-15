import React from 'react';

const SkillItem = ({
  skill,
  companies,
  specializations,
  whyMatters,
  recommendations
}) => {
  return (
    <div className="skill-item bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 m-0">
          {skill}
        </h3>
      </div>

      {specializations && specializations.length > 0 && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          <span className="font-semibold">Relevant Specializations:</span> {specializations.join(', ')}
        </p>
      )}

      {whyMatters && (
        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          <span className="font-semibold">Why It Matters:</span> {whyMatters}
        </p>
      )}

      {recommendations && (
        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          <span className="font-semibold">Recommendations:</span> {recommendations}
        </p>
      )}
    </div>
  );
};

export default SkillItem;
