import sqlite3
import hashlib
import os

def hash_password(password):
    """Hache le mot de passe en utilisant SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_recruiter(email, password, name):
    conn = None
    try:
        # --- CORRECTION DU CHEMIN SELON TON IMAGE ---
        # Le script est dans 'backend/' et la DB est dans 'backend/data/'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "data", "smart_hire.db") 

        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérification de la table 'users'
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print(f"❌ Erreur : La table 'users' n'existe pas dans {db_path}")
            return

        # Hachage et insertion
        hashed_pw = hash_password(password)
        query = "INSERT INTO users (email, password, name, role) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (email.strip(), hashed_pw, name.strip(), 'recruiter'))
        
        conn.commit()
        print(f"✅ Recruteur '{name}' ajouté avec succès !")
        print(f"📍 Base de données utilisée : {db_path}")
    
    except sqlite3.IntegrityError:
        print(f"❌ Erreur : L'email '{email}' existe déjà.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("\n--- AJOUT RECRUTEUR SMART-HIRE ---")
    u_name = input("Nom complet : ")
    u_email = input("Email : ")
    u_pass = input("Mot de passe : ")
    
    if u_name and u_email and u_pass:
        add_recruiter(u_email, u_pass, u_name)
    else:
        print("⚠️ Champs incomplets.")