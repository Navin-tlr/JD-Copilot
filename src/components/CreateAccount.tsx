import React, { useState } from "react";

interface CreateAccountProps {
  onBackToOnboarding: () => void;
  onLogin: () => void;
}

export const CreateAccount: React.FC<CreateAccountProps> = ({ onBackToOnboarding, onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleCreateAccount = () => {
    // Handle create account functionality
    console.log("Create account clicked", { email, password });
  };

  const handleLogin = () => {
    onLogin();
  };

  return (
    <div data-layer="OS - Create Account" className="OsCreateAccount w-96 h-[852px] relative overflow-hidden">
      <div data-layer="Create Account" className="CreateAccount w-80 h-[470px] left-[29px] top-[356px] absolute bg-white rounded-2xl shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] overflow-hidden">
        <div data-layer="Create Account" className="CreateAccount w-44 left-[80px] top-[60px] absolute text-center justify-start text-black text-4xl font-normal font-['PP_Mondwest'] leading-10">
          Create<br/>Account
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
        
        <div data-layer="Email" className="Email w-64 h-14 left-[43px] top-[291px] absolute opacity-60 rounded-2xl outline outline-1 outline-offset-[-1px] outline-zinc-600 overflow-hidden">
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
          onClick={handleCreateAccount}
        >
          <div data-layer="Create Account" className="CreateAccount left-[82px] top-[11px] absolute justify-start text-white text-sm font-normal font-['PP_Mondwest'] leading-loose">
            Create Account
          </div>
        </button>
        
        <div data-layer="Have an account ? Log in" className="HaveAnAccountLogIn left-[98px] top-[431px] absolute justify-start">
          <span className="text-zinc-800 text-sm font-normal font-['PP_Mondwest'] leading-loose">Have an account ? </span>
          <span className="text-indigo-600 text-sm font-normal font-['PP_Mondwest'] leading-loose"> </span>
          <button 
            className="text-stone-400 text-sm font-normal font-['PP_Mondwest'] leading-loose hover:text-indigo-600 transition-colors duration-200 cursor-pointer"
            onClick={handleLogin}
          >
            Log in
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
