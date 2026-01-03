"""
Module pour parser les CVs - Fonctionnalités de base
Ce module peut être étendu pour des fonctionnalités avancées de parsing
"""

import fitz  # PyMuPDF
import re
from typing import Dict, List, Optional

class CVParser:
    """Classe pour parser et extraire des informations structurées des CVs"""
    
    def __init__(self):
        self.text = ""
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un PDF"""
        text = ""
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            self.text = text
            return text
        except Exception as e:
            print(f"Erreur lors de l'extraction du PDF: {e}")
            return ""
    
    def extract_email(self) -> Optional[str]:
        """Extrait l'email du CV"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, self.text)
        return emails[0] if emails else None
    
    def extract_phone(self) -> Optional[str]:
        """Extrait le numéro de téléphone"""
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\d{10}',
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, self.text)
            if phones:
                return phones[0]
        return None
    
    def extract_skills(self, skill_keywords: List[str]) -> List[str]:
        """Extrait les compétences basées sur une liste de mots-clés"""
        found_skills = []
        text_lower = self.text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills
    
    def parse_cv(self, pdf_path: str, skill_keywords: Optional[List[str]] = None) -> Dict:
        """Parse un CV et retourne un dictionnaire avec les infos extraites"""
        self.extract_text_from_pdf(pdf_path)
        
        result = {
            "email": self.extract_email(),
            "phone": self.extract_phone(),
            "raw_text": self.text[:500],  # Premiers 500 caractères
            "full_text_length": len(self.text)
        }
        
        if skill_keywords:
            result["skills"] = self.extract_skills(skill_keywords)
        
        return result


# Fonction standalone pour compatibilité
def extract_cv_text(pdf_path: str) -> str:
    """Fonction simple pour extraire le texte d'un CV"""
    parser = CVParser()
    return parser.extract_text_from_pdf(pdf_path)