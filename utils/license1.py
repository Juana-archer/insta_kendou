# -*- coding: utf-8 -*-
"""
Gestionnaire de validation de licence pour insta_kendou - VERSION CORRIGÉE
Vérification avancée du code d'accès avec détection d'obfuscation améliorée
"""

import hashlib
import inspect
import sys
import os
import base64
import re

# Code d'accès requis
REQUIRED_ACCESS_CODE = "MampifalyfelicienKennyNestinFoad56266325$17Mars2004FeliciteGemmellineNestine"

# Exception personnalisée pour les erreurs de licence
class LicenseError(Exception):
    """Exception levée quand la licence n'est pas valide"""
    def __init__(self, message=None):
        if message is None:
            message = get_license_error_message()
        super().__init__(message)

def validate_license() -> bool:
    """
    Valider la licence d'utilisation avec détection avancée d'obfuscation CORRIGÉE
    """
    try:
        frame = inspect.currentframe()
        try:
            # Remonter la pile d'appels pour trouver le script principal
            caller_frame = frame.f_back
            
            while caller_frame:
                # Chercher le module principal (__main__)
                if caller_frame.f_code.co_name == '<module>':
                    # Obtenir le contenu du fichier appelant
                    filename = caller_frame.f_code.co_filename
                    
                    if os.path.exists(filename) and os.path.isfile(filename):
                        try:
                            with open(filename, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            try:
                                with open(filename, 'r', encoding='latin-1') as f:
                                    content = f.read()
                            except Exception:
                                caller_frame = caller_frame.f_back
                                continue

                        # Code d'accès requis (original)
                        required_code = REQUIRED_ACCESS_CODE

                        # Vérification 1: Code direct (non obfusqué)
                        if required_code in content:
                            return True

                        # Vérification 2: Code obfusqué en base64
                        try:
                            required_b64 = base64.b64encode(required_code.encode()).decode()
                            if required_b64 in content:
                                return True
                        except Exception:
                            pass

                        # Vérification 3: Hash du code (signature)
                        try:
                            required_hash = hashlib.sha256(required_code.encode()).hexdigest()
                            if required_hash in content:
                                return True
                        except Exception:
                            pass

                        # Vérification 4: Code inversé
                        try:
                            required_reversed = required_code[::-1]
                            if required_reversed in content:
                                return True
                        except Exception:
                            pass

                        # Vérification 5: Code ROT13
                        try:
                            def rot13(text):
                                result = ""
                                for char in text:
                                    if 'a' <= char <= 'z':
                                        result += chr((ord(char) - ord('a') + 13) % 26 + ord('a'))
                                    elif 'A' <= char <= 'Z':
                                        result += chr((ord(char) - ord('A') + 13) % 26 + ord('A'))
                                    else:
                                        result += char
                                return result

                            required_rot13 = rot13(required_code)
                            if required_rot13 in content:
                                return True
                        except Exception:
                            pass

                        # Vérification 6: Code en hexadécimal
                        try:
                            required_hex = required_code.encode().hex()
                            if required_hex in content:
                                return True
                        except Exception:
                            pass

                        # Vérification 7: Patterns obfusqués (recherche dans les strings base64)
                        try:
                            b64_patterns = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', content)
                            for pattern in b64_patterns:
                                try:
                                    decoded = base64.b64decode(pattern).decode('utf-8', errors='ignore')
                                    if required_code in decoded:
                                        return True
                                except:
                                    continue
                        except Exception:
                            pass

                        # Vérification 8: Hash partiel (pour codes très obfusqués)
                        try:
                            code_parts = [
                                "MampifalyfelicienKenny",
                                "NestinFoad56266325", 
                                "17Mars2004",
                                "FeliciteGemmellineNestine"
                            ]

                            found_parts = 0
                            for part in code_parts:
                                part_hash = hashlib.md5(part.encode()).hexdigest()[:16]
                                if part_hash in content:
                                    found_parts += 1

                            if found_parts >= 3:  # Au moins 3 parties trouvées
                                return True
                        except Exception:
                            pass

                        # Échec de toutes les vérifications pour ce fichier
                        # Continue avec le frame suivant
                        
                caller_frame = caller_frame.f_back

            # Vérification dans les arguments de ligne de commande
            try:
                cmd_line = ' '.join(sys.argv)
                if REQUIRED_ACCESS_CODE in cmd_line:
                    return True
            except Exception:
                pass

            # Aucune validation réussie
            return False

        finally:
            del frame
    except Exception:
        return False

def get_license_error_message() -> str:
    """Retourner le message d'erreur de licence"""
    return (
        "❌ ERREUR D'AUTORISATION\n"
        "Ce script n'est pas autorisé à utiliser cette bibliothèque.\n"
        "Le code d'accès n'a pas été trouvé (même obfusqué).\n"
        "Veuillez contacter le créateur du projet via:\n"
        "📞 Téléphone: 0389561802\n"
        "💬 Telegram: https://t.me/Kenny5626"
    )

def check_license_or_exit():
    """Vérifier la licence et quitter si non valide"""
    if not validate_license():
        raise LicenseError()

# Auto-vérification lors de l'importation
def _auto_validate():
    """Auto-validation lors de l'importation"""
    try:
        if not validate_license():
            raise LicenseError()
    except Exception as e:
        if isinstance(e, LicenseError):
            print("\n" + str(e) + "\n")
            sys.exit(1)

# Exécuter la validation automatique
_auto_validate()
