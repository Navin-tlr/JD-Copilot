import React, { useState } from "react";

interface OnboardingScreenProps {
  onSignUpLogin: () => void;
}

export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onSignUpLogin }) => {
  const handleSignUpLogin = () => {
    onSignUpLogin();
  };

  return (
    <div data-layer="Onboarding Screen" className="OnboardingScreen w-96 h-[852px] relative bg-white overflow-hidden">
      <div data-layer="Rectangle 1" className="Rectangle1 w-96 h-11 left-[13px] top-[37px] absolute rounded-md" />
      <div data-layer="WELCOME TO Y^2" className="WelcomeToY2 w-72 h-14 left-[55px] top-[59px] absolute justify-start text-zinc-800 text-4xl font-normal font-['That_That_New_Pixel_Test']">WELCOME TO Y^2</div>
      <div data-layer="Y" className="Y left-[30px] top-[-43px] absolute opacity-30 justify-start text-black/10 text-[700px] font-normal font-['Belmonte_Ballpoint_Trial']">Y</div>
      <div data-svg-wrapper data-layer="Rectangle 7" className="Rectangle7 left-[110px] top-[749px] absolute">
        <svg width="172" height="46" viewBox="0 0 172 46" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0.5H160C166.351 0.5 171.5 5.64873 171.5 12V34C171.5 40.3513 166.351 45.5 160 45.5H12C5.64873 45.5 0.5 40.3513 0.5 34V12C0.5 5.64873 5.64873 0.5 12 0.5Z" stroke="black" stroke-opacity="0.3"/>
        </svg>
      </div>
      <div 
        data-layer="SIGN UP/ LOG IN" 
        className="SignUpLogIn left-[141px] top-[764px] absolute opacity-70 justify-start text-zinc-600 text-xl font-bold font-['PP_NeueBit'] cursor-pointer hover:opacity-90 transition-opacity duration-200"
        onClick={handleSignUpLogin}
      >
        SIGN UP/ LOG IN
      </div>
    </div>
  );
};
