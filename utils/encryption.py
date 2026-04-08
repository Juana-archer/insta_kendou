# -*- coding: utf-8 -*-
"""
Gestionnaire du chiffrement Instagram avec décodage unifié
Gestion du chiffrement des mots de passe et décodage des réponses
"""

import time
import json
import hashlib
import hmac
import base64
import requests
import random
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from .license import validate_license

class InstagramEncryption:
    """Gestionnaire du chiffrement Instagram avec décodage unifié pour tous les environnements"""
    
    def __init__(self):
        # Validation licence obligatoire
        if not validate_license():
            raise PermissionError("Ce script n'est pas autorisé à utiliser cette bibliothèque. Veuillez contacter le créateur via: 0389561802 ou https://t.me/Kenny5626")
    
    @staticmethod
    def safe_decode_response(response: requests.Response) -> str:
        """Décoder TOUTES les réponses de manière sécurisée - MÉTHODE UNIVERSELLE"""
        try:
            # ÉTAPE 1: Vérifier d'abord si c'est déjà du texte lisible
            try:
                # Essayer de décoder directement
                text = response.text
                
                # Vérifier si c'est du JSON ou texte lisible
                if any(char in text for char in ['{', '"', 'status', 'ok', 'error']):
                    return text
                    
            except Exception:
                pass
            
            # ÉTAPE 2: Récupérer le contenu brut
            content = response.content
            
            # Si le contenu est vide, retourner vide
            if not content:
                return ""
            
            # ÉTAPE 3: Détecter et gérer la compression
            content_encoding = response.headers.get('content-encoding', '').lower()
            
            if content_encoding == 'gzip':
                try:
                    import gzip
                    decompressed = gzip.decompress(content)
                    return decompressed.decode('utf-8', errors='ignore')
                except Exception:
                    pass
            
            elif content_encoding == 'deflate':
                try:
                    import zlib
                    # Essayer deflate standard
                    try:
                        decompressed = zlib.decompress(content)
                        return decompressed.decode('utf-8', errors='ignore')
                    except:
                        # Essayer deflate avec header
                        decompressed = zlib.decompress(content, -zlib.MAX_WBITS)
                        return decompressed.decode('utf-8', errors='ignore')
                except Exception:
                    pass
            
            elif content_encoding == 'zstd':
                try:
                    # Essayer zstd si disponible
                    import zstandard as zstd
                    dctx = zstd.ZstdDecompressor()
                    decompressed = dctx.decompress(content)
                    return decompressed.decode('utf-8', errors='ignore')
                except ImportError:
                    # zstd non disponible - ignorer cette compression
                    pass
                except Exception:
                    pass
            
            # ÉTAPE 4: Essayer différents encodages sur le contenu brut
            encodings_to_try = [
                'utf-8',
                'latin1', 
                'iso-8859-1',
                'ascii',
                'cp1252'
            ]
            
            for encoding in encodings_to_try:
                try:
                    decoded = content.decode(encoding, errors='ignore')
                    
                    # Vérifier si le décodage semble correct
                    if any(char in decoded for char in ['{', '"', 'status', 'ok']):
                        return decoded
                    
                    # Si c'est du texte normal (pas forcément JSON)
                    if len(decoded) > 0 and decoded.isprintable():
                        return decoded
                        
                except Exception:
                    continue
            
            # ÉTAPE 5: Dernier recours - retourner en tant que string brute
            try:
                # Essayer de convertir les bytes en string lisible
                result = content.decode('utf-8', errors='replace')
                if result:
                    return result
            except Exception:
                pass
            
            # ÉTAPE 6: Ultime fallback
            return str(content)
            
        except Exception as e:
            # En cas d'erreur totale, retourner au moins quelque chose
            try:
                return response.text if hasattr(response, 'text') else str(response.content)
            except:
                return f"Erreur décodage: {str(e)}"
    
    @staticmethod
    def safe_parse_json(response: requests.Response) -> dict:
        """Parser JSON de manière sécurisée avec décodage unifié"""
        try:
            # Utiliser le décodage unifié
            text = InstagramEncryption.safe_decode_response(response)
            
            if not text or text == "":
                return {"error": "Réponse vide"}
            
            # Essayer de parser en JSON
            try:
                import json
                return json.loads(text)
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON valide, retourner le texte brut
                return {
                    "error": "Non-JSON",
                    "raw_text": text[:1000] + "..." if len(text) > 1000 else text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "error": f"Erreur parsing: {str(e)}",
                "status_code": getattr(response, 'status_code', 0)
            }
    
    @staticmethod
    def is_success_response(response: requests.Response, parsed_data: dict = None) -> bool:
        """Vérifier si une réponse indique un succès"""
        try:
            # Vérifier le code de statut HTTP d'abord
            if response.status_code != 200:
                return False
            
            # Si pas de données parsées, essayer de les parser
            if parsed_data is None:
                parsed_data = InstagramEncryption.safe_parse_json(response)
            
            # Vérifier les indicateurs de succès Instagram
            if isinstance(parsed_data, dict):
                # Succès explicite
                if parsed_data.get("status") == "ok":
                    return True
                
                # Pas d'erreur = succès potentiel
                if "error" not in parsed_data and "message" not in parsed_data:
                    return True
                
                # Vérifier les champs spécifiques de succès
                success_indicators = [
                    "logged_in_user",
                    "did_delete", 
                    "friendship_status",
                    "media"
                ]
                
                if any(indicator in parsed_data for indicator in success_indicators):
                    return True
            
            # Si on arrive ici et que le statut HTTP est 200, c'est probablement un succès
            return True
            
        except Exception:
            # En cas d'erreur, considérer comme échec
            return False
    
    @staticmethod
    def extract_error_from_response(response: requests.Response, parsed_data: dict = None) -> str:
        """Extraire le message d'erreur d'une réponse"""
        try:
            if parsed_data is None:
                parsed_data = InstagramEncryption.safe_parse_json(response)
            
            if isinstance(parsed_data, dict):
                # Messages d'erreur Instagram courants
                error_fields = [
                    "message",
                    "error_title", 
                    "error_body",
                    "feedback_message",
                    "error"
                ]
                
                for field in error_fields:
                    if field in parsed_data:
                        error_msg = parsed_data[field]
                        if isinstance(error_msg, str) and error_msg:
                            return error_msg
                
                # Si pas de message d'erreur spécifique
                if parsed_data.get("status") != "ok":
                    return f"Erreur Instagram: {parsed_data}"
            
            # Fallback sur le statut HTTP
            if response.status_code != 200:
                return f"HTTP {response.status_code}"
            
            return "Erreur inconnue"
            
        except Exception as e:
            return f"Erreur extraction: {str(e)}"
    
    @staticmethod
    def get_public_keys() -> tuple:
        """Récupérer les clés publiques Instagram actuelles"""
        try:
            response = requests.get('https://www.instagram.com/data/shared_data/', timeout=10)
            if response.status_code == 200:
                import re
                # Extraire les données de chiffrement depuis le HTML
                match = re.search(r'"encryption":\s*\{[^}]+\}', response.text)
                if match:
                    import json
                    encryption_data = json.loads('{' + match.group(0) + '}')
                    encryption = encryption_data.get('encryption', {})
                    
                    key_id = encryption.get('key_id', 72)
                    public_key = encryption.get('public_key', 'b3a328ff28b785092af6a578767877514c93a690a11b9d92ba0ce614c9d5db57')
                    version = encryption.get('version', 10)
                    
                    return int(key_id), public_key, int(version)
        except Exception as e:
            pass
        
        # Fallback avec clés par défaut récentes
        return 72, 'b3a328ff28b785092af6a578767877514c93a690a11b9d92ba0ce614c9d5db57', 10
    
    @staticmethod
    def encrypt_password(password: str) -> str:
        """Chiffrer mot de passe avec AES-GCM + SealedBox (format Instagram Browser)"""
        try:
            from nacl.public import PublicKey, SealedBox
            import binascii
            import struct
            import datetime
            
            # Récupérer clés publiques actuelles
            key_id, public_key_hex, version = InstagramEncryption.get_public_keys()
            
            # Générer clé AES et IV
            session_key = get_random_bytes(32)
            iv = bytes([0] * 12)  # IV zéro pour Instagram
            
            # Timestamp actuel
            timestamp = int(datetime.datetime.now().timestamp())
            timestamp_str = str(timestamp)
            
            # Chiffrer le mot de passe avec AES-GCM
            cipher_aes = AES.new(session_key, AES.MODE_GCM, nonce=iv, mac_len=16)
            cipher_aes.update(timestamp_str.encode('utf-8'))
            encrypted_password, cipher_tag = cipher_aes.encrypt_and_digest(password.encode('utf-8'))
            
            # Chiffrer la clé de session avec SealedBox (Curve25519)
            public_key_bytes = binascii.unhexlify(public_key_hex)
            public_key_nacl = PublicKey(public_key_bytes)
            sealed_box = SealedBox(public_key_nacl)
            encrypted_key = sealed_box.encrypt(session_key)
            
            # Construire payload final
            payload = bytearray()
            payload.append(1)  # Version flag
            payload.append(key_id)  # Key ID
            payload.extend(struct.pack('<H', len(encrypted_key)))  # Key length
            payload.extend(encrypted_key)  # Encrypted key
            payload.extend(cipher_tag)  # Auth tag
            payload.extend(encrypted_password)  # Encrypted password
            
            encoded = base64.b64encode(payload).decode('utf-8')
            return f"#PWD_INSTAGRAM_BROWSER:10:{timestamp}:{encoded}"
            
        except ImportError:
            # Fallback si PyNaCl pas installé
            return InstagramEncryption.encrypt_password_fallback(password)
        except Exception as e:
            return InstagramEncryption.encrypt_password_fallback(password)
    
    @staticmethod
    def encrypt_password_fallback(password: str) -> str:
        """Fallback avec ancien format (pour compatibilité)"""
        timestamp = int(time.time())
        salt = get_random_bytes(32)
        password_data = f"{password}{timestamp}".encode('utf-8')
        sha256_hash = hashlib.sha256(password_data + salt).digest()
        hmac_hash = hmac.new(salt[:16], password_data, hashlib.sha256).digest()
        combined = sha256_hash + hmac_hash + salt
        encoded = base64.b64encode(combined).decode('utf-8')
        return f"#PWD_INSTAGRAM:4:{timestamp}:{encoded}"
    
    @staticmethod
    def generate_signature(data: str) -> str:
        """Générer signature HMAC pour signed_body"""
        # Clé secrète Instagram (extraite de l'APK)
        key = "c9c5a5ba6b32e95562e5b3e95562e5b3"
        signature = hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
        return signature
    
    @staticmethod
    def create_signed_body(data: dict) -> str:
        """Créer signed_body avec signature"""
        json_data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        signature = InstagramEncryption.generate_signature(json_data)
        return f"{signature}.{json_data}"
