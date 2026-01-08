# 📄 Export de CVs et Rapports de Matching - Guide Complet

## Fonctionnalités Ajoutées

### 1. 📥 Téléchargement des CVs en PDF

Les recruteurs peuvent maintenant télécharger directement les CVs des candidats depuis l'interface.

#### Backend - Nouvelle Route API
```
GET /applications/{application_id}/cv
```

**Fonctionnalités** :
- Téléchargement sécurisé des CVs
- Vérification des permissions (seul le recruteur de l'offre peut télécharger)
- Retour du fichier PDF original avec le nom de fichier correct
- Gestion des erreurs si le fichier n'existe pas

**Paramètres** :
- `application_id` : ID de la candidature

**Réponse** :
- Fichier PDF avec le nom original du CV
- Content-Type: application/pdf

#### Frontend - Interface Utilisateur

Dans le modal des candidatures, chaque candidat a maintenant un bouton :
```jsx
📄 Télécharger CV
```

**Utilisation** :
1. Ouvrir les candidatures d'une offre
2. Cliquer sur "📄 Télécharger CV" pour n'importe quel candidat
3. Le CV se télécharge automatiquement

### 2. 📊 Rapports de Matching Détaillés

Génération automatique de rapports d'analyse pour chaque offre.

#### Backend - Nouvelle Route API
```
GET /offers/{offer_id}/matching-report
```

**Contenu du Rapport** :
- **Informations de l'offre** : titre, description, compétences requises, ville, expérience, éducation
- **Statistiques globales** :
  - Nombre total de candidatures
  - Score moyen/maximum/minimum
  - Répartition par niveau :
    - Excellents profils (≥70)
    - Bons profils (50-69)
    - Profils faibles (<50)
  - Statuts : acceptés, refusés, en attente
- **Top 5 candidats** : 
  - Nom et email
  - Score IA
  - Statut
  - Justification détaillée

**Exemple de rapport** :
```
RAPPORT DE MATCHING
==================

Offre: Développeur Full Stack Senior
Ville: Paris
Expérience: 5+ ans

STATISTIQUES
------------
Total candidatures: 15
Score moyen: 68.5/100
Score maximum: 92.3/100
Score minimum: 38.7/100

Excellents profils (≥70): 7
Bons profils (50-69): 5
Profils faibles (<50): 3

Acceptés: 2
Refusés: 8
En attente: 5

TOP 5 CANDIDATS
---------------
1. Jean Dupont (jean.dupont@email.com)
   Score: 92.3/100
   Statut: accepted
   Analyse: Excellent profil avec 7 ans d'expérience...
```

#### Frontend

Bouton "📊 Rapport de Matching" dans le modal des candidatures.

**Téléchargement** :
- Format : Fichier texte (.txt)
- Nom : `rapport_matching_offre_{id}.txt`
- Ouverture possible dans n'importe quel éditeur de texte

### 3. 📋 Export des Listes de Candidats en CSV

Export complet de tous les candidats d'une offre au format CSV.

#### Backend - Nouvelle Route API
```
GET /offers/{offer_id}/candidates/export-csv
```

**Colonnes du CSV** :
- `candidate_name` : Nom du candidat
- `candidate_email` : Email du candidat
- `score` : Score IA de matching
- `status` : Statut de la candidature (pending/accepted/rejected)
- `justification` : Analyse IA détaillée
- `cv_filename` : Nom du fichier CV
- `applied_date` : Date de candidature

**Format** :
- Séparateur : Point-virgule (;)
- Encodage : UTF-8
- Compatible Excel, Google Sheets, LibreOffice

**Exemple** :
```csv
candidate_name;candidate_email;score;status;justification;cv_filename;applied_date
Jean Dupont;jean@email.com;92.3;accepted;Excellent profil...;cv_jean.pdf;06/01/2026 14:30
Marie Martin;marie@email.com;85.7;pending;Très bon profil...;cv_marie.pdf;05/01/2026 10:15
```

#### Frontend

Bouton "📥 Exporter en CSV" dans le modal des candidatures.

**Téléchargement** :
- Nom du fichier : `candidats_{titre_offre}_{id}.csv`
- Les caractères spéciaux du titre sont nettoyés automatiquement
- Téléchargement direct dans le navigateur

### 4. 🔒 Sécurité et Permissions

Toutes les routes sont protégées :

**Vérifications** :
- ✅ Authentification obligatoire (token JWT)
- ✅ Rôle recruteur requis pour les exports
- ✅ Vérification que l'offre appartient au recruteur
- ✅ Vérification de l'existence des fichiers
- ✅ Chemins de fichiers sécurisés (pas d'accès direct au système de fichiers)

**Codes d'erreur** :
- `401` : Non authentifié
- `403` : Non autorisé (pas le bon recruteur ou mauvais rôle)
- `404` : Offre/candidature/fichier non trouvé

## Utilisation Pratique

### Pour les Recruteurs

#### Scénario 1 : Télécharger un CV spécifique
1. Aller dans "Mes Offres"
2. Cliquer sur "Voir les candidatures" pour une offre
3. Trouver le candidat souhaité
4. Cliquer sur "📄 Télécharger CV"
5. Le PDF se télécharge automatiquement

#### Scénario 2 : Analyser les candidatures
1. Ouvrir les candidatures d'une offre
2. Cliquer sur "📊 Rapport de Matching"
3. Consulter le rapport téléchargé pour :
   - Voir les statistiques globales
   - Identifier les meilleurs profils
   - Comprendre la répartition des scores

#### Scénario 3 : Exporter pour analyse externe
1. Ouvrir les candidatures d'une offre
2. Cliquer sur "📥 Exporter en CSV"
3. Ouvrir le fichier dans Excel/Google Sheets
4. Faire des analyses, graphiques, filtres, etc.

### Cas d'Usage Avancés

#### Analyse dans Excel
```
1. Télécharger le CSV
2. Ouvrir dans Excel
3. Créer un tableau croisé dynamique
4. Analyser les scores par date de candidature
5. Créer des graphiques de distribution
```

#### Partage avec l'équipe
```
1. Télécharger le rapport de matching
2. Copier dans un email ou document partagé
3. Discuter des meilleurs profils en équipe
4. Prendre des décisions de recrutement éclairées
```

#### Archivage des candidatures
```
1. Exporter en CSV régulièrement
2. Sauvegarder dans un dossier dédié
3. Garder un historique des candidatures
4. Analyser les tendances sur plusieurs mois
```

## Structure des Données

### get_candidates_list_for_offer(offer_id)
Retourne une liste complète avec :
```python
[{
    "application_id": 123,
    "candidate_id": 456,
    "candidate_name": "Jean Dupont",
    "candidate_email": "jean@email.com",
    "cv_filename": "cv_jean.pdf",
    "cv_path": "456/cv_jean.pdf",
    "score": 92.3,
    "status": "pending",
    "justification": "Excellent profil...",
    "applied_date": "06/01/2026 14:30"
}]
```

### get_matching_report(offer_id)
Structure du rapport :
```python
{
    "offer": {
        "title": "Développeur Full Stack",
        "description": "...",
        "skills": "Python, React, SQL",
        "city": "Paris",
        "experience": "5+ ans",
        "education": "Bac +5"
    },
    "statistics": {
        "total_applications": 15,
        "average_score": 68.5,
        "max_score": 92.3,
        "min_score": 38.7,
        "excellent_matches": 7,
        "good_matches": 5,
        "low_matches": 3,
        "accepted": 2,
        "rejected": 8,
        "pending": 5
    },
    "top_candidates": [...]
}
```

## Implémentation Technique

### Backend (report_service.py)

Nouvelles méthodes ajoutées :
```python
# Récupérer la liste des candidats
get_candidates_list_for_offer(offer_id: int) -> List[Dict]

# Générer un rapport de matching
get_matching_report(offer_id: int) -> Dict

# Exporter en CSV
export_candidates_csv(offer_id: int) -> str

# Obtenir le chemin d'un CV
get_cv_path(application_id: int) -> str
```

### Frontend (RecruiterDashboard.jsx)

Nouvelles fonctions ajoutées :
```javascript
// Télécharger un CV
downloadCV(applicationId, filename)

// Télécharger le rapport de matching
downloadMatchingReport(offerId)

// Exporter les candidats en CSV
exportCandidatesCSV(offerId)
```

## Tests et Validation

### Test 1 : Téléchargement CV
```bash
# Avec curl
curl -H "Authorization: Bearer {token}" \
     -o cv_test.pdf \
     http://localhost:8000/applications/123/cv
```

### Test 2 : Rapport de matching
```bash
curl -H "Authorization: Bearer {token}" \
     http://localhost:8000/offers/1/matching-report
```

### Test 3 : Export CSV
```bash
curl -H "Authorization: Bearer {token}" \
     -o candidats.csv \
     http://localhost:8000/offers/1/candidates/export-csv
```

## Dépannage

### Le CV ne se télécharge pas
**Causes possibles** :
1. Le fichier n'existe plus sur le serveur
2. Le chemin du fichier est incorrect dans la base de données
3. Permissions insuffisantes

**Solution** :
- Vérifier que le fichier existe dans `uploads/{candidate_id}/`
- Vérifier les permissions du dossier uploads
- Consulter les logs du backend

### L'export CSV est vide
**Causes possibles** :
1. Aucune candidature pour cette offre
2. L'offre n'existe pas
3. Problème de permissions

**Solution** :
- Vérifier qu'il y a des candidatures
- Vérifier l'ID de l'offre
- Consulter les logs

### Le rapport de matching ne se génère pas
**Cause** : Offre sans candidatures

**Solution** : Le rapport nécessite au moins une candidature

## Améliorations Futures Possibles

- [ ] Export PDF des rapports (avec mise en forme)
- [ ] Graphiques dans les rapports
- [ ] Export Excel (.xlsx) avec plusieurs onglets
- [ ] Téléchargement en lot de plusieurs CVs (archive ZIP)
- [ ] Envoi automatique des rapports par email
- [ ] Historique des exports
- [ ] Templates de rapports personnalisables
- [ ] Intégration avec Google Drive/Dropbox
- [ ] Annotations sur les CVs
- [ ] Comparaison de candidats côte à côte

## Support

Pour toute question :
1. Vérifier la documentation
2. Consulter les logs du backend
3. Tester les routes API directement
4. Vérifier les permissions et l'authentification

## Conclusion

Ces nouvelles fonctionnalités permettent aux recruteurs de :
- ✅ Télécharger facilement tous les CVs
- ✅ Analyser les candidatures avec des rapports détaillés
- ✅ Exporter les données pour des analyses externes
- ✅ Prendre des décisions de recrutement plus éclairées
- ✅ Archiver et partager les informations de candidatures
