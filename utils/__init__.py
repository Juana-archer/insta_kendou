# -*- coding: utf-8 -*-
"""
Module utilitaires pour insta_kendou
Gestion des devices, encryption, médias et résolution d'URLs
"""

from .device import DeviceManager, get_optimal_encoding_for_environment, detect_termux_environment
from .encryption import InstagramEncryption
from .media import MediaProcessor
from .url_resolver import URLResolver
from .license import validate_license, LicenseError

__all__ = [
    'DeviceManager',
    'get_optimal_encoding_for_environment',
    'detect_termux_environment',
    'InstagramEncryption',
    'MediaProcessor',
    'URLResolver',
    'validate_license',
    'LicenseError'
]
