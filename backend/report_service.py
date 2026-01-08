"""
Service d'export et génération de rapports
"""
import csv
import io
from datetime import datetime
from typing import List, Dict
import sqlite3
from database import get_connection
from pathlib import Path

class ReportService:
    """Service pour générer des rapports et exports."""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.upload_dir = self.base_dir / "uploads"
    
    def format_date(self, date_str: str) -> str:
        """Formate une date ISO pour l'affichage."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return date_str
    
    def get_recruiter_interviews_report(self, recruiter_id: int) -> List[Dict]:
        """Génère un rapport des entretiens d'un recruteur."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                i.id,
                i.title,
                i.interview_date,
                i.duration,
                i.status,
                i.meeting_type,
                u.name as candidate_name,
                u.email as candidate_email,
                o.title as offer_title,
                i.created_at
            FROM interviews i
            JOIN users u ON i.candidate_id = u.id
            JOIN applications a ON i.application_id = a.id
            JOIN offers o ON a.offer_id = o.id
            WHERE i.recruiter_id = ?
            ORDER BY i.interview_date DESC
        """, (recruiter_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "title": r[1],
                "interview_date": self.format_date(r[2]),
                "duration": r[3],
                "status": r[4],
                "meeting_type": r[5],
                "candidate_name": r[6],
                "candidate_email": r[7],
                "offer_title": r[8],
                "created_at": self.format_date(r[9])
            }
            for r in rows
        ]
    
    def get_candidate_interviews_report(self, candidate_id: int) -> List[Dict]:
        """Génère un rapport des entretiens d'un candidat."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                i.id,
                i.title,
                i.interview_date,
                i.duration,
                i.status,
                i.meeting_type,
                u.name as recruiter_name,
                u.email as recruiter_email,
                o.title as offer_title,
                i.created_at
            FROM interviews i
            JOIN users u ON i.recruiter_id = u.id
            JOIN applications a ON i.application_id = a.id
            JOIN offers o ON a.offer_id = o.id
            WHERE i.candidate_id = ?
            ORDER BY i.interview_date DESC
        """, (candidate_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "title": r[1],
                "interview_date": self.format_date(r[2]),
                "duration": r[3],
                "status": r[4],
                "meeting_type": r[5],
                "recruiter_name": r[6],
                "recruiter_email": r[7],
                "offer_title": r[8],
                "created_at": self.format_date(r[9])
            }
            for r in rows
        ]
    
    def get_applications_report(self, recruiter_id: int) -> List[Dict]:
        """Génère un rapport des candidatures pour un recruteur."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                a.id,
                o.title as offer_title,
                u.name as candidate_name,
                u.email as candidate_email,
                a.filename,
                a.score,
                a.status,
                a.created_at
            FROM applications a
            JOIN offers o ON a.offer_id = o.id
            JOIN users u ON a.candidate_id = u.id
            WHERE o.recruiter_id = ?
            ORDER BY a.created_at DESC
        """, (recruiter_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0],
                "offer_title": r[1],
                "candidate_name": r[2],
                "candidate_email": r[3],
                "filename": r[4],
                "score": r[5],
                "status": r[6],
                "created_at": self.format_date(r[7])
            }
            for r in rows
        ]
    
    def export_to_csv(self, data: List[Dict], filename: str = "export.csv") -> str:
        """
        Exporte des données en CSV.
        
        Returns:
            Le contenu CSV sous forme de string
        """
        if not data:
            return ""
        
        output = io.StringIO()
        
        # Utiliser les clés du premier élément comme en-têtes
        fieldnames = list(data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def get_recruiter_statistics(self, recruiter_id: int) -> Dict:
        """Génère des statistiques pour un recruteur."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Nombre d'offres actives
        cursor.execute("""
            SELECT COUNT(*) FROM offers 
            WHERE recruiter_id = ? AND status = 'active'
        """, (recruiter_id,))
        active_offers = cursor.fetchone()[0]
        
        # Nombre total de candidatures
        cursor.execute("""
            SELECT COUNT(*) FROM applications a
            JOIN offers o ON a.offer_id = o.id
            WHERE o.recruiter_id = ?
        """, (recruiter_id,))
        total_applications = cursor.fetchone()[0]
        
        # Candidatures en attente
        cursor.execute("""
            SELECT COUNT(*) FROM applications a
            JOIN offers o ON a.offer_id = o.id
            WHERE o.recruiter_id = ? AND a.status = 'pending'
        """, (recruiter_id,))
        pending_applications = cursor.fetchone()[0]
        
        # Candidatures acceptées
        cursor.execute("""
            SELECT COUNT(*) FROM applications a
            JOIN offers o ON a.offer_id = o.id
            WHERE o.recruiter_id = ? AND a.status = 'accepted'
        """, (recruiter_id,))
        accepted_applications = cursor.fetchone()[0]
        
        # Entretiens planifiés
        cursor.execute("""
            SELECT COUNT(*) FROM interviews
            WHERE recruiter_id = ? AND status IN ('proposed', 'accepted')
        """, (recruiter_id,))
        scheduled_interviews = cursor.fetchone()[0]
        
        # Entretiens complétés
        cursor.execute("""
            SELECT COUNT(*) FROM interviews
            WHERE recruiter_id = ? AND status = 'completed'
        """, (recruiter_id,))
        completed_interviews = cursor.fetchone()[0]
        
        # Score moyen des candidatures
        cursor.execute("""
            SELECT AVG(a.score) FROM applications a
            JOIN offers o ON a.offer_id = o.id
            WHERE o.recruiter_id = ? AND a.score IS NOT NULL
        """, (recruiter_id,))
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "active_offers": active_offers,
            "total_applications": total_applications,
            "pending_applications": pending_applications,
            "accepted_applications": accepted_applications,
            "rejected_applications": total_applications - pending_applications - accepted_applications,
            "scheduled_interviews": scheduled_interviews,
            "completed_interviews": completed_interviews,
            "average_score": round(avg_score, 2)
        }
    
    def get_candidate_statistics(self, candidate_id: int) -> Dict:
        """Génère des statistiques pour un candidat."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Nombre de candidatures
        cursor.execute("""
            SELECT COUNT(*) FROM applications 
            WHERE candidate_id = ?
        """, (candidate_id,))
        total_applications = cursor.fetchone()[0]
        
        # Candidatures en attente
        cursor.execute("""
            SELECT COUNT(*) FROM applications 
            WHERE candidate_id = ? AND status = 'pending'
        """, (candidate_id,))
        pending = cursor.fetchone()[0]
        
        # Candidatures acceptées
        cursor.execute("""
            SELECT COUNT(*) FROM applications 
            WHERE candidate_id = ? AND status = 'accepted'
        """, (candidate_id,))
        accepted = cursor.fetchone()[0]
        
        # Entretiens à venir
        cursor.execute("""
            SELECT COUNT(*) FROM interviews
            WHERE candidate_id = ? AND status IN ('proposed', 'accepted')
            AND interview_date > datetime('now')
        """, (candidate_id,))
        upcoming_interviews = cursor.fetchone()[0]
        
        # Entretiens passés
        cursor.execute("""
            SELECT COUNT(*) FROM interviews
            WHERE candidate_id = ? AND status = 'completed'
        """, (candidate_id,))
        completed_interviews = cursor.fetchone()[0]
        
        # Offres favorites
        cursor.execute("""
            SELECT COUNT(*) FROM favorites
            WHERE candidate_id = ?
        """, (candidate_id,))
        favorites = cursor.fetchone()[0]
        
        # Score moyen
        cursor.execute("""
            SELECT AVG(score) FROM applications
            WHERE candidate_id = ? AND score IS NOT NULL
        """, (candidate_id,))
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_applications": total_applications,
            "pending_applications": pending,
            "accepted_applications": accepted,
            "rejected_applications": total_applications - pending - accepted,
            "upcoming_interviews": upcoming_interviews,
            "completed_interviews": completed_interviews,
            "favorites": favorites,
            "average_score": round(avg_score, 2)
        }
    
    def get_candidates_list_for_offer(self, offer_id: int) -> List[Dict]:
        """Génère la liste complète des candidats pour une offre."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                a.id as application_id,
                u.id as candidate_id,
                u.name,
                u.email,
                a.filename,
                a.file_path,
                a.score,
                a.status,
                a.justification,
                a.created_at
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.offer_id = ?
            ORDER BY a.score DESC
        """, (offer_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "application_id": r[0],
                "candidate_id": r[1],
                "candidate_name": r[2],
                "candidate_email": r[3],
                "cv_filename": r[4],
                "cv_path": r[5],
                "score": round(r[6], 2) if r[6] else 0,
                "status": r[7],
                "justification": r[8],
                "applied_date": self.format_date(r[9])
            }
            for r in rows
        ]
    
    def get_matching_report(self, offer_id: int) -> Dict:
        """Génère un rapport de matching détaillé pour une offre."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Infos de l'offre
        cursor.execute("""
            SELECT title, description, skills, city, experience, education
            FROM offers
            WHERE id = ?
        """, (offer_id,))
        offer = cursor.fetchone()
        
        if not offer:
            return None
        
        # Statistiques des candidatures
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score,
                COUNT(CASE WHEN score >= 70 THEN 1 END) as excellent,
                COUNT(CASE WHEN score >= 50 AND score < 70 THEN 1 END) as good,
                COUNT(CASE WHEN score < 50 THEN 1 END) as low,
                COUNT(CASE WHEN status = 'accepted' THEN 1 END) as accepted,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
            FROM applications
            WHERE offer_id = ?
        """, (offer_id,))
        
        stats = cursor.fetchone()
        
        # Top 5 candidats
        cursor.execute("""
            SELECT 
                u.name,
                u.email,
                a.score,
                a.status,
                a.justification
            FROM applications a
            JOIN users u ON a.candidate_id = u.id
            WHERE a.offer_id = ?
            ORDER BY a.score DESC
            LIMIT 5
        """, (offer_id,))
        
        top_candidates = cursor.fetchall()
        
        conn.close()
        
        return {
            "offer": {
                "title": offer[0],
                "description": offer[1],
                "skills": offer[2],
                "city": offer[3],
                "experience": offer[4],
                "education": offer[5]
            },
            "statistics": {
                "total_applications": stats[0] or 0,
                "average_score": round(stats[1], 2) if stats[1] else 0,
                "max_score": round(stats[2], 2) if stats[2] else 0,
                "min_score": round(stats[3], 2) if stats[3] else 0,
                "excellent_matches": stats[4] or 0,
                "good_matches": stats[5] or 0,
                "low_matches": stats[6] or 0,
                "accepted": stats[7] or 0,
                "rejected": stats[8] or 0,
                "pending": stats[9] or 0
            },
            "top_candidates": [
                {
                    "name": c[0],
                    "email": c[1],
                    "score": round(c[2], 2) if c[2] else 0,
                    "status": c[3],
                    "justification": c[4]
                }
                for c in top_candidates
            ]
        }
    
    def export_candidates_csv(self, offer_id: int) -> str:
        """Exporte la liste des candidats en CSV."""
        candidates = self.get_candidates_list_for_offer(offer_id)
        
        if not candidates:
            return ""
        
        output = io.StringIO()
        fieldnames = [
            "candidate_name", "candidate_email", "score", "status", 
            "justification", "cv_filename", "applied_date"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        
        for candidate in candidates:
            writer.writerow({
                "candidate_name": candidate["candidate_name"],
                "candidate_email": candidate["candidate_email"],
                "score": candidate["score"],
                "status": candidate["status"],
                "justification": candidate["justification"],
                "cv_filename": candidate["cv_filename"],
                "applied_date": candidate["applied_date"]
            })
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def get_cv_path(self, application_id: int) -> str:
        """Récupère le chemin du CV d'une candidature."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path
            FROM applications
            WHERE id = ?
        """, (application_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return str(self.upload_dir / result[0])
        
        return None

# Instance globale
report_service = ReportService()
