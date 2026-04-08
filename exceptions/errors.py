# -*- coding: utf-8 -*-
"""
Définition des exceptions personnalisées pour insta_kendou
Gestion complète des erreurs Instagram avec types spécialisés
"""

class InstagramError(Exception):
    """Exception de base pour toutes les erreurs Instagram"""
    def __init__(self, message: str, error_code: str = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.response_data = response_data or {}
    
    def __str__(self):
        return f"InstagramError: {self.message}"

class AuthenticationError(InstagramError):
    """Erreur d'authentification générale"""
    pass

class TwoFactorError(AuthenticationError):
    """Erreur liée à l'authentification à deux facteurs"""
    def __init__(self, message: str, challenge_data: dict = None, methods: list = None):
        super().__init__(message)
        self.challenge_data = challenge_data or {}
        self.methods = methods or []

class ChallengeError(AuthenticationError):
    """Erreur de challenge/checkpoint Instagram"""
    def __init__(self, message: str, challenge_url: str = None, challenge_type: str = None):
        super().__init__(message)
        self.challenge_url = challenge_url
        self.challenge_type = challenge_type

class MediaError(InstagramError):
    """Erreur liée aux médias (upload, like, comment, etc.)"""
    def __init__(self, message: str, media_id: str = None, action: str = None):
        super().__init__(message)
        self.media_id = media_id
        self.action = action

class UserNotFoundError(InstagramError):
    """Erreur utilisateur non trouvé"""
    def __init__(self, message: str, username: str = None):
        super().__init__(message)
        self.username = username

class AccountSuspendedError(AuthenticationError):
    """Erreur compte suspendu"""
    def __init__(self, message: str, username: str = None, url: str = None):
        super().__init__(message)
        self.username = username
        self.url = url

class AccountDisabledError(AuthenticationError):
    """Erreur compte désactivé"""
    def __init__(self, message: str, username: str = None):
        super().__init__(message)
        self.username = username

class RateLimitError(InstagramError):
    """Erreur de limite de taux dépassée"""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after

class LoginRequiredError(AuthenticationError):
    """Erreur de connexion requise"""
    def __init__(self, message: str, username: str = None):
        super().__init__(message)
        self.username = username

class InvalidCredentialsError(AuthenticationError):
    """Erreur identifiants invalides"""
    def __init__(self, message: str, username: str = None):
        super().__init__(message)
        self.username = username

class PasswordIncorrectError(AuthenticationError):
    """Erreur mot de passe incorrect"""
    def __init__(self, message: str, username: str = None):
        super().__init__(message)
        self.username = username

class LicenseError(Exception):
    """Erreur de licence d'utilisation"""
    def __init__(self, message: str = None):
        default_message = (
            "Ce script n'est pas autorisé à utiliser cette bibliothèque. "
            "Veuillez contacter le créateur via: 0389561802 ou https://t.me/Kenny5626"
        )
        super().__init__(message or default_message)

class FeedbackRequiredError(InstagramError):
    """Erreur feedback requis (rate limit spécifique)"""
    def __init__(self, message: str, feedback_type: str = None):
        super().__init__(message)
        self.feedback_type = feedback_type

class MediaDeletedError(MediaError):
    """Erreur média supprimé"""
    def __init__(self, message: str = "Ce média a été supprimé", media_id: str = None):
        super().__init__(message, media_id=media_id, action="access")

class PrivateAccountError(InstagramError):
    """Erreur compte privé"""
    def __init__(self, message: str, username: str = None):
        super().__init__(message)
        self.username = username

class CheckpointRequiredError(ChallengeError):
    """Erreur checkpoint requis"""
    def __init__(self, message: str, checkpoint_url: str = None):
        super().__init__(message, challenge_url=checkpoint_url, challenge_type="checkpoint")
