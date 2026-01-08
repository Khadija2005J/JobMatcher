import { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const Auth = ({ onLogin, initialMode }) => {
  const [isLogin, setIsLogin] = useState(initialMode !== 'register');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'candidate' // Forcé à candidate pour les inscriptions
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/login' : '/register';
      
      // Préparation des données à envoyer au backend
      const payload = isLogin
        ? { email: formData.email, password: formData.password }
        : formData;

      // Appel à l'API via Axios
      const response = await axios.post(`${API_URL}${endpoint}`, payload);
      
      // --- CRUCIAL : Sauvegarde du token pour l'authentification future ---
      // Votre backend renvoie 'access_token' dans l'objet de réponse
      if (response.data && response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        console.log("Succès : Token enregistré dans le localStorage.");
      }

      // Gestion de la redirection ou de l'état de l'application
      if (response.data.user) {
        // Cas d'un login réussi
        onLogin(response.data.user);
      } else if (response.data.user_id) {
        // Cas d'une inscription réussie
        onLogin({ 
            id: response.data.user_id, 
            name: formData.name, 
            email: formData.email, 
            role: 'candidate' 
        });
      }
    } catch (err) {
      // Gestion des erreurs (ex: 401 Unauthorized si mauvais identifiants)
      console.error("Erreur d'authentification:", err);
      setError(err.response?.data?.detail || 'Une erreur est survenue lors de la connexion');
    } finally {
      setLoading(false);
    }
  };
  // Si on affiche le composant de mot de passe oublié
  if (showForgotPassword) {
    return <ForgotPasswordForm onBack={() => setShowForgotPassword(false)} />;
  }

  return (
    <section className="auth-section">
      {/* Titre dynamique : "Connexion" pour tous ou "Inscription Candidat" */}
      <h2>{isLogin ? 'Connexion' : 'Inscription Candidat'}</h2>
      <p>
        {isLogin 
          ? 'Accédez à votre espace (Candidat ou Recruteur)' 
          : 'Créez votre profil candidat pour postuler aux offres'}
      </p>
      
      {error && <div className="alert alert-error">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        {!isLogin && (
          <div className="form-group">
            <label>Nom complet</label>
            <input
              type="text"
              name="name"
              className="form-control"
              placeholder="Jean Dupont"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
        )}
        
        <div className="form-group">
          <label>Adresse email</label>
          <input
            type="email"
            name="email"
            className="form-control"
            placeholder="votre@email.com"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label>Mot de passe</label>
          <input
            type="password"
            name="password"
            className="form-control"
            placeholder="••••••••"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={isLogin ? undefined : 6}
          />
        </div>
        
        {isLogin && (
          <div style={{ textAlign: 'right', marginTop: '-0.5rem', marginBottom: '1rem' }}>
            <a 
              href="#" 
              onClick={(e) => { e.preventDefault(); setShowForgotPassword(true); }}
              style={{ 
                color: 'var(--secondary)', 
                fontSize: '0.9rem', 
                textDecoration: 'none',
                fontWeight: 500
              }}
            >
              Mot de passe oublié ?
            </a>
          </div>
        )}
        
        <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
          {loading ? <span className="loading"></span> : (isLogin ? 'Se Connecter' : "Créer mon compte Candidat")}
        </button>
      </form>
      
      <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
        {isLogin ? (
          <>
            Vous êtes un candidat ?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); setIsLogin(false); }} style={{ color: 'var(--secondary)', fontWeight: 600, textDecoration: 'none' }}>
              Créer un compte
            </a>
          </>
        ) : (
          <>
            Déjà un compte ?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); setIsLogin(true); }} style={{ color: 'var(--secondary)', fontWeight: 600, textDecoration: 'none' }}>
              Se connecter
            </a>
          </>
        )}
      </p>
    </section>
  );
};

// Composant ForgotPassword intégré
const ForgotPasswordForm = ({ onBack }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await axios.post(`${API_URL}/forgot-password`, { email });
      setSuccess(true);
      setMessage(response.data.message);
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-section">
      <h2>Mot de passe oublié</h2>
      <p>
        {success 
          ? 'Vérifiez votre boîte email pour réinitialiser votre mot de passe.'
          : 'Entrez votre adresse email pour recevoir un lien de réinitialisation.'}
      </p>
      
      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}
      
      {!success && (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Adresse email</label>
            <input
              type="email"
              className="form-control"
              placeholder="votre@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%' }} 
            disabled={loading}
          >
            {loading ? <span className="loading"></span> : 'Envoyer le lien'}
          </button>
        </form>
      )}
      
      <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
        <a 
          href="#" 
          onClick={(e) => { e.preventDefault(); onBack(); }} 
          style={{ color: 'var(--secondary)', fontWeight: 600, textDecoration: 'none' }}
        >
          ← Retour à la connexion
        </a>
      </p>
    </section>
  );
};

export default Auth;