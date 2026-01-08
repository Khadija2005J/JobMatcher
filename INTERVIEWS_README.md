# 📅 Calendrier d'Entretiens et Gestion des Réunions - Smart HIRE

## Nouvelles Fonctionnalités Ajoutées

### 1. 📅 Calendrier d'Entretiens

#### Backend
- **Nouvelles tables de base de données** :
  - `interviews` : Gestion complète des entretiens
  - `time_slots` : Créneaux horaires proposés
  - `interview_reminders` : Rappels automatiques

- **API Endpoints** :
  - `POST /interviews` - Créer un nouvel entretien
  - `GET /interviews` - Lister les entretiens (avec filtres)
  - `GET /interviews/{id}` - Détails d'un entretien
  - `PUT /interviews/{id}/status` - Mettre à jour le statut
  - `POST /interviews/{id}/timeslots` - Proposer des créneaux
  - `GET /interviews/{id}/timeslots` - Voir les créneaux proposés
  - `POST /timeslots/{id}/accept` - Accepter un créneau

#### Frontend
- **Composant InterviewCalendar.jsx** :
  - Vue calendrier avec entretiens groupés par date
  - Filtres par statut (proposé, accepté, terminé, etc.)
  - Modal de détails avec toutes les informations
  - Actions : accepter, refuser, annuler, marquer comme terminé
  - Affichage du type de réunion (physique, Zoom, Teams, téléphone)

### 2. 🤝 Proposition et Acceptation de Créneaux

- Les recruteurs peuvent proposer plusieurs créneaux horaires
- Les candidats peuvent accepter un créneau parmi ceux proposés
- Rejet automatique des autres créneaux une fois qu'un est accepté
- Mise à jour automatique de la date de l'entretien

### 3. 🔔 Rappels Automatiques

#### Service de Rappels (`reminder_service.py`)
- Vérification périodique des rappels en attente (toutes les 5 minutes par défaut)
- Envoi automatique d'emails et/ou notifications in-app
- Rappels configurables : 24h avant et 1h avant l'entretien
- Support de plusieurs types de rappels :
  - `email` : Email uniquement
  - `notification` : Notification in-app uniquement
  - `both` : Email + Notification

#### Configuration
- Le service démarre automatiquement avec l'application FastAPI
- Intervalle de vérification : 300 secondes (5 minutes)
- Personnalisable dans `main.py` : `reminder_service.run(interval=300)`

### 4. 📹 Intégration Zoom et Microsoft Teams

#### Service d'Intégration (`meeting_service.py`)

**Zoom**
- Création automatique de réunions Zoom
- Configuration OAuth Server-to-Server
- Variables d'environnement requises :
  ```
  ZOOM_ACCOUNT_ID=your_account_id
  ZOOM_CLIENT_ID=your_client_id
  ZOOM_CLIENT_SECRET=your_client_secret
  ```

**Microsoft Teams**
- Création de réunions Microsoft Teams via Microsoft Graph API
- Variables d'environnement requises :
  ```
  TEAMS_TENANT_ID=your_tenant_id
  TEAMS_CLIENT_ID=your_client_id
  TEAMS_CLIENT_SECRET=your_client_secret
  ```

#### API Endpoint
- `POST /interviews/{id}/meeting` - Créer un lien de réunion Zoom/Teams
  ```json
  {
    "platform": "zoom",  // ou "teams"
    "participant_email": "candidate@example.com"
  }
  ```

### 5. 📊 Export et Rapports

#### Service de Rapports (`report_service.py`)

**Statistiques**
- Pour les recruteurs :
  - Offres actives
  - Candidatures totales/en attente/acceptées
  - Entretiens planifiés/complétés
  - Score moyen des candidatures

- Pour les candidats :
  - Candidatures envoyées
  - Candidatures en attente/acceptées/rejetées
  - Entretiens à venir/passés
  - Offres favorites
  - Score moyen

**Exports CSV**
- Export des entretiens (tous les utilisateurs)
- Export des candidatures (recruteurs uniquement)
- Format CSV avec séparateur point-virgule (;)
- Téléchargement direct depuis le navigateur

#### API Endpoints
- `GET /reports/statistics` - Statistiques de l'utilisateur
- `GET /reports/interviews` - Rapport des entretiens
- `GET /reports/applications` - Rapport des candidatures (recruteurs)
- `GET /export/interviews/csv` - Export CSV des entretiens
- `GET /export/applications/csv` - Export CSV des candidatures

#### Composant Frontend
- **ReportsExport.jsx** :
  - Vue d'ensemble avec cartes de statistiques
  - Boutons d'export CSV
  - Tableaux de données avec pagination
  - Design responsive

### 6. 🎨 Interface Utilisateur

#### Navigation par Onglets
Les dashboards Recruteur et Candidat ont maintenant une navigation par onglets :

**Recruteur** :
- 📝 Mes Offres
- 📅 Entretiens
- 📊 Rapports

**Candidat** :
- 💼 Offres d'emploi
- 📬 Mes Candidatures
- 📅 Entretiens
- 📊 Mes Statistiques

## Installation et Configuration

### 1. Installer les dépendances Python
```bash
pip install httpx
```

### 2. Configuration des variables d'environnement
Créez un fichier `.env` dans le dossier `backend/` :
```env
# Configuration Email (existant)
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Configuration Zoom (optionnel)
ZOOM_ACCOUNT_ID=your_zoom_account_id
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret

# Configuration Microsoft Teams (optionnel)
TEAMS_TENANT_ID=your_teams_tenant_id
TEAMS_CLIENT_ID=your_teams_client_id
TEAMS_CLIENT_SECRET=your_teams_client_secret

# Environnement
ENV=development  # ou "production"
```

### 3. Initialiser la base de données
La base de données sera automatiquement mise à jour au démarrage :
```bash
cd backend
python main.py
```

Les nouvelles tables seront créées automatiquement grâce à `CREATE TABLE IF NOT EXISTS`.

### 4. Démarrer l'application

**Backend** :
```bash
cd backend
python main.py
```

**Frontend** :
```bash
cd frontend
npm install
npm run dev
```

## Utilisation

### Pour les Recruteurs

1. **Créer un entretien** :
   - Aller dans "Entretiens"
   - Les entretiens sont créés automatiquement lors de l'acceptation d'une candidature
   - Ou créer manuellement via l'API

2. **Ajouter un lien Zoom/Teams** :
   - Ouvrir les détails d'un entretien
   - Créer un lien de réunion
   - Le lien sera automatiquement ajouté et envoyé au candidat

3. **Consulter les statistiques** :
   - Aller dans "Rapports"
   - Voir les statistiques en temps réel
   - Exporter les données en CSV

### Pour les Candidats

1. **Voir les entretiens** :
   - Aller dans "Entretiens"
   - Voir tous les entretiens proposés
   - Accepter ou refuser les propositions

2. **Accepter un créneau** :
   - Ouvrir les détails d'un entretien avec statut "Proposé"
   - Cliquer sur "Accepter" pour confirmer

3. **Consulter les statistiques** :
   - Aller dans "Mes Statistiques"
   - Voir le nombre de candidatures, entretiens, etc.
   - Exporter ses données

## Flux de Travail Typique

1. **Candidature** : Le candidat postule à une offre
2. **Acceptation** : Le recruteur accepte la candidature
3. **Entretien créé** : Un entretien est automatiquement créé
4. **Créneaux proposés** : Le recruteur peut proposer plusieurs créneaux
5. **Acceptation** : Le candidat accepte un créneau
6. **Lien de réunion** : Le recruteur crée un lien Zoom/Teams
7. **Rappels** : Rappels automatiques 24h et 1h avant
8. **Entretien** : L'entretien a lieu
9. **Finalisation** : Marquer l'entretien comme "Terminé"

## Personnalisation

### Modifier l'intervalle des rappels
Dans `backend/main.py` :
```python
asyncio.create_task(reminder_service.run(interval=60))  # Vérifier toutes les minutes
```

### Ajouter des rappels personnalisés
Dans `backend/database.py`, modifier la fonction `create_interview` pour ajouter différents rappels :
```python
# Rappel 2 jours avant
reminder_2d = interview_dt - timedelta(days=2)
create_reminder(interview_id, user_id, reminder_2d.isoformat(), "email")
```

### Personnaliser les emails de rappels
Modifier le template dans `backend/reminder_service.py`, méthode `send_reminder_email`.

## Sécurité

- Les tokens Zoom/Teams ne sont jamais exposés aux utilisateurs
- Authentification requise pour toutes les routes d'entretiens
- Vérification des permissions (un utilisateur ne peut voir que ses propres entretiens)
- Validation des données avec Pydantic

## Dépannage

### Les rappels ne s'envoient pas
1. Vérifier que le service de rappels est démarré (voir logs au démarrage)
2. Vérifier la configuration email dans `.env`
3. Vérifier les dates des rappels dans la base de données

### Les liens Zoom/Teams ne se créent pas
1. Vérifier les variables d'environnement
2. Vérifier les credentials OAuth
3. Voir les logs d'erreur dans la console

### Erreurs de base de données
1. Supprimer le fichier `backend/data/smart_hire.db`
2. Redémarrer le backend pour recréer la base

## Technologies Utilisées

- **Backend** : FastAPI, SQLite, httpx (pour les appels API Zoom/Teams)
- **Frontend** : React, Axios
- **Intégrations** : Zoom API, Microsoft Graph API
- **Base de données** : SQLite avec nouvelles tables pour les entretiens

## Support

Pour toute question ou problème, vérifiez :
1. Les logs du backend
2. La console du navigateur (F12)
3. La base de données SQLite avec un viewer

## Prochaines Améliorations Possibles

- [ ] Synchronisation avec Google Calendar
- [ ] Notifications push (via Firebase)
- [ ] Salle d'attente virtuelle
- [ ] Enregistrement des entretiens
- [ ] Templates d'emails personnalisables
- [ ] Rappels par SMS (via Twilio)
- [ ] Système de feedback post-entretien
- [ ] Analytics avancées avec graphiques
- [ ] Export PDF des rapports
