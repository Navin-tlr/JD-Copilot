import React, { useState, useEffect } from 'react';
import { MessageSquare, Plus, Trash2, X } from 'lucide-react';

interface ChatSession {
  id: string;
  name: string;
  created_at: string;
  last_activity: string;
  message_count: number;
}

interface ChatHistoryProps {
  isOpen: boolean;
  onClose: () => void;
  currentSessionId: string;
  userId: string;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  variant?: 'default' | 'rag' | 'benchmark';
}

export default function ChatHistory({
  isOpen,
  onClose,
  currentSessionId,
  userId,
  onSessionSelect,
  onNewChat,
  variant = 'default'
}: ChatHistoryProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchSessions();
    }
  }, [isOpen, userId]);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/sessions/${userId}`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this chat?')) return;

    try {
      await fetch(`http://localhost:8000/sessions/${sessionId}`, {
        method: 'DELETE'
      });
      setSessions(sessions.filter(s => s.id !== sessionId));
      if (sessionId === currentSessionId) {
        onNewChat();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-40 transition-opacity backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Sidebar - Dark theme matching existing UI */}
      <div className="fixed top-0 right-0 h-full w-80 bg-[#2A2A2A] shadow-2xl z-50 flex flex-col animate-slide-in-right border-l border-[#404040]">
        {/* Header */}
        <div className="p-4 border-b border-[#404040]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[16px] font-semibold text-[#E0E0E0]">Chat History</h2>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-[#3D3D3D] text-[#C1C1C1] hover:text-[#FFFFFF] transition-all"
              aria-label="Close history"
            >
              <X size={18} />
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#3D3D3D] hover:bg-[#4A4A4A] text-[#E0E0E0] rounded-lg transition-all hover:scale-[1.02] active:scale-[0.98] border border-[#505050]"
          >
            <Plus size={18} />
            <span className="font-medium text-[14px]">New Chat</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#C1C1C1]" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-[#6A6A6A]">
              <MessageSquare size={32} className="mb-2 opacity-50" />
              <p className="text-sm">No chat history yet</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => {
                  onSessionSelect(session.id);
                  onClose();
                }}
                className={`
                  group relative p-3 rounded-lg border cursor-pointer transition-all
                  ${session.id === currentSessionId 
                    ? 'bg-[#3D3D3D] border-[#D38B21]' 
                    : 'bg-[#2f2f2f] border-transparent hover:bg-[#353535] hover:border-[#505050]'
                  }
                `}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-[13px] text-[#E0E0E0] truncate leading-tight">
                      {session.name}
                    </p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="text-[11px] text-[#8A8A8A]">
                        {formatTime(session.last_activity)}
                      </span>
                      <span className="text-[11px] text-[#6A6A6A]">
                        · {session.message_count} msgs
                      </span>
                    </div>
                  </div>

                  {/* Delete Button */}
                  <button
                    onClick={(e) => handleDelete(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-[#4A4A4A] text-[#8A8A8A] hover:text-[#FF6B6B] transition-all"
                    aria-label="Delete session"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-[#404040] text-[11px] text-[#8A8A8A] text-center">
          {sessions.length} of 10 chats stored
        </div>
      </div>
    </>
  );
}
