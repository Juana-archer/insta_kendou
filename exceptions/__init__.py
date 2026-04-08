# -*- coding: utf-8 -*-
"""
Module d'exceptions pour insta_kendou
Définition des exceptions personnalisées pour la gestion d'erreurs
"""

from .errors import (
    InstagramError,
    AuthenticationError,
    TwoFactorError,
    ChallengeError,
    MediaError,
    UserNotFoundError,
    AccountSuspendedError,
    AccountDisabledError,
    RateLimitError,
    LoginRequiredError,
    InvalidCredentialsError,
    PasswordIncorrectError,
    UserNotFoundError,
    LicenseError
)

__all__ = [
    'InstagramError',
    'AuthenticationError',
    'TwoFactorError', 
    'ChallengeError',
    'MediaError',
    'UserNotFoundError',
    'AccountSuspendedError',
    'AccountDisabledError',
    'RateLimitError',
    'LoginRequiredError',
    'InvalidCredentialsError',
    'PasswordIncorrectError',
    'UserNotFoundError',
    'LicenseError'
]
