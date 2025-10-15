interface SapientLogoProps {
  variant?: 'default' | 'rag' | 'benchmark';
}

export default function SapientLogo({ variant = 'default' }: SapientLogoProps) {
  const getColors = () => {
    switch (variant) {
      case 'rag':
        return {
          asterisk: 'rgba(246, 159, 28, 0.8)',
          text: '#c1c1c1',
        };
      case 'benchmark':
        return {
          asterisk: 'rgba(246, 159, 28, 0.8)',
          text: '#B729C1',
        };
      default:
        return {
          asterisk: 'rgba(246, 159, 28, 0.8)',
          text: '#FFFFFF',
        };
    }
  };

  const colors = getColors();

  return (
    <div className="flex items-center gap-1.5">
      <svg
        width="18"
        height="18"
        viewBox="0 0 18 18"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M9 0.642822V17.3571"
          stroke={colors.asterisk}
          strokeWidth="1.28571"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M1.92857 4.5L16.0714 13.5"
          stroke={colors.asterisk}
          strokeWidth="1.28571"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M1.92857 13.5L16.0714 4.5"
          stroke={colors.asterisk}
          strokeWidth="1.28571"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span
        className="text-[13.94px] font-normal"
        style={{ 
          color: colors.text,
          fontFamily: 'Hack, monospace'
        }}
      >
        Sapient
      </span>
    </div>
  );
}
