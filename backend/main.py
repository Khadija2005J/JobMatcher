from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
import shutil
from pathlib import Path
from typing import Optional, List
import sqlite3
import sys
import os


class ApplicationAction(BaseModel):
    application_ids: List[int]
# Ajouter le dossier backend au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports depuis le dossier backend
from database import (
    init_db, get_connection, create_user, authenticate_user, 
    get_user_by_id
)
from matching import CVMatcher
from email_service import send_acceptance_email, send_rejection_email

# Initialisation
init_db()
app = FastAPI(
    title="Smart HIRE - GenAI Edition",
    description="Système de recrutement intelligent avec IA Générative",
    version="3.0.0"
)

# Instance du moteur IA
matcher = CVMatcher()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemins relatifs au dossier backend
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# --- MODÈLES DE DONNÉES ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # 'recruiter' ou 'candidate'

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class JobOfferDraft(BaseModel):
    title: str
    city: str
    contract: str
    experience: str
    education: str
    technical_skills: str
    soft_skills: Optional[str] = ""
    missions: str
    salary: Optional[str] = "Non communiqué"
    benefits: Optional[str] = "Selon profil"
    work_mode: Optional[str] = "Présentiel"
    languages: Optional[str] = "Français"
    recruiter_id: int

class JobOfferPublish(BaseModel):
    title: str
    description: str
    contract: str
    skills: str
    city: str           # NOUVEAU
    experience: str     # NOUVEAU
    education: str      # NOUVEAU
    salary: str         # NOUVEAU
    recruiter_id: int

# --- FONCTION UTILITAIRE POUR LOG EMAIL ---
def log_email_internal(conn, recipient_email: str, subject: str, body: str):
    """Enregistre un email en utilisant une connexion existante."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO emails (recipient_email, subject, body) VALUES (?, ?, ?)",
        (recipient_email, subject, body)
    )

# --- ROUTES D'AUTHENTIFICATION ---

@app.get("/", response_class=HTMLResponse)
def root():
    """Sert l'interface frontend."""
    frontend_path = BASE_DIR / "frontend_clean.html"
    try:
        with open(frontend_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Smart HIRE API is running 🚀</h1><p>Frontend not found</p>", status_code=200)

@app.post("/register")
async def register(user: UserRegister):
    # Sécurité : On bloque l'inscription si quelqu'un force le rôle 'recruiter'
    if user.role == 'recruiter':
        raise HTTPException(
            status_code=403, 
            detail="La création de compte recruteur est réservée à l'administrateur système."
        )
    
    user_id = create_user(user.email, user.password, user.name, 'candidate')
    
    if user_id is None:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    
    return {
        "message": "Inscription réussie",
        "user_id": user_id,
        "email": user.email,
        "name": user.name,
        "role": user.role
    }

@app.post("/login")
async def login(credentials: UserLogin):
    """Connexion d'un utilisateur."""
    user = authenticate_user(credentials.email, credentials.password)
    
    if user is None:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    return {
        "message": "Connexion réussie",
        "user": user
    }

# --- ROUTES RECRUTEUR ---

@app.post("/offers/draft")
async def create_offer_draft(offer: JobOfferDraft):
    """
    MODIFICATION : Génère un brouillon d'annonce expert avec tous les paramètres.
    """
    # Vérifier que l'utilisateur est bien un recruteur
    user = get_user_by_id(offer.recruiter_id)
    if not user or user['role'] != 'recruiter':
        raise HTTPException(status_code=403, detail="Seuls les recruteurs peuvent créer des offres")
    
    # Génération de l'annonce par l'IA avec la nouvelle signature de fonction
    ad_content = matcher.generate_job_ad(
        title=offer.title,
        city=offer.city,
        contract=offer.contract,
        experience=offer.experience,
        education=offer.education,
        technical_skills=offer.technical_skills,
        soft_skills=offer.soft_skills,
        missions=offer.missions,
        salary=offer.salary,
        benefits=offer.benefits,
        work_mode=offer.work_mode,
        languages=offer.languages
    )
    
    # Retourne les données pour affichage dans le frontend
    return {
        "title": offer.title,
        "description": ad_content,
        "contract": offer.contract,
        "skills": offer.technical_skills,
        "message": "Annonce experte générée. Vous pouvez la peaufiner avant publication."
    }
@app.post("/offers/publish")
async def publish_offer(offer: JobOfferPublish):
    user = get_user_by_id(offer.recruiter_id)
    if not user or user['role'] != 'recruiter':
        raise HTTPException(status_code=403, detail="Interdit")
    
    conn = get_connection()
    cursor = conn.cursor()
    # On insère maintenant les nouvelles colonnes
    cursor.execute("""
    INSERT INTO offers (
        recruiter_id, title, city, experience, education, 
        salary, description, contract_type, skills
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    offer.recruiter_id, offer.title, offer.city, offer.experience, 
    offer.education, offer.salary, offer.description, offer.contract, offer.skills
))
    offer_id = cursor.lastrowid
    conn.commit()
    # Récupérer l'offre insérée pour renvoyer toutes les infos utiles au frontend
    cursor.execute("""
        SELECT id, title, contract_type, status, created_at, city, experience, education, salary, description
        FROM offers
        WHERE id = ?
    """, (offer_id,))
    row = cursor.fetchone()
    conn.close()
    
    created_offer = {
        "id": row[0],
        "title": row[1],
        "contract": row[2],
        "status": row[3],
        "created_at": row[4],
        "city": row[5],
        "experience": row[6],
        "education": row[7],
        "salary": row[8],
        "description": row[9],
    }
    
    return {"offer": created_offer, "message": "Offre publiée avec succès"}

@app.get("/recruiter/{recruiter_id}/offers")
async def get_recruiter_offers(recruiter_id: int):
    """Récupère toutes les offres d'un recruteur avec les nouveaux détails."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # On ajoute city, experience, education et salary dans le SELECT
    cursor.execute("""
        SELECT id, title, contract_type, status, created_at, 
               city, experience, education, salary, description
        FROM offers 
        WHERE recruiter_id = ? 
        ORDER BY created_at DESC
    """, (recruiter_id,))
    
    offers = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": o[0],
            "title": o[1],
            "contract": o[2],
            "status": o[3],
            "created_at": o[4],
            "city": o[5],
            "experience": o[6],
            "education": o[7],
            "salary": o[8],
            "description": o[9]
        }
        for o in offers
    ]

@app.get("/offers/{offer_id}/applications")
async def get_offer_applications(offer_id: int):
    """
    Récupère TOUTES les candidatures pour une offre (pas de limite).
    MODIFICATION 2: Les scores sont visibles (réservé au recruteur).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            a.id, 
            a.candidate_id,
            u.name, 
            u.email,
            a.filename, 
            a.score, 
            a.justification,
            a.status,
            a.created_at
        FROM applications a
        JOIN users u ON a.candidate_id = u.id
        WHERE a.offer_id = ?
        ORDER BY a.score DESC
    """, (offer_id,))
    
    applications = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": app[0],
            "candidate_id": app[1],
            "candidate_name": app[2],
            "candidate_email": app[3],
            "filename": app[4],
            "score": app[5],
            "justification": app[6],
            "status": app[7],
            "created_at": app[8]
        }
        for app in applications
    ]

@app.post("/offers/{offer_id}/accept-multiple")
async def accept_multiple_candidates(
    offer_id: int, 
    application_ids: List[int] = Form(...)
):
    """
    MODIFICATION 3: Accepte plusieurs candidats à la fois.
    Tous les autres candidats reçoivent automatiquement un refus.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Récupérer l'offre
        cursor.execute("SELECT title, recruiter_id FROM offers WHERE id = ?", (offer_id,))
        offer = cursor.fetchone()
        if not offer:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
        
        job_title = offer[0]
        
        # 2. Récupérer les candidats acceptés
        placeholders = ','.join('?' * len(application_ids))
        cursor.execute(f"""
            SELECT a.id, u.name, u.email 
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.id IN ({placeholders})
        """, application_ids)
        
        accepted_candidates = cursor.fetchall()
        if not accepted_candidates:
            raise HTTPException(status_code=404, detail="Aucune candidature trouvée")
        
        emails_sent = 0
        
        # 3. Mettre à jour et envoyer les emails d'acceptation
        for app_id, name, email in accepted_candidates:
            cursor.execute(
                "UPDATE applications SET status = 'accepted' WHERE id = ?",
                (app_id,)
            )
            success, msg = send_acceptance_email(email, name, job_title)
            if success:
                log_email_internal(conn, email, f"✓ Acceptation {job_title}", msg)
                emails_sent += 1
            else:
                log_email_internal(conn, email, f"✗ Erreur acceptation {job_title}", msg)
        
        # 4. Récupérer tous les candidats NON acceptés
        cursor.execute(f"""
            SELECT u.name, u.email, a.id
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.offer_id = ? AND a.id NOT IN ({placeholders})
        """, [offer_id] + application_ids)
        
        rejected_candidates = cursor.fetchall()
        
        # 5. Envoyer les emails de refus automatiques
        for name, email, app_id in rejected_candidates:
            cursor.execute(
                "UPDATE applications SET status = 'rejected' WHERE id = ?",
                (app_id,)
            )
            success, msg = send_rejection_email(email, name, job_title)
            if success:
                log_email_internal(conn, email, f"✓ Refus {job_title}", msg)
                emails_sent += 1
            else:
                log_email_internal(conn, email, f"✗ Erreur refus {job_title}", msg)
        
        # 6. Fermer l'offre
        cursor.execute("UPDATE offers SET status = 'closed' WHERE id = ?", (offer_id,))
        
        # 7. Commit toutes les modifications
        conn.commit()
        
        return {
            "message": f"{len(accepted_candidates)} candidat(s) accepté(s) avec succès",
            "accepted_count": len(accepted_candidates),
            "rejected_count": len(rejected_candidates),
            "emails_sent": emails_sent,
            "total_emails": len(accepted_candidates) + len(rejected_candidates)
        }
    
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


@app.post("/offers/{offer_id}/reject-multiple")
async def reject_multiple_candidates(offer_id: int, action: ApplicationAction): # <--- Changement ici
    application_ids = action.application_ids # On récupère la liste depuis l'objet action
    
    if not application_ids:
        raise HTTPException(status_code=400, detail="Aucune candidature sélectionnée")

    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(application_ids))

    try:
        # Récupérer le titre de l'offre
        cursor.execute("SELECT title FROM offers WHERE id = ?", (offer_id,))
        offer = cursor.fetchone()
        if not offer:
            raise HTTPException(status_code=404, detail="Offre introuvable")
        job_title = offer[0]

        # Récupérer les infos des candidats
        cursor.execute(f"""
            SELECT u.name, u.email, a.id
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.id IN ({placeholders})
        """, application_ids)

        candidates = cursor.fetchall()
        
        emails_sent = 0
        for name, email, app_id in candidates:
            # Mettre à jour le statut en base
            cursor.execute(
                "UPDATE applications SET status = 'rejected' WHERE id = ?",
                (app_id,)
            )
            # ENVOI DE L'EMAIL
            success, msg = send_rejection_email(email, name, job_title)
            
            if success:
                log_email_internal(conn, email, f"✓ Refus {job_title}", msg)
                emails_sent += 1
            else:
                # Log l'erreur si l'email ne part pas (mauvais mot de passe app, etc.)
                log_email_internal(conn, email, f"✗ Erreur refus {job_title}", msg)

        conn.commit()
        return {"message": f"{len(candidates)} refus traités", "emails_sent": emails_sent}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
# --- ROUTES CANDIDAT ---

@app.get("/offers")
async def get_all_active_offers():
    """Récupère toutes les offres actives avec les nouveaux détails pour les candidats."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ajout de city, experience, education, salary dans le SELECT
    cursor.execute("""
        SELECT o.id, o.title, o.description, o.contract_type, o.skills, 
               u.name as recruiter_name, o.city, o.experience, o.salary
        FROM offers o
        JOIN users u ON o.recruiter_id = u.id
        WHERE o.status = 'active'
        ORDER BY o.created_at DESC
    """)
    
    offers = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": o[0],
            "title": o[1],
            "description": o[2],
            "contract": o[3],
            "skills": o[4],
            "recruiter": o[5],
            "city": o[6],        # NOUVEAU
            "experience": o[7],  # NOUVEAU
            "salary": o[8]       # NOUVEAU
        }
        for o in offers
    ]

@app.post("/apply")
async def apply_to_offer(
    candidate_id: int = Form(...),
    offer_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Un candidat postule à une offre en uploadant son CV."""
    
    # Vérifier que l'utilisateur est bien un candidat
    user = get_user_by_id(candidate_id)
    if not user or user['role'] != 'candidate':
        raise HTTPException(status_code=403, detail="Seuls les candidats peuvent postuler")
    
    # Vérifier que l'offre existe et est active
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description, status FROM offers WHERE id = ?", (offer_id,))
    offer = cursor.fetchone()
    
    if not offer:
        conn.close()
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    if offer[1] != 'active':
        conn.close()
        raise HTTPException(status_code=400, detail="Cette offre n'est plus active")
    
    job_desc = offer[0]
    
    # Vérifier si le candidat a déjà postulé
    cursor.execute(
        "SELECT id FROM applications WHERE candidate_id = ? AND offer_id = ?",
        (candidate_id, offer_id)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Vous avez déjà postulé à cette offre")
    
    # Sauvegarder le CV
    candidate_dir = UPLOAD_DIR / str(candidate_id)
    candidate_dir.mkdir(exist_ok=True)
    file_path = candidate_dir / f"{offer_id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Analyse du CV avec l'IA
    score, justification = matcher.get_score(str(file_path), job_desc)
    
    # Enregistrer la candidature
    cursor.execute(
        """INSERT INTO applications 
        (candidate_id, offer_id, filename, file_path, score, justification) 
        VALUES (?, ?, ?, ?, ?, ?)""",
        (candidate_id, offer_id, file.filename, str(file_path), score, justification)
    )
    
    conn.commit()
    conn.close()
    
    # Retourner un message de succès (l'analyse reste cachée pour le candidat)
    return {
        "message": "Candidature envoyée avec succès. Le recruteur étudiera votre profil."
    }

@app.get("/candidate/{candidate_id}/applications")
async def get_candidate_applications(candidate_id: int):
    """
    Récupère toutes les candidatures d'un candidat.
    MODIFICATION 2: Le score n'est PAS retourné au candidat.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            a.id,
            a.offer_id,
            o.title,
            o.contract_type,
            a.status,
            a.created_at,
            a.score,
            a.justification
        FROM applications a
        JOIN offers o ON a.offer_id = o.id
        WHERE a.candidate_id = ?
        ORDER BY a.created_at DESC
    """, (candidate_id,))
    
    applications = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": app[0],
            "offer_id": app[1],
            "job_title": app[2],
            "contract": app[3],
            "status": app[4],
            "applied_at": app[5],
            "score": app[6],
            "justification": app[7]
        }
        for app in applications
    ]

# --- ROUTE POUR VOIR LES DÉTAILS D'UNE OFFRE ---

@app.get("/offers/{offer_id}")
async def get_offer_detail(offer_id: int):
    """Affiche les détails complets d'une offre (Vue Candidat/Public)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # On récupère absolument tout pour la page de détail
    cursor.execute("""
        SELECT o.title, o.description, o.contract_type, o.skills, o.status, 
               u.name, o.city, o.experience, o.education, o.salary
        FROM offers o
        JOIN users u ON o.recruiter_id = u.id
        WHERE o.id = ?
    """, (offer_id,))
    
    offer = cursor.fetchone()
    conn.close()
    
    if not offer:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    return {
        "title": offer[0],
        "description": offer[1],
        "contract": offer[2],
        "skills": offer[3],
        "status": offer[4],
        "recruiter": offer[5],
        "city": offer[6],        # NOUVEAU
        "experience": offer[7],  # NOUVEAU
        "education": offer[8],   # NOUVEAU
        "salary": offer[9]       # NOUVEAU
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)