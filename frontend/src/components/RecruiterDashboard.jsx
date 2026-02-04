import { useState, useEffect } from 'react';
import axios from 'axios';
import InterviewCalendar from './InterviewCalendar';
import ReportsExport from './ReportsExport';

const API_URL = 'http://localhost:8000';

const RecruiterDashboard = ({ user, onLogout }) => {
  const [currentView, setCurrentView] = useState('offers'); // offers, interviews, reports
  const [offers, setOffers] = useState([]);
  const [applications, setApplications] = useState([]);
  const [selectedOfferId, setSelectedOfferId] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showApplicationsModal, setShowApplicationsModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedApplications, setSelectedApplications] = useState(new Set());
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifLoading, setNotifLoading] = useState(false);
  
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
    loadNotifications();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await axios.get(`${API_URL}/recruiter/${user.id}/offers`);
      setOffers(response.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await axios.get(`${API_URL}/users/${user.id}/notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error loading notifications:', error);
    }
  };

  const markAllNotificationsRead = async () => {
    setNotifLoading(true);
    try {
      await axios.post(`${API_URL}/notifications/mark-read`, { user_id: user.id });
      const refreshed = await axios.get(`${API_URL}/users/${user.id}/notifications`);
      setNotifications(refreshed.data);
    } catch (error) {
      console.error('Error marking notifications as read:', error);
    } finally {
      setNotifLoading(false);
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
      
      const response = await axios.post(`${API_URL}/offers/${selectedOfferId}/accept-multiple`, {
        application_ids: [applicationId]
      });
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

  // Télécharger un CV
  const downloadCV = async (applicationId, filename) => {
  try {
    const token = localStorage.getItem('access_token');
    
    // DEBUG: Vérifiez si le token existe dans la console
    console.log("Token envoyé :", token); 

    if (!token || token === "null" || token === "undefined") {
      alert("Votre session a expiré. Veuillez vous reconnecter.");
      return;
    }

    const response = await fetch(`${API_URL}/applications/${applicationId}/cv`, {
      method: 'GET', // Précisez la méthode par clarté
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `CV_${applicationId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } else {
      // Si le backend renvoie 401, on affiche un message plus précis
      if (response.status === 401) {
        alert("Session expirée ou accès non autorisé (401).");
      } else {
        alert(`Erreur serveur (${response.status}) lors du téléchargement.`);
      }
    }
  } catch (error) {
    console.error('Erreur téléchargement CV:', error);
    alert('Impossible de contacter le serveur.');
  }
};

  // Télécharger le rapport de matching
  const downloadMatchingReport = async (offerId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/offers/${offerId}/matching-report`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const report = await response.json();
        // Créer un fichier texte avec le rapport
        const reportText = `
RAPPORT DE MATCHING
==================

Offre: ${report.offer.title}
Ville: ${report.offer.city || 'Non spécifié'}
Expérience: ${report.offer.experience || 'Non spécifié'}

STATISTIQUES
------------
Total candidatures: ${report.statistics.total_applications}
Score moyen: ${report.statistics.average_score}/100
Score maximum: ${report.statistics.max_score}/100
Score minimum: ${report.statistics.min_score}/100

Excellents profils (≥70): ${report.statistics.excellent_matches}
Bons profils (50-69): ${report.statistics.good_matches}
Profils faibles (<50): ${report.statistics.low_matches}

Acceptés: ${report.statistics.accepted}
Refusés: ${report.statistics.rejected}
En attente: ${report.statistics.pending}

TOP 5 CANDIDATS
---------------
${report.top_candidates.map((c, i) => `
${i + 1}. ${c.name} (${c.email})
   Score: ${c.score}/100
   Statut: ${c.status}
   Analyse: ${c.justification}
`).join('\n')}
        `;

        const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rapport_matching_offre_${offerId}.txt`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        alert('Erreur lors de la génération du rapport');
      }
    } catch (error) {
      console.error('Erreur rapport:', error);
      alert('Erreur lors de la génération du rapport');
    }
  };

  // Exporter la liste des candidats en CSV
  const exportCandidatesCSV = async (offerId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/offers/${offerId}/candidates/export-csv`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const filename = response.headers.get('content-disposition')?.split('filename=')[1] || `candidats_offre_${offerId}.csv`;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        alert('Export réussi !');
      } else {
        alert('Erreur lors de l\'export');
      }
    } catch (error) {
      console.error('Erreur export:', error);
      alert('Erreur lors de l\'export');
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
  if (selectedApplications.size === 0) return;

  const token = localStorage.getItem('access_token');
  const dateTime = prompt("PLANIFICATION GROUPÉE\nFormat: YYYY-MM-DD HH:MM", "2026-02-15 09:00");

  if (!dateTime) return;

  try {
    // 1. Conversion des IDs en nombres et préparation de la date
    const selectedIds = Array.from(selectedApplications).map(id => Number(id));
    const formattedDate = dateTime.replace(' ', 'T') + ":00";

    // 2. Créer les entretiens un par un (car le backend crée 1 ligne par RDV)
    for (const appId of selectedIds) {
      const app = applications.find(a => a.id === appId);
      await axios.post(`${API_URL}/interviews`, {
        application_id: appId,
        title: `Entretien : ${app?.offer_title || 'Poste'}`,
        interview_date: formattedDate,
        duration: 30,
        meeting_type: "physical",
        location: "Bureau RH"
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }

    // 3. ENVOI GROUPÉ UNIQUE (Correction de l'erreur 422)
    // Au lieu de boucler, on envoie TOUS les IDs en une seule fois dans l'objet attendu
    await axios.post(`${API_URL}/offers/${selectedOfferId}/accept-multiple`, 
      { application_ids: selectedIds }, 
      {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );

    alert("✅ Session groupée planifiée avec succès !");
    setSelectedApplications(new Set());
    setShowApplicationsModal(false);
    loadDashboard();
    
  } catch (error) {
    console.error("Détail erreur 422 :", error.response?.data);
    alert("Erreur de format. Vérifiez les logs de la console.");
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
  const handleAcceptAndSchedule = async (app) => {
  const token = localStorage.getItem('access_token');
  
  // 1. Demander la date et l'heure au recruteur
  const selectedDate = prompt("Entrez la date et l'heure de la session (Format: YYYY-MM-DD HH:MM)", "2026-02-20 09:00");
  
  if (!selectedDate) return; // Annuler si vide

  const interviewData = {
    application_id: app.id,
    title: `Session d'entretien : ${app.offer_title}`,
    description: "Session groupée - Passage individuel un par un.",
    interview_date: selectedDate.replace(' ', 'T'), // Format ISO
    duration: 30, // Durée estimée par personne
    meeting_type: "physical",
    location: "Salle d'attente - 2ème étage"
  };

  try {
    // Étape A : On crée l'entretien dans la base
    const response = await fetch('http://localhost:8000/interviews', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(interviewData)
    });

    if (response.ok) {
      // Étape B : On met à jour le statut de la candidature en 'accepted'
      await fetch(`http://localhost:8000/applications/${app.id}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'accepted' })
      });

      alert(`Candidat ${app.candidate_name} accepté et ajouté à la session de ${selectedDate}`);
      loadApplications(); // Recharger la liste
    }
  } catch (error) {
    console.error("Erreur:", error);
  }
};
  const activeOffers = offers.filter(o => o.status === 'active').length;
  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <section className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>Tableau de bord Recruteur</h1>
              <p style={{ fontSize: '1.05em', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Bienvenue <span style={{ fontWeight: '600', color: 'var(--accent)' }}>{user.name}</span> !
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', position: 'relative' }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setShowNotifications(!showNotifications)}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', position: 'relative' }}
              >
                <span role="img" aria-label="Notifications">🔔</span>
                {unreadCount > 0 && (
                  <span className="badge badge-danger" style={{ position: 'absolute', top: '-0.35rem', right: '-0.35rem' }}>
                    {unreadCount}
                  </span>
                )}
              </button>
              <button className="btn btn-secondary" onClick={onLogout}>Déconnexion</button>

              {showNotifications && (
                <div
                  className="card"
                  style={{ position: 'absolute', right: 0, top: '3.25rem', width: '400px', zIndex: 5, boxShadow: '0 12px 30px rgba(0,0,0,0.15)' }}
                >
                  <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 className="card-title" style={{ margin: 0 }}>Notifications</h2>
                    <button className="btn btn-secondary" onClick={markAllNotificationsRead} disabled={notifLoading}>
                      {notifLoading ? '...' : 'Tout lu'}
                    </button>
                  </div>
                  <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
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
                          if (n.notif_type === 'application') {
                            bgColor = 'var(--bg-accent-light)';
                            borderColor = 'var(--accent)';
                            badgeColor = 'badge-blue';
                          } else if (n.notif_type === 'success') {
                            bgColor = 'rgba(76, 175, 80, 0.08)';
                            borderColor = '#4CAF50';
                            badgeColor = 'badge-success';
                          } else if (n.notif_type === 'warning') {
                            bgColor = 'rgba(255, 152, 0, 0.08)';
                            borderColor = '#FF9800';
                            badgeColor = 'badge-warning';
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
            </div>
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

        {/* Navigation par onglets */}
        <div style={{ marginBottom: '20px', borderBottom: '2px solid #e5e7eb' }}>
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
               Mes Offres
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
               Entretiens
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
               Rapports
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

        {currentView === 'offers' && (
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
                <div className="empty-state-icon"></div>
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
      )}

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

            {/* Boutons d'export et rapport */}
            <div style={{ marginBottom: '15px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button 
                className="btn btn-secondary"
                onClick={() => downloadMatchingReport(selectedOfferId)}
                style={{ fontSize: '14px', padding: '8px 16px' }}
              >
                 Rapport de Matching
              </button>
              <button 
                className="btn btn-secondary"
                onClick={() => exportCandidatesCSV(selectedOfferId)}
                style={{ fontSize: '14px', padding: '8px 16px' }}
              >
                 Exporter en CSV
              </button>
            </div>

            {selectedApplications.size > 0 && (
              <div className="selection-actions" style={{ marginBottom: '12px' }}>
                <span>{selectedApplications.size} candidat(s) sélectionné(s)</span>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Les candidats non sélectionnés recevront automatiquement un email de refus.</div>
                  <button className="btn btn-success" onClick={acceptSelected} style={{ marginLeft: '15px', fontWeight: 'bold' }}>✅ Accepter et Planifier la session groupée</button>
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
                          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                            <span className={`badge ${app.status === 'accepted' ? 'badge-success' : app.status === 'rejected' ? 'badge-danger' : 'badge-warning'}`}>
                              {app.status === 'pending' ? 'En attente' : app.status === 'accepted' ? 'Accepté' : 'Refusé'}
                            </span>
                            <button 
                              className="btn btn-secondary"
                              onClick={() => downloadCV(app.id, app.filename)}
                              style={{ fontSize: '12px', padding: '4px 12px' }}
                            >
                               Télécharger CV
                            </button>
                            
                          </div>
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
      </div>
    </section>
  );
};



export default RecruiterDashboard;
