import { useState, KeyboardEvent, useRef } from 'react';
import { Button } from './ui/button';
import { Send, Paperclip, Smile, Sparkles } from 'lucide-react';
import { ModelSelector } from './ModelSelector';
import { SageToolsPopup } from './SageToolsPopup';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onExpand?: () => void;
  onCollapse?: () => void;
  onUserStartTyping?: () => void;
  onUserStopTyping?: () => void;
  disabled?: boolean;
}

export function ChatInput({ 
  onSendMessage, 
  onExpand, 
  onCollapse, 
  onUserStartTyping,
  onUserStopTyping,
  disabled = false 
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [showSageTools, setShowSageTools] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Enter') {
      onUserStartTyping?.();
    }
    
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleMessageChange = (value: string) => {
    setMessage(value);
    if (value.trim()) {
      onUserStartTyping?.();
    } else {
      onUserStopTyping?.();
    }

    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  };

  const handleToolSelect = (toolId: string) => {
    console.log('Selected tool:', toolId);
  };

  return (
    <div className="bg-background border-t border-border/50">
      <div className="max-w-4xl mx-auto p-4">
        {/* Main input container */}
        <div className="relative bg-background border border-border rounded-xl shadow-sm">
          {/* Input area */}
          <div className="flex items-end gap-3 p-3">
            {/* Left controls */}
            <div className="flex items-center gap-2">
              <ModelSelector />
              <div className="h-4 w-px bg-border/50" />
              
              {/* Sage Tools Button */}
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowSageTools(true)}
                className="h-8 gap-1.5 px-2.5 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/20 rounded-lg"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span className="text-xs font-medium">Sage</span>
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 hover:bg-muted/50 rounded-lg"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
              
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 hover:bg-muted/50 rounded-lg"
              >
                <Smile className="h-4 w-4" />
              </Button>
            </div>
            
            {/* Text input */}
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => handleMessageChange(e.target.value)}
                onKeyDown={handleKeyPress}
                onFocus={() => onExpand?.()}
                onBlur={() => onUserStopTyping?.()}
                placeholder="Aim, Shoot, and I deliver.."
                disabled={disabled}
                className="w-full bg-transparent border-none outline-none resize-none placeholder:text-muted-foreground scrollbar-thin scrollbar-thumb-border scrollbar-track-transparent"
                rows={1}
                style={{
                  minHeight: '20px',
                  maxHeight: '120px'
                }}
              />
            </div>
            
            {/* Send button */}
            <Button
              onClick={handleSend}
              disabled={!message.trim() || disabled}
              size="icon"
              className={`h-8 w-8 rounded-lg ${
                message.trim() && !disabled
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90' 
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
              }`}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Footer with character count */}
          {message.length > 0 && (
            <div className="flex items-center justify-between px-3 pb-2 pt-1 border-t border-border/20">
              <span className="text-xs text-muted-foreground">
                Press ⏎ to send, ⇧⏎ for new line
              </span>
              <span className={`text-xs ${
                message.length > 3800 ? 'text-destructive' : 
                message.length > 3000 ? 'text-yellow-500' : 
                'text-muted-foreground'
              }`}>
                {message.length}/4000
              </span>
            </div>
          )}
        </div>

        {/* Sage Tools Popup */}
        <SageToolsPopup
          isOpen={showSageTools}
          onClose={() => setShowSageTools(false)}
          onToolSelect={handleToolSelect}
        />
      </div>
    </div>
  );
}