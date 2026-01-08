import { useState, useEffect } from 'react';
import axios from 'axios';
import InterviewCalendar from './InterviewCalendar';
import ReportsExport from './ReportsExport';

const API_URL = 'http://localhost:8000';

const CandidateDashboard = ({ user, onLogout }) => {
  const [currentView, setCurrentView] = useState('offers'); // offers, applications, interviews, reports
  const [offers, setOffers] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [showNotifPanel, setShowNotifPanel] = useState(false);
  const [showFavPanel, setShowFavPanel] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState(null);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [cvFile, setCvFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [notifLoading, setNotifLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterContract, setFilterContract] = useState('');
  const [filterCity, setFilterCity] = useState('');
  const [filterExperience, setFilterExperience] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [appResponse, offersResponse, notifResponse, favResponse] = await Promise.all([
        axios.get(`${API_URL}/candidate/${user.id}/applications`),
        axios.get(`${API_URL}/offers`),
        axios.get(`${API_URL}/users/${user.id}/notifications`),
        axios.get(`${API_URL}/candidate/${user.id}/favorites`)
      ]);
      setMyApplications(appResponse.data);
      setOffers(offersResponse.data);
      setNotifications(notifResponse.data);
      setFavorites(favResponse.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const markAllNotificationsRead = async () => {
    setNotifLoading(true);
    try {
      await axios.post(`${API_URL}/notifications/mark-read`, { user_id: user.id });
      const refreshed = await axios.get(`${API_URL}/users/${user.id}/notifications`);
      setNotifications(refreshed.data);
      setShowNotifPanel(false);
    } catch (error) {
      console.error('Error marking notifications as read:', error);
    } finally {
      setNotifLoading(false);
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

  const isFavorite = (offerId) => favorites.some(fav => fav.id === offerId);

  const toggleFavoriteOffer = async (offerId) => {
    try {
      await axios.post(`${API_URL}/favorites/toggle`, { candidate_id: user.id, offer_id: offerId });
      const refreshed = await axios.get(`${API_URL}/candidate/${user.id}/favorites`);
      setFavorites(refreshed.data);
    } catch (error) {
      console.error('Error updating favorite:', error);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const filteredOffers = offers.filter(offer => {
    const matchSearch = !searchTerm || 
      offer.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (offer.description && offer.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchContract = !filterContract || offer.contract === filterContract;
    const matchCity = !filterCity || (offer.city && offer.city.toLowerCase().includes(filterCity.toLowerCase()));
    const matchExperience = !filterExperience || (offer.experience && offer.experience.toLowerCase().includes(filterExperience.toLowerCase()));
    return matchSearch && matchContract && matchCity && matchExperience;
  });

  const contractTypes = ['CDI', 'CDD', 'Stage', 'Alternance', 'Freelance', 'Intérim', 'Temps partiel'];
  const cities = ['Casablanca', 'Rabat', 'Marrakech', 'Fès', 'Tanger', 'Agadir', 'Meknès', 'Oujda', 'Kenitra', 'Tétouan', 'Safi', 'Mohammedia', 'El Jadida'];

  return (
    <section className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>Tableau de bord Candidat</h1>
              <p style={{ fontSize: '1.05em', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Bienvenue <span style={{ fontWeight: '600', color: 'var(--accent)' }}>{user.name}</span> !
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', position: 'relative' }}>
              <button
                className="btn btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', position: 'relative' }}
                onClick={() => setShowNotifPanel(prev => !prev)}
              >
                <span role="img" aria-label="Notifications">🔔</span>
                {unreadCount > 0 && (
                  <span className="badge badge-danger" style={{ position: 'absolute', top: '-0.35rem', right: '-0.35rem' }}>
                    {unreadCount}
                  </span>
                )}
              </button>
              <button
                className="btn btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', position: 'relative' }}
                onClick={() => setShowFavPanel(prev => !prev)}
              >
                <span role="img" aria-label="Favoris">⭐</span>
                {favorites.length > 0 && (
                  <span className="badge badge-warning" style={{ position: 'absolute', top: '-0.35rem', right: '-0.35rem' }}>
                    {favorites.length}
                  </span>
                )}
              </button>
              <button className="btn btn-secondary" onClick={onLogout}>Déconnexion</button>

              {showNotifPanel && (
                <div
                  className="card"
                  style={{ position: 'absolute', right: 0, top: '3.25rem', width: '340px', zIndex: 5, boxShadow: '0 12px 30px rgba(0,0,0,0.15)' }}
                >
                  <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 className="card-title" style={{ margin: 0 }}>Notifications</h2>
                    <button className="btn btn-secondary" onClick={markAllNotificationsRead} disabled={notifLoading}>
                      {notifLoading ? '...' : 'Tout lu'}
                    </button>
                  </div>
                  <div style={{ maxHeight: '340px', overflowY: 'auto' }}>
                    {notifications.length === 0 ? (
                      <div className="empty-state" style={{ padding: '1rem 1.25rem' }}>
                        <div className="empty-state-icon">🔔</div>
                        <p>Aucune notification pour le moment.</p>
                      </div>
                    ) : (
                      notifications.map((n) => {
                        let bgColor = 'var(--bg-secondary)';
                        let borderColor = 'transparent';
                        let badgeColor = 'badge-blue';
                        
                        if (!n.is_read) {
                          if (n.notif_type === 'success') {
                            bgColor = 'rgba(76, 175, 80, 0.08)';
                            borderColor = '#4CAF50';
                            badgeColor = 'badge-success';
                          } else if (n.notif_type === 'warning') {
                            bgColor = 'rgba(255, 152, 0, 0.08)';
                            borderColor = '#FF9800';
                            badgeColor = 'badge-warning';
                          } else if (n.notif_type === 'application') {
                            bgColor = 'var(--bg-accent-light)';
                            borderColor = 'var(--accent)';
                            badgeColor = 'badge-blue';
                          } else {
                            bgColor = 'var(--bg-accent-light)';
                            borderColor = 'var(--accent)';
                          }
                        }
                        
                        return (
                          <div
                            key={n.id}
                            className="candidate-card"
                            style={{ 
                              background: bgColor, 
                              marginBottom: '0.75rem',
                              borderLeft: borderColor !== 'transparent' ? `3px solid ${borderColor}` : 'none'
                            }}
                          >
                            <div className="candidate-info">
                              <h4 style={{ marginBottom: '0.35rem', fontWeight: n.is_read ? 'normal' : 'bold' }}>{n.title}</h4>
                              <p style={{ color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>{n.message}</p>
                              {!n.is_read && <span className={`badge ${badgeColor}`}>Nouveau</span>}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}

              {showFavPanel && (
                <div
                  className="card"
                  style={{ position: 'absolute', right: 0, top: '3.25rem', width: '380px', zIndex: 5, boxShadow: '0 12px 30px rgba(0,0,0,0.15)' }}
                >
                  <div className="card-header">
                    <h2 className="card-title" style={{ margin: 0 }}>Mes Favoris</h2>
                  </div>
                  <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
                    {favorites.length === 0 ? (
                      <div className="empty-state" style={{ padding: '1rem 1.25rem' }}>
                        <div className="empty-state-icon">⭐</div>
                        <p>Aucun favori. Ajoutez des offres !</p>
                      </div>
                    ) : (
                      favorites.map(fav => (
                        <div key={fav.id} className="candidate-card" style={{ marginBottom: '0.75rem' }}>
                          <div className="candidate-info">
                            <h4 style={{ marginBottom: '0.35rem' }}>{fav.title}</h4>
                            <div className="offer-meta" style={{ margin: '0.35rem 0' }}>
                              <span className="badge badge-blue">{fav.contract}</span>
                              <span className="badge badge-cyan">{fav.recruiter}</span>
                              {fav.city && <span className="badge badge-secondary">{fav.city}</span>}
                            </div>
                            <p style={{ color: 'var(--text-secondary)', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
                              {fav.description ? fav.description.substring(0, 100) + '...' : 'Aucune description'}
                            </p>
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                              <button className="btn btn-secondary" style={{ fontSize: '0.85rem', padding: '0.4rem 0.75rem' }} onClick={() => toggleFavoriteOffer(fav.id)}>
                                Retirer
                              </button>
                              <button
                                className="btn btn-accent"
                                style={{ fontSize: '0.85rem', padding: '0.4rem 0.75rem' }}
                                onClick={() => { openApplyModal(fav); setShowFavPanel(false); }}
                                disabled={hasApplied(fav.id)}
                              >
                                {hasApplied(fav.id) ? 'Déjà postulé' : 'Postuler'}
                              </button>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
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
              <div className="workflow-step-icon">📬</div>
              <div className="workflow-step-text">Réponse recruteur</div>
            </div>
          </div>
        </div>

        {/* Navigation par onglets */}
        <div style={{ marginTop: '20px', marginBottom: '20px', borderBottom: '2px solid #e5e7eb' }}>
          <div style={{ display: 'flex', gap: '0' }}>
            <button
              onClick={() => setCurrentView('offers')}
              style={{
                padding: '12px 24px',
                background: currentView === 'offers' ? 'white' : 'transparent',
                border: 'none',
                borderBottom: currentView === 'offers' ? '3px solid var(--accent)' : '3px solid transparent',
                fontWeight: currentView === 'offers' ? '600' : 'normal',
                color: currentView === 'offers' ? 'var(--accent)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '15px'
              }}
            >
              💼 Offres d'emploi
            </button>
            <button
              onClick={() => setCurrentView('applications')}
              style={{
                padding: '12px 24px',
                background: currentView === 'applications' ? 'white' : 'transparent',
                border: 'none',
                borderBottom: currentView === 'applications' ? '3px solid var(--accent)' : '3px solid transparent',
                fontWeight: currentView === 'applications' ? '600' : 'normal',
                color: currentView === 'applications' ? 'var(--accent)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '15px'
              }}
            >
              📬 Mes Candidatures
            </button>
            <button
              onClick={() => setCurrentView('interviews')}
              style={{
                padding: '12px 24px',
                background: currentView === 'interviews' ? 'white' : 'transparent',
                border: 'none',
                borderBottom: currentView === 'interviews' ? '3px solid var(--accent)' : '3px solid transparent',
                fontWeight: currentView === 'interviews' ? '600' : 'normal',
                color: currentView === 'interviews' ? 'var(--accent)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '15px'
              }}
            >
              📅 Entretiens
            </button>
            <button
              onClick={() => setCurrentView('reports')}
              style={{
                padding: '12px 24px',
                background: currentView === 'reports' ? 'white' : 'transparent',
                border: 'none',
                borderBottom: currentView === 'reports' ? '3px solid var(--accent)' : '3px solid transparent',
                fontWeight: currentView === 'reports' ? '600' : 'normal',
                color: currentView === 'reports' ? 'var(--accent)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '15px'
              }}
            >
              📊 Mes Statistiques
            </button>
          </div>
        </div>

        {/* Affichage conditionnel selon la vue */}
        {currentView === 'interviews' && (
          <InterviewCalendar user={user} />
        )}

        {currentView === 'reports' && (
          <ReportsExport user={user} />
        )}

        {currentView === 'applications' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Mes Candidatures ({myApplications.length})</h2>
            </div>
            {myApplications.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📭</div>
                <p>Aucune candidature envoyée pour le moment.</p>
              </div>
            ) : (
              myApplications.map((app) => (
                <div key={app.id} className="candidate-card">
                  <div className="candidate-info">
                    <h4>{app.job_title}</h4>
                    <div className="offer-meta">
                      <span className="badge badge-blue">{app.contract}</span>
                      <span className={`badge ${app.status === 'pending' ? 'badge-warning' : app.status === 'accepted' ? 'badge-success' : 'badge-danger'}`}>
                        {app.status === 'pending' ? 'En attente' : app.status === 'accepted' ? 'Acceptée' : 'Refusée'}
                      </span>
                      <span className="badge badge-secondary">{new Date(app.applied_at).toLocaleDateString('fr-FR')}</span>
                    </div>
                    {app.justification && <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>{app.justification}</p>}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {currentView === 'offers' && (
          <>
            {/* Filters */}
            <div className="card">
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  placeholder="🔍 Rechercher une offre..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="form-control"
                  style={{ flex: '1 1 250px' }}
                />
                <select className="form-control" value={filterContract} onChange={(e) => setFilterContract(e.target.value)} style={{ flex: '1 1 150px' }}>
                  <option value="">Tous les contrats</option>
                  <option value="CDI">CDI</option>
                  <option value="CDD">CDD</option>
                  <option value="Stage">Stage</option>
                  <option value="Alternance">Alternance</option>
                  <option value="Freelance">Freelance</option>
                </select>
                <input
                  type="text"
                  placeholder="📍 Ville..."
                  value={filterCity}
                  onChange={(e) => setFilterCity(e.target.value)}
                  className="form-control"
                  style={{ flex: '1 1 150px' }}
                />
                <input
                  type="text"
                  placeholder="🎓 Expérience..."
                  value={filterExperience}
                  onChange={(e) => setFilterExperience(e.target.value)}
                  className="form-control"
                  style={{ flex: '1 1 150px' }}
                />
              </div>

              {(searchTerm || filterContract || filterCity || filterExperience) && (
                <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {filteredOffers.length} offre(s) trouvée(s)
                  </span>
                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: '0.85rem', padding: '0.25rem 0.75rem' }}
                    onClick={() => {
                      setSearchTerm('');
                      setFilterContract('');
                      setFilterCity('');
                      setFilterExperience('');
                    }}
                  >
                    Réinitialiser
                  </button>
                </div>
              )}
            </div>
          
            <div className="offers-grid">
            {filteredOffers.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🔍</div>
                <p>{offers.length === 0 ? 'Aucune offre disponible pour le moment. Revenez plus tard !' : 'Aucune offre ne correspond à vos critères.'}</p>
              </div>
            ) : (
              filteredOffers.map(offer => (
                <div key={offer.id} className="offer-card">
                  <div className="offer-title">{offer.title}</div>
                  <div className="offer-meta">
                    <span className="badge badge-blue">{offer.contract}</span>
                    <span className="badge badge-cyan">{offer.recruiter}</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', margin: '1rem 0', fontSize: '0.9rem', lineHeight: '1.5' }}>
                    {offer.description ? offer.description.substring(0, 120) + '...' : 'Aucune description'}
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <button
                      className="btn btn-secondary"
                      onClick={() => toggleFavoriteOffer(offer.id)}
                    >
                      {isFavorite(offer.id) ? '★ Retirer' : '☆ Favori'}
                    </button>
                    <button 
                      className="btn btn-accent" 
                      onClick={() => openApplyModal(offer)}
                      disabled={hasApplied(offer.id)}
                    >
                      {hasApplied(offer.id) ? 'Déjà postulé' : 'Postuler avec mon CV'}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* Apply Modal */}
      {showApplyModal && selectedOffer && (
        <div className="modal active" onClick={(e) => e.target.className === 'modal active' && setShowApplyModal(false)}>
          <div className="modal-content">
            <button className="modal-close" onClick={() => setShowApplyModal(false)}>×</button>
            <h2>Postuler à l'offre</h2>
            <div id="offerDetails" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: '0.75rem', border: '1px solid var(--border-light)' }}>
              <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>{selectedOffer.title}</h3>
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
      </div>
    </section>
  );
};

export default CandidateDashboard;
