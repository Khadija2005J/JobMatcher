import React from 'react';
import '../App.css';

const Benefits = () => {
  return (
    <section className="page">
      <div className="page-content">
        <h1 className="card-title">Avantages</h1>
        <p>
          Les bénéfices pour les recruteurs et les candidats en utilisant JobMatcher.
        </p>

        <div className="feature-grid">
          <div className="feature-card">
            <h4>Gain de temps</h4>
            <p className="muted">Automatisation des tâches répétitives et présélection intelligente.</p>
          </div>
          <div className="feature-card">
            <h4>Meilleure qualité</h4>
            <p className="muted">Des candidats plus pertinents grâce au scoring IA.</p>
          </div>
          <div className="feature-card">
            <h4>Visibilité</h4>
            <p className="muted">Dashboards et rapports pour piloter vos recrutements.</p>
          </div>
          <div className="feature-card">
            <h4>Conformité</h4>
            <p className="muted">Contrôles d'accès et protection des données personnelles.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Benefits;
