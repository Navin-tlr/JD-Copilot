import { Button } from './ui/button';
import { MoreHorizontal, Settings, User, Menu } from 'lucide-react';
import avatarImage from 'figma:asset/49e1c59c05101ee88132a24fdd051bbf030d2c22.png';

interface ChatHeaderProps {
  onOpenChatHistory: () => void;
}

export function ChatHeader({ onOpenChatHistory }: ChatHeaderProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 bg-background border-b border-border/50">
      <div className="flex items-center gap-3">
        {/* Chat History Button */}
        <Button 
          onClick={onOpenChatHistory}
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 rounded-lg hover:bg-muted/50"
        >
          <Menu className="h-4 w-4" />
        </Button>

        <div className="flex items-center gap-3">
          <img
            src={avatarImage}
            alt="YAKKSSHA Avatar"
            className="w-8 h-8 md:w-9 md:h-9 rounded-lg object-cover"
            style={{
              objectPosition: 'center 20%',
              transform: 'scale(1.3)',
              transformOrigin: 'center'
            }}
          />
          <div>
            <h2 className="font-medium text-sm text-foreground">YAKKSSHA</h2>
            <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
              Online
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 rounded-lg hover:bg-muted/50"
        >
          <User className="h-4 w-4" />
        </Button>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 rounded-lg hover:bg-muted/50"
        >
          <Settings className="h-4 w-4" />
        </Button>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 rounded-lg hover:bg-muted/50"
        >
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}