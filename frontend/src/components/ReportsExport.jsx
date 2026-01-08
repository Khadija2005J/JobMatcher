import React, { useState } from 'react';

const ReportsExport = ({ user }) => {
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [interviewsReport, setInterviewsReport] = useState([]);
  const [applicationsReport, setApplicationsReport] = useState([]);

  // Charger les statistiques
  const loadStatistics = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/reports/statistics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('Erreur chargement statistiques:', error);
    } finally {
      setLoading(false);
    }
  };

  // Charger le rapport des entretiens
  const loadInterviewsReport = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/reports/interviews', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setInterviewsReport(data);
      }
    } catch (error) {
      console.error('Erreur chargement rapport entretiens:', error);
    } finally {
      setLoading(false);
    }
  };

  // Charger le rapport des candidatures (recruteur seulement)
  const loadApplicationsReport = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/reports/applications', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setApplicationsReport(data);
      }
    } catch (error) {
      console.error('Erreur chargement rapport candidatures:', error);
    } finally {
      setLoading(false);
    }
  };

  // Exporter les entretiens en CSV
  const exportInterviewsCSV = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/export/interviews/csv', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `entretiens_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        alert('Export réussi !');
      }
    } catch (error) {
      console.error('Erreur export:', error);
      alert('Erreur lors de l\'export');
    }
  };

  // Exporter les candidatures en CSV (recruteur seulement)
  const exportApplicationsCSV = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/export/applications/csv', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `candidatures_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        alert('Export réussi !');
      }
    } catch (error) {
      console.error('Erreur export:', error);
      alert('Erreur lors de l\'export');
    }
  };

  // Initialiser les données
  React.useEffect(() => {
    loadStatistics();
    loadInterviewsReport();
    if (user.role === 'recruiter') {
      loadApplicationsReport();
    }
  }, []);

  // Carte de statistique
  const StatCard = ({ icon, title, value, color }) => (
    <div style={{
      backgroundColor: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '12px',
      padding: '24px',
      textAlign: 'center',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    }}>
      <div style={{ fontSize: '32px', marginBottom: '12px' }}>{icon}</div>
      <h3 style={{ 
        margin: '0 0 8px 0', 
        fontSize: '28px', 
        fontWeight: 'bold',
        color: color || '#111827'
      }}>
        {value}
      </h3>
      <p style={{ margin: 0, color: '#6b7280', fontSize: '14px' }}>{title}</p>
    </div>
  );

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ margin: '0 0 10px 0' }}>📊 Rapports & Statistiques</h1>
        <p style={{ color: '#6b7280', margin: 0 }}>
          Consultez vos statistiques et exportez vos données
        </p>
      </div>

      {/* Statistiques */}
      {statistics && (
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ marginBottom: '20px' }}>Vue d'ensemble</h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '20px'
          }}>
            {user.role === 'recruiter' ? (
              <>
                <StatCard 
                  icon="📝" 
                  title="Offres actives" 
                  value={statistics.active_offers}
                  color="#2563eb"
                />
                <StatCard 
                  icon="📬" 
                  title="Candidatures totales" 
                  value={statistics.total_applications}
                  color="#10b981"
                />
                <StatCard 
                  icon="⏳" 
                  title="En attente" 
                  value={statistics.pending_applications}
                  color="#f59e0b"
                />
                <StatCard 
                  icon="✅" 
                  title="Acceptées" 
                  value={statistics.accepted_applications}
                  color="#34d399"
                />
                <StatCard 
                  icon="📅" 
                  title="Entretiens planifiés" 
                  value={statistics.scheduled_interviews}
                  color="#8b5cf6"
                />
                <StatCard 
                  icon="⭐" 
                  title="Score moyen" 
                  value={`${statistics.average_score}/100`}
                  color="#f59e0b"
                />
              </>
            ) : (
              <>
                <StatCard 
                  icon="📬" 
                  title="Candidatures envoyées" 
                  value={statistics.total_applications}
                  color="#2563eb"
                />
                <StatCard 
                  icon="⏳" 
                  title="En attente" 
                  value={statistics.pending_applications}
                  color="#f59e0b"
                />
                <StatCard 
                  icon="✅" 
                  title="Acceptées" 
                  value={statistics.accepted_applications}
                  color="#10b981"
                />
                <StatCard 
                  icon="📅" 
                  title="Entretiens à venir" 
                  value={statistics.upcoming_interviews}
                  color="#8b5cf6"
                />
                <StatCard 
                  icon="⭐" 
                  title="Offres favorites" 
                  value={statistics.favorites}
                  color="#ec4899"
                />
                <StatCard 
                  icon="📊" 
                  title="Score moyen" 
                  value={`${statistics.average_score}/100`}
                  color="#f59e0b"
                />
              </>
            )}
          </div>
        </div>
      )}

      {/* Section Export */}
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '20px' }}>📥 Exports CSV</h2>
        <div style={{
          display: 'grid',
          gap: '15px',
          gridTemplateColumns: user.role === 'recruiter' ? 'repeat(auto-fit, minmax(300px, 1fr))' : '1fr'
        }}>
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '24px'
          }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>📅 Entretiens</h3>
            <p style={{ color: '#6b7280', margin: '0 0 20px 0', fontSize: '14px' }}>
              Exportez la liste complète de vos entretiens au format CSV
            </p>
            <button
              onClick={exportInterviewsCSV}
              style={{
                padding: '12px 24px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px',
                width: '100%'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#1d4ed8'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#2563eb'}
            >
              📥 Télécharger les entretiens (.csv)
            </button>
          </div>

          {user.role === 'recruiter' && (
            <div style={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '12px',
              padding: '24px'
            }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>📬 Candidatures</h3>
              <p style={{ color: '#6b7280', margin: '0 0 20px 0', fontSize: '14px' }}>
                Exportez toutes les candidatures reçues avec les scores IA
              </p>
              <button
                onClick={exportApplicationsCSV}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  fontSize: '14px',
                  width: '100%'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#059669'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#10b981'}
              >
                📥 Télécharger les candidatures (.csv)
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Tableau des entretiens */}
      {interviewsReport.length > 0 && (
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ marginBottom: '20px' }}>📅 Historique des entretiens</h2>
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            overflow: 'hidden'
          }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Date
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Titre
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      {user.role === 'recruiter' ? 'Candidat' : 'Recruteur'}
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Type
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Statut
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {interviewsReport.slice(0, 10).map((interview, index) => (
                    <tr key={index} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '12px', fontSize: '14px' }}>{interview.interview_date}</td>
                      <td style={{ padding: '12px', fontSize: '14px', fontWeight: '600' }}>{interview.title}</td>
                      <td style={{ padding: '12px', fontSize: '14px' }}>
                        {user.role === 'recruiter' ? interview.candidate_name : interview.recruiter_name}
                      </td>
                      <td style={{ padding: '12px', fontSize: '14px', textTransform: 'capitalize' }}>
                        {interview.meeting_type}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600',
                          backgroundColor: 
                            interview.status === 'completed' ? '#d1fae5' :
                            interview.status === 'accepted' ? '#dbeafe' :
                            interview.status === 'proposed' ? '#fef3c7' : '#fee2e2',
                          color: 
                            interview.status === 'completed' ? '#065f46' :
                            interview.status === 'accepted' ? '#1e40af' :
                            interview.status === 'proposed' ? '#92400e' : '#991b1b'
                        }}>
                          {interview.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {interviewsReport.length > 10 && (
              <div style={{ padding: '12px', textAlign: 'center', fontSize: '14px', color: '#6b7280', backgroundColor: '#f9fafb' }}>
                Et {interviewsReport.length - 10} autre(s) entretien(s)...
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tableau des candidatures (recruteur uniquement) */}
      {user.role === 'recruiter' && applicationsReport.length > 0 && (
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ marginBottom: '20px' }}>📬 Candidatures récentes</h2>
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            overflow: 'hidden'
          }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Date
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Offre
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Candidat
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Score IA
                    </th>
                    <th style={{ padding: '12px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>
                      Statut
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {applicationsReport.slice(0, 10).map((app, index) => (
                    <tr key={index} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '12px', fontSize: '14px' }}>{app.created_at}</td>
                      <td style={{ padding: '12px', fontSize: '14px', fontWeight: '600' }}>{app.offer_title}</td>
                      <td style={{ padding: '12px', fontSize: '14px' }}>{app.candidate_name}</td>
                      <td style={{ padding: '12px', fontSize: '14px' }}>
                        <span style={{ 
                          fontWeight: 'bold',
                          color: app.score >= 70 ? '#10b981' : app.score >= 50 ? '#f59e0b' : '#ef4444'
                        }}>
                          {app.score ? `${app.score.toFixed(1)}/100` : 'N/A'}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600',
                          backgroundColor: 
                            app.status === 'accepted' ? '#d1fae5' :
                            app.status === 'pending' ? '#fef3c7' : '#fee2e2',
                          color: 
                            app.status === 'accepted' ? '#065f46' :
                            app.status === 'pending' ? '#92400e' : '#991b1b'
                        }}>
                          {app.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {applicationsReport.length > 10 && (
              <div style={{ padding: '12px', textAlign: 'center', fontSize: '14px', color: '#6b7280', backgroundColor: '#f9fafb' }}>
                Et {applicationsReport.length - 10} autre(s) candidature(s)...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsExport;
