import React from 'react';
import '../App.css';

const About = () => {
  return (
    <section className="page about-page">
      <div className="page-content">
        <h1 className="card-title">À propos de JobMatcher</h1>
        <p className="lead">JobMatcher est une plateforme qui connecte intelligemment les candidats et les recruteurs grâce à l'intelligence artificielle. Notre objectif est de simplifier le processus de recrutement et d'augmenter la qualité des mises en relation.</p>

        <h3 className="section-subtitle">Notre mission</h3>
        <p>Fournir des outils transparents et performants pour aider les entreprises à identifier rapidement les meilleurs talents et aider les candidats à trouver des emplois qui correspondent réellement à leurs compétences et aspirations.</p>

        <h3 className="section-subtitle">Roadmap / fonctionnalités futures</h3>
        <ul className="muted-list">
          <li>SSO / OAuth et intégrations d'entreprise</li>
          <li>API publique et portail développeur</li>
          <li>Matching en temps réel et suggestions proactives</li>
          <li>Analytique avancée et alertes</li>
        </ul>

        <h3 className="section-subtitle">Contact</h3>
        <p>Pour toute question, contactez-nous à <strong>smarthire221@gmail.com</strong></p>
      </div>
    </section>
  );
}

export default About;
