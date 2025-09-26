import React from 'react';
import { motion } from 'framer-motion';

interface NotionStyleResponseProps {
  content: string;
}

export function NotionStyleResponse({ content }: NotionStyleResponseProps) {
  // Parse the content to identify different sections
  const parseContent = (text: string) => {
    const lines = text.split('\n');
    const sections: Array<{ type: 'header' | 'subheader' | 'content' | 'separator' | 'bullet' | 'highlight' | 'table'; text: string }> = [];
    
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      
      if (trimmedLine.startsWith('CHRIST UNIVERSITY PLACEMENT CELL')) {
        sections.push({ type: 'header', text: trimmedLine });
      } else if (trimmedLine.startsWith('---')) {
        sections.push({ type: 'separator', text: trimmedLine });
      } else if (trimmedLine.match(/^\d+\.\s+/)) {
        sections.push({ type: 'subheader', text: trimmedLine });
      } else if (trimmedLine.startsWith('•') || trimmedLine.startsWith('✓') || trimmedLine.startsWith('-')) {
        sections.push({ type: 'bullet', text: trimmedLine });
      } else if (trimmedLine.includes('QUERY ANALYSIS') || trimmedLine.includes('STRATEGIC INSIGHTS') || trimmedLine.includes('RECOMMENDATIONS')) {
        sections.push({ type: 'highlight', text: trimmedLine });
      } else if (trimmedLine.includes('|') && trimmedLine.split('|').length > 2) {
        sections.push({ type: 'table', text: trimmedLine });
      } else if (trimmedLine.length > 0) {
        sections.push({ type: 'content', text: trimmedLine });
      }
    });
    
    return sections;
  };

  const sections = parseContent(content);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="w-full space-y-4 font-sans"
    >
      {sections.map((section, index) => {
        switch (section.type) {
          case 'header':
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                className="relative"
              >
                {/* Main heading in RED as requested */}
                <h1 className="text-2xl md:text-3xl font-bold text-red-800 dark:text-red-600 leading-tight mb-4">
                  {section.text}
                </h1>
              </motion.div>
            );
            
          case 'subheader':
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                className="mt-6"
              >
                {/* Subtle neutral warm colors for section heading backgrounds */}
                <div className="bg-gray-100 dark:bg-gray-800 border-l-4 border-gray-300 dark:border-gray-600 pl-4 py-3 rounded-r-lg">
                  <h2 className="text-lg md:text-xl font-semibold text-gray-800 dark:text-gray-200 leading-tight">
                    {section.text}
                  </h2>
                </div>
              </motion.div>
            );
            
          case 'highlight':
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                className="mt-4"
              >
                {/* Subtle neutral warm background for highlight sections */}
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 pl-4 py-3 rounded-lg">
                  <h3 className="text-base md:text-lg font-medium text-gray-700 dark:text-gray-300">
                    {section.text}
                  </h3>
                </div>
              </motion.div>
            );
            
          case 'table':
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                className="mt-4 overflow-x-auto"
              >
                {/* Clean table styling with subtle borders */}
                <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <code className="text-sm text-gray-700 dark:text-gray-300 font-mono">
                      {section.text}
                    </code>
                  </div>
                </div>
              </motion.div>
            );
            
          case 'content':
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                className="mt-3"
              >
                <p className="text-sm md:text-base text-gray-600 dark:text-gray-400 leading-relaxed">
                  {section.text}
                </p>
              </motion.div>
            );
            
          case 'bullet':
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
                className="mt-3 flex items-start gap-3"
              >
                {/* Subtle bullet points */}
                <div className="w-1.5 h-1.5 rounded-full bg-gray-400 mt-2 flex-shrink-0" />
                <p className="text-sm md:text-base text-gray-600 dark:text-gray-400 leading-relaxed">
                  {section.text}
                </p>
              </motion.div>
            );
            
          case 'separator':
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, scaleX: 0 }}
                animate={{ opacity: 1, scaleX: 1 }}
                transition={{ delay: index * 0.05, duration: 0.4 }}
                className="my-6"
              >
                <div className="w-full h-px bg-gray-200 dark:bg-gray-700" />
              </motion.div>
            );
            
          default:
            return null;
        }
      })}
    </motion.div>
  );
}
