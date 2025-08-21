import React, { useState } from 'react';
import './App.css';
import { OnboardingScreen } from './components/OnboardingScreen';
import { CreateAccount } from './components/CreateAccount';
import { Login } from './components/Login';

type Screen = 'onboarding' | 'createAccount' | 'login';

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('onboarding');

  const handleSignUpLogin = () => {
    setCurrentScreen('createAccount');
  };

  const handleBackToOnboarding = () => {
    setCurrentScreen('onboarding');
  };

  const handleCreateAccount = () => {
    setCurrentScreen('createAccount');
  };

  const handleLogin = () => {
    setCurrentScreen('login');
  };

  const renderScreen = () => {
    switch (currentScreen) {
      case 'onboarding':
        return <OnboardingScreen onSignUpLogin={handleSignUpLogin} />;
      case 'createAccount':
        return <CreateAccount onBackToOnboarding={handleBackToOnboarding} onLogin={handleLogin} />;
      case 'login':
        return <Login onBackToOnboarding={handleBackToOnboarding} onCreateAccount={handleCreateAccount} />;
      default:
        return <OnboardingScreen onSignUpLogin={handleSignUpLogin} />;
    }
  };

  return (
    <div className="App">
      {renderScreen()}
    </div>
  );
}

export default App;
