import { useState } from 'react';
import { motion } from 'motion/react';
import { Button } from './ui/button';
import { ArrowLeft, ArrowRight, MousePointer2 } from 'lucide-react';

interface SpecializationSelectionProps {
  onContinue: (specialization: string) => void;
  onBack: () => void;
}

const specializations = [
  'Marketing',
  'Lean Operations & Systems',
  'Finance',
  'Human Resources',
  'Business Analytics'
];

export function SpecializationSelection({ onContinue, onBack }: SpecializationSelectionProps) {
  const [selectedSpecialization, setSelectedSpecialization] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handleContinue = async () => {
    if (!selectedSpecialization) return;

    setIsLoading(true);
    // Simulate processing
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
    onContinue(selectedSpecialization);
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center justify-between p-4"
      >
        <Button
          variant="ghost"
          size="icon"
          onClick={onBack}
          className="h-10 w-10 rounded-full text-white hover:bg-white/10"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="w-10"></div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col justify-center px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-md mx-auto w-full"
        >
          {/* Title */}
          <div className="text-center mb-12">
            <h1 className="text-3xl font-medium mb-2">
              Select Your
            </h1>
            <h1 className="text-3xl font-medium">
              Specialization
            </h1>
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.5 }}
              className="inline-block ml-2"
            >
              <MousePointer2 className="h-6 w-6 text-white" />
            </motion.div>
          </div>

          {/* Specialization Options */}
          <div className="space-y-4 mb-12">
            {specializations.map((specialization, index) => (
              <motion.div
                key={specialization}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
              >
                <Button
                  variant="outline"
                  onClick={() => setSelectedSpecialization(specialization)}
                  className={`
                    w-full h-16 rounded-2xl border-2 text-base font-medium transition-all duration-300
                    ${selectedSpecialization === specialization
                      ? 'border-white bg-white text-black hover:bg-white/90'
                      : 'border-gray-600 bg-transparent text-white hover:border-gray-400 hover:bg-gray-800/50'
                    }
                  `}
                >
                  {specialization}
                </Button>
              </motion.div>
            ))}
          </div>

          {/* Continue Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.8 }}
          >
            <Button
              onClick={handleContinue}
              disabled={!selectedSpecialization || isLoading}
              className={`
                w-full h-14 rounded-xl text-base font-medium transition-all duration-300
                ${selectedSpecialization
                  ? 'bg-white text-black hover:bg-white/90'
                  : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              {isLoading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-black border-t-transparent rounded-full"
                />
              ) : (
                <>
                  Get Started
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}