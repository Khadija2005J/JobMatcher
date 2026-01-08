#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier la configuration Ollama
et tester le matching CV
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du backend
sys.path.append(str(Path(__file__).parent))

def check_ollama_installation():
    """Vérifie si Ollama est installé et fonctionnel."""
    print("\n" + "="*70)
    print("🔍 DIAGNOSTIC OLLAMA")
    print("="*70 + "\n")
    
    # Test 1: Importer ollama
    print("📦 Test 1: Import du module ollama...")
    try:
        import ollama
        print("✅ Module ollama importé avec succès\n")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("💡 Solution: pip install ollama\n")
        return False
    
    # Test 2: Lister les modèles disponibles
    print("📋 Test 2: Liste des modèles installés...")
    try:
        models = ollama.list()
        
        if not models or not models.get('models'):
            print("❌ Aucun modèle trouvé!")
            print("💡 Solution: ollama pull llama3.2\n")
            return False
        
        print(f"✅ {len(models['models'])} modèle(s) trouvé(s):\n")
        for model in models['models']:
            model_name = model.get('name', 'Unknown')
            size = model.get('size', 0) / (1024**3)  # Convert to GB
            print(f"   • {model_name} ({size:.2f} GB)")
        print()
        
    except Exception as e:
        print(f"❌ Erreur lors de la liste des modèles: {e}")
        print("💡 Vérifiez qu'Ollama est démarré: ollama serve\n")
        return False
    
    # Test 3: Vérifier le modèle configuré
    MODEL = os.getenv('MATCHER_MODEL', 'llama3.2')
    print(f"🎯 Test 3: Vérification du modèle configuré: {MODEL}...")
    
    model_found = False
    for model in models['models']:
        if MODEL in model.get('name', ''):
            model_found = True
            print(f"✅ Modèle '{MODEL}' trouvé\n")
            break
    
    if not model_found:
        print(f"❌ Modèle '{MODEL}' non trouvé!")
        print(f"💡 Solutions:")
        print(f"   1. Télécharger le modèle : ollama pull {MODEL}")
        print(f"   2. Utiliser un autre modèle disponible")
        print(f"   3. Définir MATCHER_MODEL avec un modèle installé\n")
        return False
    
    # Test 4: Test simple de génération
    print("🤖 Test 4: Test de génération simple...")
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{
                'role': 'user',
                'content': 'Réponds uniquement avec un JSON: {"test": "ok", "nombre": 42}'
            }],
            options={'timeout': 30}
        )
        
        content = response.get('message', {}).get('content', '')
        print(f"✅ Réponse reçue:")
        print(f"   {content[:200]}\n")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}\n")
        return False
    
    print("="*70)
    print("✅ DIAGNOSTIC RÉUSSI - Ollama est opérationnel")
    print("="*70 + "\n")
    return True


def test_cv_matching():
    """Test du système de matching CV."""
    print("\n" + "="*70)
    print("🧪 TEST DU MATCHING CV")
    print("="*70 + "\n")
    
    # Importer le matcher
    try:
        from matching import CVMatcher
        matcher = CVMatcher()
        print("✅ CVMatcher importé\n")
    except Exception as e:
        print(f"❌ Erreur d'import CVMatcher: {e}\n")
        return False
    
    # Créer un CV de test
    print("📝 Création d'un CV de test...")
    test_cv_path = Path(__file__).parent / "test_cv.txt"
    
    test_cv_content = """
JEAN DUPONT
Développeur Full Stack Senior

EXPÉRIENCE:
- 5 ans d'expérience en développement web
- Expert Python, Django, FastAPI
- Maîtrise de React, TypeScript
- Expérience en DevOps (Docker, CI/CD)
- Gestion de bases de données PostgreSQL, MongoDB

FORMATION:
- Master Informatique - Université Paris

COMPÉTENCES:
- Langages: Python, JavaScript, TypeScript, SQL
- Frameworks: Django, FastAPI, React, Next.js
- Outils: Git, Docker, Kubernetes
- Méthodologies: Agile, Scrum

LANGUES:
- Français (natif)
- Anglais (courant)
"""
    
    # Créer un faux PDF ou utiliser du texte
    print("📄 Simulation d'extraction de texte du CV...")
    
    # Description du poste de test
    job_description = """
Développeur Full Stack
Nous recherchons un développeur avec 3-5 ans d'expérience en Python et React.
Compétences requises: Django, FastAPI, React, PostgreSQL, Docker
"""
    
    print(f"💼 Description du poste:\n{job_description}\n")
    
    # Test de scoring (simulation)
    print("🎯 Test de l'analyse de matching...")
    print("⚠️  Note: Ce test nécessite un vrai CV PDF pour fonctionner complètement\n")
    
    # Test avec Ollama directement
    try:
        import ollama
        MODEL = os.getenv('MATCHER_MODEL', 'llama3.2')
        
        prompt = f"""Tu es un expert RH. Analyse ce CV par rapport à l'offre d'emploi.

OFFRE D'EMPLOI :
{job_description}

CONTENU DU CV :
{test_cv_content}

INSTRUCTIONS :
1. Évalue le CV sur 100 points
2. Donne une justification de 2-3 phrases
3. Réponds UNIQUEMENT avec ce format JSON:
{{
  "score": 75,
  "justification": "Votre analyse ici"
}}

RÉPONDS MAINTENANT:"""
        
        print(f"🤖 Envoi de la requête à {MODEL}...")
        response = ollama.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'timeout': 60, 'temperature': 0.3}
        )
        
        content = response.get('message', {}).get('content', '')
        print(f"\n📨 Réponse brute de l'IA:")
        print("-" * 70)
        print(content)
        print("-" * 70 + "\n")
        
        # Tenter d'extraire le score et la justification
        import re
        import json
        
        # Nettoyer et extraire le JSON
        cleaned = content.strip()
        cleaned = re.sub(r'^```json\s*', '', cleaned)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        
        json_match = re.search(r'\{[^{}]*"score"[^{}]*"justification"[^{}]*\}', cleaned, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                score = data.get('score', 'N/A')
                justification = data.get('justification', 'N/A')
                
                print("✅ RÉSULTAT EXTRAIT:")
                print(f"   Score: {score}/100")
                print(f"   Justification: {justification}\n")
                
                if score == 50 or score == 'N/A':
                    print("⚠️  Le score est à 50 (valeur par défaut) - Problème de parsing!")
                else:
                    print("✅ Le matching fonctionne correctement!\n")
                
            except json.JSONDecodeError as e:
                print(f"❌ Erreur de parsing JSON: {e}")
                print("⚠️  L'IA ne retourne pas un JSON valide\n")
        else:
            print("❌ Aucun JSON trouvé dans la réponse")
            print("⚠️  L'IA ne suit pas le format demandé\n")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    print("="*70)
    print("✅ TEST TERMINÉ")
    print("="*70 + "\n")
    return True


def show_solutions():
    """Affiche les solutions aux problèmes courants."""
    print("\n" + "="*70)
    print("💡 SOLUTIONS AUX PROBLÈMES COURANTS")
    print("="*70 + "\n")
    
    print("❌ PROBLÈME 1: Score toujours à 50%")
    print("   Causes possibles:")
    print("   • L'IA Ollama ne répond pas correctement")
    print("   • Le modèle n'est pas installé")
    print("   • Le parsing JSON échoue")
    print("   ")
    print("   Solutions:")
    print("   1. Vérifier qu'Ollama est démarré:")
    print("      → ollama serve")
    print("   ")
    print("   2. Vérifier les modèles installés:")
    print("      → ollama ls")
    print("   ")
    print("   3. Télécharger le bon modèle:")
    print("      → ollama pull llama3.2")
    print("   ")
    print("   4. Activer le mode debug:")
    print("      → export MATCHER_DEBUG=1")
    print("      → Puis vérifier les logs dans backend/logs/")
    print("   ")
    print("   5. Augmenter le timeout:")
    print("      → export MATCHER_TIMEOUT=120")
    print("   ")
    print("   6. Remplacer matching.py par matching_improved.py")
    print("      → cp matching_improved.py matching.py")
    print("\n")
    
    print("❌ PROBLÈME 2: Pas de justification détaillée")
    print("   Solutions:")
    print("   • Utiliser un modèle plus performant:")
    print("     → ollama pull llama3.2:13b  (modèle plus gros)")
    print("   • Améliorer le prompt (déjà fait dans matching_improved.py)")
    print("   • Réduire la température pour plus de cohérence:")
    print("     → Déjà paramétré à 0.3 dans la version améliorée")
    print("\n")
    
    print("❌ PROBLÈME 3: Ollama ne démarre pas")
    print("   Solutions:")
    print("   • Vérifier l'installation:")
    print("     → ollama --version")
    print("   • Redémarrer le service:")
    print("     → killall ollama")
    print("     → ollama serve &")
    print("   • Vérifier les ports:")
    print("     → netstat -tulpn | grep 11434")
    print("\n")
    
    print("="*70)
    print("📞 BESOIN D'AIDE?")
    print("="*70)
    print("1. Exécutez ce script de diagnostic: python diagnose_ollama.py")
    print("2. Consultez les logs: backend/logs/matcher_errors.log")
    print("3. Activez le debug: export MATCHER_DEBUG=1")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║          DIAGNOSTIC SYSTÈME DE MATCHING CV - SMART HIRE           ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Étape 1: Diagnostic Ollama
    ollama_ok = check_ollama_installation()
    
    if not ollama_ok:
        print("\n⚠️  Ollama n'est pas correctement configuré!")
        show_solutions()
        sys.exit(1)
    
    # Étape 2: Test de matching
    print("\n🔄 Passage au test de matching CV...\n")
    input("Appuyez sur Entrée pour continuer...")
    
    matching_ok = test_cv_matching()
    
    # Étape 3: Afficher les solutions si nécessaire
    if not matching_ok:
        show_solutions()
        sys.exit(1)
    
    print("\n" + "="*70)
    print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
    print("="*70)
    print("\n💡 Prochaines étapes:")
    print("   1. Remplacez matching.py par matching_improved.py")
    print("   2. Redémarrez votre application")
    print("   3. Testez avec un vrai CV PDF")
    print("\n")