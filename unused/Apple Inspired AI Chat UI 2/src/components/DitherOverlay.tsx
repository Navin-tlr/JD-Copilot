import { motion } from 'motion/react';

interface DitherOverlayProps {
  intensity?: number;
  className?: string;
  isActive?: boolean;
}

export function DitherOverlay({ 
  intensity = 0.1, 
  className = "",
  isActive = true 
}: DitherOverlayProps) {
  if (!isActive) return null;

  // Generate a simple dither pattern
  const ditherPattern = Array.from({ length: 16 }, (_, i) => {
    const row = Math.floor(i / 4);
    const col = i % 4;
    const threshold = ((row + col) % 2) * 0.5 + 0.25;
    return threshold;
  });

  return (
    <motion.div
      className={`absolute inset-0 pointer-events-none ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: intensity }}
      transition={{ duration: 0.3 }}
    >
      {/* CSS-based dither pattern overlay */}
      <div 
        className="w-full h-full opacity-20"
        style={{
          backgroundImage: `
            radial-gradient(circle at 25% 25%, rgba(0,0,0,0.1) 1px, transparent 1px),
            radial-gradient(circle at 75% 25%, rgba(0,0,0,0.05) 1px, transparent 1px),
            radial-gradient(circle at 25% 75%, rgba(0,0,0,0.05) 1px, transparent 1px),
            radial-gradient(circle at 75% 75%, rgba(0,0,0,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '4px 4px',
          animation: 'pixel-shift 0.8s infinite ease-in-out'
        }}
      />
      
      {/* Scanline effect */}
      <motion.div
        className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-foreground/10 to-transparent"
        animate={{
          y: ['0%', '100vh']
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: "linear"
        }}
      />
      
      {/* Subtle noise texture */}
      <div 
        className="w-full h-full mix-blend-multiply opacity-5"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='1' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          backgroundSize: '128px 128px'
        }}
      />
    </motion.div>
  );
}