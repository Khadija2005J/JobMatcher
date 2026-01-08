"""
Service d'intégration pour Zoom et Microsoft Teams
"""
import os
import httpx
import json
from datetime import datetime, timedelta
from typing import Optional, Dict

class MeetingService:
    """Service pour créer des réunions Zoom ou Teams."""
    
    def __init__(self):
        # Configuration Zoom
        self.zoom_account_id = os.getenv("ZOOM_ACCOUNT_ID", "")
        self.zoom_client_id = os.getenv("ZOOM_CLIENT_ID", "")
        self.zoom_client_secret = os.getenv("ZOOM_CLIENT_SECRET", "")
        
        # Configuration Teams
        self.teams_tenant_id = os.getenv("TEAMS_TENANT_ID", "")
        self.teams_client_id = os.getenv("TEAMS_CLIENT_ID", "")
        self.teams_client_secret = os.getenv("TEAMS_CLIENT_SECRET", "")
        
        self.zoom_access_token = None
        self.teams_access_token = None
    
    async def get_zoom_token(self) -> Optional[str]:
        """Obtient un token d'accès Zoom via OAuth Server-to-Server."""
        if not all([self.zoom_account_id, self.zoom_client_id, self.zoom_client_secret]):
            print("⚠️ Configuration Zoom manquante")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://zoom.us/oauth/token",
                    params={
                        "grant_type": "account_credentials",
                        "account_id": self.zoom_account_id
                    },
                    auth=(self.zoom_client_id, self.zoom_client_secret)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.zoom_access_token = data.get("access_token")
                    return self.zoom_access_token
                else:
                    print(f"❌ Erreur Zoom OAuth: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"❌ Erreur connexion Zoom: {e}")
            return None
    
    async def create_zoom_meeting(self, title: str, start_time: datetime, duration: int = 60,
                                  participant_email: str = None) -> Optional[Dict]:
        """
        Crée une réunion Zoom.
        
        Args:
            title: Titre de la réunion
            start_time: Date et heure de début
            duration: Durée en minutes
            participant_email: Email du participant (optionnel)
        
        Returns:
            Dict avec join_url, meeting_id, password
        """
        token = await self.get_zoom_token()
        if not token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                # Format ISO 8601 pour Zoom
                start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
                
                payload = {
                    "topic": title,
                    "type": 2,  # Scheduled meeting
                    "start_time": start_time_str,
                    "duration": duration,
                    "timezone": "Europe/Paris",
                    "settings": {
                        "host_video": True,
                        "participant_video": True,
                        "join_before_host": False,
                        "mute_upon_entry": True,
                        "waiting_room": True,
                        "auto_recording": "none"
                    }
                }
                
                response = await client.post(
                    "https://api.zoom.us/v2/users/me/meetings",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return {
                        "meeting_url": data.get("join_url"),
                        "meeting_id": str(data.get("id")),
                        "password": data.get("password", ""),
                        "host_url": data.get("start_url")
                    }
                else:
                    print(f"❌ Erreur création Zoom: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Erreur création meeting Zoom: {e}")
            return None
    
    async def get_teams_token(self) -> Optional[str]:
        """Obtient un token d'accès Microsoft Teams."""
        if not all([self.teams_tenant_id, self.teams_client_id, self.teams_client_secret]):
            print("⚠️ Configuration Teams manquante")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://login.microsoftonline.com/{self.teams_tenant_id}/oauth2/v2.0/token",
                    data={
                        "client_id": self.teams_client_id,
                        "client_secret": self.teams_client_secret,
                        "scope": "https://graph.microsoft.com/.default",
                        "grant_type": "client_credentials"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.teams_access_token = data.get("access_token")
                    return self.teams_access_token
                else:
                    print(f"❌ Erreur Teams OAuth: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"❌ Erreur connexion Teams: {e}")
            return None
    
    async def create_teams_meeting(self, title: str, start_time: datetime, duration: int = 60,
                                   participant_email: str = None) -> Optional[Dict]:
        """
        Crée une réunion Microsoft Teams.
        
        Args:
            title: Titre de la réunion
            start_time: Date et heure de début
            duration: Durée en minutes
            participant_email: Email du participant (optionnel)
        
        Returns:
            Dict avec join_url, meeting_id
        """
        token = await self.get_teams_token()
        if not token:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                end_time = start_time + timedelta(minutes=duration)
                
                payload = {
                    "subject": title,
                    "startDateTime": start_time.isoformat(),
                    "endDateTime": end_time.isoformat(),
                    "participants": {
                        "attendees": []
                    }
                }
                
                if participant_email:
                    payload["participants"]["attendees"].append({
                        "emailAddress": {
                            "address": participant_email
                        },
                        "type": "required"
                    })
                
                response = await client.post(
                    "https://graph.microsoft.com/v1.0/me/onlineMeetings",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return {
                        "meeting_url": data.get("joinUrl"),
                        "meeting_id": data.get("id"),
                        "conference_id": data.get("audioConferencing", {}).get("conferenceId", "")
                    }
                else:
                    print(f"❌ Erreur création Teams: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Erreur création meeting Teams: {e}")
            return None
    
    async def create_meeting(self, platform: str, title: str, start_time: datetime,
                            duration: int = 60, participant_email: str = None) -> Optional[Dict]:
        """
        Crée une réunion selon la plateforme demandée.
        
        Args:
            platform: 'zoom' ou 'teams'
            title: Titre de la réunion
            start_time: Date et heure de début
            duration: Durée en minutes
            participant_email: Email du participant
        
        Returns:
            Dict avec meeting_url et meeting_id
        """
        if platform.lower() == "zoom":
            return await self.create_zoom_meeting(title, start_time, duration, participant_email)
        elif platform.lower() == "teams":
            return await self.create_teams_meeting(title, start_time, duration, participant_email)
        else:
            print(f"⚠️ Plateforme non supportée: {platform}")
            return None

# Instance globale
meeting_service = MeetingService()
