import React, { useState } from "react";

interface LoginProps {
  onBackToOnboarding: () => void;
  onCreateAccount: () => void;
}

export const Login: React.FC<LoginProps> = ({ onBackToOnboarding, onCreateAccount }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = () => {
    // Handle login functionality
    console.log("Login clicked", { email, password });
  };

  const handleCreateAccount = () => {
    onCreateAccount();
  };

  return (
    <div data-layer="OS - Login" className="OsLogin w-96 h-[852px] relative overflow-hidden">
      <div data-layer="Login" className="Login w-80 h-[470px] left-[29px] top-[356px] absolute bg-white rounded-2xl shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] overflow-hidden">
        <div data-layer="Login" className="Login w-44 left-[120px] top-[60px] absolute text-center justify-start text-black text-4xl font-normal font-['PP_Mondwest'] leading-10">
          Login
        </div>
        
        <div data-layer="Email" className="Email w-64 h-14 left-[43px] top-[221px] absolute opacity-60 rounded-2xl outline outline-1 outline-offset-[-1px] outline-zinc-600 overflow-hidden">
          <input
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full h-full px-5 py-3 bg-transparent text-zinc-600 text-xl font-bold font-['PP_NeueBit'] leading-7 outline-none"
          />
        </div>
        
        <div data-layer="Password" className="Password w-64 h-14 left-[43px] top-[291px] absolute opacity-60 rounded-2xl outline outline-1 outline-offset-[-1px] outline-zinc-600 overflow-hidden">
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full h-full px-5 py-3 bg-transparent text-zinc-600 text-xl font-bold font-['PP_NeueBit'] leading-7 outline-none"
          />
        </div>
        
        <button
          data-layer="CTA" 
          className="Cta w-64 h-14 left-[43px] top-[361px] absolute opacity-70 bg-lime-600 rounded-2xl shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] overflow-hidden hover:opacity-90 transition-opacity duration-200 cursor-pointer"
          onClick={handleLogin}
        >
          <div data-layer="Login" className="Login left-[110px] top-[11px] absolute justify-start text-white text-sm font-normal font-['PP_Mondwest'] leading-loose">
            Login
          </div>
        </button>
        
        <div data-layer="Don't have an account ? Create one" className="DontHaveAccount left-[98px] top-[431px] absolute justify-start">
          <span className="text-zinc-800 text-sm font-normal font-['PP_Mondwest'] leading-loose">Don't have an account ? </span>
          <button 
            className="text-stone-400 text-sm font-normal font-['PP_Mondwest'] leading-loose hover:text-indigo-600 transition-colors duration-200 cursor-pointer"
            onClick={handleCreateAccount}
          >
            Create one
          </button>
        </div>
      </div>
      
      {/* Back button */}
      <button
        className="absolute top-8 left-8 text-zinc-600 hover:text-zinc-800 transition-colors duration-200 cursor-pointer"
        onClick={onBackToOnboarding}
      >
        ← Back
      </button>
    </div>
  );
};
