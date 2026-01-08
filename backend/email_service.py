"""
Service d'envoi d'emails réels via SMTP Gmail - VERSION SÉCURISÉE
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ====================================================================
# 🔐 CONFIGURATION SÉCURISÉE VIA VARIABLES D'ENVIRONNEMENT
# ====================================================================
# Les identifiants sont maintenant dans le fichier .env (non versionné)

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# ====================================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_NAME = "Smart HIRE"

def send_email(recipient_email: str, subject: str, body: str) -> Tuple[bool, str]:
    """
    Envoie un email réel via SMTP Gmail.
    
    Returns:
        Tuple[bool, str]: (succès, message)
    """
    # Vérifier que les credentials sont configurés
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return False, "❌ Configuration SMTP manquante. Vérifiez le fichier .env"
    
    try:
        # Créer le message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        message["To"] = recipient_email
        
        # Version texte
        text_part = MIMEText(body, "plain", "utf-8")
        message.attach(text_part)
        
        # Version HTML (optionnelle, plus jolie)
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">Smart HIRE</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Recrutement Intelligent</p>
                    </div>
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                        <div style="background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                            {body.replace(chr(10), '<br>')}
                        </div>
                        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
                            © 2026 Smart HIRE - Tous droits réservés
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        html_part = MIMEText(html_body, "html", "utf-8")
        message.attach(html_part)
        
        # Connexion et envoi
        print(f"📧 Tentative d'envoi d'email à {recipient_email}...")
        print(f"📤 Utilisation du compte: {SENDER_EMAIL}")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Sécuriser la connexion
            print("🔐 Connexion sécurisée établie (TLS)")
            
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("✅ Authentification réussie")
            
            server.send_message(message)
            print(f"✅ Email envoyé avec succès à {recipient_email}")
        
        return True, f"Email envoyé avec succès à {recipient_email}"
    
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"❌ Erreur d'authentification SMTP: {str(e)}\n"
        error_msg += "Vérifiez :\n"
        error_msg += "1. Que vous avez activé la validation en 2 étapes sur Gmail\n"
        error_msg += "2. Que vous utilisez un MOT DE PASSE D'APPLICATION (pas votre mot de passe Gmail normal)\n"
        error_msg += "3. Créez-en un sur: https://myaccount.google.com/apppasswords\n"
        error_msg += "4. Que le fichier .env contient les bonnes valeurs"
        print(error_msg)
        return False, error_msg
    
    except smtplib.SMTPException as e:
        error_msg = f"❌ Erreur SMTP: {str(e)}"
        print(error_msg)
        return False, error_msg
    
    except Exception as e:
        error_msg = f"❌ Erreur lors de l'envoi: {str(e)}"
        print(error_msg)
        return False, error_msg


def send_acceptance_email(recipient_email: str, candidate_name: str, job_title: str) -> Tuple[bool, str]:
    """Envoie un email d'acceptation."""
    subject = f"🎉 Félicitations ! Votre candidature pour {job_title}"
    body = f"""Bonjour {candidate_name},

Nous avons le grand plaisir de vous informer que votre candidature pour le poste de {job_title} a été retenue !

Nous avons été très impressionnés par votre profil et vos compétences, et nous sommes convaincus que vous serez un excellent ajout à notre équipe.

Notre équipe RH vous contactera dans les prochains jours pour discuter des prochaines étapes du processus de recrutement.

Félicitations encore une fois !

Cordialement,
L'équipe Smart HIRE"""
    
    return send_email(recipient_email, subject, body)


def send_rejection_email(recipient_email: str, candidate_name: str, job_title: str) -> Tuple[bool, str]:
    """Envoie un email de refus."""
    subject = f"Votre candidature pour {job_title}"
    body = f"""Bonjour {candidate_name},

Nous vous remercions sincèrement pour l'intérêt que vous avez porté à notre poste de {job_title} et pour le temps que vous avez consacré à votre candidature.

Après avoir examiné attentivement l'ensemble des candidatures reçues, nous avons décidé de poursuivre avec d'autres profils dont l'expérience correspond plus étroitement à nos besoins actuels.

Cette décision ne remet en aucun cas en question vos compétences et votre parcours professionnel. Nous vous encourageons vivement à postuler à nos futures offres qui pourraient mieux correspondre à votre profil.

Nous vous souhaitons beaucoup de succès dans vos recherches professionnelles.

Cordialement,
L'équipe Smart HIRE"""
    
    return send_email(recipient_email, subject, body)


def send_password_reset_email(recipient_email: str, recipient_name: str, reset_token: str) -> Tuple[bool, str]:
    """Envoie un email de réinitialisation de mot de passe."""
    # Lien vers le frontend (racine) pour éviter les 404 côté Vite en dev
    reset_link = f"http://localhost:5173/?token={reset_token}"
    
    subject = "Smart HIRE - Réinitialisation de votre mot de passe"
    
    body = f"""Bonjour {recipient_name},

Vous avez demandé à réinitialiser votre mot de passe pour votre compte Smart HIRE.

Pour créer un nouveau mot de passe, cliquez sur le lien ci-dessous :

{reset_link}

Ce lien est valable pendant 1 heure.

Si vous n'avez pas demandé cette réinitialisation, vous pouvez ignorer cet email en toute sécurité.

Cordialement,
L'équipe Smart HIRE"""
    
    return send_email(recipient_email, subject, body)


def test_email_configuration():
    """Teste la configuration email"""
    print("\n" + "="*70)
    print("🔍 TEST DE CONFIGURATION EMAIL")
    print("="*70)
    print(f"\n📧 Email configuré: {SENDER_EMAIL if SENDER_EMAIL else '❌ NON CONFIGURÉ'}")
    print(f"🔑 Mot de passe configuré: {'✅ OUI' if SENDER_PASSWORD else '❌ NON'}")
    print(f"🌐 Serveur SMTP: {SMTP_SERVER}:{SMTP_PORT}")
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("\n❌ CONFIGURATION INCOMPLÈTE !")
        print("\n📝 Pour configurer:")
        print("1. Créez un fichier .env à la racine du projet")
        print("2. Ajoutez ces lignes dans le fichier .env :")
        print("   SENDER_EMAIL=votre_email@gmail.com")
        print("   SENDER_PASSWORD=votre_mot_de_passe_application")
        print("\n🔐 Pour obtenir un mot de passe d'application:")
        print("1. Allez sur https://myaccount.google.com/security")
        print("2. Activez la validation en 2 étapes")
        print("3. Allez dans 'Mots de passe d'application'")
        print("4. Créez un nouveau mot de passe pour 'Mail'")
        print("5. Copiez-collez ce mot de passe dans le fichier .env")
        print("\n⚠️  IMPORTANT: Ajoutez .env dans votre .gitignore !")
    else:
        print("\n✅ Configuration semble correcte!")
        print("\n🧪 Voulez-vous envoyer un email de test?")
        print("   Décommentez les lignes à la fin de ce fichier et relancez.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    # Afficher la configuration
    test_email_configuration()
    
    # 🧪 TEST D'ENVOI - Décommentez pour tester
    # print("\n📤 Envoi d'un email de test...")
    # success, message = send_email(
    #     "destinataire@example.com",  # ✏️ Remplacez par l'email du destinataire
    #     "Test Smart HIRE",
    #     "Ceci est un email de test depuis Smart HIRE!"
    # )
    # print(f"\n{'✅' if success else '❌'} Résultat: {message}")