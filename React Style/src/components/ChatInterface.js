import React from 'react';

const ChatInterface = ({ onToggleTheme, isDarkMode }) => {
  return (
    <div className="chat-interface">
      <header className="chat-header">
        <h1>YAKKSSHA</h1>
        <button onClick={onToggleTheme}>
          {isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        </button>
      </header>
      <main className="chat-main">
        <p>Chat content goes here...</p>
      </main>
    </div>
  );
};

export default ChatInterface;
