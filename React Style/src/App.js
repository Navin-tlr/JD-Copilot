import React, { useState, useEffect } from 'react';
import SkillsList from './components/SkillsList';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    } else {
      setIsDarkMode(false);
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);

    if (newTheme) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

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
    <div className="App">
      <header style={{ backgroundColor: '#1f77b4', color: 'white', padding: '20px', textAlign: 'center' }}>
        <h1>🎯 JD-Copilot - Skills Analysis with Citations</h1>
        <p>Click the ℹ️ icon next to each skill to see citation sources</p>
      </header>

      <main style={{ padding: '20px' }}>
        <SkillsList
          skills={sampleSkills}
          title="Most Sought-After Skills"
        />
      </main>

      <footer style={{ backgroundColor: '#f5f5f5', padding: '20px', textAlign: 'center', marginTop: '40px' }}>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Built with ❤️ by JD-Copilot Team | Citations help verify skill requirements from real company data
        </p>
      </footer>

      <ChatInterface onToggleTheme={toggleTheme} isDarkMode={isDarkMode} />
    </div>
  );
}

export default App;
