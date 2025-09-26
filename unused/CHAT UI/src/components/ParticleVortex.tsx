import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface ParticleVortexProps {
  isVisible: boolean;
}

interface Particle {
  id: number;
  x: number;
  y: number;
  baseX: number;
  baseY: number;
  size: number;
  opacity: number;
  speed: number;
  phase: number;
}

export function ParticleVortex({ isVisible }: ParticleVortexProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const particlesRef = useRef<Particle[]>([]);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Initialize particles
  useEffect(() => {
    if (dimensions.width === 0 || dimensions.height === 0) return;

    const particles: Particle[] = [];
    const particleCount = 50; // Much fewer particles

    for (let i = 0; i < particleCount; i++) {
      const x = Math.random() * dimensions.width;
      const y = Math.random() * dimensions.height;
      
      particles.push({
        id: i,
        x: x,
        y: y,
        baseX: x,
        baseY: y,
        size: 1 + Math.random() * 2, // Small sizes
        opacity: 0.1 + Math.random() * 0.3, // Subtle opacity
        speed: 0.5 + Math.random() * 1, // Slow movement
        phase: Math.random() * Math.PI * 2
      });
    }

    particlesRef.current = particles;
  }, [dimensions]);

  // Handle window resize
  useEffect(() => {
    const updateDimensions = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Simple animation loop
  useEffect(() => {
    if (!isVisible) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = (timestamp: number) => {
      // Clear canvas
      ctx.clearRect(0, 0, dimensions.width, dimensions.height);

      // Update and draw particles
      particlesRef.current.forEach(particle => {
        // Simple floating motion
        const time = timestamp * 0.001;
        particle.x = particle.baseX + Math.sin(time * particle.speed + particle.phase) * 20;
        particle.y = particle.baseY + Math.cos(time * particle.speed * 0.7 + particle.phase) * 15;

        // Gentle opacity breathing
        const breathingOpacity = particle.opacity + Math.sin(time * 0.8 + particle.phase) * 0.1;

        // Draw simple circle
        ctx.save();
        ctx.globalAlpha = Math.max(0, breathingOpacity);
        ctx.fillStyle = '#6b7280'; // Muted gray color
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isVisible, dimensions]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.6, ease: "easeInOut" }}
          className="fixed inset-0 pointer-events-none z-10"
        >
          <canvas
            ref={canvasRef}
            width={dimensions.width}
            height={dimensions.height}
            className="absolute inset-0"
            style={{ background: 'transparent' }}
          />
          
          {/* Subtle central glow */}
          <motion.div
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.1, 0.2, 0.1]
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-gradient-radial from-muted/20 to-transparent rounded-full"
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}