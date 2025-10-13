import { useEffect, useRef, useState } from "react";

type Phase = "enter" | "active" | "exit";

interface ThinkingIndicatorProps {
  active: boolean;
  message?: string;
}

const ENTER_DURATION_MS = 180;
const EXIT_DURATION_MS = 140;
const MIN_VISIBLE_MS = 1200;

export default function ThinkingIndicator({ active, message = "Preparing your insights" }: ThinkingIndicatorProps) {
  const [visible, setVisible] = useState(false);
  const [phase, setPhase] = useState<Phase>("enter");
  const shownAtRef = useRef<number>(0);
  const exitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cleanupTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (active) {
      if (exitTimerRef.current) {
        clearTimeout(exitTimerRef.current);
        exitTimerRef.current = null;
      }
      if (cleanupTimerRef.current) {
        clearTimeout(cleanupTimerRef.current);
        cleanupTimerRef.current = null;
      }

      shownAtRef.current = Date.now();
      setVisible(true);
      setPhase("enter");

      const enterTimer = setTimeout(() => {
        setPhase("active");
      }, ENTER_DURATION_MS);

      return () => clearTimeout(enterTimer);
    }

    if (!visible) {
      return;
    }

    const elapsed = Date.now() - shownAtRef.current;
    const delay = Math.max(0, MIN_VISIBLE_MS - elapsed);

    exitTimerRef.current = setTimeout(() => {
      setPhase("exit");
      cleanupTimerRef.current = setTimeout(() => {
        setVisible(false);
        setPhase("enter");
      }, EXIT_DURATION_MS);
    }, delay);

    return () => {
      if (exitTimerRef.current) {
        clearTimeout(exitTimerRef.current);
        exitTimerRef.current = null;
      }
      if (cleanupTimerRef.current) {
        clearTimeout(cleanupTimerRef.current);
        cleanupTimerRef.current = null;
      }
    };
  }, [active, visible]);

  if (!visible) {
    return null;
  }

  const className = [
    "thinking-indicator",
    phase === "enter" ? "thinking-indicator--enter" : "",
    phase === "active" ? "thinking-indicator--active" : "",
    phase === "exit" ? "thinking-indicator--exit" : ""
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className} role="status" aria-live="polite">
      <span className="thinking-indicator__dot" aria-hidden="true" />
      <span className="thinking-indicator__text">{message}</span>
    </div>
  );
}
