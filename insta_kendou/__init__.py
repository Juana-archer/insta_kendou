# -*- coding: utf-8 -*-
"""
insta_kendou - Bibliothèque Instagram complète
Gestion de l'authentification, 2FA, actions et médias Instagram

Version: 1.0.0 - Licence désactivée
Auteur: Utilisateur
"""

from .client import InstagramClient
from .exceptions import *

# ✅ LICENCE DÉSACTIVÉE - Plus de validation
# from .utils.license import validate_license, LicenseError
# if not validate_license():
#     raise LicenseError()

# Informations de la bibliothèque modifiées
__version__ = "1.0.0"
__author__ = "Utilisateur"
__email__ = ""
__url__ = ""
__description__ = "Bibliothèque Instagram avec licence désactivée"

# Exports principaux
__all__ = [
    'InstagramClient',
    # Exceptions
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
    'PasswordIncorrectError'
    # 'LicenseError'  # Retiré car licence désactivée
]

def get_version():
    """Retourner la version de la bibliothèque"""
    return __version__

def check_license():
    """Vérifier la licence d'utilisation - TOUJOURS VALIDE"""
    return True  # ✅ Licence toujours valide

# Message de bienvenue (silencieux)
def _init_message():
    """Message d'initialisation silencieux"""
    try:
        import sys
        if hasattr(sys.stdout, 'write'):
            pass  # Initialisation silencieuse
    except:
        pass

_init_message()
