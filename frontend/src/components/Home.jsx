const Home = ({ onShowLogin, onShowRegister }) => {
  return (
    <section className="hero">
      <div className="container">
        <h1>
          Recrutement Intelligent<br />
          Propulsé par <span className="hero-highlight">l'IA</span>
        </h1>
        <p>
          Matching automatique, scoring intelligent et génération d'annonces avec l'intelligence artificielle générative
        </p>
        <div className="hero-buttons">
          {/* Correction ici : onClick (un seul 'o') et appel de onShowRegister */}
          <button className="btn btn-primary" onClick={onShowRegister}>
            Commencer Gratuitement
          </button>
          
          <button className="btn btn-outline" onClick={onShowLogin}>
            Se Connecter
          </button>
        </div>
      </div>
    </section>
  );
};

export default Home;