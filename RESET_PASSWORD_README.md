# 🔐 Fonctionnalité Mot de Passe Oublié

## ✅ Fonctionnalité Implémentée

La fonctionnalité de réinitialisation de mot de passe a été ajoutée avec succès à Smart HIRE. Les candidats peuvent maintenant réinitialiser leur mot de passe en cas d'oubli.

## 📋 Ce qui a été ajouté

### Backend (Python/FastAPI)

1. **Base de données** (`backend/database.py`)
   - Nouvelle table `password_reset_tokens` pour stocker les tokens de réinitialisation
   - Fonctions :
     - `get_user_by_email()` : Récupère un utilisateur par email
     - `create_password_reset_token()` : Crée un token de réinitialisation
     - `get_password_reset_token()` : Récupère et valide un token
     - `mark_token_as_used()` : Marque un token comme utilisé
     - `update_user_password()` : Met à jour le mot de passe d'un utilisateur

2. **API Endpoints** (`backend/main.py`)
   - `POST /forgot-password` : Demande de réinitialisation (envoie un email)
   - `POST /reset-password` : Réinitialisation avec le token

3. **Service Email** (`backend/email_service.py`)
   - `send_password_reset_email()` : Envoie l'email avec le lien de réinitialisation

### Frontend (React)

1. **Composants créés**
   - `ForgotPasswordForm` (intégré dans Auth.jsx) : Formulaire de demande
   - `ResetPassword.jsx` : Page de réinitialisation avec le nouveau mot de passe

2. **Modifications**
   - `Auth.jsx` : Ajout du lien "Mot de passe oublié ?"
   - `App.jsx` : Gestion de la route de réinitialisation

## 🚀 Comment utiliser

### 1. Côté Utilisateur (Candidat)

1. **Demander la réinitialisation** :
   - Aller sur la page de connexion
   - Cliquer sur "Mot de passe oublié ?"
   - Entrer son adresse email
   - Cliquer sur "Envoyer le lien"

2. **Réinitialiser le mot de passe** :
   - Ouvrir l'email reçu
   - Cliquer sur le lien de réinitialisation
   - Entrer le nouveau mot de passe (minimum 6 caractères)
   - Confirmer le nouveau mot de passe
   - Cliquer sur "Réinitialiser le mot de passe"

3. **Se connecter** :
   - Vous serez automatiquement redirigé vers la page de connexion
   - Se connecter avec le nouveau mot de passe

### 2. Configuration Email (Backend)

Pour que l'envoi d'emails fonctionne, assurez-vous que le fichier `.env` est configuré :

```env
SENDER_EMAIL=votre_email@gmail.com
SENDER_PASSWORD=votre_mot_de_passe_application
```

**Note** : Utilisez un mot de passe d'application Gmail, pas votre mot de passe principal.

## 🔒 Sécurité

- **Tokens sécurisés** : Générés avec `secrets.token_urlsafe(32)`
- **Expiration** : Les tokens expirent après 1 heure
- **Usage unique** : Un token ne peut être utilisé qu'une seule fois
- **Hachage** : Les mots de passe sont hachés avec SHA-256
- **Protection contre l'énumération** : L'API retourne toujours le même message, que l'email existe ou non

## 📊 Flux de la fonctionnalité

```
1. Candidat → "Mot de passe oublié"
           ↓
2. Frontend → POST /forgot-password (email)
           ↓
3. Backend → Vérifie si l'utilisateur existe
           ↓
4. Backend → Génère un token unique
           ↓
5. Backend → Enregistre le token dans la BD (expire dans 1h)
           ↓
6. Backend → Envoie un email avec le lien
           ↓
7. Candidat → Clique sur le lien dans l'email
           ↓
8. Frontend → Affiche le formulaire de réinitialisation
           ↓
9. Candidat → Entre son nouveau mot de passe
           ↓
10. Frontend → POST /reset-password (token + nouveau mot de passe)
            ↓
11. Backend → Vérifie le token (validité, expiration, usage)
            ↓
12. Backend → Met à jour le mot de passe
            ↓
13. Backend → Marque le token comme utilisé
            ↓
14. Frontend → Redirige vers la page de connexion
```

## 🧪 Test de la fonctionnalité

### Prérequis
1. Backend en cours d'exécution : `python backend/main.py`
2. Frontend en cours d'exécution : `cd frontend && npm run dev`
3. Configuration email dans `.env`

### Scénarios de test

**Test 1 : Réinitialisation réussie**
1. Créer un compte candidat
2. Se déconnecter
3. Cliquer sur "Mot de passe oublié ?"
4. Entrer l'email du compte
5. Vérifier la réception de l'email
6. Cliquer sur le lien dans l'email
7. Entrer un nouveau mot de passe
8. Se connecter avec le nouveau mot de passe

**Test 2 : Email inexistant**
1. Demander la réinitialisation avec un email qui n'existe pas
2. Vérifier que le message est le même (sécurité)

**Test 3 : Token expiré**
1. Générer un token (demander la réinitialisation)
2. Attendre 1 heure
3. Essayer d'utiliser le lien
4. Vérifier le message d'erreur "Ce lien a expiré"

**Test 4 : Token déjà utilisé**
1. Réinitialiser le mot de passe avec succès
2. Essayer d'utiliser le même lien à nouveau
3. Vérifier le message d'erreur "Ce lien a déjà été utilisé"

## 📝 Base de données

La nouvelle table `password_reset_tokens` :

```sql
CREATE TABLE password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
```

## 🎨 Interface Utilisateur

- **Page "Mot de passe oublié"** : Formulaire simple avec un champ email
- **Message de confirmation** : Indique que l'email a été envoyé
- **Page de réinitialisation** : Deux champs (nouveau mot de passe + confirmation)
- **Lien "Retour à la connexion"** : Disponible sur toutes les pages
- **Validation** : Minimum 6 caractères pour le mot de passe

## 🔧 Dépannage

**L'email n'est pas reçu ?**
- Vérifier la configuration du fichier `.env`
- Vérifier les logs du backend pour les erreurs SMTP
- Vérifier le dossier spam

**Le lien ne fonctionne pas ?**
- Vérifier que le token est dans l'URL : `?token=...`
- Vérifier que le lien n'a pas expiré (1h)
- Vérifier que le lien n'a pas déjà été utilisé

**Erreur lors de la mise à jour du mot de passe ?**
- Vérifier que le mot de passe a au moins 6 caractères
- Vérifier que les deux mots de passe correspondent

## ✨ Améliorations futures possibles

- [ ] Ajouter une limite de tentatives de réinitialisation par email
- [ ] Permettre la personnalisation du délai d'expiration des tokens
- [ ] Ajouter la possibilité pour les recruteurs de réinitialiser leur mot de passe
- [ ] Envoyer une notification quand le mot de passe est modifié
- [ ] Ajouter un historique des changements de mot de passe
- [ ] Implémenter l'authentification à deux facteurs (2FA)

---

**Développé pour Smart HIRE - Smart Learning DAO**
*Date : 4 janvier 2026*
