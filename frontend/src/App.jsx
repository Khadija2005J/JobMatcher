import { useState, useEffect } from 'react';
import Home from './components/Home';
import Auth from './components/Auth';
import RecruiterDashboard from './components/RecruiterDashboard';
import CandidateDashboard from './components/CandidateDashboard';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [showHome, setShowHome] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setShowHome(false);
      setShowAuth(false);
    }
  }, []);

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
    setShowAuth(true);
    setShowHome(false);
  };

  const showRegister = () => {
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
          {showHome && <Home onShowLogin={showLogin} onShowRegister={showRegister} />}
          {showAuth && <Auth onLogin={handleLogin} />}
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
