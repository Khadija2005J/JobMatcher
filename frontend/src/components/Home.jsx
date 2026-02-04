import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

const Home = ({ onShowLogin, onShowRegister }) => {
  const heroRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // float animation for the decorative background
      gsap.to('.hero-bg', {
        y: -18,
        rotation: 3,
        duration: 6,
        yoyo: true,
        repeat: -1,
        ease: 'sine.inOut'
      });

      // staggered reveal for hero lines
      gsap.fromTo('.hero-line',
        { opacity: 0, y: 18, scale: 0.995 },
        { opacity: 1, y: 0, scale: 1, duration: 0.7, stagger: 0.08, ease: 'power3.out' }
      );

      // subtle parallax following mouse movement
      const el = heroRef.current;
      function onMove(e) {
        const rect = el.getBoundingClientRect();
        const relX = (e.clientX - rect.left) / rect.width - 0.5;
        const relY = (e.clientY - rect.top) / rect.height - 0.5;
        gsap.to('.hero-bg', { x: relX * 24, y: -18 + relY * 18, duration: 0.6, ease: 'power2.out' });
      }

      el?.addEventListener('mousemove', onMove);
      return () => {
        el?.removeEventListener('mousemove', onMove);
      };
    }, heroRef);

    return () => ctx.revert();
  }, []);

  return (
    <section className="hero" ref={heroRef}>
      <div className="hero-bg" aria-hidden="true"></div>
      <div className="container">
        <h1>
          <span className="hero-line delay-1">Recrutement Intelligent</span>
          <span className="hero-line delay-2">Propulsé par <span className="hero-highlight">l'IA</span></span>
        </h1>
        <p>
          Matching automatique, scoring intelligent et génération d'annonces avec l'intelligence artificielle générative
        </p>
        <div className="hero-buttons">
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