import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Clock, MessageSquare, Trash2, Plus } from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

interface ChatHistoryProps {
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  currentChatId?: string;
}

export function ChatHistory({ onSelectChat, onNewChat, currentChatId }: ChatHistoryProps) {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);

  // Load chat sessions from localStorage
  useEffect(() => {
    const savedChats = localStorage.getItem('yakkssha-chat-sessions');
    if (savedChats) {
      try {
        const parsedChats = JSON.parse(savedChats);
        setChatSessions(parsedChats.map((chat: any) => ({
          ...chat,
          timestamp: new Date(chat.timestamp)
        })));
      } catch (error) {
        console.error('Error loading chat sessions:', error);
      }
    }
  }, []);

  // Save chat sessions to localStorage
  const saveChatSessions = (sessions: ChatSession[]) => {
    localStorage.setItem('yakkssha-chat-sessions', JSON.stringify(sessions));
    setChatSessions(sessions);
  };

  const deleteChat = (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const updatedSessions = chatSessions.filter(chat => chat.id !== chatId);
    saveChatSessions(updatedSessions);
  };

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diffInHours = (now.getTime() - timestamp.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) {
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return timestamp.toLocaleDateString();
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 pb-3">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">Chat History</h2>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button
              onClick={onNewChat}
              size="sm"
              className="h-8 px-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 shadow-sm"
            >
              <Plus className="h-3.5 w-3.5 mr-1.5" />
              New Chat
            </Button>
          </motion.div>
        </motion.div>
        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
          {chatSessions.length} conversation{chatSessions.length !== 1 ? 's' : ''}
        </p>
      </div>

      <Separator className="mx-4" />

      {/* Chat Sessions List */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-2 p-2">
          {chatSessions.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12 text-center"
            >
              <MessageSquare className="h-12 w-12 text-gray-400 dark:text-gray-600 mb-3" />
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">No chat history yet</p>
              <p className="text-xs text-gray-500 dark:text-gray-500">Start a conversation to see it here</p>
            </motion.div>
          ) : (
            chatSessions
              .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
              .map((chat, index) => (
                <motion.div
                  key={chat.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`
                    group cursor-pointer rounded-xl p-3 transition-all duration-200
                    ${currentChatId === chat.id 
                      ? 'bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30 border border-blue-200 dark:border-blue-800/50' 
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800/50 border border-transparent'
                    }
                  `}
                  onClick={() => onSelectChat(chat.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <MessageSquare className="h-3.5 w-3.5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {truncateText(chat.title, 25)}
                        </h3>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
                        {truncateText(chat.lastMessage, 60)}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-500">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatTimestamp(chat.timestamp)}
                        </div>
                        <span>•</span>
                        <span>{chat.messageCount} message{chat.messageCount !== 1 ? 's' : ''}</span>
                      </div>
                    </div>
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={(e) => deleteChat(chat.id, e)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-md"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-red-500" />
                    </motion.button>
                  </div>
                </motion.div>
              ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-4 pt-2 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-500 text-center">
          Chats are stored locally on your device
        </p>
      </div>
    </div>
  );
}