import { useState, useEffect } from 'react';
import Home from './components/Home';
import Auth from './components/Auth';
import RecruiterDashboard from './components/RecruiterDashboard';
import CandidateDashboard from './components/CandidateDashboard';
import ResetPassword from './components/ResetPassword';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [showHome, setShowHome] = useState(true);
  const [showResetPassword, setShowResetPassword] = useState(false);

  useEffect(() => {
    // Vérifier si c'est une page de réinitialisation de mot de passe
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('token');
    
    if (resetToken) {
      setShowResetPassword(true);
      setShowHome(false);
      setShowAuth(false);
      return;
    }
    
    // Sinon, vérifier l'utilisateur connecté
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setShowHome(false);
      setShowAuth(false);
    }
  }, []);
  const [authMode, setAuthMode] = useState('login');
  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('currentUser', JSON.stringify(userData));
    setShowAuth(false);
    setShowHome(false);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('currentUser');
    setShowHome(true);
    setShowAuth(false);
  };

  const showLogin = () => {
   setAuthMode('login'); // On prépare le mode connexion
   setShowAuth(true);
   setShowHome(false);
  };

  const showRegister = () => {
    setAuthMode('register');
    setShowAuth(true);
    setShowHome(false);
  };

  return (
    <div className="App">
      <header className="header">
        <div className="header-content">
          <div className="logo">Smart<span className="logo-accent">HIRE</span></div>
          <nav className="nav-links">
            {!user && (
              <>
                <a href="#" className="nav-link" onClick={(e) => { e.preventDefault(); setShowHome(true); setShowAuth(false); }}>Accueil</a>
                <button className="btn btn-primary" onClick={showLogin}>Connexion</button>
              </>
            )}
          </nav>
        </div>
      </header>

      {!user ? (
        <>
          {showResetPassword && <ResetPassword />}
          {showHome && !showResetPassword && <Home onShowLogin={showLogin} onShowRegister={showRegister} />}
          {showAuth && !showResetPassword && <Auth onLogin={handleLogin} initialMode={authMode} />}
        </>
      ) : (
        user.role === 'recruiter' ? (
          <RecruiterDashboard user={user} onLogout={handleLogout} />
        ) : (
          <CandidateDashboard user={user} onLogout={handleLogout} />
        )
      )}
    </div>
  );
}

export default App;