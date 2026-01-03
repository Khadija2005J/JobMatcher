import fitz  # PyMuPDF
import ollama
import json
import re
import os
import traceback
from pathlib import Path
from datetime import datetime

# Model configuration: use MATCHER_MODEL env var, default to a known working model
MODEL = os.getenv('MATCHER_MODEL', 'llama3.2')
# Timeout and retries configurable
MATCHER_TIMEOUT = int(os.getenv('MATCHER_TIMEOUT', '60'))
MATCHER_RETRIES = int(os.getenv('MATCHER_RETRIES', '2'))

class CVMatcher:
    def extract_text(self, pdf_path: str) -> str:
        """Extrait le texte brut du PDF pour l'envoyer au LLM."""
        text = ""
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except Exception as e:
            print(f"Erreur extraction PDF: {e}")
            return ""

    def get_score(self, pdf_path: str, job_desc: str):
        """Analyse le CV par rapport à une offre et retourne score + justification."""
        text = self.extract_text(pdf_path)
        
        if not text:
            return 0, "Impossible de lire le contenu du PDF."

        prompt = f"""
        En tant qu'expert RH, analyse ce CV pour le poste suivant : {job_desc}
        
        CONTENU DU CV :
        {text[:3000]}
        
        Réponds UNIQUEMENT au format JSON strict :
        {{
            "score": nombre_entre_0_et_100,
            "justification": "ta brève analyse en 2-3 phrases"
        }}
        """

        try:
            import time
            # Retry loop for transient errors
            retries = 2
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    start_time = time.time()
                    response = ollama.chat(model=MODEL, messages=[{'role': 'user', 'content': prompt}], options={'timeout': MATCHER_TIMEOUT})
                    elapsed = time.time() - start_time
                    print(f"Analyse CV terminée en {elapsed:.2f}s (attempt {attempt})")

                    # Basic validation of response shape
                    content = None
                    if isinstance(response, dict):
                        content = response.get('message', {}).get('content')
                    if not content:
                        raise ValueError('Réponse vide de l\'API GenAI')

                    # Dev-only: write raw response and content to log if enabled
                    if os.getenv('MATCHER_DEBUG', '').lower() in ('1', 'true', 'yes'):
                        try:
                            logs_dir = Path(__file__).resolve().parent / 'logs'
                            logs_dir.mkdir(exist_ok=True)
                            log_file = logs_dir / 'matcher_debug.log'
                            with open(log_file, 'a', encoding='utf-8') as f:
                                f.write(f"--- {datetime.utcnow().isoformat()} UTC attempt {attempt} ---\n")
                                f.write('RAW_RESPONSE:\n')
                                f.write(repr(response)[:10000] + '\n')
                                f.write('CONTENT_SNIPPET:\n')
                                f.write((content[:10000] if content else '') + '\n')
                                f.write('\n')
                        except Exception as le:
                            print('Failed to write matcher debug log:', le)

                    # Try to extract the first JSON object using regex (robust to extra text)
                    m = re.search(r"\{[\s\S]*\}", content)
                    if m:
                        json_text = m.group(0)
                        try:
                            data = json.loads(json_text)
                            score = data.get('score', 0)
                            justification = data.get('justification', 'Analyse effectuée.')
                            # Normalize score to an integer between 0 and 100
                            try:
                                score = int(round(float(score)))
                                if score < 0: score = 0
                                if score > 100: score = 100
                            except Exception:
                                pass
                            return score, justification
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}; raw JSON snippet: {json_text[:200]}")
                            # fallthrough to try pattern matching

                    # Fallback: try to find score/justification with looser patterns
                    score_match = re.search(r'"?score"?\s*[:=]\s*(\d{1,3})', content, re.IGNORECASE)
                    justification_match = re.search(r'"?justification"?\s*[:=]\s*"([\s\S]{10,500})"', content, re.IGNORECASE)
                    if score_match:
                        s = int(score_match.group(1))
                        j = justification_match.group(1).strip() if justification_match else 'Analyse effectuée.'
                        s = max(0, min(100, s))
                        return s, j

                    # If nothing worked, raise to trigger retry
                    raise ValueError('Impossible d\'extraire JSON depuis la réponse GenAI')

                except Exception as e:
                    last_exc = e
                    msg = str(e)
                    print(f"Attempt {attempt} failed: {e}")
                    # If the error looks like a missing model, emit a helpful hint
                    if 'model' in msg and 'not found' in msg.lower():
                        print(f"Model '{MODEL}' not found. Run 'ollama ls' to list installed models and 'ollama pull {MODEL}' to download it, or set MATCHER_MODEL to a model you have installed.")
                    if attempt < MATCHER_RETRIES:
                        time.sleep(1 * attempt)
                    else:
                        raise

        except Exception as e:
            # Final fallback with clearer message and debug logging
            tb = traceback.format_exc()
            print(f"Erreur lors de l'appel GenAI : {e}\n{tb}")
            if os.getenv('MATCHER_DEBUG', '').lower() in ('1', 'true', 'yes'):
                try:
                    logs_dir = Path(__file__).resolve().parent / 'logs'
                    logs_dir.mkdir(exist_ok=True)
                    log_file = logs_dir / 'matcher_debug.log'
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"--- {datetime.utcnow().isoformat()} UTC FINAL EXCEPTION ---\n")
                        f.write(tb + '\n')
                except Exception as le:
                    print('Failed to write matcher final exception log:', le)
            return 50, "Analyse impossible (GenAI error) : veuillez réessayer plus tard."

    def generate_job_ad(
        self,
        title: str,
        city: str,
        contract: str,
        experience: str,
        education: str,
        technical_skills: str,
        soft_skills: str,
        missions: str,
        salary: str = "Non communiqué",
        benefits: str = "Selon profil",
        work_mode: str = "Présentiel",
        languages: str = "Français"
    ) -> str:
        """Génère une annonce d'emploi professionnelle via GenAI."""

        prompt = f"""
        Tu es un expert RH.

        Rédige une annonce d'emploi professionnelle et attractive.

        📌 Informations du poste :
        - Intitulé : {title}
        - Ville : {city}
        - Type de contrat : {contract}
        - Mode de travail : {work_mode}
        - Expérience requise : {experience}
        - Niveau d'études : {education}
        - Langues : {languages}
        - Salaire : {salary}

        🛠 Compétences techniques :
        {technical_skills}

        🤝 Compétences comportementales :
        {soft_skills}

        📋 Missions principales :
        {missions}

        🎁 Avantages :
        {benefits}

        Structure obligatoire :
        - Introduction
        - Missions
        - Profil recherché
        - Avantages
        - Informations pratiques
        - Call to action
        """

        try:
            import time
            start_time = time.time()

            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}],
                options={'timeout': 30}
            )

            elapsed = time.time() - start_time
            print(f"Génération d'annonce terminée en {elapsed:.2f}s")
            return response['message']['content']

        except Exception as e:
            print(f"Erreur génération annonce: {e}")
            return f"""
📋 Poste : {title}
📍 Ville : {city}
📄 Contrat : {contract}

Nous recherchons un(e) {title} avec {experience} d'expérience.

🎯 Compétences techniques : {technical_skills}

📋 Missions : {missions}

📧 Postulez avec votre CV.
"""

    def generate_acceptance_email(self, candidate_name: str, job_title: str) -> tuple:
        """Génère un email d'acceptation personnalisé."""
        prompt = f"""
        Rédige un email professionnel et chaleureux pour informer {candidate_name} qu'il/elle a été sélectionné(e) pour le poste de {job_title}.
        
        L'email doit être :
        - Positif et encourageant
        - Professionnel
        - Court (5-6 lignes maximum)
        
        Réponds avec UNIQUEMENT l'email, sans en-tête "Objet:" ou "Corps:".
        """
        
        try:
            response = ollama.chat(model='llama3.2', messages=[
                {'role': 'user', 'content': prompt}
            ])
            body = response['message']['content'].strip()
            subject = f"Félicitations ! Votre candidature pour {job_title}"
            return subject, body
        except Exception as e:
            subject = f"Félicitations ! Votre candidature pour {job_title}"
            body = f"""
Bonjour {candidate_name},

Nous avons le plaisir de vous informer que votre candidature pour le poste de {job_title} a été retenue !

Nous avons été impressionnés par votre profil et vos compétences.

Notre équipe RH vous contactera prochainement pour les prochaines étapes.

Cordialement,
L'équipe Smart HIRE
            """
            return subject, body

    def generate_rejection_email(self, candidate_name: str, job_title: str) -> tuple:
        """Génère un email de refus respectueux."""
        prompt = f"""
        Rédige un email professionnel, respectueux et encourageant pour informer {candidate_name} que sa candidature pour le poste de {job_title} n'a pas été retenue.
        
        L'email doit être :
        - Respectueux et positif
        - Encourageant pour l'avenir
        - Court (4-5 lignes maximum)
        
        Réponds avec UNIQUEMENT l'email, sans en-tête "Objet:" ou "Corps:".
        """
        
        try:
            response = ollama.chat(model='llama3.2', messages=[
                {'role': 'user', 'content': prompt}
            ])
            body = response['message']['content'].strip()
            subject = f"Votre candidature pour {job_title}"
            return subject, body
        except Exception as e:
            subject = f"Votre candidature pour {job_title}"
            body = f"""
Bonjour {candidate_name},

Nous vous remercions pour l'intérêt que vous avez porté à notre poste de {job_title}.

Après avoir examiné attentivement votre candidature, nous avons décidé de poursuivre avec d'autres profils plus alignés avec nos besoins actuels.

Nous vous souhaitons beaucoup de succès dans vos recherches professionnelles.

Cordialement,
L'équipe Smart HIRE
            """
            return subject, body