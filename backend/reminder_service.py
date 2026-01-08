"""
Service de rappels automatiques pour les entretiens
Envoie des emails et notifications avant les entretiens
"""
import asyncio
from datetime import datetime, timedelta
from database import get_pending_reminders, mark_reminder_sent, create_notification
from email_service import send_email
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReminderService:
    """Service pour envoyer des rappels automatiques."""
    
    def __init__(self):
        self.running = False
    
    def format_interview_date(self, date_str: str) -> str:
        """Formate une date pour l'affichage."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y à %H:%M")
        except:
            return date_str
    
    async def send_reminder_email(self, reminder: dict):
        """Envoie un email de rappel."""
        try:
            subject = f"Rappel: Entretien {reminder['interview_title']}"
            
            date_formatted = self.format_interview_date(reminder['interview_date'])
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2 style="color: #2563eb;">Rappel d'Entretien</h2>
                
                <p>Bonjour {reminder['user_name']},</p>
                
                <p>Ceci est un rappel pour votre entretien :</p>
                
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1f2937;">{reminder['interview_title']}</h3>
                    <p style="margin: 10px 0;">
                        <strong>📅 Date :</strong> {date_formatted}
                    </p>
            """
            
            if reminder.get('location'):
                body += f"""
                    <p style="margin: 10px 0;">
                        <strong>📍 Lieu :</strong> {reminder['location']}
                    </p>
                """
            
            if reminder.get('meeting_url'):
                body += f"""
                    <p style="margin: 10px 0;">
                        <strong>🔗 Lien de réunion :</strong><br>
                        <a href="{reminder['meeting_url']}" style="color: #2563eb; word-break: break-all;">
                            {reminder['meeting_url']}
                        </a>
                    </p>
                """
            
            body += """
                </div>
                
                <p>Nous vous souhaitons bonne chance !</p>
                
                <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                    Smart HIRE - Système de recrutement intelligent
                </p>
            </body>
            </html>
            """
            
            success = send_email(reminder['user_email'], subject, body)
            
            if success:
                logger.info(f"✅ Email de rappel envoyé à {reminder['user_email']}")
            else:
                logger.error(f"❌ Échec envoi email à {reminder['user_email']}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email de rappel: {e}")
            return False
    
    async def send_reminder_notification(self, reminder: dict):
        """Envoie une notification in-app."""
        try:
            date_formatted = self.format_interview_date(reminder['interview_date'])
            
            message = f"Votre entretien '{reminder['interview_title']}' aura lieu le {date_formatted}"
            
            if reminder.get('location'):
                message += f" à {reminder['location']}"
            
            success = create_notification(
                user_id=reminder['user_id'],
                title="Rappel d'Entretien",
                message=message,
                notif_type="reminder"
            )
            
            if success:
                logger.info(f"✅ Notification envoyée à l'utilisateur {reminder['user_id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erreur création notification: {e}")
            return False
    
    async def process_pending_reminders(self):
        """Traite tous les rappels en attente."""
        try:
            reminders = get_pending_reminders()
            
            if not reminders:
                logger.debug("Aucun rappel en attente")
                return
            
            logger.info(f"📬 {len(reminders)} rappel(s) à traiter")
            
            for reminder in reminders:
                success = False
                
                reminder_type = reminder.get('reminder_type', 'both')
                
                if reminder_type in ['email', 'both']:
                    email_success = await self.send_reminder_email(reminder)
                    success = email_success
                
                if reminder_type in ['notification', 'both']:
                    notif_success = await self.send_reminder_notification(reminder)
                    if reminder_type == 'notification':
                        success = notif_success
                    else:
                        success = success or notif_success
                
                # Marquer le rappel comme envoyé même en cas d'échec partiel
                # pour éviter les envois multiples
                mark_reminder_sent(reminder['id'])
                
                logger.info(f"✅ Rappel {reminder['id']} traité")
                
                # Petit délai entre les envois
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement rappels: {e}")
    
    async def run(self, interval: int = 60):
        """
        Lance le service de rappels en continu.
        
        Args:
            interval: Intervalle entre chaque vérification (en secondes)
        """
        self.running = True
        logger.info(f"🚀 Service de rappels démarré (vérification toutes les {interval}s)")
        
        while self.running:
            try:
                await self.process_pending_reminders()
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de rappels: {e}")
            
            await asyncio.sleep(interval)
    
    def stop(self):
        """Arrête le service de rappels."""
        self.running = False
        logger.info("⏹️ Service de rappels arrêté")

# Instance globale
reminder_service = ReminderService()

async def start_reminder_service():
    """Démarre le service de rappels en arrière-plan."""
    await reminder_service.run()
