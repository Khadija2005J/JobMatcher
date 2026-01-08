import React, { useState, useEffect } from 'react';
import '../App.css';

const InterviewCalendar = ({ user }) => {
  const [interviews, setInterviews] = useState([]);
  const [selectedInterview, setSelectedInterview] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');

  // FONCTION CORRIGÉE
  const loadInterviews = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const statusParam = filterStatus !== 'all' ? `?status=${filterStatus}` : '';
      
      const response = await fetch(`http://localhost:8000/interviews${statusParam}`, {
        headers: { 
          'Authorization': `Bearer ${token}` 
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Mapping des noms pour l'affichage
        const adaptedData = data.map(interview => ({
          ...interview,
          other_user_name: user.role === 'recruiter' 
            ? interview.candidate_name 
            : interview.recruiter_name
        }));

        setInterviews(adaptedData);
      }
    } catch (error) {
      console.error('Erreur chargement entretiens:', error);
    }
  };

  // APPEL AUTOMATIQUE
  useEffect(() => {
    loadInterviews();
  }, [filterStatus]); // Se relance quand on change le filtre
  
  // Formater une date
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Obtenir le badge de statut
  const getStatusBadge = (status) => {
    const badges = {
      'proposed': { label: 'Proposé', color: '#fbbf24' },
      'accepted': { label: 'Accepté', color: '#34d399' },
      'rejected': { label: 'Rejeté', color: '#ef4444' },
      'completed': { label: 'Terminé', color: '#8b5cf6' },
      'cancelled': { label: 'Annulé', color: '#6b7280' }
    };
    
    const badge = badges[status] || badges['proposed'];
    
    return (
      <span style={{
        padding: '4px 12px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: '600',
        backgroundColor: badge.color + '20',
        color: badge.color
      }}>
        {badge.label}
      </span>
    );
  };

  // Obtenir l'icône du type de réunion
  const getMeetingTypeIcon = (type) => {
    const icons = {
      'physical': '📍',
      'zoom': '📹',
      'teams': '💼',
      'phone': '📞'
    };
    return icons[type] || '📍';
  };

  // Mettre à jour le statut
  const updateStatus = async (interviewId, newStatus, notes = '') => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`http://localhost:8000/interviews/${interviewId}/status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus, notes })
      });

      if (response.ok) {
        alert('Statut mis à jour avec succès !');
        loadInterviews();
        setShowDetailModal(false);
      } else {
        alert('Erreur lors de la mise à jour');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la mise à jour');
    } finally {
      setLoading(false);
    }
  };

  // Voir les détails
  const viewDetails = async (interview) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/interviews/${interview.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedInterview(data);
        setShowDetailModal(true);
      }
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  // Modal de détails
  const DetailModal = () => {
    if (!selectedInterview) return null;

    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '30px',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
            <div>
              <h2 style={{ margin: 0, marginBottom: '10px' }}>{selectedInterview.title}</h2>
              {getStatusBadge(selectedInterview.status)}
            </div>
            <button 
              onClick={() => setShowDetailModal(false)}
              style={{
                border: 'none',
                background: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#6b7280'
              }}
            >
              ×
            </button>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <p style={{ color: '#6b7280', marginBottom: '5px' }}>📅 Date</p>
            <p style={{ fontWeight: '600', marginTop: '5px' }}>{formatDate(selectedInterview.interview_date)}</p>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <p style={{ color: '#6b7280', marginBottom: '5px' }}>⏱️ Durée</p>
            <p style={{ fontWeight: '600', marginTop: '5px' }}>{selectedInterview.duration} minutes</p>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <p style={{ color: '#6b7280', marginBottom: '5px' }}>{getMeetingTypeIcon(selectedInterview.meeting_type)} Type</p>
            <p style={{ fontWeight: '600', marginTop: '5px', textTransform: 'capitalize' }}>{selectedInterview.meeting_type}</p>
          </div>

          {selectedInterview.location && (
            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#6b7280', marginBottom: '5px' }}>📍 Lieu</p>
              <p style={{ fontWeight: '600', marginTop: '5px' }}>{selectedInterview.location}</p>
            </div>
          )}

          {selectedInterview.meeting_url && (
            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#6b7280', marginBottom: '5px' }}>🔗 Lien de réunion</p>
              <a 
                href={selectedInterview.meeting_url} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: '#2563eb', wordBreak: 'break-all' }}
              >
                {selectedInterview.meeting_url}
              </a>
            </div>
          )}

          <div style={{ marginBottom: '20px' }}>
            <p style={{ color: '#6b7280', marginBottom: '5px' }}>
              {user.role === 'recruiter' ? '👤 Candidat' : '👤 Recruteur'}
            </p>
            <p style={{ fontWeight: '600', marginTop: '5px' }}>
              {user.role === 'recruiter' 
                ? selectedInterview.candidate.name 
                : selectedInterview.recruiter.name}
            </p>
            <p style={{ color: '#6b7280', fontSize: '14px' }}>
              {user.role === 'recruiter' 
                ? selectedInterview.candidate.email 
                : selectedInterview.recruiter.email}
            </p>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <p style={{ color: '#6b7280', marginBottom: '5px' }}>💼 Offre</p>
            <p style={{ fontWeight: '600', marginTop: '5px' }}>{selectedInterview.offer_title}</p>
          </div>

          {selectedInterview.description && (
            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#6b7280', marginBottom: '5px' }}>📝 Description</p>
              <p style={{ marginTop: '5px' }}>{selectedInterview.description}</p>
            </div>
          )}

          {selectedInterview.notes && (
            <div style={{ marginBottom: '20px' }}>
              <p style={{ color: '#6b7280', marginBottom: '5px' }}>📋 Notes</p>
              <p style={{ marginTop: '5px' }}>{selectedInterview.notes}</p>
            </div>
          )}

          {/* Actions selon le statut et le rôle */}
          <div style={{ marginTop: '30px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {selectedInterview.status === 'proposed' && user.role === 'candidate' && (
              <>
                <button
                  onClick={() => updateStatus(selectedInterview.id, 'accepted')}
                  disabled={loading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontWeight: '600'
                  }}
                >
                  ✅ Accepter
                </button>
                <button
                  onClick={() => updateStatus(selectedInterview.id, 'rejected')}
                  disabled={loading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#ef4444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontWeight: '600'
                  }}
                >
                  ❌ Refuser
                </button>
              </>
            )}

            {selectedInterview.status === 'accepted' && (
              <button
                onClick={() => updateStatus(selectedInterview.id, 'completed')}
                disabled={loading}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#8b5cf6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: '600'
                }}
              >
                ✓ Marquer comme terminé
              </button>
            )}

            <button
              onClick={() => updateStatus(selectedInterview.id, 'cancelled')}
              disabled={loading}
              style={{
                padding: '10px 20px',
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontWeight: '600'
              }}
            >
              🚫 Annuler
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Grouper les entretiens par date
  const groupByDate = (interviews) => {
    const groups = {};
    
    interviews.forEach(interview => {
      const date = new Date(interview.interview_date);
      const dateKey = date.toLocaleDateString('fr-FR');
      
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(interview);
    });

    return groups;
  };

  const groupedInterviews = groupByDate(interviews);

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '15px' }}>
        <h1 style={{ margin: 0 }}>📅 Mes Entretiens</h1>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select 
            value={filterStatus} 
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{
              padding: '10px 15px',
              borderRadius: '6px',
              border: '1px solid #e5e7eb',
              fontSize: '14px'
            }}
          >
            <option value="all">Tous les statuts</option>
            <option value="proposed">Proposés</option>
            <option value="accepted">Acceptés</option>
            <option value="completed">Terminés</option>
            <option value="rejected">Rejetés</option>
            <option value="cancelled">Annulés</option>
          </select>
        </div>
      </div>

      {interviews.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          backgroundColor: '#f9fafb',
          borderRadius: '12px'
        }}>
          <p style={{ fontSize: '48px', margin: '0 0 15px 0' }}>📅</p>
          <h3 style={{ margin: '0 0 10px 0', color: '#374151' }}>Aucun entretien</h3>
          <p style={{ color: '#6b7280' }}>
            {filterStatus !== 'all' 
              ? `Aucun entretien avec le statut "${filterStatus}"`
              : "Vous n'avez pas encore d'entretien planifié"}
          </p>
        </div>
      ) : (
        <div>
          {Object.entries(groupedInterviews).map(([date, dayInterviews]) => (
            <div key={date} style={{ marginBottom: '30px' }}>
              <h3 style={{ 
                color: '#374151', 
                marginBottom: '15px',
                paddingBottom: '10px',
                borderBottom: '2px solid #e5e7eb'
              }}>
                {date}
              </h3>
              
              <div style={{ display: 'grid', gap: '15px' }}>
                {dayInterviews.map((interview) => (
                  <div 
                    key={interview.id}
                    style={{
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      padding: '20px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                    }}
                    onClick={() => viewDetails(interview)}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.05)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
                      <div style={{ flex: 1 }}>
                        <h4 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>{interview.title}</h4>
                        <p style={{ margin: 0, color: '#6b7280', fontSize: '14px' }}>
                          {getMeetingTypeIcon(interview.meeting_type)} {new Date(interview.interview_date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} • {interview.duration} min
                        </p>
                      </div>
                      {getStatusBadge(interview.status)}
                    </div>

                    <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                      <div>
                        <p style={{ margin: '0 0 5px 0', fontSize: '12px', color: '#6b7280' }}>
                          {user.role === 'recruiter' ? 'Candidat' : 'Recruteur'}
                        </p>
                        <p style={{ margin: 0, fontWeight: '600', fontSize: '14px' }}>
                          {interview.other_user_name}
                        </p>
                      </div>
                      
                      <div>
                        <p style={{ margin: '0 0 5px 0', fontSize: '12px', color: '#6b7280' }}>Offre</p>
                        <p style={{ margin: 0, fontWeight: '600', fontSize: '14px' }}>
                          {interview.offer_title}
                        </p>
                      </div>
                    </div>

                    {interview.location && (
                      <p style={{ 
                        margin: '15px 0 0 0', 
                        fontSize: '14px', 
                        color: '#6b7280',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}>
                        📍 {interview.location}
                      </p>
                    )}

                    {interview.meeting_url && (
                      <p style={{ 
                        margin: '10px 0 0 0', 
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}>
                        🔗 <span style={{ color: '#2563eb' }}>Lien de réunion disponible</span>
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {showDetailModal && <DetailModal />}
    </div>
  );
};

export default InterviewCalendar;
