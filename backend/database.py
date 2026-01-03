import sqlite3
import os
from pathlib import Path
from datetime import datetime
import hashlib

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