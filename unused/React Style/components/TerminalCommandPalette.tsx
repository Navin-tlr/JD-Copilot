import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Command {
  id: string;
  command: string;
  description: string;
  category: 'action' | 'tool' | 'navigation' | 'help';
}

const commands: Command[] = [
  { id: 'new', command: '//new', description: 'Start a new chat session', category: 'action' },
  { id: 'help', command: '//help', description: 'Show available commands', category: 'help' },
  { id: 'clear', command: '//clear', description: 'Clear current conversation', category: 'action' },
  { id: 'save', command: '//save', description: 'Save current conversation', category: 'action' },
  { id: 'load', command: '//load', description: 'Load previous conversation', category: 'action' },
  { id: 'agents', command: '//agents', description: 'List available AI agents', category: 'tool' },
  { id: 'tools', command: '//tools', description: 'Open Sage tools menu', category: 'tool' },
  { id: 'tasks', command: '//tasks', description: 'Open project management', category: 'tool' },
  { id: 'analytics', command: '//analytics', description: 'View analytics dashboard', category: 'tool' },
  { id: 'radar', command: '//radar', description: 'Monitor trends and data', category: 'tool' },
  { id: 'resume', command: '//resume', description: 'Resume strategist tool', category: 'tool' },
  { id: 'research', command: '//research', description: 'Research assistant', category: 'tool' },
  { id: 'grill', command: '//grill', description: 'Interview preparation', category: 'tool' },
  { id: 'settings', command: '//settings', description: 'Open settings menu', category: 'navigation' },
  { id: 'theme', command: '//theme', description: 'Toggle dark/light theme', category: 'navigation' },
  { id: 'export', command: '//export', description: 'Export conversation', category: 'action' },
];

interface TerminalCommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onCommandSelect: (command: Command) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function TerminalCommandPalette({
  isOpen,
  onClose,
  onCommandSelect,
  searchQuery,
  onSearchChange
}: TerminalCommandPaletteProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [filteredCommands, setFilteredCommands] = useState<Command[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter commands based on search query
  useEffect(() => {
    const query = searchQuery.replace('/', '').toLowerCase();
    const filtered = commands.filter(cmd =>
      cmd.command.toLowerCase().includes(query) ||
      cmd.description.toLowerCase().includes(query)
    );
    setFilteredCommands(filtered);
    setSelectedIndex(0);
  }, [searchQuery]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        transition={{
          type: "tween",
          ease: [0.25, 0.1, 0.25, 1],
          duration: 0.2
        }}
        className="absolute bottom-full left-0 right-0 mb-2 z-50"
      >
        <div className="bg-card/95 backdrop-blur-md border border-border/50 rounded-lg shadow-lg overflow-hidden max-h-48">
          {/* Minimal Header */}
          <div className="px-3 py-2 border-b border-border/30 bg-muted/20">
            <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
              <span className="text-blue-500">//</span>
              <span>commands</span>
              {searchQuery && searchQuery.startsWith('//') && (
                <span className="text-emerald-400">"{searchQuery.slice(2)}"</span>
              )}
            </div>
          </div>

          {/* Commands List */}
          <div className="max-h-96 overflow-y-auto">
            {filteredCommands.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground font-mono text-sm">
                No commands found
              </div>
            ) : (
              filteredCommands.slice(0, 6).map((command, index) => (
                <motion.div
                  key={command.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    delay: index * 0.02,
                    duration: 0.15
                  }}
                  className={`px-3 py-2 cursor-pointer text-sm transition-colors duration-100 ${
                    index === selectedIndex
                      ? 'bg-accent text-accent-foreground'
                      : 'hover:bg-muted/50'
                  }`}
                  onClick={() => onCommandSelect(command)}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div className="flex items-center gap-2">
                    {index === selectedIndex && (
                      <span className="text-blue-500 text-xs">▶</span>
                    )}
                    <span className="font-mono text-xs text-muted-foreground">
                      {command.command}
                    </span>
                    <span className="text-xs truncate">
                      {command.description}
                    </span>
                  </div>
                </motion.div>
              ))
            )}
          </div>

          {/* Minimal Footer */}
          <div className="px-3 py-1.5 border-t border-border/30 bg-muted/10">
            <div className="flex justify-between items-center text-xs text-muted-foreground">
              <span>↑↓ navigate • ↵ execute</span>
              <span>{Math.min(filteredCommands.length, 6)}{filteredCommands.length > 6 ? '+' : ''}</span>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
