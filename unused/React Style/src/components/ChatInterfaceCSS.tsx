import React from 'react';
import styles from './ChatInterface.module.css';

export const ChatInterfaceCSS: React.FC<{onToggleTheme?: () => void; isDarkMode?: boolean}> = (props) => {
  return (
    <div className={styles.container}>
      <div className={styles.scrollView}>
        <img
          src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/06qqsua7_expires_30_days.png"
          alt="main icon"
          className={styles.image}
        />
        <div className={styles.column}>
          <button
            className={styles.buttonRow}
            onClick={() => alert('Pressed!')}
          >
            <img
              src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/swb43i6i_expires_30_days.png"
              alt="rag icon"
              className={styles.image2}
            />
            <span className={styles.text}>
              RAG
            </span>
          </button>
          <p className={styles.text2}>
            Ask, search and I'll answer....
          </p>
          <div className={styles.row}>
            <img
              src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/jp5ykuk4_expires_30_days.png"
              alt="icon 1"
              className={styles.image3}
            />
            <img
              src="https://storage.googleapis.com/tagjs-prod.appspot.com/v1/DDdrEecD65/xx8dfl3s_expires_30_days.png"
              alt="icon 2"
              className={styles.image4}
            />
          </div>
        </div>
      </div>
    </div>
  );
};