import React from 'react';
import '../App.css';

const Features = () => {
  return (
    <section className="page">
      <div className="page-content">
        <h1 className="card-title">Fonctionnalités</h1>
        <p>
          Découvrez les principales fonctionnalités de JobMatcher conçues pour optimiser
          vos processus de recrutement.
        </p>

        <div className="feature-grid">
          <div className="feature-card">
            <h4>Matching IA</h4>
            <p className="muted">Algorithmes de scoring pour rapprocher automatiquement les profils et les offres.</p>
          </div>
          <div className="feature-card">
            <h4>Analyse de CV</h4>
            <p className="muted">Extraction automatique des compétences, expériences et formations.</p>
          </div>
          <div className="feature-card">
            <h4>Exports & Rapports</h4>
            <p className="muted">Exports CSV/XLSX et tableaux de bord pour suivre vos métriques.</p>
          </div>
          <div className="feature-card">
            <h4>Gestion des entretiens</h4>
            <p className="muted">Planification, notifications et suivi des statuts d'entretien.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Features;
