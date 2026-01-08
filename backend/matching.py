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
MATCHER_TIMEOUT = int(os.getenv('MATCHER_TIMEOUT', '120'))  # Augmenté à 120s
MATCHER_RETRIES = int(os.getenv('MATCHER_RETRIES', '3'))    # Augmenté à 3

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

        # PROMPT AMÉLIORÉ - Plus clair et plus strict
        prompt = f"""Tu es un expert en recrutement RH. Analyse ce CV par rapport à l'offre d'emploi.

OFFRE D'EMPLOI :
{job_desc}

CONTENU DU CV :
{text[:4000]}

INSTRUCTIONS IMPORTANTES :
1. Évalue le CV sur 100 points
2. Compare les compétences du candidat avec celles requises
3. Considère l'expérience, la formation et les compétences techniques
4. Réponds UNIQUEMENT avec un objet JSON valide (pas de texte avant ou après)

FORMAT DE RÉPONSE OBLIGATOIRE :
{{
  "score": 75,
  "justification": "Le candidat possède 5 ans d'expérience en développement Python et maîtrise Django et React, ce qui correspond bien aux exigences. Cependant, il manque d'expérience en DevOps. Score global : 75/100."
}}

RÉPONDS MAINTENANT AVEC UNIQUEMENT LE JSON :"""

        try:
            import time
            last_exc = None
            
            for attempt in range(1, MATCHER_RETRIES + 1):
                try:
                    print(f"🤖 Tentative {attempt}/{MATCHER_RETRIES} - Analyse en cours...")
                    start_time = time.time()
                    
                    response = ollama.chat(
                        model=MODEL, 
                        messages=[{'role': 'user', 'content': prompt}], 
                        options={
                            'timeout': MATCHER_TIMEOUT,
                            'temperature': 0.3,  # Réduire la créativité pour plus de cohérence
                        }
                    )
                    
                    elapsed = time.time() - start_time
                    print(f"✅ Réponse reçue en {elapsed:.2f}s")

                    # Validation de la réponse
                    content = None
                    if isinstance(response, dict):
                        content = response.get('message', {}).get('content')
                    
                    if not content:
                        raise ValueError('Réponse vide de l\'API Ollama')

                    print(f"📄 Contenu brut reçu (premiers 500 chars) :\n{content[:500]}\n")

                    # MÉTHODE 1 : Extraction JSON stricte avec nettoyage
                    # Nettoyer les backticks markdown et autres caractères parasites
                    cleaned_content = content.strip()
                    cleaned_content = re.sub(r'^```json\s*', '', cleaned_content)
                    cleaned_content = re.sub(r'^```\s*', '', cleaned_content)
                    cleaned_content = re.sub(r'\s*```$', '', cleaned_content)
                    cleaned_content = cleaned_content.strip()
                    
                    # Extraire le JSON
                    json_match = re.search(r'\{[^{}]*"score"[^{}]*"justification"[^{}]*\}', cleaned_content, re.DOTALL)
                    
                    if json_match:
                        json_text = json_match.group(0)
                        print(f"🔍 JSON extrait : {json_text[:200]}")
                        
                        try:
                            data = json.loads(json_text)
                            score = data.get('score', 0)
                            justification = data.get('justification', '').strip()
                            
                            # Validation du score
                            if isinstance(score, str):
                                score = int(re.search(r'\d+', score).group())
                            score = int(round(float(score)))
                            score = max(0, min(100, score))
                            
                            # Validation de la justification
                            if not justification or len(justification) < 20:
                                justification = f"Le candidat obtient un score de {score}/100 basé sur l'analyse de son profil."
                            
                            print(f"✅ Score: {score}/100")
                            print(f"✅ Justification: {justification[:100]}...")
                            
                            return score, justification
                            
                        except (json.JSONDecodeError, ValueError, AttributeError) as e:
                            print(f"❌ Erreur parsing JSON: {e}")
                            # Continuer vers la méthode 2

                    # MÉTHODE 2 : Regex flexible pour extraire score et justification séparément
                    print("🔄 Tentative avec regex flexible...")
                    
                    # Chercher le score
                    score_patterns = [
                        r'"?score"?\s*[:=]\s*(\d{1,3})',
                        r'score\s*[:=]\s*(\d{1,3})',
                        r'(\d{1,3})\s*[/\\]\s*100',
                        r'(\d{1,3})%',
                    ]
                    
                    score = None
                    for pattern in score_patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            score = int(match.group(1))
                            break
                    
                    # Chercher la justification
                    justification_patterns = [
                        r'"?justification"?\s*[:=]\s*"([^"]{20,800})"',
                        r'"?justification"?\s*[:=]\s*([^\n]{20,800})',
                        r'analyse\s*[:]\s*([^\n]{20,800})',
                    ]
                    
                    justification = None
                    for pattern in justification_patterns:
                        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                        if match:
                            justification = match.group(1).strip()
                            break
                    
                    if score is not None:
                        score = max(0, min(100, score))
                        if not justification:
                            justification = f"Analyse effectuée. Score attribué : {score}/100."
                        
                        print(f"✅ Score extrait par regex: {score}/100")
                        print(f"✅ Justification extraite: {justification[:100]}...")
                        return score, justification

                    # MÉTHODE 3 : Analyse sémantique du texte
                    print("🔄 Tentative d'analyse sémantique du contenu...")
                    
                    # Chercher des indices de score dans le texte
                    if 'excellent' in content.lower() or 'parfait' in content.lower():
                        score = 85
                    elif 'bon' in content.lower() or 'correspond' in content.lower():
                        score = 70
                    elif 'moyen' in content.lower() or 'acceptable' in content.lower():
                        score = 55
                    elif 'faible' in content.lower() or 'insuffisant' in content.lower():
                        score = 35
                    else:
                        score = 60  # Score par défaut raisonnable
                    
                    # Extraire la première phrase cohérente comme justification
                    sentences = re.split(r'[.!?]\s+', content)
                    justification = sentences[0] if sentences else "Analyse effectuée."
                    
                    if len(justification) < 20:
                        justification = f"Profil évalué à {score}/100 selon les critères de l'offre."
                    
                    print(f"⚠️ Analyse sémantique : Score={score}, Justification={justification[:100]}...")
                    return score, justification

                except Exception as e:
                    last_exc = e
                    msg = str(e)
                    print(f"❌ Tentative {attempt} échouée : {e}")
                    
                    # Vérifier si le modèle existe
                    if 'model' in msg.lower() and 'not found' in msg.lower():
                        print(f"⚠️ Modèle '{MODEL}' introuvable!")
                        print(f"💡 Solutions:")
                        print(f"   1. Vérifier les modèles disponibles : ollama ls")
                        print(f"   2. Télécharger le modèle : ollama pull {MODEL}")
                        print(f"   3. Utiliser un autre modèle : export MATCHER_MODEL=llama3.2")
                    
                    if attempt < MATCHER_RETRIES:
                        wait_time = 2 * attempt
                        print(f"⏳ Nouvelle tentative dans {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise

        except Exception as e:
            tb = traceback.format_exc()
            print(f"\n❌ ERREUR CRITIQUE lors de l'analyse CV:")
            print(f"   Message: {e}")
            print(f"   Traceback complet:\n{tb}")
            
            # Enregistrer dans un fichier de log
            try:
                logs_dir = Path(__file__).resolve().parent / 'logs'
                logs_dir.mkdir(exist_ok=True)
                log_file = logs_dir / 'matcher_errors.log'
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"[{datetime.now().isoformat()}] ERREUR ANALYSE CV\n")
                    f.write(f"Modèle: {MODEL}\n")
                    f.write(f"Exception: {e}\n")
                    f.write(f"Traceback:\n{tb}\n")
                    f.write(f"{'='*80}\n")
                
                print(f"📝 Erreur enregistrée dans : {log_file}")
            except Exception as log_error:
                print(f"⚠️ Impossible d'écrire le log: {log_error}")
            
            # Retourner un score par défaut avec un message d'erreur détaillé
            return 50, f"Erreur d'analyse IA ({str(e)[:100]}). Le système a attribué un score par défaut. Veuillez vérifier la configuration d'Ollama."

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

        ⚠️ CONSIGNE IMPORTANTE : 
        Ne mentionne JAMAIS de numéro de téléphone, d'adresse e-mail ou de lien externe pour postuler. 
        Termine l'annonce par une invitation courte à utiliser le bouton de candidature ci-dessous.

        Structure obligatoire :
        - Introduction
        - Missions
        - Profil recherché
        - Avantages
        - Conclusion (sans coordonnées)
        """

        try:
            import time
            start_time = time.time()

            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}],
                options={'timeout': 60}
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