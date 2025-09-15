import React from 'react';
import SkillsList from './SkillsList';

const SkillsAnalysisDemo: React.FC = () => {
  // Sample skills data with citations
  const sampleSkills = [
    {
      skill: 'Communication Execution',
      companies: ['Masters\' Union', 'Alstom', 'Tap Academy'],
      specializations: ['Marketing', 'HR', 'Operations'],
      why_matters: 'Your words are tactical strikes. Hesitation or ambiguity = immediate disqualification.',
      recommendations: 'Master executive brevity. Record and analyze every pitch.'
    },
    {
      skill: 'Data Analytics',
      companies: ['Accorian', 'Masters\' Union'],
      specializations: ['Business Analytics', 'Finance'],
      why_matters: 'Analytics isn\'t insight—its your battlefield evidence.',
      recommendations: 'Build 3 case studies with hard metrics before placements.'
    },
    {
      skill: 'Time Warfare',
      companies: ['Masters\' Union', 'Alstom', 'Accorian'],
      specializations: ['Operations', 'All specializations'],
      why_matters: 'The 6-day workweek is your new normal. Adapt or perish.',
      recommendations: 'Implement time-blocking with 15-minute increments.'
    },
    {
      skill: 'CRM Certifications',
      companies: ['Masters\' Union', 'Tap Academy'],
      specializations: ['Marketing', 'Business Analytics'],
      why_matters: 'No Salesforce/HubSpot mastery? Marketing roles reject automatically.',
      recommendations: 'Two certifications in 90 days. Build live sales dashboard.'
    }
  ];

  return (
    <div className="skills-analysis-demo p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            🎯 JD-Copilot Skills Analysis
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Click the ℹ️ icon next to each skill to see company citations
          </p>
        </div>

        <SkillsList
          skills={sampleSkills}
          title="Most Sought-After Skills"
        />
      </div>
    </div>
  );
};

export default SkillsAnalysisDemo;