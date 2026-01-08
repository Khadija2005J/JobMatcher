# TODO: Add Forgot Password Feature for Candidates

## Backend Changes
- [x] Add password_reset_tokens table to database.py
- [x] Add functions for token generation and verification in database.py
- [x] Add forgot password endpoint in main.py
- [x] Add reset password endpoint in main.py
- [x] Add password reset email function in email_service.py

## Frontend Changes
- [x] Add "Mot de passe oublié ?" link in Auth.jsx
- [x] Create ForgotPassword component
- [x] Create ResetPassword component
- [x] Update App.jsx to handle new routes

## Testing
- [ ] Test the complete password reset flow
- [ ] Ensure token security (expiration, one-time use)
