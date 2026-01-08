import { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const ForgotPassword = ({ onBackToLogin }) => {
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
          onClick={(e) => { e.preventDefault(); onBackToLogin(); }} 
          style={{ color: 'var(--secondary)', fontWeight: 600, textDecoration: 'none' }}
        >
          ← Retour à la connexion
        </a>
      </p>
    </section>
  );
};

export default ForgotPassword;
