import { useState } from 'react';
import { motion } from 'motion/react';
import { Button } from './ui/button';
import { Apple } from 'lucide-react';

interface OnboardingScreenProps {
  onContinue: () => void;
  onSignIn: () => void;
}

export function OnboardingScreen({ onContinue, onSignIn }: OnboardingScreenProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleSignUp = async () => {
    setIsLoading(true);
    // Simulate loading delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
    onContinue();
  };

  return (
    <div className="min-h-screen bg-background flex flex-col relative overflow-hidden">
      {/* Status bar area */}
      <div className="h-12 flex items-center justify-center relative">
        <div className="absolute left-6 text-sm font-medium">9:41</div>
        <div className="w-24 h-6 bg-foreground rounded-full"></div>
        <div className="absolute right-6 flex items-center gap-1">
          <div className="flex gap-1">
            <div className="w-1 h-3 bg-foreground rounded-full"></div>
            <div className="w-1 h-3 bg-foreground rounded-full"></div>
            <div className="w-1 h-3 bg-foreground rounded-full"></div>
            <div className="w-1 h-3 bg-muted rounded-full"></div>
          </div>
          <div className="ml-1 text-sm">📶</div>
          <div className="text-sm">🔋</div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col px-6 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <h1 className="text-2xl font-medium mb-2">rooms</h1>
        </motion.div>

        {/* Hero content */}
        <div className="flex-1 flex flex-col justify-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-medium leading-tight mb-4">
              chat <span className="inline-block">🧠</span> rooms
            </h2>
            <div className="text-4xl font-medium leading-tight text-muted-foreground">
              <span>with the </span>
              <span className="text-foreground">most</span>
            </div>
            <div className="text-4xl font-medium leading-tight">
              valuable <span className="inline-block">🧠</span>
            </div>
          </motion.div>

          {/* Action buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="space-y-4"
          >
            <Button
              onClick={handleSignUp}
              disabled={isLoading}
              className="w-full h-14 bg-foreground text-background hover:bg-foreground/90 rounded-2xl text-base font-medium"
            >
              {isLoading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-background border-t-transparent rounded-full"
                />
              ) : (
                <>
                  <Apple className="w-5 h-5 mr-2" />
                  Sign up with Apple
                </>
              )}
            </Button>

            <Button
              onClick={onSignIn}
              variant="ghost"
              className="w-full h-14 text-foreground hover:bg-muted/50 rounded-2xl text-base font-medium"
            >
              I have an account
            </Button>
          </motion.div>
        </div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1 }}
          className="text-center text-xs text-muted-foreground leading-relaxed mt-8"
        >
          By continuing, you confirm that you agree to our Terms
          of Service, Privacy Policy and you agree to receive
          marketing communications. Opt-out any time.
        </motion.div>
      </div>

      {/* Home indicator */}
      <div className="h-8 flex items-center justify-center">
        <div className="w-32 h-1 bg-foreground/20 rounded-full"></div>
      </div>
    </div>
  );
}