import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const CandidateDashboard = ({ user, onLogout }) => {
  const [offers, setOffers] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [selectedOffer, setSelectedOffer] = useState(null);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [cvFile, setCvFile] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [appResponse, offersResponse] = await Promise.all([
        axios.get(`${API_URL}/candidate/${user.id}/applications`),
        axios.get(`${API_URL}/offers`)
      ]);
      setMyApplications(appResponse.data);
      setOffers(offersResponse.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const openApplyModal = (offer) => {
    setSelectedOffer(offer);
    setShowApplyModal(true);
  };

  const handleApply = async (e) => {
    e.preventDefault();
    
    if (!cvFile) {
      alert('Veuillez sélectionner un CV');
      return;
    }

    if (!cvFile.name.toLowerCase().endsWith('.pdf')) {
      alert('Seuls les fichiers PDF sont acceptés');
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('candidate_id', user.id);
    formData.append('offer_id', selectedOffer.id);
    formData.append('file', cvFile);

    try {
      const response = await axios.post(`${API_URL}/apply`, formData);
      alert(response.data.message);

      setShowApplyModal(false);
      setCvFile(null);
      setSelectedOffer(null);
      loadDashboard();
    } catch (error) {
      alert(error.response?.data?.detail || 'Erreur lors de la candidature');
    } finally {
      setLoading(false);
    }
  };

  const hasApplied = (offerId) => {
    return myApplications.some(app => app.offer_id === offerId);
  };

  return (
    <section className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>Tableau de bord Candidat</h1>
              <p>Bienvenue {user.name} !</p>
            </div>
            <button className="btn btn-secondary" onClick={onLogout}>Déconnexion</button>
          </div>
        </div>

        <div className="info-section">
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>💡</div>
          <h3>Comment postuler aux offres ?</h3>
          <p>Pour chaque offre qui vous intéresse, cliquez sur "Postuler" et uploadez votre CV en PDF. Notre IA analysera automatiquement votre profil et le recruteur pourra voir votre score de compatibilité.</p>
          
          <div className="workflow-steps">
            <div className="workflow-step">
              <div className="workflow-step-icon">📋</div>
              <div className="workflow-step-text">Choisir une offre</div>
            </div>
            <div className="workflow-arrow">→</div>
            <div className="workflow-step">
              <div className="workflow-step-icon">📄</div>
              <div className="workflow-step-text">Upload CV (PDF)</div>
            </div>
            <div className="workflow-arrow">→</div>
            <div className="workflow-step">
              <div className="workflow-step-icon">🤖</div>
              <div className="workflow-step-text">Analyse IA</div>
            </div>
            <div className="workflow-arrow">→</div>
            <div className="workflow-step">
              <div className="workflow-step-icon">✅</div>
              <div className="workflow-step-text">Candidature envoyée</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Mes Candidatures</h2>
          </div>
          <div>
            {myApplications.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📝</div>
                <p>Vous n'avez pas encore postulé à une offre. Parcourez les offres disponibles ci-dessous !</p>
              </div>
            ) : (
              myApplications.map(app => (
                <div key={app.id} className="candidate-card">
                  <div className="candidate-info">
                    <h4>{app.job_title}</h4>
                    <p style={{ color: 'var(--text-secondary)' }}>{app.contract}</p>
                    <span className={`badge ${app.status === 'accepted' ? 'badge-success' : app.status === 'rejected' ? 'badge-danger' : 'badge-warning'}`} style={{ marginTop: '0.5rem' }}>
                      {app.status === 'pending' ? 'En attente' : app.status === 'accepted' ? '✓ Accepté' : '✗ Refusé'}
                    </span>
                    {typeof app.score !== 'undefined' && (
                      <div style={{ marginTop: '0.75rem', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                        <div style={{ fontWeight: 700, color: 'var(--accent)', fontSize: '1.15rem' }}>{Math.round(app.score)}%</div>
                        <div style={{ color: 'var(--text-primary)', lineHeight: 1.4 }}>{app.justification}</div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Offres Disponibles</h2>
          </div>
          <div className="offers-grid">
            {offers.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🔍</div>
                <p>Aucune offre disponible pour le moment. Revenez plus tard !</p>
              </div>
            ) : (
              offers.map(offer => (
                <div key={offer.id} className="offer-card">
                  <div className="offer-title">{offer.title}</div>
                  <div className="offer-meta">
                    <span className="badge badge-blue">{offer.contract}</span>
                    <span className="badge badge-cyan">{offer.recruiter}</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', margin: '1rem 0', fontSize: '0.9rem', lineHeight: '1.5' }}>
                    {offer.description ? offer.description.substring(0, 120) + '...' : 'Aucune description'}
                  </p>
                  <button 
                    className="btn btn-accent" 
                    onClick={() => openApplyModal(offer)}
                    disabled={hasApplied(offer.id)}
                  >
                    {hasApplied(offer.id) ? 'Déjà postulé' : 'Postuler avec mon CV'}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Apply Modal */}
      {showApplyModal && selectedOffer && (
        <div className="modal active" onClick={(e) => e.target.className === 'modal active' && setShowApplyModal(false)}>
          <div className="modal-content">
            <button className="modal-close" onClick={() => setShowApplyModal(false)}>×</button>
            <h2>Postuler à l'offre</h2>
            <div id="offerDetails" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '0.75rem', border: '1px solid var(--border-light)' }}>
              <h3 style={{ fontFamily: "'Bricolage Grotesque', sans-serif", marginBottom: '1rem', fontSize: '1.25rem' }}>{selectedOffer.title}</h3>
              <p style={{ color: 'var(--text-primary)', whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{selectedOffer.description}</p>
            </div>
            <form onSubmit={handleApply}>
              <div className="form-group">
                <label>Télécharger votre CV (PDF)</label>
                <div className="file-upload" onClick={() => document.getElementById('cvFile').click()}>
                  <input 
                    type="file" 
                    id="cvFile" 
                    accept=".pdf" 
                    onChange={(e) => setCvFile(e.target.files[0])}
                    style={{ display: 'none' }}
                    required
                  />
                  <div className="file-upload-icon">📎</div>
                  <p>Cliquez pour sélectionner votre CV en PDF</p>
                  {cvFile && <p className="file-name">✓ {cvFile.name}</p>}
                </div>
              </div>
              <button type="submit" className="btn btn-accent" style={{ width: '100%' }} disabled={loading}>
                {loading ? <span className="loading"></span> : "Envoyer ma candidature"}
              </button>
            </form>
          </div>
        </div>
      )}
    </section>
  );
};

export default CandidateDashboard;
