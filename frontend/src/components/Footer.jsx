import React from 'react';
import '../App.css';

const Footer = () => {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div className="footer-col">
          <h4>JobMatcher</h4>
          <p className="muted">Plateforme intelligente de mise en relation candidats / recruteurs.</p>
        </div>

        <div className="footer-col">
          <h5>Pour le futur</h5>
          <ul>
            <li>Documentation API</li>
            <li>Intégration SSO (SSO / OAuth)</li>
            <li>Webhooks & Events</li>
            <li>Portail développeur</li>
          </ul>
        </div>

        <div className="footer-col">
          <h5>Produits</h5>
          <ul>
            <li>Export avancé (CSV / XLSX)</li>
            <li>Tableau de bord RH</li>
            <li>Matching IA en temps réel</li>
          </ul>
        </div>

        <div className="footer-col">
          <h5>Support</h5>
          <ul>
            <li>Centre d'aide</li>
            <li>Contact commercial</li>
            <li>Statut du service</li>
            <li>Accessibilité</li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <small className="muted">© {new Date().getFullYear()} JobMatcher — Tous droits réservés.</small>
          <div className="footer-links muted">Version: alpha • Confidentialité • Mentions légales</div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
