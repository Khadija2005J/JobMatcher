import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const RecruiterDashboard = ({ user, onLogout }) => {
  const [offers, setOffers] = useState([]);
  const [applications, setApplications] = useState([]);
  const [selectedOfferId, setSelectedOfferId] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showApplicationsModal, setShowApplicationsModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedApplications, setSelectedApplications] = useState(new Set());
  
  const [draftData, setDraftData] = useState({
    title: '',
    city: '',
    contract: 'CDI',
    experience: '',
    education: '',
    technical_skills: '',
    missions: '',
    salary: '',
    work_mode: 'Présentiel',
    soft_skills: ''
  });
  const [aiDescription, setAiDescription] = useState('');
  const [draftOfferId, setDraftOfferId] = useState(null);
  const [expandedOffers, setExpandedOffers] = useState(new Set());
  const [applicationsAlert, setApplicationsAlert] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await axios.get(`${API_URL}/recruiter/${user.id}/offers`);
      setOffers(response.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const handleCreateDraft = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/offers/draft`, {
        ...draftData,
        recruiter_id: user.id
      });
      
      setAiDescription(response.data.description);
      setShowCreateModal(false);
      setShowEditModal(true);
      // Ajouter un aperçu brouillon dans la liste pour affichage immédiat
      const tempId = `draft-${Date.now()}`;
      const draftOffer = {
        id: tempId,
        title: draftData.title || response.data.title || 'Brouillon',
        contract: draftData.contract,
        status: 'draft',
        created_at: new Date().toISOString(),
        description: response.data.description
      };
      setDraftOfferId(tempId);
      setOffers(prev => [draftOffer, ...prev]);
    } catch (error) {
      alert("Erreur lors de la génération par l'IA");
    } finally {
      setLoading(false);
    }
  }; 

  const closeEditModal = () => {
    setShowEditModal(false);
    // Retirer l'aperçu brouillon si l'utilisateur annule
    if (draftOfferId) {
      setOffers(prev => prev.filter(o => o.id !== draftOfferId));
      setDraftOfferId(null);
      setAiDescription('');
    }
  };

  // Toggle the expanded state for a given offer (voir plus / voir moins)
  const toggleExpand = (offerId) => {
    setExpandedOffers(prev => {
      const setCopy = new Set(Array.from(prev));
      const key = String(offerId);
      if (setCopy.has(key)) setCopy.delete(key);
      else setCopy.add(key);
      return setCopy;
    });
  };

  // Alert helper for applications modal
  const showApplicationsAlert = (message, type = 'success') => {
    setApplicationsAlert({ message, type });
    setTimeout(() => setApplicationsAlert(null), 4000);
  };

  // Accept single application (uses the same endpoint as multiple)
  const acceptApplication = async (applicationId) => {
    if (!confirm(`Êtes-vous sûr de vouloir accepter ce candidat ? Les autres candidats recevront un email de refus et l'offre sera fermée.`)) return;

    const formData = new FormData();
    formData.append('application_ids', applicationId);

    try {
      const response = await axios.post(`${API_URL}/offers/${selectedOfferId}/accept-multiple`, formData);
      showApplicationsAlert(`✅ ${response.data.accepted_count} candidat(s) accepté(s), ${response.data.rejected_count} refusé(s). ${response.data.emails_sent} emails envoyés.`, 'success');
      // Refresh applications list and dashboard
      const resp = await axios.get(`${API_URL}/offers/${selectedOfferId}/applications`);
      setApplications(resp.data);
      loadDashboard();
    } catch (error) {
      console.error('Accept error:', error);
      showApplicationsAlert('Erreur lors de l\'acceptation', 'error');
    }
  };

  // Reject single application
  const rejectApplication = async (applicationId) => {
    if (!confirm(`Confirmer le refus de ce candidat ?`)) return;

    try {
      const response = await axios.post(`${API_URL}/offers/${selectedOfferId}/reject-multiple`, {
        application_ids: [applicationId]
      }, {
        headers: { 'Content-Type': 'application/json' }
      });
      showApplicationsAlert(`❌ ${response.data.message || 'Refus envoyé'}. ${response.data.emails_sent || 0} email(s) transmis.`, 'success');
      const resp = await axios.get(`${API_URL}/offers/${selectedOfferId}/applications`);
      setApplications(resp.data);
      loadDashboard();
    } catch (error) {
      console.error('Reject error:', error);
      showApplicationsAlert('Erreur lors du refus', 'error');
    }
  };

  const handlePublish = async (e) => {
    e.preventDefault();
    
    try {
      const response = await axios.post(`${API_URL}/offers/publish`, {
        ...draftData,
        description: aiDescription,
        skills: draftData.technical_skills,
        recruiter_id: user.id
      });
      
      alert("✅ Offre publiée avec succès !");
      setShowEditModal(false);
      setAiDescription('');
      setDraftData({
        title: '', city: '', contract: 'CDI', experience: '',
        education: '', technical_skills: '', missions: '', salary: '',
        work_mode: 'Présentiel', soft_skills: ''
      });
      // Si l'API renvoie l'offre créée, on remplace le brouillon par l'offre réelle pour un rendu propre
      if (response.data.offer) {
        if (draftOfferId) {
          setOffers(prev => prev.map(o => o.id === draftOfferId ? response.data.offer : o));
          setDraftOfferId(null);
        } else {
          setOffers(prev => [response.data.offer, ...prev]);
        }
      } else {
        loadDashboard();
      }
    } catch (error) {
      alert("Erreur lors de la publication");
    }
  };

  const viewApplications = async (offerId) => {
    setSelectedOfferId(offerId);
    setSelectedApplications(new Set());
    
    try {
      const response = await axios.get(`${API_URL}/offers/${offerId}/applications`);
      setApplications(response.data);
      setShowApplicationsModal(true);
    } catch (error) {
      console.error('Error loading applications:', error);
      alert("Impossible de charger les candidatures");
    }
  };

  const toggleSelection = (applicationId) => {
    const newSet = new Set(selectedApplications);
    if (newSet.has(applicationId)) {
      newSet.delete(applicationId);
    } else {
      newSet.add(applicationId);
    }
    setSelectedApplications(newSet);
  };

  const acceptSelected = async () => {
    if (selectedApplications.size === 0) {
      showApplicationsAlert('Veuillez sélectionner au moins un candidat', 'error');
      return;
    }

    const selectedIds = Array.from(selectedApplications);
    const selectedNames = applications.filter(a => selectedIds.includes(a.id)).map(a => a.candidate_name);
    const namesPreview = selectedNames.length > 5 ? `${selectedNames.slice(0,5).join(', ')} et ${selectedNames.length - 5} autres` : selectedNames.join(', ');

    if (!confirm(`Êtes-vous sûr de vouloir accepter ${selectedIds.length} candidat(s) (${namesPreview}) ? Les autres candidats recevront automatiquement un email de refus et l'offre sera fermée.`)) {
      return;
    }

    const formData = new FormData();
    selectedIds.forEach(id => formData.append('application_ids', id));

    try {
      const response = await axios.post(`${API_URL}/offers/${selectedOfferId}/accept-multiple`, formData);
      showApplicationsAlert(`✅ ${response.data.accepted_count} candidat(s) accepté(s), ${response.data.rejected_count} refusé(s). ${response.data.emails_sent} emails envoyés.`, 'success');
      setShowApplicationsModal(false);
      setSelectedApplications(new Set());
      loadDashboard();
    } catch (error) {
      showApplicationsAlert('Erreur lors de l\'acceptation', 'error');
    }
  };

  const rejectSelected = async () => {
    if (selectedApplications.size === 0) {
      showApplicationsAlert('Veuillez sélectionner au moins un candidat', 'error');
      return;
    }

    if (!confirm(`Confirmer le refus de ${selectedApplications.size} candidat(s) ?`)) {
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/offers/${selectedOfferId}/reject-multiple`, {
        application_ids: Array.from(selectedApplications)
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      showApplicationsAlert(`❌ ${response.data.message || `${selectedApplications.size} refus envoyé(s)`}. ${response.data.emails_sent || 0} email(s) transmis.`, 'success');
      setShowApplicationsModal(false);
      loadDashboard();
    } catch (error) {
      console.error('Reject error:', error);
      showApplicationsAlert('Erreur lors du refus: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const activeOffers = offers.filter(o => o.status === 'active').length;

  return (
    <section className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>Tableau de bord Recruteur</h1>
              <p>Bienvenue {user.name} !</p>
            </div>
            <button className="btn btn-secondary" onClick={onLogout}>Déconnexion</button>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Offres</div>
            <div className="stat-value">{offers.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Offres Actives</div>
            <div className="stat-value">{activeOffers}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Offres Fermées</div>
            <div className="stat-value">{offers.length - activeOffers}</div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Mes Offres d'Emploi</h2>
            <button className="btn btn-accent" onClick={() => setShowCreateModal(true)}>
              + Créer une offre
            </button>
          </div>
          <div className="offers-grid">
            {offers.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📋</div>
                <p>Aucune offre créée. Cliquez sur "Créer une offre" pour commencer !</p>
              </div>
            ) : (
              offers.map(offer => (
                <div key={offer.id} className="offer-card">
                  <div className="offer-title">{offer.title}</div>
                  {offer.description && (
                    <div className="offer-description" style={{ marginTop: '10px', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                      {expandedOffers.has(String(offer.id)) ? (
                        offer.description
                      ) : (
                        offer.description.length > 250 ? offer.description.substring(0, 250) + '...' : offer.description
                      )}
                      {offer.description.length > 250 && (
                        <div style={{ marginTop: '6px' }}>
                          <button
                            type="button"
                            className="btn btn-link"
                            onClick={() => toggleExpand(offer.id)}
                            style={{ padding: 0, border: 'none', background: 'none', color: 'var(--accent)', cursor: 'pointer' }}
                          >
                            {expandedOffers.has(String(offer.id)) ? 'Voir moins' : 'Voir plus'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                  <div className="offer-meta">
                    <span className="badge badge-blue">{offer.contract}</span>
                    <span className={`badge ${offer.status === 'active' ? 'badge-success' : offer.status === 'draft' ? 'badge-warning' : 'badge-gray'}`}>
                      {offer.status === 'active' ? 'Active' : offer.status === 'draft' ? 'Brouillon' : 'Fermée'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                    <button className="btn btn-accent" onClick={() => viewApplications(offer.id)}>
                      Voir les candidatures
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Create Offer Modal */}
      {showCreateModal && (
        <div className="modal active" onClick={(e) => e.target.className === 'modal active' && setShowCreateModal(false)}>
          <div className="modal-content" style={{ maxWidth: '600px' }}>
            <button className="modal-close" onClick={() => setShowCreateModal(false)}>×</button>
            <h2>Créer une nouvelle offre</h2>
            <form onSubmit={handleCreateDraft}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Titre du poste</label>
                  <input type="text" className="form-control" value={draftData.title} onChange={(e) => setDraftData({...draftData, title: e.target.value})} required placeholder="Ex: Développeur Full Stack" />
                </div>
                <div className="form-group">
                  <label>Ville</label>
                  <input type="text" className="form-control" value={draftData.city} onChange={(e) => setDraftData({...draftData, city: e.target.value})} required placeholder="Ex: Paris" />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Type de contrat</label>
                  <select className="form-control" value={draftData.contract} onChange={(e) => setDraftData({...draftData, contract: e.target.value})} required>
                    <option value="CDI">CDI</option>
                    <option value="CDD">CDD</option>
                    <option value="Stage">Stage</option>
                    <option value="Freelance">Freelance</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Mode de travail</label>
                  <select className="form-control" value={draftData.work_mode} onChange={(e) => setDraftData({...draftData, work_mode: e.target.value})}>
                    <option value="Présentiel">Présentiel</option>
                    <option value="Hybride">Hybride</option>
                    <option value="Télétravail">Full Remote</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Expérience</label>
                  <input type="text" className="form-control" value={draftData.experience} onChange={(e) => setDraftData({...draftData, experience: e.target.value})} placeholder="Ex: 3-5 ans" />
                </div>
                <div className="form-group">
                  <label>Éducation</label>
                  <input type="text" className="form-control" value={draftData.education} onChange={(e) => setDraftData({...draftData, education: e.target.value})} placeholder="Ex: Bac +5" />
                </div>
              </div>

              <div className="form-group">
                <label>Compétences Techniques</label>
                <input type="text" className="form-control" value={draftData.technical_skills} onChange={(e) => setDraftData({...draftData, technical_skills: e.target.value})} required placeholder="Ex: Python, React, SQL" />
              </div>

              <div className="form-group">
                <label>Missions principales</label>
                <textarea className="form-control" value={draftData.missions} onChange={(e) => setDraftData({...draftData, missions: e.target.value})} rows="3" placeholder="Décrivez les tâches..."></textarea>
              </div>

              <details style={{ marginBottom: '15px', cursor: 'pointer' }}>
                <summary>Plus d'options (Salaire, Avantages...)</summary>
                <div style={{ paddingTop: '10px' }}>
                  <div className="form-group">
                    <label>Soft Skills</label>
                    <input type="text" className="form-control" value={draftData.soft_skills} onChange={(e) => setDraftData({...draftData, soft_skills: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>Salaire</label>
                    <input type="text" className="form-control" value={draftData.salary} onChange={(e) => setDraftData({...draftData, salary: e.target.value})} placeholder="Ex: 45k - 55k €" />
                  </div>
                </div>
              </details>

              <button type="submit" className="btn btn-accent" style={{ width: '100%' }} disabled={loading}>
                {loading ? <span className="loading"></span> : "Générer l'annonce détaillée avec l'IA"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Edit/Publish Modal */}
      {showEditModal && (
        <div className="modal active" onClick={(e) => e.target.className === 'modal active' && closeEditModal()}>
          <div className="modal-content">
            <button className="modal-close" onClick={closeEditModal}>×</button>
            <h2>Modifier et publier l'annonce</h2>
            <form onSubmit={handlePublish}>
              <div className="form-group">
                <label>Description de l'annonce (générée par l'IA - modifiable)</label>
                <textarea className="form-control" value={aiDescription} onChange={(e) => setAiDescription(e.target.value)} required style={{ minHeight: '200px' }}></textarea>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={closeEditModal} style={{ flex: 1 }}>Annuler</button>
                <button type="submit" className="btn btn-success" style={{ flex: 1 }}>Publier l'offre</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Applications Modal */}
      {showApplicationsModal && (
        <div className="modal active" onClick={(e) => e.target.className === 'modal active' && setShowApplicationsModal(false)}>
          <div className="modal-content large">
            <button className="modal-close" onClick={() => setShowApplicationsModal(false)}>×</button>

            <h2>Candidatures reçues</h2>
            {applicationsAlert && (
              <div style={{ marginBottom: '12px', padding: '10px', borderRadius: '6px', background: applicationsAlert.type === 'success' ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)', color: applicationsAlert.type === 'success' ? '#065f46' : '#7f1d1d' }}>
                {applicationsAlert.message}
              </div>
            )}

            {selectedApplications.size > 0 && (
              <div className="selection-actions" style={{ marginBottom: '12px' }}>
                <span>{selectedApplications.size} candidat(s) sélectionné(s)</span>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Les candidats non sélectionnés recevront automatiquement un email de refus.</div>
                  <button className="btn btn-success" onClick={acceptSelected}>Accepter la sélection</button>
                </div>
              </div>
            )}

            <div>
              {applications.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📭</div>
                  <p>Aucune candidature pour le moment.</p>
                </div>
              ) : (
                applications.map((app, index) => (
                  <div key={app.id} className="candidate-card">
                    <input
                      type="checkbox"
                      id={`app-${app.id}`}
                      checked={selectedApplications.has(app.id)}
                      onChange={() => toggleSelection(app.id)}
                      disabled={app.status !== 'pending'}
                    />
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', width: '100%' }}>
                      <div style={{ flex: 1 }}>
                        <div className="candidate-info">
                          <h4>{index + 1}. {app.candidate_name}</h4>
                          <p style={{ color: 'var(--text-secondary)' }}>{app.candidate_email}</p>
                          <p style={{ color: 'var(--text-primary)', marginTop: '0.5rem' }}>{app.justification}</p>
                          <span className={`badge ${app.status === 'accepted' ? 'badge-success' : app.status === 'rejected' ? 'badge-danger' : 'badge-warning'}`} style={{ marginTop: '0.5rem' }}>
                            {app.status === 'pending' ? 'En attente' : app.status === 'accepted' ? 'Accepté' : 'Refusé'}
                          </span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                        <div className="candidate-score">{Math.round(app.score)}%</div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default RecruiterDashboard;
