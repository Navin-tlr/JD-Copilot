import React from 'react';

type Props = {
  title?: string; // used for the heading text; defaults to Figma copy
  description?: string; // used for the body copy; defaults to Figma copy
  onActivate: () => void;
  onCancel: () => void; // provided for backdrop click outside; not used inside exact design
};

// Renders the exact Figma layout with absolute positioning and pixel-precise styles
export default function DeepDiveConsentCard({
  title = 'Deep Dive ?',
  description = 'Query returned no results. Offer deep-dive search of unstructured job descriptions.',
  onActivate,
}: Props) {
  return (
    <div
      data-layer="Component 2"
      className="Component2"
      style={{ width: 256, height: 242.58, position: 'relative' }}
    >
      {/* Background rectangles */}
      <div
        data-layer="Rectangle 4"
        className="Rectangle4"
        style={{
          width: 256,
          height: 242.58,
          left: 0,
          top: 0,
          position: 'absolute',
          background: '#C5C5C5',
          borderRadius: 1.32,
        }}
      />
      <div
        data-layer="Rectangle 5"
        className="Rectangle5"
        style={{
          width: 239,
          height: 228.19,
          left: 8,
          top: 7,
          position: 'absolute',
          background: '#EBEBEB',
          boxShadow: '0px 4.120689868927002px 4.120689868927002px rgba(0, 0, 0, 0.25)',
          borderRadius: 2,
        }}
      />

      {/* Heading */}
      <div
        data-layer="Deep Dive ?"
        className="DeepDive"
        style={{
          left: 33,
          top: 102,
          position: 'absolute',
          color: 'black',
          fontSize: 20,
          fontFamily: 'BlinkMacSystemFont, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
          fontWeight: 500,
          whiteSpace: 'pre-wrap',
        }}
      >
        {title}
      </div>

      {/* Description */}
      <div
        data-layer="The structured database gave 0 results, shall I proceed with deep-dive"
        className="TheStructuredDatabaseGave0ResultsShallIProceedWithDeepDive"
        style={{
          left: 33,
          top: 133,
          position: 'absolute',
          color: 'black',
          fontSize: 14.06,
          fontFamily: 'BlinkMacSystemFont, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
          fontWeight: 300,
          whiteSpace: 'pre-wrap',
          lineHeight: 1.3,
          width: 180,
        }}
      >
        {description}
      </div>

      {/* Activate button background rectangle */}
      <button
        type="button"
        aria-label="Activate Deep Dive"
        onClick={onActivate}
        style={{
          width: 88,
          height: 31,
          left: 142,
          top: 191,
          position: 'absolute',
          background: 'rgba(68, 152, 69, 0.80)',
          boxShadow: '1px 1px 10px rgba(0, 0, 0, 0.25)',
          borderRadius: 10,
          border: 'none',
          cursor: 'pointer',
          padding: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span
          style={{
            color: 'white',
            fontSize: 11.59,
            fontFamily: 'BlinkMacSystemFont, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif',
            fontWeight: 400,
            whiteSpace: 'nowrap',
          }}
        >
          Activate
        </span>
      </button>

      {/* SVG icon */}
      <div
        data-svg-wrapper
        data-layer="interface-edit-pathfinder-intersect--pathfinder-intersect-work--Streamline-Core"
        className="InterfaceEditPathfinderIntersectPathfinderIntersectWorkStreamlineCore"
        style={{ left: 46, top: 24, position: 'absolute' }}
      >
        <svg
          width="59"
          height="59"
          viewBox="0 0 59 59"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g clipPath="url(#clip0_172_128)">
            <path d="M2.10712 35.8214C2.10712 36.9391 2.55112 38.011 3.34145 38.8014C4.13178 39.5917 5.2037 40.0357 6.3214 40.0357" stroke="url(#paint0_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M6.3214 2.10718C5.2037 2.10718 4.13178 2.55118 3.34145 3.34151C2.55112 4.13185 2.10712 5.20377 2.10712 6.32146" stroke="url(#paint1_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M40.0357 6.32146C40.0357 5.20377 39.5917 4.13185 38.8014 3.34151C38.011 2.55118 36.9391 2.10718 35.8214 2.10718" stroke="url(#paint2_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M16.8571 2.10718H25.2857" stroke="url(#paint3_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2.10712 16.8572V25.2857" stroke="url(#paint4_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M18.9643 52.6786C18.9643 53.7963 19.4083 54.8682 20.1986 55.6585C20.989 56.4489 22.0609 56.8929 23.1786 56.8929" stroke="url(#paint5_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M56.8929 23.1785C56.8929 22.0608 56.4489 20.9889 55.6585 20.1986C54.8682 19.4082 53.7963 18.9642 52.6786 18.9642" stroke="url(#paint6_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M52.6786 56.8929C53.7963 56.8929 54.8682 56.4489 55.6585 55.6585C56.4489 54.8682 56.8929 53.7963 56.8929 52.6786" stroke="url(#paint7_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M33.7143 56.8928H42.1429" stroke="url(#paint8_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M56.8929 33.7142V42.1428" stroke="url(#paint9_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M40.0357 35.8214V18.9642H23.1786C22.0609 18.9642 20.989 19.4082 20.1986 20.1986C19.4083 20.9889 18.9643 22.0608 18.9643 23.1785V40.0357H35.8214C36.9391 40.0357 38.0111 39.5917 38.8014 38.8013C39.5917 38.011 40.0357 36.9391 40.0357 35.8214Z" stroke="url(#paint10_linear_172_128)" strokeOpacity="0.7" strokeWidth="4.21429" strokeLinecap="round" strokeLinejoin="round"/>
          </g>
          <defs>
            <linearGradient id="paint0_linear_172_128" x1="4.21426" y1="35.8214" x2="4.21426" y2="40.0357" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint1_linear_172_128" x1="4.21426" y1="2.10718" x2="4.21426" y2="6.32146" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint2_linear_172_128" x1="37.9286" y1="2.10718" x2="37.9286" y2="6.32146" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint3_linear_172_128" x1="21.0714" y1="2.10718" x2="21.0714" y2="3.10718" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint4_linear_172_128" x1="2.60712" y1="16.8572" x2="2.60712" y2="25.2857" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint5_linear_172_128" x1="21.0714" y1="52.6786" x2="21.0714" y2="56.8929" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint6_linear_172_128" x1="54.7857" y1="18.9642" x2="54.7857" y2="23.1785" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint7_linear_172_128" x1="54.7857" y1="52.6786" x2="54.7857" y2="56.8929" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint8_linear_172_128" x1="37.9286" y1="56.8928" x2="37.9286" y2="57.8928" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint9_linear_172_128" x1="57.3929" y1="33.7142" x2="57.3929" y2="42.1428" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <linearGradient id="paint10_linear_172_128" x1="29.5" y1="18.9642" x2="29.5" y2="40.0357" gradientUnits="userSpaceOnUse">
              <stop stopColor="#000001"/>
              <stop offset="0.423077" stopColor="#A3A3C4"/>
              <stop offset="1" stopColor="#000067"/>
            </linearGradient>
            <clipPath id="clip0_172_128">
              <rect width="59" height="59" fill="white"/>
            </clipPath>
          </defs>
        </svg>
      </div>
    </div>
  );
}
