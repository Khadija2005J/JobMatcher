import sqlite3
import os
from pathlib import Path
from datetime import datetime
import hashlib
from typing import Optional, List
import bcrypt

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe en clair par rapport au hash bcrypt stocké."""
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Chemins de fichiers
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "smart_hire.db"

def get_connection():
    """Établit la connexion et crée le dossier data si nécessaire."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def hash_password(password: str) -> str:
    """Hash un mot de passe avec SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialise la structure de la base de données complète."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Table Users (Recruteurs et Candidats)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('recruiter', 'candidate')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Table pour les offres d'emploi
    # Dans la fonction init_db()

# 2. Table pour les offres d'emploi (Version Optimisée)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recruiter_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    city TEXT,                 -- NOUVEAU
    experience TEXT,           -- NOUVEAU
    education TEXT,            -- NOUVEAU
    salary TEXT,               -- NOUVEAU
    description TEXT,          -- Contiendra l'annonce générée par l'IA
    contract_type TEXT,
    skills TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'closed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recruiter_id) REFERENCES users(id)
    )
    """)
    
    # 3. Table pour les candidatures (CVs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        offer_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        score REAL,
        justification TEXT,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES users(id),
        FOREIGN KEY (offer_id) REFERENCES offers(id),
        UNIQUE(candidate_id, offer_id)
    )
    """)
    
    # 4. Table pour les emails envoyés
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        status TEXT DEFAULT 'sent',
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 5. Table pour les tokens de réinitialisation de mot de passe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        used BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # 6. Table pour les notifications in-app
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notif_type TEXT DEFAULT 'info',
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # 7. Table pour les favoris (candidat ↔ offre)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        offer_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(candidate_id, offer_id),
        FOREIGN KEY (candidate_id) REFERENCES users(id),
        FOREIGN KEY (offer_id) REFERENCES offers(id)
    )
    """)
    
    # 8. Table pour les entretiens
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        recruiter_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        interview_date TIMESTAMP NOT NULL,
        duration INTEGER DEFAULT 60,
        status TEXT DEFAULT 'proposed' CHECK(status IN ('proposed', 'accepted', 'rejected', 'completed', 'cancelled')),
        meeting_type TEXT DEFAULT 'physical' CHECK(meeting_type IN ('physical', 'zoom', 'teams', 'phone')),
        meeting_url TEXT,
        meeting_id TEXT,
        location TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications(id),
        FOREIGN KEY (recruiter_id) REFERENCES users(id),
        FOREIGN KEY (candidate_id) REFERENCES users(id)
    )
    """)
    
    # 9. Table pour les créneaux horaires proposés
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS time_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id INTEGER,
        proposed_by INTEGER NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        status TEXT DEFAULT 'proposed' CHECK(status IN ('proposed', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
        FOREIGN KEY (proposed_by) REFERENCES users(id)
    )
    """)
    
    # 10. Table pour les rappels d'entretiens
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        reminder_time TIMESTAMP NOT NULL,
        sent BOOLEAN DEFAULT 0,
        reminder_type TEXT DEFAULT 'email' CHECK(reminder_type IN ('email', 'notification', 'both')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Base de données initialisée avec succès!")

def create_user(email: str, password: str, name: str, role: str):
    """Crée un nouvel utilisateur."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        cursor.execute(
            "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)",
            (email, hashed_pw, name, role)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    """Authentifie un utilisateur et retourne ses infos."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = hash_password(password)
    cursor.execute(
        "SELECT id, email, name, role FROM users WHERE email = ? AND password = ?",
        (email, hashed_pw)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user[0],
            "email": user[1],
            "name": user[2],
            "role": user[3]
        }
    return None

def get_user_by_id(user_id: int):
    """Récupère un utilisateur par son ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user[0],
            "email": user[1],
            "name": user[2],
            "role": user[3]
        }
    return None

def log_email(recipient_email: str, subject: str, body: str):
    """Enregistre un email envoyé."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO emails (recipient_email, subject, body) VALUES (?, ?, ?)",
        (recipient_email, subject, body)
    )
    conn.commit()
    conn.close()

def get_user_by_email(email: str):
    """Récupère un utilisateur par son email."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, role FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            "id": user[0],
            "email": user[1],
            "name": user[2],
            "role": user[3]
        }
    return None

def create_password_reset_token(user_id: int, token: str, expires_at: str):
    """Crée un token de réinitialisation de mot de passe."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_password_reset_token(token: str):
    """Récupère un token de réinitialisation s'il est valide."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_id, expires_at, used 
           FROM password_reset_tokens 
           WHERE token = ?""",
        (token,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "user_id": result[0],
            "expires_at": result[1],
            "used": result[2]
        }
    return None

def mark_token_as_used(token: str):
    """Marque un token comme utilisé."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE password_reset_tokens SET used = 1 WHERE token = ?",
        (token,)
    )
    conn.commit()
    conn.close()

def update_user_password(user_id: int, new_password: str):
    """Met à jour le mot de passe d'un utilisateur."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (hashed_pw, user_id)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

# --- Notifications ---

def create_notification(user_id: int, title: str, message: str, notif_type: str = "info") -> bool:
    """Crée une notification pour un utilisateur."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO notifications (user_id, title, message, notif_type)
            VALUES (?, ?, ?, ?)""",
            (user_id, title, message, notif_type)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_notifications(user_id: int, unread_only: bool = False):
    """Récupère les notifications d'un utilisateur."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """SELECT id, title, message, notif_type, is_read, created_at
               FROM notifications
               WHERE user_id = ?"""
    params = [user_id]
    if unread_only:
        query += " AND is_read = 0"
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "title": r[1],
            "message": r[2],
            "type": r[3],
            "is_read": bool(r[4]),
            "created_at": r[5]
        }
        for r in rows
    ]


def mark_notifications_read(user_id: int, notification_ids: Optional[List[int]] = None):
    """Marque comme lues toutes les notifications d'un utilisateur, ou une liste donnée."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if notification_ids:
            placeholders = ','.join('?' * len(notification_ids))
            cursor.execute(
                f"UPDATE notifications SET is_read = 1 WHERE user_id = ? AND id IN ({placeholders})",
                [user_id] + notification_ids
            )
        else:
            cursor.execute(
                "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
                (user_id,)
            )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()
# --- Favoris ---

def toggle_favorite(candidate_id, offer_id):
    """Ajoute ou retire un favori. Retourne le statut ('added' ou 'removed')."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM favorites WHERE candidate_id = ? AND offer_id = ?",
            (candidate_id, offer_id)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "DELETE FROM favorites WHERE candidate_id = ? AND offer_id = ?",
                (candidate_id, offer_id)
            )
            conn.commit()
            return "removed"
        cursor.execute(
            "INSERT OR IGNORE INTO favorites (candidate_id, offer_id) VALUES (?, ?)",
            (candidate_id, offer_id)
        )
        conn.commit()
        return "added"
    except Exception:
        return None
    finally:
        conn.close()


def get_favorites(candidate_id):
    """Liste les offres mises en favori par un candidat."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT o.id, o.title, o.description, o.contract_type, o.skills,
               u.name as recruiter_name, o.city, o.experience, o.salary
        FROM favorites f
        JOIN offers o ON f.offer_id = o.id
        JOIN users u ON o.recruiter_id = u.id
        WHERE f.candidate_id = ?
        ORDER BY f.created_at DESC
        """,
        (candidate_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "contract": r[3],
            "skills": r[4],
            "recruiter": r[5],
            "city": r[6],
            "experience": r[7],
            "salary": r[8]
        }
        for r in rows
    ]
# --- Gestion des Entretiens ---

def create_interview(application_id: int, recruiter_id: int, candidate_id: int, 
                    title: str, interview_date: str, duration: int = 60,
                    meeting_type: str = "physical", description: str = None,
                    location: str = None):
    """Crée un nouvel entretien."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO interviews 
            (application_id, recruiter_id, candidate_id, title, description, 
             interview_date, duration, meeting_type, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (application_id, recruiter_id, candidate_id, title, description,
             interview_date, duration, meeting_type, location)
        )
        interview_id = cursor.lastrowid
        conn.commit()
        return interview_id
    except Exception as e:
        print(f"Erreur création entretien: {e}")
        return None
    finally:
        conn.close()

def get_interviews(user_id: int, role: str, status: str = None):
    """Récupère les entretiens d'un utilisateur (recruiter ou candidate)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if role == "recruiter":
        query = """
        SELECT i.id, i.title, i.description, i.interview_date, i.duration, 
               i.status, i.meeting_type, i.meeting_url, i.location, i.notes,
               i.application_id, i.candidate_id, u.name as candidate_name, u.email as candidate_email,
               o.title as offer_title
        FROM interviews i
        JOIN users u ON i.candidate_id = u.id
        JOIN applications a ON i.application_id = a.id
        JOIN offers o ON a.offer_id = o.id
        WHERE i.recruiter_id = ?
        """
    else:  # candidate
        query = """
        SELECT i.id, i.title, i.description, i.interview_date, i.duration,
               i.status, i.meeting_type, i.meeting_url, i.location, i.notes,
               i.application_id, i.recruiter_id, u.name as recruiter_name, u.email as recruiter_email,
               o.title as offer_title
        FROM interviews i
        JOIN users u ON i.recruiter_id = u.id
        JOIN applications a ON i.application_id = a.id
        JOIN offers o ON a.offer_id = o.id
        WHERE i.candidate_id = ?
        """
    
    params = [user_id]
    if status:
        query += " AND i.status = ?"
        params.append(status)
    
    query += " ORDER BY i.interview_date ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "interview_date": r[3],
            "duration": r[4],
            "status": r[5],
            "meeting_type": r[6],
            "meeting_url": r[7],
            "location": r[8],
            "notes": r[9],
            "application_id": r[10],
            "other_user_id": r[11],
            "other_user_name": r[12],
            "other_user_email": r[13],
            "offer_title": r[14]
        }
        for r in rows
    ]

def update_interview_status(interview_id: int, status: str, notes: str = None):
    """Met à jour le statut d'un entretien."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if notes:
            cursor.execute(
                """UPDATE interviews 
                SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (status, notes, interview_id)
            )
        else:
            cursor.execute(
                """UPDATE interviews 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (status, interview_id)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Erreur mise à jour entretien: {e}")
        return False
    finally:
        conn.close()

def update_interview_meeting(interview_id: int, meeting_url: str, meeting_id: str = None):
    """Met à jour les informations de réunion (Zoom/Teams)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """UPDATE interviews 
            SET meeting_url = ?, meeting_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""",
            (meeting_url, meeting_id, interview_id)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

# --- Gestion des Créneaux Horaires ---

def create_time_slot(interview_id: int, proposed_by: int, start_time: str, end_time: str):
    """Crée un créneau horaire proposé."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO time_slots 
            (interview_id, proposed_by, start_time, end_time)
            VALUES (?, ?, ?, ?)""",
            (interview_id, proposed_by, start_time, end_time)
        )
        slot_id = cursor.lastrowid
        conn.commit()
        return slot_id
    except Exception:
        return None
    finally:
        conn.close()

def get_time_slots(interview_id: int):
    """Récupère les créneaux proposés pour un entretien."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, proposed_by, start_time, end_time, status, created_at
        FROM time_slots
        WHERE interview_id = ?
        ORDER BY start_time ASC""",
        (interview_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "proposed_by": r[1],
            "start_time": r[2],
            "end_time": r[3],
            "status": r[4],
            "created_at": r[5]
        }
        for r in rows
    ]

def accept_time_slot(slot_id: int, interview_id: int):
    """Accepte un créneau horaire et met à jour l'entretien."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Récupérer les infos du créneau
        cursor.execute(
            "SELECT start_time FROM time_slots WHERE id = ?",
            (slot_id,)
        )
        slot = cursor.fetchone()
        if not slot:
            return False
        
        # Rejeter les autres créneaux
        cursor.execute(
            """UPDATE time_slots 
            SET status = 'rejected'
            WHERE interview_id = ? AND id != ?""",
            (interview_id, slot_id)
        )
        
        # Accepter le créneau sélectionné
        cursor.execute(
            "UPDATE time_slots SET status = 'accepted' WHERE id = ?",
            (slot_id,)
        )
        
        # Mettre à jour la date de l'entretien
        cursor.execute(
            """UPDATE interviews 
            SET interview_date = ?, status = 'accepted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""",
            (slot[0], interview_id)
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erreur acceptation créneau: {e}")
        return False
    finally:
        conn.close()

# --- Gestion des Rappels ---

def create_reminder(interview_id: int, user_id: int, reminder_time: str, reminder_type: str = "both"):
    """Crée un rappel pour un entretien."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO interview_reminders 
            (interview_id, user_id, reminder_time, reminder_type)
            VALUES (?, ?, ?, ?)""",
            (interview_id, user_id, reminder_time, reminder_type)
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        return reminder_id
    except Exception:
        return None
    finally:
        conn.close()

def get_pending_reminders():
    """Récupère tous les rappels non envoyés dont l'heure est passée."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.id, r.interview_id, r.user_id, r.reminder_type,
               i.title, i.interview_date, i.location, i.meeting_url,
               u.email, u.name
        FROM interview_reminders r
        JOIN interviews i ON r.interview_id = i.id
        JOIN users u ON r.user_id = u.id
        WHERE r.sent = 0 AND r.reminder_time <= datetime('now')
        ORDER BY r.reminder_time ASC"""
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0],
            "interview_id": r[1],
            "user_id": r[2],
            "reminder_type": r[3],
            "interview_title": r[4],
            "interview_date": r[5],
            "location": r[6],
            "meeting_url": r[7],
            "user_email": r[8],
            "user_name": r[9]
        }
        for r in rows
    ]

def mark_reminder_sent(reminder_id: int):
    """Marque un rappel comme envoyé."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE interview_reminders SET sent = 1 WHERE id = ?",
            (reminder_id,)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()