from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends,Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
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
    get_user_by_id, get_user_by_email, create_password_reset_token,
    get_password_reset_token, mark_token_as_used, update_user_password,
    create_notification, get_notifications, mark_notifications_read,
    toggle_favorite, get_favorites,
    create_interview, get_interviews, update_interview_status, update_interview_meeting,
    create_time_slot, get_time_slots, accept_time_slot,
    create_reminder
)
from auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from matching import CVMatcher
from email_service import send_acceptance_email, send_rejection_email, send_password_reset_email
from meeting_service import meeting_service
from report_service import report_service
from reminder_service import reminder_service
import asyncio

# Initialisation
init_db()
app = FastAPI(
    title="Smart HIRE - GenAI Edition",
    description="Système de recrutement intelligent avec IA Générative",
    version="3.0.0"
)

# Instance du moteur IA
matcher = CVMatcher()

# Démarrage du service de rappels en arrière-plan
@app.on_event("startup")
async def startup_event():
    """Démarre les services en arrière-plan au démarrage de l'application."""
    # Lancer le service de rappels toutes les 5 minutes
    asyncio.create_task(reminder_service.run(interval=300))
    print("✅ Service de rappels démarré")

@app.on_event("shutdown")
async def shutdown_event():
    """Arrête les services en arrière-plan."""
    reminder_service.stop()
    print("⏹️ Services arrêtés")

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"] est incompatible avec allow_credentials=True
    allow_origin_regex="http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["http://localhost:5173"],
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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class MarkNotifications(BaseModel):
    user_id: int
    notification_ids: Optional[List[int]] = None

class FavoriteToggle(BaseModel):
    candidate_id: int
    offer_id: int

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
async def login(response: Response,credentials: UserLogin):
    """Connexion d'un utilisateur."""
    user = authenticate_user(credentials.email, credentials.password)
    
    if user is None:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    access_token = create_access_token(data={"sub": user["id"]})
    # Use secure cookies only in production (HTTPS). In development (localhost HTTP)
    # browsers will refuse secure cookies, which breaks auth during local testing.
    secure_cookie = os.environ.get("ENV", "development") == "production"
    max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,        # 🔥 PROTECTION XSS
        secure=secure_cookie, # HTTPS ONLY in production
        samesite="lax",       # 🔥 PROTECTION CSRF (Lax permet les téléchargements)
        max_age=max_age
    )
    return {
        "message": "Connexion réussie",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "role": user.get("role")
        },
    }

@app.post("/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint compatible OAuth2 pour obtenir un token (username=email)."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Demande de réinitialisation de mot de passe."""
    import secrets
    from datetime import datetime, timedelta
    
    # Vérifier si l'utilisateur existe
    user = get_user_by_email(request.email)
    if not user:
        # Pour des raisons de sécurité, on retourne toujours un succès
        # même si l'email n'existe pas (évite l'énumération des comptes)
        return {
            "message": "Si cet email existe, un lien de réinitialisation a été envoyé."
        }
    
    # Générer un token sécurisé
    reset_token = secrets.token_urlsafe(32)
    
    # Le token expire dans 1 heure
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    
    # Enregistrer le token dans la base de données
    if not create_password_reset_token(user['id'], reset_token, expires_at):
        raise HTTPException(status_code=500, detail="Erreur lors de la création du token")
    
    # Envoyer l'email de réinitialisation
    success, message = send_password_reset_email(user['email'], user['name'], reset_token)
    
    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email")
    
    return {
        "message": "Si cet email existe, un lien de réinitialisation a été envoyé."
    }

@app.post("/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Réinitialise le mot de passe avec un token valide."""
    from datetime import datetime
    
    # Vérifier le token
    token_data = get_password_reset_token(request.token)
    
    if not token_data:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")
    
    # Vérifier si le token a déjà été utilisé
    if token_data['used']:
        raise HTTPException(status_code=400, detail="Ce lien a déjà été utilisé")
    
    # Vérifier si le token a expiré
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    if datetime.now() > expires_at:
        raise HTTPException(status_code=400, detail="Ce lien a expiré")
    
    # Valider le nouveau mot de passe
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 6 caractères")
    
    # Mettre à jour le mot de passe
    if not update_user_password(token_data['user_id'], request.new_password):
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du mot de passe")
    
    # Marquer le token comme utilisé
    mark_token_as_used(request.token)
    
    return {
        "message": "Votre mot de passe a été réinitialisé avec succès"
    }


# --- NOTIFICATIONS ---

@app.get("/users/{user_id}/notifications")
async def list_notifications(user_id: int, unread_only: bool = False):
    return get_notifications(user_id=user_id, unread_only=unread_only)


@app.post("/notifications/mark-read")
async def mark_notifications(req: MarkNotifications):
    ok = mark_notifications_read(req.user_id, req.notification_ids)
    if not ok:
        raise HTTPException(status_code=500, detail="Impossible de mettre à jour les notifications")
    return {"message": "Notifications mises à jour"}


# --- FAVORIS ---

@app.get("/candidate/{candidate_id}/favorites")
async def list_favorites(candidate_id: int):
    user = get_user_by_id(candidate_id)
    if not user or user['role'] != 'candidate':
        raise HTTPException(status_code=403, detail="Seuls les candidats peuvent consulter leurs favoris")
    return get_favorites(candidate_id)


@app.post("/favorites/toggle")
async def toggle_favorite_route(payload: FavoriteToggle):
    user = get_user_by_id(payload.candidate_id)
    if not user or user['role'] != 'candidate':
        raise HTTPException(status_code=403, detail="Seuls les candidats peuvent gérer leurs favoris")
    status = toggle_favorite(payload.candidate_id, payload.offer_id)
    if status is None:
        raise HTTPException(status_code=500, detail="Impossible de mettre à jour le favori")
    return {"status": status}

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
    # On insère maintenant les nouvelles colonnes avec status='active'
    cursor.execute("""
    INSERT INTO offers (
        recruiter_id, title, city, experience, education, 
        salary, description, contract_type, skills, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
""", (
    offer.recruiter_id, offer.title, offer.city, offer.experience, 
    offer.education, offer.salary, offer.description, offer.contract, offer.skills
))
    offer_id = cursor.lastrowid
    conn.commit()
    
    # Récupérer tous les candidats pour leur envoyer une notification
    cursor.execute("SELECT id FROM users WHERE role = 'candidate'")
    candidates = cursor.fetchall()
    
    # Créer une notification pour chaque candidat
    for (candidate_id,) in candidates:
        create_notification(
            user_id=candidate_id,
            title="Nouvelle offre d'emploi",
            message=f"Une nouvelle offre '{offer.title}' vient d'être publiée. Consultez-la maintenant !",
            notif_type="info"
        )
    
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
    action: ApplicationAction
):
    """
    MODIFICATION 3: Accepte plusieurs candidats à la fois.
    Tous les autres candidats reçoivent automatiquement un refus.
    """
    application_ids = action.application_ids
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
            SELECT a.id, u.name, u.email, a.candidate_id
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.id IN ({placeholders})
        """, application_ids)
        
        accepted_candidates = cursor.fetchall()
        if not accepted_candidates:
            raise HTTPException(status_code=404, detail="Aucune candidature trouvée")
        
        emails_sent = 0
        
        # 3. Mettre à jour et envoyer les emails d'acceptation
        for app_id, name, email, cand_id in accepted_candidates:
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
            SELECT u.name, u.email, a.id, a.candidate_id
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.offer_id = ? AND a.id NOT IN ({placeholders})
        """, [offer_id] + application_ids)
        
        rejected_candidates = cursor.fetchall()
        
        # 5. Envoyer les emails de refus automatiques
        for name, email, app_id, cand_id in rejected_candidates:
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
        conn.close()
        
        # 8. Créer les notifications APRÈS le commit (pour éviter les problèmes de transaction)
        for app_id, name, email, cand_id in accepted_candidates:
            create_notification(
                user_id=cand_id,
                title="✅ Candidature acceptée",
                message=f"Félicitations ! Votre candidature pour '{job_title}' a été acceptée.",
                notif_type="success"
            )
        
        for name, email, app_id, cand_id in rejected_candidates:
            create_notification(
                user_id=cand_id,
                title="Candidature refusée",
                message=f"Votre candidature pour '{job_title}' n'a pas été retenue cette fois-ci.",
                notif_type="warning"
            )
        
        return {
            "message": f"{len(accepted_candidates)} candidat(s) accepté(s) avec succès",
            "accepted_count": len(accepted_candidates),
            "rejected_count": len(rejected_candidates),
            "emails_sent": emails_sent,
            "total_emails": len(accepted_candidates) + len(rejected_candidates)
        }
    
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


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
            SELECT u.name, u.email, a.id, a.candidate_id
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.id IN ({placeholders})
        """, application_ids)

        candidates = cursor.fetchall()
        
        emails_sent = 0
        for name, email, app_id, cand_id in candidates:
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

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    # Création des notifications APRÈS la fermeture de la connexion (évite le verrouillage SQLite)
    for name, email, app_id, cand_id in candidates:
        create_notification(
            user_id=cand_id,
            title="Candidature refusée",
            message=f"Votre candidature pour {job_title} a été refusée.",
            notif_type="warning"
        )

    return {"message": f"{len(candidates)} refus traités", "emails_sent": emails_sent}
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
    cursor.execute("SELECT title, description, status FROM offers WHERE id = ?", (offer_id,))
    offer = cursor.fetchone()
    
    if not offer:
        conn.close()
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    if offer[2] != 'active':
        conn.close()
        raise HTTPException(status_code=400, detail="Cette offre n'est plus active")
    
    job_title = offer[0]
    job_desc = offer[1]
    
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
    
    # Récupérer l'ID du recruteur pour l'offre
    cursor.execute("SELECT recruiter_id FROM offers WHERE id = ?", (offer_id,))
    recruiter_row = cursor.fetchone()
    recruiter_id = recruiter_row[0] if recruiter_row else None
    
    # Récupérer le nom du candidat
    cursor.execute("SELECT name FROM users WHERE id = ?", (candidate_id,))
    candidate_row = cursor.fetchone()
    candidate_name = candidate_row[0] if candidate_row else "Candidat"
    
    conn.commit()
    conn.close()

    # Créer une notification pour le candidat
    create_notification(
        user_id=candidate_id,
        title="Candidature envoyée",
        message=f"Votre candidature pour l'offre '{job_title}' a été envoyée.",
        notif_type="info"
    )
    
    # Créer une notification pour le recruteur
    if recruiter_id:
        create_notification(
            user_id=recruiter_id,
            title="Nouvelle candidature",
            message=f"{candidate_name} a postulé à votre offre '{job_title}' (Score IA: {score:.1f}/100)",
            notif_type="application"
        )
    
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

# --- ROUTES POUR LA GESTION DES ENTRETIENS ---

class InterviewCreate(BaseModel):
    application_id: int
    title: str
    description: Optional[str] = None
    interview_date: str
    duration: int = 60
    meeting_type: str = "physical"  # physical, zoom, teams, phone
    location: Optional[str] = None

class InterviewStatusUpdate(BaseModel):
    status: str  # accepted, rejected, completed, cancelled
    notes: Optional[str] = None

class TimeSlotCreate(BaseModel):
    interview_id: Optional[int] = None
    start_time: str
    end_time: str

class MeetingCreate(BaseModel):
    platform: str  # zoom ou teams
    participant_email: str

@app.post("/interviews")
async def create_new_interview(interview_data: InterviewCreate, current_user: dict = Depends(get_current_user)):
    """Crée un nouvel entretien."""
    # Vérifier que l'application existe et récupérer les infos
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT a.candidate_id, a.offer_id, o.recruiter_id, o.title
        FROM applications a
        JOIN offers o ON a.offer_id = o.id
        WHERE a.id = ?
    """, (interview_data.application_id,))
    
    app_data = cursor.fetchone()
    conn.close()
    
    if not app_data:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    
    candidate_id, offer_id, recruiter_id, offer_title = app_data
    
    # Vérifier que l'utilisateur est bien le recruteur
    if current_user["role"] != "recruiter" or current_user["id"] != recruiter_id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    # Créer l'entretien
    interview_id = create_interview(
        application_id=interview_data.application_id,
        recruiter_id=recruiter_id,
        candidate_id=candidate_id,
        title=interview_data.title,
        interview_date=interview_data.interview_date,
        duration=interview_data.duration,
        meeting_type=interview_data.meeting_type,
        description=interview_data.description,
        location=interview_data.location
    )
    
    if not interview_id:
        raise HTTPException(status_code=500, detail="Erreur lors de la création de l'entretien")
    
    # Créer des notifications
    create_notification(
        user_id=candidate_id,
        title="Nouvel entretien proposé",
        message=f"Un entretien a été proposé pour l'offre '{offer_title}'",
        notif_type="interview"
    )
    
    # Créer des rappels automatiques (24h avant et 1h avant)
    from datetime import datetime, timedelta
    interview_dt = datetime.fromisoformat(interview_data.interview_date)
    
    # Rappel 24h avant
    reminder_24h = interview_dt - timedelta(hours=24)
    if reminder_24h > datetime.now():
        create_reminder(interview_id, candidate_id, reminder_24h.isoformat(), "both")
        create_reminder(interview_id, recruiter_id, reminder_24h.isoformat(), "notification")
    
    # Rappel 1h avant
    reminder_1h = interview_dt - timedelta(hours=1)
    if reminder_1h > datetime.now():
        create_reminder(interview_id, candidate_id, reminder_1h.isoformat(), "notification")
        create_reminder(interview_id, recruiter_id, reminder_1h.isoformat(), "notification")
    
    return {
        "message": "Entretien créé avec succès",
        "interview_id": interview_id
    }

@app.get("/interviews")
async def get_user_interviews(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Récupère les entretiens de l'utilisateur connecté."""
    interviews = get_interviews(current_user["id"], current_user["role"], status)
    return interviews

@app.get("/interviews/{interview_id}")
async def get_interview_detail(interview_id: int, current_user: dict = Depends(get_current_user)):
    """Récupère les détails d'un entretien."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT i.id, i.title, i.description, i.interview_date, i.duration,
               i.status, i.meeting_type, i.meeting_url, i.meeting_id, i.location, i.notes,
               i.recruiter_id, i.candidate_id, i.application_id,
               r.name as recruiter_name, r.email as recruiter_email,
               c.name as candidate_name, c.email as candidate_email,
               o.title as offer_title
        FROM interviews i
        JOIN users r ON i.recruiter_id = r.id
        JOIN users c ON i.candidate_id = c.id
        JOIN applications a ON i.application_id = a.id
        JOIN offers o ON a.offer_id = o.id
        WHERE i.id = ?
    """, (interview_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Entretien non trouvé")
    
    # Vérifier que l'utilisateur est impliqué
    if current_user["id"] not in [row[11], row[12]]:
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "interview_date": row[3],
        "duration": row[4],
        "status": row[5],
        "meeting_type": row[6],
        "meeting_url": row[7],
        "meeting_id": row[8],
        "location": row[9],
        "notes": row[10],
        "recruiter": {
            "id": row[11],
            "name": row[14],
            "email": row[15]
        },
        "candidate": {
            "id": row[12],
            "name": row[16],
            "email": row[17]
        },
        "application_id": row[13],
        "offer_title": row[18]
    }

@app.put("/interviews/{interview_id}/status")
async def update_interview_status_route(interview_id: int, update_data: InterviewStatusUpdate, 
                                       current_user: dict = Depends(get_current_user)):
    """Met à jour le statut d'un entretien."""
    success = update_interview_status(interview_id, update_data.status, update_data.notes)
    
    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour")
    
    return {"message": "Statut mis à jour avec succès"}

# --- ROUTES POUR LES CRÉNEAUX HORAIRES ---

@app.post("/interviews/{interview_id}/timeslots")
async def propose_time_slots(interview_id: int, slots: List[TimeSlotCreate], 
                            current_user: dict = Depends(get_current_user)):
    """Propose plusieurs créneaux horaires pour un entretien."""
    created_slots = []
    
    for slot in slots:
        slot_id = create_time_slot(
            interview_id=interview_id,
            proposed_by=current_user["id"],
            start_time=slot.start_time,
            end_time=slot.end_time
        )
        if slot_id:
            created_slots.append(slot_id)
    
    if not created_slots:
        raise HTTPException(status_code=500, detail="Erreur lors de la création des créneaux")
    
    return {
        "message": f"{len(created_slots)} créneau(x) proposé(s) avec succès",
        "slot_ids": created_slots
    }

@app.get("/interviews/{interview_id}/timeslots")
async def get_interview_time_slots(interview_id: int, current_user: dict = Depends(get_current_user)):
    """Récupère les créneaux proposés pour un entretien."""
    slots = get_time_slots(interview_id)
    return slots

@app.post("/timeslots/{slot_id}/accept")
async def accept_slot(slot_id: int, interview_id: int, current_user: dict = Depends(get_current_user)):
    """Accepte un créneau horaire proposé."""
    success = accept_time_slot(slot_id, interview_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de l'acceptation du créneau")
    
    return {"message": "Créneau accepté avec succès"}

# --- ROUTES POUR L'INTÉGRATION ZOOM/TEAMS ---

@app.post("/interviews/{interview_id}/meeting")
async def create_meeting_link(interview_id: int, meeting_data: MeetingCreate, 
                             current_user: dict = Depends(get_current_user)):
    """Crée un lien de réunion Zoom ou Teams pour un entretien."""
    # Récupérer les infos de l'entretien
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, interview_date, duration, recruiter_id
        FROM interviews
        WHERE id = ?
    """, (interview_id,))
    
    interview = cursor.fetchone()
    conn.close()
    
    if not interview:
        raise HTTPException(status_code=404, detail="Entretien non trouvé")
    
    title, interview_date, duration, recruiter_id = interview
    
    # Vérifier que c'est le recruteur
    if current_user["id"] != recruiter_id:
        raise HTTPException(status_code=403, detail="Seul le recruteur peut créer le lien de réunion")
    
    # Créer la réunion
    from datetime import datetime
    interview_dt = datetime.fromisoformat(interview_date)
    
    meeting_info = await meeting_service.create_meeting(
        platform=meeting_data.platform,
        title=title,
        start_time=interview_dt,
        duration=duration,
        participant_email=meeting_data.participant_email
    )
    
    if not meeting_info:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la réunion {meeting_data.platform}")
    
    # Mettre à jour l'entretien avec le lien
    success = update_interview_meeting(
        interview_id=interview_id,
        meeting_url=meeting_info["meeting_url"],
        meeting_id=meeting_info.get("meeting_id", "")
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour de l'entretien")
    
    return {
        "message": "Lien de réunion créé avec succès",
        "meeting_url": meeting_info["meeting_url"],
        "meeting_id": meeting_info.get("meeting_id", "")
    }

# --- ROUTES POUR LES RAPPORTS ET EXPORTS ---

@app.get("/reports/interviews")
async def get_interviews_report(current_user: dict = Depends(get_current_user)):
    """Génère un rapport des entretiens."""
    if current_user["role"] == "recruiter":
        data = report_service.get_recruiter_interviews_report(current_user["id"])
    else:
        data = report_service.get_candidate_interviews_report(current_user["id"])
    
    return data

@app.get("/reports/applications")
async def get_applications_report(current_user: dict = Depends(get_current_user)):
    """Génère un rapport des candidatures (recruteurs seulement)."""
    if current_user["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Réservé aux recruteurs")
    
    data = report_service.get_applications_report(current_user["id"])
    return data

@app.get("/reports/statistics")
async def get_statistics(current_user: dict = Depends(get_current_user)):
    """Génère des statistiques pour l'utilisateur."""
    if current_user["role"] == "recruiter":
        stats = report_service.get_recruiter_statistics(current_user["id"])
    else:
        stats = report_service.get_candidate_statistics(current_user["id"])
    
    return stats

@app.get("/export/interviews/csv")
async def export_interviews_csv(current_user: dict = Depends(get_current_user)):
    """Exporte les entretiens en CSV."""
    from fastapi.responses import Response
    
    if current_user["role"] == "recruiter":
        data = report_service.get_recruiter_interviews_report(current_user["id"])
    else:
        data = report_service.get_candidate_interviews_report(current_user["id"])
    
    csv_content = report_service.export_to_csv(data)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=entretiens_export.csv"
        }
    )

@app.get("/export/applications/csv")
async def export_applications_csv(current_user: dict = Depends(get_current_user)):
    """Exporte les candidatures en CSV (recruteurs seulement)."""
    from fastapi.responses import Response
    
    if current_user["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Réservé aux recruteurs")
    
    data = report_service.get_applications_report(current_user["id"])
    csv_content = report_service.export_to_csv(data)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=candidatures_export.csv"
        }
    )

# --- ROUTES POUR L'EXPORT DES CVS ET RAPPORTS DE MATCHING ---

@app.get("/offers/{offer_id}/candidates/list")
async def get_candidates_list(offer_id: int, current_user: dict = Depends(get_current_user)):
    """Récupère la liste complète des candidats pour une offre."""
    if current_user["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Réservé aux recruteurs")
    
    # Vérifier que l'offre appartient au recruteur
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT recruiter_id FROM offers WHERE id = ?", (offer_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or result[0] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Offre non trouvée ou non autorisé")
    
    candidates = report_service.get_candidates_list_for_offer(offer_id)
    return candidates

@app.get("/offers/{offer_id}/matching-report")
async def get_matching_report(offer_id: int, current_user: dict = Depends(get_current_user)):
    """Génère un rapport de matching détaillé pour une offre."""
    if current_user["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Réservé aux recruteurs")
    
    # Vérifier que l'offre appartient au recruteur
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT recruiter_id FROM offers WHERE id = ?", (offer_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or result[0] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Offre non trouvée ou non autorisé")
    
    report = report_service.get_matching_report(offer_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    return report

@app.get("/offers/{offer_id}/candidates/export-csv")
async def export_candidates_for_offer(offer_id: int, current_user: dict = Depends(get_current_user)):
    """Exporte la liste des candidats d'une offre en CSV."""
    from fastapi.responses import Response
    
    if current_user["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Réservé aux recruteurs")
    
    # Vérifier que l'offre appartient au recruteur
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT recruiter_id, title FROM offers WHERE id = ?", (offer_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or result[0] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Offre non trouvée ou non autorisé")
    
    offer_title = result[1]
    csv_content = report_service.export_candidates_csv(offer_id)
    
    if not csv_content:
        raise HTTPException(status_code=404, detail="Aucun candidat trouvé")
    
    # Nettoyer le titre pour le nom de fichier
    safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in offer_title)
    filename = f"candidats_{safe_title}_{offer_id}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/applications/{application_id}/cv")
async def download_cv(application_id: int, current_user: dict = Depends(get_current_user)):
    """Télécharge le CV d'une candidature."""
    from fastapi.responses import FileResponse
    import os
    
    # Vérifier que l'utilisateur a le droit d'accéder au CV
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.candidate_id, a.file_path, a.filename, o.recruiter_id
        FROM applications a
        JOIN offers o ON a.offer_id = o.id
        WHERE a.id = ?
    """, (application_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    
    candidate_id, file_path, filename, recruiter_id = result
    
    # Vérifier les permissions
    if current_user["role"] == "recruiter" and current_user["id"] != recruiter_id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    elif current_user["role"] == "candidate" and current_user["id"] != candidate_id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    # Construire le chemin complet
    cv_path = report_service.get_cv_path(application_id)
    
    if not cv_path or not os.path.exists(cv_path):
        raise HTTPException(status_code=404, detail="Fichier CV non trouvé")
    
    return FileResponse(
        path=cv_path,
        filename=filename,
        media_type="application/pdf"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)