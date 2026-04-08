# -*- coding: utf-8 -*-
"""
Module d'authentification Instagram pour insta_kendou
Gestion complète de la connexion et de l'authentification 2FA
"""

from .authentication import InstagramAuth
from .bloks_2fa import BloksManager
from .alternative_2fa import AlternativeManager  
from .classic_2fa import ClassicManager
from .challenge_handler import ChallengeHandler
from .authentication import InstagramAuth, InstagramSignup

__all__ = [
    'InstagramAuth',
    'InstagramSignup',
    'BloksManager', 
    'AlternativeManager',
    'ClassicManager',
    'ChallengeHandler'
]
