import { useState, useEffect } from 'react';
import Home from './components/Home';
import Auth from './components/Auth';
import RecruiterDashboard from './components/RecruiterDashboard';
import CandidateDashboard from './components/CandidateDashboard';
import ResetPassword from './components/ResetPassword';
import About from './components/About';
import Features from './components/Features';
import Benefits from './components/Benefits';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import Footer from './components/Footer';
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
  const navigate = useNavigate();
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
   navigate('/');
   setShowAuth(true);
   setShowHome(false);
  };

  const showRegister = () => {
    setAuthMode('register');
    navigate('/');
    setShowAuth(true);
    setShowHome(false);
  };

  const mainContent = (
    <>
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
    </>
  );

  return (
    <div className="App">
      <header className="header">
        <div className="header-content">
          <div className="logo">Job<span className="logo-accent">Matcher</span></div>
          <nav className="nav-links">
            {!user && (
              <>
                <Link to="/" className="nav-link" onClick={() => { setShowHome(true); setShowAuth(false); }}>Accueil</Link>
                <Link to="/about" className="nav-link">À propos</Link>
                <Link to="/features" className="nav-link" style={{ marginLeft: '6px' }}>Fonctionnalités</Link>
                <Link to="/benefits" className="nav-link" style={{ marginLeft: '6px' }}>Avantages</Link>
                <button className="btn btn-primary" onClick={showLogin} style={{ marginLeft: '8px' }}>Connexion</button>
              </>
            )}
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={mainContent} />
        <Route path="/about" element={<About />} />
        <Route path="/features" element={<Features />} />
        <Route path="/benefits" element={<Benefits />} />
      </Routes>

      <Footer />
    </div>
  );
}

export default App;