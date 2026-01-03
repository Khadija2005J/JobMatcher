import { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const Auth = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'recruiter'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const selectRole = (role) => {
    setFormData({ ...formData, role });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/login' : '/register';
      const payload = isLogin
        ? { email: formData.email, password: formData.password }
        : formData;

      const response = await axios.post(`${API_URL}${endpoint}`, payload);
      
      if (response.data.user) {
        onLogin(response.data.user);
      } else if (response.data.user_id) {
        // Registration success
        onLogin({ id: response.data.user_id, name: formData.name, email: formData.email, role: formData.role });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-section">
      <h2>{isLogin ? 'Connexion' : 'Inscription'}</h2>
      <p>{isLogin ? 'Accédez à votre espace personnel' : 'Créez votre compte gratuitement'}</p>
      
      {error && <div className="alert alert-error">{error}</div>}
      
      <form onSubmit={handleSubmit}>
        {!isLogin && (
          <>
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
            <div className="form-group">
              <label>Vous êtes...</label>
              <div className="role-selector">
                <label 
                  className={`role-option ${formData.role === 'recruiter' ? 'active' : ''}`}
                  onClick={() => selectRole('recruiter')}
                >
                  <input type="radio" name="role" value="recruiter" checked={formData.role === 'recruiter'} readOnly />
                  <span className="role-icon">💼</span>
                  <strong>Recruteur</strong>
                </label>
                <label 
                  className={`role-option ${formData.role === 'candidate' ? 'active' : ''}`}
                  onClick={() => selectRole('candidate')}
                >
                  <input type="radio" name="role" value="candidate" checked={formData.role === 'candidate'} readOnly />
                  <span className="role-icon">👤</span>
                  <strong>Candidat</strong>
                </label>
              </div>
            </div>
          </>
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
        
        <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
          {loading ? <span className="loading"></span> : (isLogin ? 'Se Connecter' : "Créer mon compte")}
        </button>
      </form>
      
      <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
        {isLogin ? (
          <>Pas encore de compte ? <a href="#" onClick={(e) => { e.preventDefault(); setIsLogin(false); }} style={{ color: 'var(--secondary)', fontWeight: 600, textDecoration: 'none' }}>Créer un compte</a></>
        ) : (
          <>Déjà un compte ? <a href="#" onClick={(e) => { e.preventDefault(); setIsLogin(true); }} style={{ color: 'var(--secondary)', fontWeight: 600, textDecoration: 'none' }}>Se connecter</a></>
        )}
      </p>
    </section>
  );
};

export default Auth;
