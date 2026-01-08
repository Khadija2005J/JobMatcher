import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const ResetPassword = () => {
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Extraire le token de l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    
    if (tokenFromUrl) {
      setToken(tokenFromUrl);
    } else {
      setError('Token de réinitialisation manquant ou invalide');
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (newPassword.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/reset-password`, {
        token,
        new_password: newPassword
      });
      
      setSuccess(true);
      setError('');
      
      // Rediriger vers la page de connexion après 3 secondes
      setTimeout(() => {
        window.location.href = '/';
      }, 3000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  };

  if (!token && !error) {
    return (
      <section className="auth-section">
        <h2>Chargement...</h2>
      </section>
    );
  }

  return (
    <section className="auth-section">
      <h2>Réinitialiser votre mot de passe</h2>
      <p>Choisissez un nouveau mot de passe pour votre compte.</p>
      
      {error && <div className="alert alert-error">{error}</div>}
      {success && (
        <div className="alert alert-success">
          ✅ Votre mot de passe a été réinitialisé avec succès ! 
          <br />
          Redirection vers la connexion...
        </div>
      )}
      
      {!success && token && (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Nouveau mot de passe</label>
            <input
              type="password"
              className="form-control"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
            />
            <small style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Minimum 6 caractères
            </small>
          </div>
          
          <div className="form-group">
            <label>Confirmer le mot de passe</label>
            <input
              type="password"
              className="form-control"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%' }} 
            disabled={loading}
          >
            {loading ? <span className="loading"></span> : 'Réinitialiser le mot de passe'}
          </button>
        </form>
      )}
      
      {!success && (
        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          <a 
            href="/" 
            style={{ color: 'var(--secondary)', fontWeight: 600, textDecoration: 'none' }}
          >
            ← Retour à la connexion
          </a>
        </p>
      )}
    </section>
  );
};

export default ResetPassword;
