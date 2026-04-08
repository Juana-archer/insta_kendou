# -*- coding: utf-8 -*-
"""
Gestionnaire principal d'authentification Instagram
Gestion de la connexion sessions et device management avec flux Web complet
"""

import os
import json
import time
import uuid
import random
import hashlib
import hmac
import base64
import requests
import urllib.parse
import subprocess
import struct
import re
from urllib.parse import unquote
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import nacl.secret
import nacl.utils
from nacl.public import SealedBox, PublicKey
from datetime import datetime
from ..utils.license import validate_license
from ..utils.encryption import InstagramEncryption

def generate_random_dpi():
    """Générer un DPI aléatoire réaliste"""
    return random.randint(200, 500)

def generate_random_resolution():
    """Générer une résolution aléatoire réaliste"""
    width = random.randint(720, 1440)
    height = random.randint(1280, 3200)
    return f"{width}x{height}"

def generate_random_string(length=8, prefix="", suffix=""):
    """Générer une chaîne aléatoire de caractères"""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    random_str = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}{random_str}{suffix}"

def generate_random_model():
    """Générer un modèle de téléphone aléatoire"""
    prefixes = ["SM-", "GT-", "RM-", "V2", "M2", "CPH", "NE2", "PVL", "DEKGE"]
    prefix = random.choice(prefixes)
    if prefix == "DEKGE":
        suffix = generate_random_string(6, prefix="").upper()
        return f"{prefix}{suffix}"
    else:
        suffix = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=random.randint(4, 6)))
        return f"{prefix}{suffix}"

def generate_random_brand():
    """Générer une marque aléatoire"""
    brands = ["samsung", "google", "xiaomi", "oppo", "vivo", "realme", "oneplus", "nothing", "honor"]
    random_brands = [generate_random_string(6).lower() for _ in range(5)]
    return random.choice(brands + random_brands)

def generate_random_manufacturer():
    """Générer un fabricant aléatoire"""
    manufacturers = ["samsung", "Google", "Xiaomi", "OPPO", "vivo", "realme", "OnePlus", "Nothing", "HONOR"]
    random_manufacturers = [generate_random_string(7).capitalize() for _ in range(5)]
    return random.choice(manufacturers + random_manufacturers)

def generate_random_device():
    """Générer un code device aléatoire"""
    return generate_random_string(4).lower()

def generate_random_cpu():
    """Générer un CPU aléatoire"""
    cpus = ["mt6989", "mt6985", "sm8550", "sm8650", "gs201", "gs301"]
    random_cpus = [generate_random_string(6).lower() for _ in range(3)]
    return random.choice(cpus + random_cpus)

def generate_random_version_code():
    """Générer un version code Instagram aléatoire"""
    return str(random.randint(370000000, 380000000))

def generate_random_instagram_version():
    """Générer une version Instagram aléatoire"""
    major = random.randint(300, 320)
    minor = random.randint(0, 5)
    patch = random.randint(0, 20)
    build = random.randint(30, 150)
    return f"{major}.0.0.{patch}.{build}"

class TermuxDeviceGenerator:
    """Générateur de device Android - Génération 100% aléatoire, aucune récupération Termux"""

    @staticmethod
    def get_real_android_device_info():
        """Générer des informations de device 100% aléatoires (aucune récupération Termux)"""
        device_info = {}

        # Génération 100% aléatoire - aucune récupération système
        device_info['model'] = generate_random_model()
        device_info['brand'] = generate_random_brand()
        device_info['manufacturer'] = generate_random_manufacturer()
        device_info['device'] = generate_random_device()
        device_info['android_version'] = random.choice(["10", "11", "12", "13", "14"])
        device_info['sdk_version'] = str(random.randint(29, 34))
        device_info['build_id'] = generate_random_string(10).upper()
        device_info['screen_width'] = random.randint(390, 450)
        device_info['screen_height'] = random.randint(844, 956)
        device_info['dpr'] = round(random.uniform(2.5, 3.5), 3)

        # Générer des valeurs aléatoires pour mobile
        device_info['android_release'] = device_info.get('android_version', '14')
        device_info['dpi'] = f"{generate_random_dpi()}dpi"
        device_info['resolution'] = generate_random_resolution()
        device_info['cpu'] = generate_random_cpu()
        device_info['version_code'] = generate_random_version_code()
        device_info['instagram_version'] = generate_random_instagram_version()

        # User-Agent Web réaliste avec timestamp pour unicité
        device_info['user_agent'] = (
            f"Mozilla/5.0 (Linux; Android {device_info['android_version']}; "
            f"{device_info['model']}) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/140.0.0.0 Mobile Safari/537.36"
        )

        # User-Agent Mobile Instagram avec valeurs aléatoires
        device_info['user_agent_mobile'] = (
            f"Instagram {device_info['instagram_version']} Android ({device_info['android_version']}/"
            f"{device_info['android_release']}; {device_info['dpi']}; "
            f"{device_info['resolution']}; {device_info['manufacturer']}; "
            f"{device_info['model']}; {device_info['device']}; {device_info['cpu']}; "
            f"en_US; {device_info['version_code']})"
        )
        
        device_info['platform_version'] = f"{device_info['android_version']}.0.0"
        device_info['retrieved_at'] = int(time.time())
        
        return device_info

    
    @staticmethod
    def get_instagram_mid_from_web(device_info: dict) -> str:
        """Récupérer MID Instagram depuis le web"""
        temp_session = requests.Session()
        
        try:
            shared_headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "user-agent": device_info['user_agent'],
                "cache-control": "no-cache"
            }
            
            response = temp_session.get(
                "https://www.instagram.com/data/shared_data/",
                headers=shared_headers,
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                content = InstagramEncryption.safe_decode_response(response)
                
                try:
                    data = json.loads(content)
                    mid_locations = [
                        data.get("machine_id"),
                        data.get("mid"),
                        data.get("config", {}).get("machine_id"),
                        data.get("config", {}).get("mid"),
                        data.get("rollout_hash")
                    ]
                    
                    for mid_candidate in mid_locations:
                        if mid_candidate and len(str(mid_candidate)) > 15:
                            return str(mid_candidate)
                            
                except json.JSONDecodeError:
                    pass
                
                mid_patterns = [
                    r'"machine_id"\s*:\s*"([A-Za-z0-9+/=_-]{20,})"',
                    r'"mid"\s*:\s*"([A-Za-z0-9+/=_-]{20,})"',
                    r'"rollout_hash"\s*:\s*"([A-Za-z0-9+/=_-]{20,})"'
                ]
                
                for pattern in mid_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        mid_candidate = matches[0].strip()
                        if len(mid_candidate) > 15:
                            return mid_candidate
        
        except Exception as e:
            pass
        
        # Fallback - générer un MID basé sur le device + timestamp
        try:
            device_string = f"{device_info['model']}{device_info['android_version']}{int(time.time())}"
            device_hash = hashlib.sha256(device_string.encode()).hexdigest()
            mid_bytes = device_hash[:32].encode()
            mid_b64 = base64.b64encode(mid_bytes).decode().rstrip('=')
            return f"aK{mid_b64}AABAABAAGr1cGeLxBgxSR2V-Nk"[:30]
        except:
            return f"aK{hashlib.md5(str(time.time()).encode()).hexdigest()[:20]}AABAA"
        
# -*- coding: utf-8 -*-
"""
Classe InstagramSignup améliorée avec gestion d'erreurs user-friendly
Intégration complète du flux d'inscription Web avec détection de suspension
"""

class InstagramSignup:
    """Gestionnaire de création de compte Instagram via Web - Version améliorée"""
    
    def __init__(self, client=None):
        """Initialiser le gestionnaire d'inscription
        
        Args:
            client: Instance du client Instagram (optionnel)
        """
        self.client = client
        self.session = client.auth.session if client else None
        self.device_info = {}
        
        # Variables Web spécifiques
        self.csrf_token = ""
        self.device_id = ""
        self.mid = ""
        self.datr = ""
        self.encryption_key_id = ""
        self.encryption_public_key = ""
        
        # Variables signup
        self.signup_data = {}
        self.signup_code = ""
        self.web_session_id = ""
        
        # État du processus
        self._state = "idle"  # idle, initialized, user_input, username_verified, age_verified, email_sent, code_verified, ready_to_create
        self._username_suggestions = []
        self._birth_date = {}
        
    def generate_device_info(self):
        """Générer des informations de device Android réalistes avec Chrome moderne"""
        import random
        
        # Modèles de téléphones populaires (pour les headers sec-ch-ua-model)
        devices = [
            {"model": "SM-G991B", "brand": "samsung", "manufacturer": "samsung", "device": "o1q", "android": "14"},
            {"model": "Pixel 8", "brand": "google", "manufacturer": "Google", "device": "shiba", "android": "14"},
            {"model": "SM-A54", "brand": "samsung", "manufacturer": "samsung", "device": "a54x", "android": "14"},
            {"model": "Redmi Note 13", "brand": "xiaomi", "manufacturer": "Xiaomi", "device": "sapphire", "android": "14"},
            {"model": "POCO F6", "brand": "xiaomi", "manufacturer": "Xiaomi", "device": "mondrian", "android": "14"},
            {"model": "OnePlus 12", "brand": "oneplus", "manufacturer": "OnePlus", "device": "salami", "android": "14"},
            {"model": "SM-S918B", "brand": "samsung", "manufacturer": "samsung", "device": "dm1q", "android": "14"},
            {"model": "Pixel 9", "brand": "google", "manufacturer": "Google", "device": "tokay", "android": "14"},
            {"model": "Mi 14", "brand": "xiaomi", "manufacturer": "Xiaomi", "device": "fuxi", "android": "14"},
            {"model": "Find X7", "brand": "oppo", "manufacturer": "OPPO", "device": "oplus2309", "android": "14"},
            {"model": "Galaxy S24", "brand": "samsung", "manufacturer": "samsung", "device": "e1q", "android": "14"},
            {"model": "Nothing Phone 2", "brand": "nothing", "manufacturer": "Nothing", "device": "spacewar", "android": "14"},
            {"model": "Realme GT 6", "brand": "realme", "manufacturer": "realme", "device": "lunaa", "android": "14"},
            {"model": "Vivo X100", "brand": "vivo", "manufacturer": "vivo", "device": "V2309A", "android": "14"},
            {"model": "Honor Magic6", "brand": "honor", "manufacturer": "HONOR", "device": "BVL-AN00", "android": "14"}
        ]
        
        device = random.choice(devices)
        
        # Versions Android modernes
        android_versions = ["10", "11", "12", "13", "14"]
        android_version = random.choice(android_versions)
        
        self.device_info = {
            "model": device["model"],
            "brand": device["brand"],
            "manufacturer": device["manufacturer"],
            "device": device["device"],
            "android_version": android_version,
            "sdk_version": str(29 + int(android_version) - 10) if android_version.isdigit() else "34",
            "screen_width": random.randint(390, 450),
            "screen_height": random.randint(844, 956),
            "dpr": round(random.uniform(2.5, 3.5), 1),
            "platform_version": f"{android_version}.0.0"
        }
        
        # Versions Chrome modernes réelles (142+)
        chrome_versions = [
            # Chrome 143 (les plus récentes)
            "143.0.0.0", "143.0.6351.186", "143.0.6351.181", "143.0.6351.164",
            "143.0.6351.159", "143.0.6351.153", "143.0.6351.143", "143.0.6351.121",
            # Chrome 142
            "142.0.0.0", "142.0.6367.243", "142.0.6367.235", "142.0.6367.228", 
            "142.0.6367.218", "142.0.6367.201", "142.0.6367.187", "142.0.6367.172",
            "142.0.6367.158", "142.0.6367.142", "142.0.6367.118", "142.0.6367.91"
        ]
        chrome_version = random.choice(chrome_versions)
        
        # Format moderne de User-Agent (avec "K" au lieu du modèle spécifique)
        self.device_info['user_agent'] = (
            f"Mozilla/5.0 (Linux; Android {android_version}; K) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_version} Mobile Safari/537.36"
        )
        
        return self.device_info
    
    def get_base_headers(self):
        """Headers de base pour toutes les requêtes avec versions Chrome cohérentes"""
        # Extraire la version Chrome majeure du user agent pour cohérence
        user_agent = self.device_info.get("user_agent", "")
        chrome_version = "143"  # Default moderne
        full_chrome_version = "143.0.0.0"
        
        if "Chrome/" in user_agent:
            try:
                chrome_part = user_agent.split("Chrome/")[1].split(" ")[0]
                chrome_version = chrome_part.split(".")[0]
                full_chrome_version = chrome_part
            except:
                chrome_version = "143"
                full_chrome_version = "143.0.0.0"
        
        return {
            "host": "www.instagram.com",
            "connection": "keep-alive",
            "sec-ch-ua": f'"Google Chrome";v="{chrome_version}", "Chromium";v="{chrome_version}", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-ch-ua-platform-version": f'"{self.device_info.get("android_version", "14")}.0.0"',
            "sec-ch-ua-model": f'"{self.device_info.get("model", "SM-G991B")}"',
            "sec-ch-ua-full-version-list": f'"Google Chrome";v="{full_chrome_version}", "Chromium";v="{full_chrome_version}", "Not?A_Brand";v="99.0.0.0"',
            "user-agent": self.device_info.get("user_agent"),
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "accept-encoding": "gzip, deflate, br",
            "sec-ch-prefers-color-scheme": "light",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "viewport-width": str(self.device_info.get("screen_width", "393"))
        }
    
    def initialize_session(self) -> dict:
        """ÉTAPE 1: Initialiser la session pour l'inscription"""
        try:
            if not self.session:
                return {"success": False, "error": "Session non disponible"}
            
            # Générer device info
            self.generate_device_info()
            
            # ÉTAPE 1: Récupération shared_data
            if not self.step1_get_shared_data():
                return {"success": False, "error": "Échec récupération shared_data"}
            
            # ÉTAPE 2: Récupération cookies page signup
            if not self.step2_get_signup_cookies():
                return {"success": False, "error": "Échec récupération cookies signup"}
            
            self._state = "initialized"
            return {
                "success": True,
                "message": "Session initialisée avec succès",
                "device_info": {
                    "model": self.device_info["model"],
                    "android_version": self.device_info["android_version"],
                    "chrome_version": self.device_info["user_agent"].split("Chrome/")[1].split(" ")[0] if "Chrome/" in self.device_info["user_agent"] else "141.0.0.0",
                    "device_id_short": self.device_id[:20] + "..." if self.device_id else "Non défini"
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Erreur initialisation: {str(e)}"}
    
    def step1_get_shared_data(self):
        """ÉTAPE 1: Récupération shared_data"""
        import time
        
        screen_width = self.device_info.get("screen_width", 412)
        dpr = self.device_info.get("dpr", 2.625)
        
        headers = {
            **self.get_base_headers(),
            "dpr": str(dpr),
            "viewport-width": str(screen_width),
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document"
        }
        
        try:
            response = self.session.get("https://www.instagram.com/data/shared_data/", headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                self.device_id = data.get("device_id", "")
                encryption = data.get("encryption", {})
                self.encryption_key_id = encryption.get("key_id", "")
                self.encryption_public_key = encryption.get("public_key", "")
                return True
            return False
        except Exception as e:
            return False
    
    def step2_get_signup_cookies(self):
        """ÉTAPE 2: Récupération cookies page d'inscription"""
        import re
        import time
        
        screen_width = self.device_info.get("screen_width", 412)
        dpr = self.device_info.get("dpr", 2.625)
        
        headers = {
            **self.get_base_headers(),
            "dpr": str(dpr),
            "viewport-width": str(screen_width),
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "referer": "https://www.instagram.com/data/shared_data/",
            "cookie": f"ig_did={self.device_id}"
        }
        
        try:
            # D'abord aller vers la homepage
            response_home = self.session.get("https://www.instagram.com/", headers=headers, timeout=15)
            
            if response_home.status_code == 200:
                # Extraire les cookies depuis la homepage
                for cookie in response_home.cookies:
                    if cookie.name == "csrftoken":
                        self.csrf_token = cookie.value
                    elif cookie.name == "mid":
                        self.mid = cookie.value
                    elif cookie.name == "datr":
                        self.datr = cookie.value
                
                # Si pas de mid depuis les cookies, chercher dans le HTML
                if not self.mid:
                    html_text = response_home.text
                    patterns = [
                        r'"machine_id"\s*:\s*"([^"]+)"',
                        r'"mid"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
                        r'"deferredCookies"\s*:\s*{[^}]*"mid"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, html_text)
                        if match:
                            self.mid = match.group(1)
                            break
            
            # Aller vers la page signup avec les cookies récupérés
            if self.csrf_token:
                headers["cookie"] = f"ig_did={self.device_id}; csrftoken={self.csrf_token}; datr={self.datr}; mid={self.mid}"
                
                response_signup = self.session.get("https://www.instagram.com/accounts/emailsignup/", headers=headers, timeout=15)
                
                if response_signup.status_code == 200:
                    # Mettre à jour les cookies depuis la page signup si nécessaire
                    for cookie in response_signup.cookies:
                        if cookie.name == "csrftoken":
                            self.csrf_token = cookie.value
                
                # Générer web session ID
                self.web_session_id = f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}"
                
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def _random_hex(self, length):
        """Générer une chaîne hexadécimale aléatoire"""
        import random
        return ''.join(random.choices('0123456789abcdef', k=length))
    
    def set_user_data(self, email: str, username: str, password: str, full_name: str) -> dict:
        """Définir les données utilisateur pour l'inscription"""
        try:
            if self._state != "initialized":
                return {"success": False, "error": "Session non initialisée. Appelez initialize_session() d'abord."}
            
            # Validation des données
            if not email or '@' not in email or '.' not in email:
                return {"success": False, "error": "Adresse email invalide"}
            
            if not username or len(username) < 3:
                return {"success": False, "error": "Nom d'utilisateur trop court (min 3 caractères)"}
            
            if not password or len(password) < 6:
                return {"success": False, "error": "Mot de passe trop court (min 6 caractères)"}
            
            if not full_name:
                return {"success": False, "error": "Nom complet requis"}
            
            self.signup_data = {
                "email": email.strip(),
                "username": username.strip(),
                "password": password,
                "full_name": full_name.strip()
            }
            
            self._state = "user_input"
            return {
                "success": True,
                "message": "Données utilisateur enregistrées",
                "data": {
                    "email": email,
                    "username": username,
                    "full_name": full_name
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Erreur enregistrement données: {str(e)}"}
    
    def check_username_availability(self, username: str = None) -> dict:
        """Vérifier la disponibilité du nom d'utilisateur"""
        import time
        import random
        
        try:
            if self._state not in ["user_input", "username_verified"]:
                return {"success": False, "error": "Données utilisateur non définies"}
            
            username_to_check = username or self.signup_data.get("username")
            if not username_to_check:
                return {"success": False, "error": "Nom d'utilisateur non défini"}
            
            # Vérifier que la session est prête
            if not self.verify_session_ready():
                return {"success": False, "error": "Session non prête pour les requêtes API"}
            
            encrypted_password = self.encrypt_password(self.signup_data["password"])
            
            headers = {
                **self.get_base_headers(),
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": self.web_session_id,
                "x-asbd-id": "359341",
                "x-ig-www-claim": "0",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/emailsignup/",
                "cookie": self.get_cookie_string()
            }
            
            payload = {
                "enc_password": encrypted_password,
                "email": self.signup_data["email"],
                "failed_birthday_year_count": "{}",
                "first_name": self.signup_data["full_name"],
                "username": username_to_check,
                "opt_into_one_tap": "false",
                "use_new_suggested_user_name": "true",
                "jazoest": str(random.randint(20000, 99999))
            }
            
            response = self.session.post(
                "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/",
                data=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get("dryrun_passed") == True:
                        self.signup_data["username"] = username_to_check
                        self._state = "username_verified"
                        return {
                            "success": True,
                            "available": True,
                            "username": username_to_check,
                            "message": f"Le nom d'utilisateur '{username_to_check}' est disponible"
                        }
                    
                    elif "username_is_taken" in str(data.get("errors", {})):
                        suggestions = data.get("username_suggestions", [])
                        self._username_suggestions = suggestions
                        return {
                            "success": True,
                            "available": False,
                            "username": username_to_check,
                            "suggestions": suggestions[:5],
                            "message": f"Le nom d'utilisateur '{username_to_check}' n'est pas disponible"
                        }
                    
                    else:
                        return {"success": False, "error": f"Erreur lors de la vérification: {data}"}
                        
                except Exception as e:
                    return {"success": False, "error": "Réponse invalide du serveur"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur vérification username: {str(e)}"}
    
    def set_birth_date(self, day: int, month: int, year: int) -> dict:
        """Définir la date de naissance et vérifier l'éligibilité"""
        try:
            if self._state != "username_verified":
                return {"success": False, "error": "Nom d'utilisateur non vérifié"}
            
            # Validation de base
            if not (1 <= day <= 31):
                return {"success": False, "error": "Jour invalide (1-31)"}
            
            if not (1 <= month <= 12):
                return {"success": False, "error": "Mois invalide (1-12)"}
            
            if not (1900 <= year <= 2010):
                return {"success": False, "error": "Année invalide (1900-2010)"}
            
            self._birth_date = {
                "day": str(day),
                "month": str(month),
                "year": str(year)
            }
            
            # Vérifier l'éligibilité d'âge
            age_check = self.check_age_eligibility(str(day), str(month), str(year))
            
            if age_check:
                self._state = "age_verified"
                return {
                    "success": True,
                    "eligible": True,
                    "birth_date": f"{day}/{month}/{year}",
                    "message": "Date de naissance valide et éligible"
                }
            else:
                return {
                    "success": False,
                    "eligible": False,
                    "birth_date": f"{day}/{month}/{year}",
                    "error": "Âge non éligible pour l'inscription"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Erreur validation date: {str(e)}"}
    
    def check_age_eligibility(self, day, month, year):
        """Vérifier l'éligibilité d'âge"""
        import time
        import random
        import json
        
        headers = {
            **self.get_base_headers(),
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
            "x-csrftoken": self.csrf_token,
            "x-web-session-id": self.web_session_id,
            "x-asbd-id": "359341",
            "x-ig-www-claim": "0",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.instagram.com/accounts/emailsignup/",
            "cookie": self.get_cookie_string()
        }
        
        payload = {
            "day": day,
            "month": month,
            "year": year,
            "jazoest": str(random.randint(20000, 99999))
        }
        
        try:
            response = self.session.post(
                "https://www.instagram.com/api/v1/web/consent/check_age_eligibility/",
                data=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return data.get("eligible_to_register") == True
                except json.JSONDecodeError:
                    return False
            
            return False
                
        except Exception as e:
            return False
    
    def send_verification_email(self) -> dict:
        """Envoyer le code de vérification par email"""
        import time
        import random
        import json
        
        try:
            if self._state != "age_verified":
                return {"success": False, "error": "Date de naissance non vérifiée"}
            
            headers = {
                **self.get_base_headers(),
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": self.web_session_id,
                "x-asbd-id": "359341",
                "x-ig-www-claim": "0",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/emailsignup/",
                "cookie": self.get_cookie_string()
            }
            
            payload = {
                "device_id": self.mid,
                "email": self.signup_data["email"],
                "jazoest": str(random.randint(20000, 99999))
            }
            
            response = self.session.post(
                "https://www.instagram.com/api/v1/accounts/send_verify_email/",
                data=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok":
                        self._state = "email_sent"
                        return {
                            "success": True,
                            "email": self.signup_data["email"],
                            "message": f"Code envoyé à {self.signup_data['email']}"
                        }
                    elif data.get("status") == "fail":
                        error_message = data.get("message", "Erreur inconnue")
                        return {"success": False, "error": f"Échec envoi: {error_message}"}
                    else:
                        return {"success": False, "error": f"Réponse inattendue: {data}"}
                except json.JSONDecodeError:
                    return {"success": False, "error": "Réponse invalide du serveur"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur envoi email: {str(e)}"}
    
    def verify_confirmation_code(self, code: str) -> dict:
        """Vérifier le code de confirmation"""
        import time
        import random
        
        try:
            if self._state != "email_sent":
                return {"success": False, "error": "Code non envoyé"}
            
            if not code or len(code) != 6 or not code.isdigit():
                return {"success": False, "error": "Le code doit contenir exactement 6 chiffres"}
            
            headers = {
                **self.get_base_headers(),
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": self.web_session_id,
                "x-asbd-id": "359341",
                "x-ig-www-claim": "0",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/emailsignup/",
                "cookie": self.get_cookie_string()
            }
            
            payload = {
                "code": code,
                "device_id": self.mid,
                "email": self.signup_data["email"],
                "jazoest": str(random.randint(20000, 99999))
            }
            
            response = self.session.post(
                "https://www.instagram.com/api/v1/accounts/check_confirmation_code/",
                data=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get("status") == "ok" and "signup_code" in data:
                        self.signup_code = data["signup_code"]
                        self._state = "code_verified"
                        return {
                            "success": True,
                            "verified": True,
                            "message": "Code vérifié avec succès"
                        }
                    elif data.get("status") == "fail":
                        return {"success": False, "error": data.get('message', 'Code invalide')}
                    else:
                        return {"success": False, "error": "Réponse inattendue"}
                        
                except Exception as e:
                    return {"success": False, "error": "Réponse invalide du serveur"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur vérification code: {str(e)}"}
    
    def create_account(self) -> dict:
        """Créer le compte Instagram avec gestion d'erreurs améliorée"""
        import time
        import random
        import os
        import json
        from datetime import datetime
        
        try:
            if self._state != "code_verified":
                return {"success": False, "error": "Code de vérification non confirmé"}
            
            if not self._birth_date:
                return {"success": False, "error": "Date de naissance non définie"}
            
            encrypted_password = self.encrypt_password(self.signup_data["password"])
            
            headers = {
                **self.get_base_headers(),
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": self.web_session_id,
                "x-asbd-id": "359341",
                "x-ig-www-claim": "0",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/emailsignup/",
                "cookie": self.get_cookie_string()
            }
            
            payload = {
                "enc_password": encrypted_password,
                "day": self._birth_date["day"],
                "email": self.signup_data["email"],
                "failed_birthday_year_count": "{}",
                "first_name": self.signup_data["full_name"],
                "month": self._birth_date["month"],
                "username": self.signup_data["username"],
                "year": self._birth_date["year"],
                "client_id": self.mid,
                "seamless_login_enabled": "1",
                "tos_version": "row",
                "force_sign_up_code": self.signup_code,
                "extra_session_id": self.web_session_id,
                "jazoest": str(random.randint(20000, 99999))
            }
            
            response = self.session.post(
                "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/",
                data=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get("account_created") == True:
                        user_id = data.get("user_id")
                        
                        # Extraire les cookies de session
                        cookies_dict = dict(self.session.cookies)
                        
                        # Informations du compte créé
                        account_result = {
                            "success": True,
                            "account_created": True,
                            "user_data": {
                                "user_id": user_id,
                                "username": self.signup_data["username"],
                                "email": self.signup_data["email"],
                                "full_name": self.signup_data["full_name"],
                                "password": self.signup_data["password"],
                                "birth_date": f"{self._birth_date['day']}/{self._birth_date['month']}/{self._birth_date['year']}"
                            },
                            "cookies": cookies_dict,
                            "device_info": self.device_info,
                            "created_at": int(time.time()),
                            "message": f"Compte @{self.signup_data['username']} créé avec succès!"
                        }
                        
                        # Sauvegarder les informations automatiquement
                        try:
                            self.save_account_info(account_result)
                        except:
                            pass  # Ne pas faire échouer si sauvegarde échoue
                        
                        # VÉRIFIER SI LE COMPTE EST SUSPENDU
                        suspension_check = self.check_account_suspension()
                        if suspension_check.get("suspended"):
                            account_result["suspended"] = True
                            account_result["message"] = f"⚠️ Compte @{self.signup_data['username']} créé mais SUSPENDU"
                            account_result["warning"] = "Changez de réseau de connexion ou d'email pour éviter la suspension à l'avenir"
                        
                        self._state = "account_created"
                        return account_result
                        
                    else:
                        # GESTION DES ERREURS AMÉLIORÉE
                        return self._handle_creation_errors(data)
                        
                except Exception as e:
                    return {"success": False, "error": "Réponse invalide du serveur"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur création compte: {str(e)}"}
    
    def _handle_creation_errors(self, data) -> dict:
        """Gérer les erreurs de création de compte de manière user-friendly"""
        errors = data.get("errors", {})
        error_type = data.get("error_type", "")
        
        # Erreur d'IP/Proxy
        if "ip" in errors or "proxy" in str(errors).lower():
            return {
                "success": False,
                "error": f"Création de compte échouée pour @{self.signup_data.get('username', 'N/A')}",
                "message": "Veuillez changer de réseau de connexion ou d'adresse email pour créer le compte",
                "error_type": "network_blocked",
                "retry_suggestions": [
                    "Changer de réseau de connexion (WiFi, données mobiles, VPN)",
                    "Utiliser une autre adresse email",
                    "Réessayer plus tard depuis un autre réseau"
                ]
            }
        
        # Erreur de rate limiting
        if "signup_block" in error_type or "rate" in str(errors).lower():
            return {
                "success": False,
                "error": f"Création de compte échouée pour @{self.signup_data.get('username', 'N/A')}",
                "message": "Trop de tentatives détectées. Veuillez changer de réseau ou d'email",
                "error_type": "rate_limited",
                "retry_suggestions": [
                    "Attendre quelques heures",
                    "Changer de réseau de connexion",
                    "Utiliser une autre adresse email"
                ]
            }
        
        # Erreur d'email
        if "email" in errors:
            return {
                "success": False,
                "error": f"Problème avec l'adresse email {self.signup_data.get('email', 'N/A')}",
                "message": "Cette adresse email ne peut pas être utilisée. Veuillez en choisir une autre",
                "error_type": "email_blocked",
                "retry_suggestions": [
                    "Utiliser une autre adresse email",
                    "Vérifier que l'email est valide",
                    "Essayer un autre fournisseur d'email"
                ]
            }
        
        # Erreur générale
        return {
            "success": False,
            "error": f"Création de compte échouée pour @{self.signup_data.get('username', 'N/A')}",
            "message": "Erreur lors de la création. Veuillez réessayer avec des informations différentes",
            "error_type": "general_error",
            "details": str(data),
            "retry_suggestions": [
                "Changer de réseau de connexion",
                "Utiliser une autre adresse email",
                "Réessayer plus tard"
            ]
        }
    
    def check_account_suspension(self) -> dict:
        """Vérifier si le compte nouvellement créé est suspendu"""
        import time
        
        try:
            # Naviguer vers la page principale Instagram pour vérifier l'état
            headers = {
                **self.get_base_headers(),
                "upgrade-insecure-requests": "1",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
                "referer": "https://www.instagram.com/accounts/emailsignup/",
                "cookie": self.get_cookie_string()
            }
            
            # Attendre un peu pour que les cookies se propagent
            time.sleep(2)
            
            response = self.session.get("https://www.instagram.com/", headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Vérifier si on est redirigé vers une page de suspension
                final_url = response.url
                response_text = response.text
                
                # Détecter les signes de suspension
                suspension_indicators = [
                    "/accounts/suspended/" in final_url,
                    "/accounts/suspended/" in response_text,
                    "suspended" in final_url.lower(),
                    "Your account has been suspended" in response_text,
                    "Votre compte a été suspendu" in response_text,
                    "Account suspended" in response_text
                ]
                
                if any(suspension_indicators):
                    return {
                        "suspended": True,
                        "final_url": final_url,
                        "message": "Compte créé mais suspendu immédiatement"
                    }
                else:
                    return {
                        "suspended": False,
                        "final_url": final_url,
                        "message": "Compte créé et actif"
                    }
            else:
                return {"suspended": False, "message": "Impossible de vérifier le statut"}
                
        except Exception as e:
            return {"suspended": False, "message": f"Erreur vérification suspension: {str(e)}"}
    
    def save_account_info(self, account_result):
        """Sauvegarder les informations du compte et créer une session compatible"""
        import os
        import json
        import uuid
        import urllib.parse
        import base64
        from datetime import datetime
        
        try:
            os.makedirs("accounts", exist_ok=True)
            os.makedirs("sessions", exist_ok=True)
            
            user_data = account_result["user_data"]
            cookies_dict = account_result.get("cookies", {})
            username = user_data["username"]
            user_id = user_data["user_id"]
            
            # 1. SAUVEGARDER LES INFORMATIONS BRUTES DU COMPTE
            # Combiner les cookies en une seule chaîne
            cookie_parts = []
            for name, value in cookies_dict.items():
                cookie_parts.append(f"{name}={value}")
            cookies_string = "; ".join(cookie_parts)
            
            account_info = {
                "account_data": {
                    "account_created": True,
                    "user_id": user_id,
                    "nonce": cookies_dict.get("nonce", ""),
                    "user_is_in_ufac_after_create_step": False,
                    "status": "ok",
                    "show_privacy_page": False,
                    "suspended": account_result.get("suspended", False)
                },
                "signup_info": self.signup_data,
                "device_info": self.device_info,
                "cookies": cookies_string,
                "created_at": account_result.get("created_at"),
                "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "chrome_version": self.device_info["user_agent"].split("Chrome/")[1].split(" ")[0] if "Chrome/" in self.device_info["user_agent"] else "141.0.0.0"
            }
            
            filename = f"accounts/{username}_account.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(account_info, f, indent=2, ensure_ascii=False)
            
            # 2. CRÉER UNE SESSION COMPATIBLE AVEC LE LOGIN
            sessionid = cookies_dict.get("sessionid", "")
            
            # Encoder sessionid si nécessaire pour l'autorisation
            if sessionid and '%3A' not in sessionid:
                sessionid_encoded = urllib.parse.quote(sessionid)
            else:
                sessionid_encoded = sessionid
            
            # Token d'autorisation compatible
            token_data = {
                "ds_user_id": user_id,
                "sessionid": sessionid_encoded
            }
            
            encoded_token = base64.b64encode(json.dumps(token_data).encode()).decode()
            
            # Session compatible pour le client
            session_data = {
                "pk": int(user_id),
                "username": username,
                "full_name": user_data["full_name"],
                "is_private": False,
                "profile_pic_url": "",
                "profile_pic_url_hd": "",
                "is_verified": False,
                "media_count": 0,
                "follower_count": 0,
                "following_count": 0,
                "authorization_data": {
                    "sessionid": sessionid,
                    "ds_user_id": user_id,
                    "csrftoken": self.csrf_token,
                    "mid": self.mid
                },
                "device_settings": {
                    "app_version": "302.0.0.23.61",
                    "android_version": self.device_info["android_version"],
                    "android_release": self.device_info["android_version"],
                    "dpi": str(int(float(self.device_info["dpr"]) * 160)),
                    "resolution": f"{self.device_info['screen_width']}x{self.device_info['screen_height']}",
                    "manufacturer": self.device_info["manufacturer"],
                    "device": self.device_info["device"],
                    "model": self.device_info["model"],
                    "cpu": "qcom",
                    "version_code": "314665256"
                },
                "cookies": cookies_string,
                "suspended": account_result.get("suspended", False)
            }
            
            session_filename = f"sessions/{username}.json"
            with open(session_filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            pass
    
    def get_cookie_string(self):
        """Construire le cookie string complet"""
        screen_width = self.device_info.get("screen_width", 412)
        screen_height = self.device_info.get("screen_height", 915)
        
        cookie_parts = []
        cookie_parts.append(f"ig_did={self.device_id}")
        cookie_parts.append(f"csrftoken={self.csrf_token}")
        cookie_parts.append(f"datr={self.datr}")
        cookie_parts.append(f"mid={self.mid}")
        cookie_parts.append(f"wd={screen_width}x{screen_height}")
        cookie_parts.append("ig_nrcb=1")
        
        return "; ".join(cookie_parts)
    
    def verify_session_ready(self):
        """Vérifier que la session est prête avec tous les cookies nécessaires"""
        required_elements = [
            self.device_id, self.csrf_token, self.mid, self.datr,
            self.encryption_key_id, self.encryption_public_key
        ]
        
        return all(required_elements)
    
    def encrypt_password(self, password):
        """Chiffrer le mot de passe avec AES-GCM + SealedBox"""
        import time
        import base64
        import struct
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
        from nacl.public import SealedBox, PublicKey
        
        try:
            timestamp = int(time.time())
            aes_key = get_random_bytes(32)
            iv = bytes(12)
            aad = str(timestamp).encode('utf-8')
            
            cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
            cipher_aes.update(aad)
            ciphertext, tag = cipher_aes.encrypt_and_digest(password.encode('utf-8'))
            
            public_key_bytes = self.hex_to_bytes(self.encryption_public_key)
            if len(public_key_bytes) != 32:
                if len(public_key_bytes) > 32:
                    public_key_bytes = public_key_bytes[:32]
                else:
                    public_key_bytes = public_key_bytes.ljust(32, b'\x00')
            
            public_key = PublicKey(public_key_bytes)
            sealed_box = SealedBox(public_key)
            encrypted_aes_key = sealed_box.encrypt(aes_key)
            
            version = 1
            key_id = int(self.encryption_key_id)
            encrypted_key_length = len(encrypted_aes_key)
            
            message = bytearray()
            message.extend(struct.pack('B', version))
            message.extend(struct.pack('B', key_id))
            message.extend(struct.pack('<H', encrypted_key_length))
            message.extend(encrypted_aes_key)
            message.extend(tag)
            message.extend(ciphertext)
            
            encrypted_b64 = base64.b64encode(message).decode('utf-8')
            encrypted_password = f"#PWD_INSTAGRAM_BROWSER:10:{timestamp}:{encrypted_b64}"
            
            return encrypted_password
        except Exception as e:
            return password
    
    def hex_to_bytes(self, hex_string):
        """Convertir hex en bytes"""
        return bytes.fromhex(hex_string)
    
    def get_state(self) -> dict:
        """Récupérer l'état actuel du processus d'inscription"""
        return {
            "state": self._state,
            "username_suggestions": self._username_suggestions,
            "signup_data": {
                "email": self.signup_data.get("email"),
                "username": self.signup_data.get("username"),
                "full_name": self.signup_data.get("full_name")
            } if self.signup_data else {},
            "birth_date": self._birth_date,
            "session_ready": self.verify_session_ready(),
            "chrome_version": self.device_info.get("user_agent", "").split("Chrome/")[1].split(" ")[0] if "Chrome/" in self.device_info.get("user_agent", "") else "141.0.0.0"
        }
class InstagramAuth:
    """Gestionnaire d'authentification Instagram complet avec flux Web et 2FA"""
    
    def __init__(self):
        # Validation licence obligatoire
        if not validate_license():
            raise PermissionError("Ce script n'est pas autorisé à utiliser cette bibliothèque. Veuillez contacter le créateur via: 0389561802 ou https://t.me/Kenny5626")
        
        self.session = requests.Session()
        self.session_data = {}
        self.current_device_info = {}  # Device info pour la session actuelle
        
        # Variables Web spécifiques
        self.csrf_token = ""
        self.device_id = ""
        self.mid = ""
        self.datr = ""
        self.encryption_key_id = ""
        self.encryption_public_key = ""
        self.apc = ""
        self.silent_mode = True
        
        # Variables pour les challenges traditionnels
        self.challenge_context = ""
        self.challenge_type = ""
        self.challenge_navigation = {}
        self.current_challenge_url = ""  # Pour le nouveau flux SelectVerificationMethodForm
        
        # Variables pour 2FA
        self.two_factor_identifier = ""
        self.two_factor_info = {}
        
        # Créer un objet device_manager temporaire pour compatibilité
        class TempDeviceManager:
            def __init__(self, parent):
                self.parent = parent
            
            @property
            def device_info(self):
                return self.parent.current_device_info
            
            def get_x_mid(self):
                return self.parent.current_device_info.get('x_mid', '')
        
        self.device_manager = TempDeviceManager(self)
    
    def _generate_fresh_device_info(self):
        """Générer de nouvelles informations de device pour chaque connexion"""
        
        # Récupérer les vraies informations du device
        device_info = TermuxDeviceGenerator.get_real_android_device_info()
        
        # Récupérer un nouveau MID depuis Instagram
        real_mid = TermuxDeviceGenerator.get_instagram_mid_from_web(device_info)
        device_info['x_mid'] = real_mid
        
        self.current_device_info = device_info
        
        # Configurer les headers de base avec les nouvelles infos
        self._setup_base_headers(device_info)
        
        return device_info
    
    def _setup_base_headers(self, device_info):
        """Configuration des headers de base avec les nouvelles infos device"""
        self.base_headers = {
            "host": "www.instagram.com",
            "connection": "keep-alive",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-ch-ua-platform-version": f'"{device_info.get("platform_version", "14.0.0")}"',
            "sec-ch-ua-model": f'"{device_info.get("model", "SM-G991B")}"',
            "sec-ch-ua-full-version-list": '"Chromium";v="140.0.7339.128", "Not=A?Brand";v="24.0.0.0", "Google Chrome";v="140.0.7339.128"',
            "sec-ch-prefers-color-scheme": "light",
            "user-agent": device_info.get("user_agent"),
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def login_with_cookies(self, cookies_string: str) -> dict:
        """Connexion Instagram via cookies existants"""
        result = {
            "success": False,
            "message": "",
            "user_data": {},
            "session_data": {}
        }
        
        try:
            # Générer device info même pour les cookies
            device_info = self._generate_fresh_device_info()
            
            # Parser la chaîne de cookies
            cookies_dict = self._parse_cookie_string(cookies_string)
            
            if not cookies_dict:
                result["message"] = "Format de cookies invalide"
                return result
            
            # Vérifier les cookies essentiels
            required_cookies = ["sessionid", "ds_user_id", "csrftoken"]
            missing_cookies = [cookie for cookie in required_cookies if cookie not in cookies_dict]
            
            if missing_cookies:
                result["message"] = f"Cookies manquants: {', '.join(missing_cookies)}"
                return result
            
            # Extraire user ID depuis ds_user_id
            user_id = cookies_dict.get("ds_user_id")
            if not user_id or not user_id.isdigit():
                result["message"] = "User ID invalide dans les cookies"
                return result
            
            # Configurer les cookies dans la session
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value)
            
            # Tester la validité des cookies en récupérant le profil
            profile_result = self._get_profile_info_from_cookies(user_id, cookies_dict)
            
            if not profile_result["success"]:
                result["message"] = profile_result["error"]
                return result
            
            user_data = profile_result["user_data"]
            
            # Construire les données de session complètes avec device info
            session_data = self._build_session_from_cookies(cookies_dict, user_data, device_info)
            
            # Vérifier le statut du compte
            final_result = self.check_account_status_after_login(
                user_data.get("username", ""), "", {
                    "success": True,
                    "user_data": user_data,
                    "session_data": session_data
                }
            )
            
            if final_result["success"] and final_result.get("status") != "disabled":
                self._save_session_with_device(user_data.get("username", ""), session_data, user_data, device_info)
            
            return final_result
            
        except Exception as e:
            result["message"] = f"Erreur lors de la connexion par cookies: {str(e)}"
            return result
    
    def login(self, username: str, password: str) -> dict:
        """Connexion Instagram avec flux Web complet et gestion 2FA"""
        result = {
            "success": False,
            "message": "",
            "user_data": {},
            "session_data": {}
        }
        
        try:
            # Générer de nouvelles infos device pour cette connexion
            device_info = self._generate_fresh_device_info()
            
            # ÉTAPE 1: Récupération shared_data
            if not self.step1_get_shared_data():
                result["message"] = "Échec étape 1"
                return result
            
            # ÉTAPE 2: Récupération cookies homepage
            if not self.step2_get_homepage_cookies():
                result["message"] = "Échec étape 2"
                return result
            
            # ÉTAPE 3: Connexion
            login_result = self.step3_login(username, password)
            
            return login_result
            
        except Exception as e:
            result["message"] = f"Erreur connexion: {str(e)}"
            return result
    
    def step1_get_shared_data(self):
        """ÉTAPE 1: Récupération shared_data"""
        screen_width = self.current_device_info.get("screen_width", 412)
        dpr = self.current_device_info.get("dpr", 2.625)
        
        headers = {
            **self.base_headers,
            "dpr": str(dpr),
            "viewport-width": str(screen_width),
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document"
        }
        
        try:
            response = self.session.get("https://www.instagram.com/data/shared_data/", headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                self.device_id = data.get("device_id", "")
                encryption = data.get("encryption", {})
                self.encryption_key_id = encryption.get("key_id", "")
                self.encryption_public_key = encryption.get("public_key", "")
                return True
            return False
        except Exception as e:
            return False
    
    def step2_get_homepage_cookies(self):
        """ÉTAPE 2: Récupération cookies homepage"""
        screen_width = self.current_device_info.get("screen_width", 412)
        dpr = self.current_device_info.get("dpr", 2.625)
        
        headers = {
            **self.base_headers,
            "dpr": str(dpr),
            "viewport-width": str(screen_width),
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "cookie": f"ig_did={self.device_id}"
        }
        
        try:
            response = self.session.get("https://www.instagram.com/", headers=headers, timeout=15)
            
            if response.status_code == 200:
                for cookie in response.cookies:
                    if cookie.name == "csrftoken":
                        self.csrf_token = cookie.value
                    elif cookie.name == "mid":
                        self.mid = cookie.value
                    elif cookie.name == "datr":
                        self.datr = cookie.value
                
                if not self.mid:
                    html_text = response.text
                    patterns = [
                        r'"machine_id"\s*:\s*"([^"]+)"',
                        r'"mid"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"',
                        r'"deferredCookies"\s*:\s*{[^}]*"mid"\s*:\s*{\s*"value"\s*:\s*"([^"]+)"'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, html_text)
                        if match:
                            self.mid = match.group(1)
                            break
                
                return True
            return False
        except Exception as e:
            return False
    
    def encrypt_password_aes_gcm_sealedbox(self, password):
        """Chiffrement mot de passe identique au script Web"""
        try:
            timestamp = int(time.time())
            aes_key = get_random_bytes(32)
            iv = bytes(12)
            aad = str(timestamp).encode('utf-8')
            
            cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
            cipher_aes.update(aad)
            ciphertext, tag = cipher_aes.encrypt_and_digest(password.encode('utf-8'))
            
            public_key_bytes = self.hex_to_bytes(self.encryption_public_key)
            if len(public_key_bytes) != 32:
                if len(public_key_bytes) > 32:
                    public_key_bytes = public_key_bytes[:32]
                else:
                    public_key_bytes = public_key_bytes.ljust(32, b'\x00')
            
            public_key = PublicKey(public_key_bytes)
            sealed_box = SealedBox(public_key)
            encrypted_aes_key = sealed_box.encrypt(aes_key)
            
            version = 1
            key_id = int(self.encryption_key_id)
            encrypted_key_length = len(encrypted_aes_key)
            
            message = bytearray()
            message.extend(struct.pack('B', version))
            message.extend(struct.pack('B', key_id))
            message.extend(struct.pack('<H', encrypted_key_length))
            message.extend(encrypted_aes_key)
            message.extend(tag)
            message.extend(ciphertext)
            
            encrypted_b64 = base64.b64encode(message).decode('utf-8')
            encrypted_password = f"#PWD_INSTAGRAM_BROWSER:10:{timestamp}:{encrypted_b64}"
            
            return encrypted_password
        except Exception as e:
            return password
    
    def hex_to_bytes(self, hex_string):
        return bytes.fromhex(hex_string)
    
    def _random_hex(self, length):
        return ''.join(random.choices('0123456789ABCDEF', k=length))
    
    def step3_login(self, username, password):
        """ÉTAPE 3: Connexion - identique au script Web avec gestion 2FA"""
        encrypted_password = self.encrypt_password_aes_gcm_sealedbox(password)
        
        screen_width = self.current_device_info.get("screen_width", 412)
        screen_height = self.current_device_info.get("screen_height", 915)
        
        cookies_string = f"csrftoken={self.csrf_token}; datr={self.datr}; ig_did={self.device_id}; wd={screen_width}x{screen_height}; mid={self.mid}; ig_nrcb=1"
        
        headers = {
            **self.base_headers,
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "x-csrftoken": self.csrf_token,
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.instagram.com/",
            "cookie": cookies_string
        }
        
        ajax_id = str(int(time.time() * 1000))[-10:]
        
        payload = {
            "enc_password": encrypted_password,
            "username": username,
            "queryParams": "{}",
            "optIntoOneTap": "false",
            "trustedDeviceRecords": "{}",
            "jazoest": ajax_id
        }
        
        try:
            response = self.session.post(
                "https://www.instagram.com/api/v1/web/accounts/login/ajax/",
                data=payload,
                headers=headers,
                timeout=30
            )
            
            try:
                data = response.json()
                
                # Connexion réussie
                if data.get("authenticated") == True:
                    user_data = data.get("user", {})
                    session_result = self.build_success_response(response, username)
                    if session_result["success"]:
                        return session_result
                    else:
                        return {
                            "success": True,
                            "user_data": user_data,
                            "cookies": dict(self.session.cookies)
                        }
                
                # 2FA requis - NOUVEAU CODE
                elif data.get("two_factor_required") == True:
                    self.two_factor_info = data.get("two_factor_info", {})
                    self.two_factor_identifier = self.two_factor_info.get("two_factor_identifier", "")
                    username_2fa = self.two_factor_info.get("username", username)
                    
                    return self.handle_two_factor_authentication(username_2fa, cookies_string)
                
                # Challenge requis
                elif "checkpoint_required" in str(data) or data.get("message") == "checkpoint_required":
                    checkpoint_url = data.get("checkpoint_url", "")
                    return self.handle_checkpoint_router(checkpoint_url, cookies_string, username)
                
                # Mot de passe incorrect
                elif data.get("user") == True and data.get("authenticated") == False and data.get("showAccountRecoveryModal") == True:
                    return {"success": False, "message": "password_incorrect", "retry": True}
                
                # Identifiants incorrects
                elif data.get("user") == True and data.get("authenticated") == False and not data.get("showAccountRecoveryModal"):
                    return {"success": False, "message": "credentials_incorrect", "retry": True}
                
                else:
                    error_type = data.get("error_type", "")
                    message = data.get("message", "")
                    return {
                        "success": False,
                        "message": f"{error_type}: {message}",
                        "retry": False
                    }
            
            except json.JSONDecodeError:
                return {"success": False, "message": "Réponse invalide", "retry": False}
        
        except Exception as e:
            return {"success": False, "message": str(e), "retry": False}
    
    def handle_two_factor_authentication(self, username, cookies_string):
        """Gérer l'authentification 2FA complète"""
        try:
            # ÉTAPE 1: Faire les deux requêtes préparatoires
            if not self.prepare_two_factor_flow(cookies_string):
                return {"success": False, "message": "Erreur préparation 2FA"}
            
            print("\n" + "="*60)
            print("🔐 AUTHENTIFICATION À DEUX FACTEURS REQUISE")
            print("="*60)
            print(f"👤 Compte: {username}")
            
            if self.two_factor_info.get("totp_two_factor_on"):
                print("🔢 Authentificateur TOTP activé")
            if self.two_factor_info.get("sms_two_factor_on"):
                phone = self.two_factor_info.get("obfuscated_phone_number", "")
                print(f"📱 SMS activé: {phone}")
            
            print("-"*60)
            
            # Boucle de saisie du code 2FA
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts:
                print(f"Tentative {attempt + 1}/{max_attempts}")
                code = input("🔑 Entrez le code d'authentification (6 chiffres): ").strip()
                
                # Validation côté client - NE PAS compter comme tentative
                if not code or len(code) != 6 or not code.isdigit():
                    print("❌ Le code doit contenir exactement 6 chiffres")
                    continue  # Redemander sans incrémenter le compteur
                
                # Incrémenter le compteur seulement quand on soumet au serveur
                attempt += 1
                
                # Soumettre le code 2FA
                result = self.submit_two_factor_code(code, username, cookies_string)
                
                if result["success"]:
                    return result
                elif result.get("invalid_code"):
                    print(f"❌ {result['message']}")
                    if attempt < max_attempts:
                        print("Veuillez réessayer...")
                    continue
                else:
                    return result
            
            return {"success": False, "message": "Trop de tentatives échouées"}
            
        except Exception as e:
            return {"success": False, "message": f"Erreur 2FA: {str(e)}"}
    
    def prepare_two_factor_flow(self, cookies_string):
        """Faire les deux requêtes préparatoires pour 2FA"""
        try:
            screen_width = self.current_device_info.get("screen_width", 412)
            
            # REQUÊTE 1: QuickPromotionSupportIGSchemaBatchFetchQuery
            headers1 = {
                **self.base_headers,
                "viewport-width": str(screen_width),
                "x-ig-app-id": "936619743392459",
                "x-fb-lsd": "AdEBwV3MLIw",
                "content-type": "application/x-www-form-urlencoded",
                "x-csrftoken": self.csrf_token,
                "x-fb-friendly-name": "QuickPromotionSupportIGSchemaBatchFetchQuery",
                "x-asbd-id": "359341",
                "dpr": "1",
                "accept": "*/*",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors", 
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/login/two_factor?next=%2F&source=mobile_nav",
                "cookie": cookies_string
            }
            
            payload1 = {
                "av": "0",
                "__d": "www",
                "__user": "0",
                "__a": "1",
                "__req": "15",
                "__hs": "20409.HYP:instagram_web_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "GOOD",
                "__rev": "1029966864",
                "__s": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
                "__hsi": str(random.randint(7000000000000000000, 8000000000000000000)),
                "__dyn": "7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJw5ux609vCwjE1EE2Cw8G11wBz81s8hwGxu786a3a1YwBgao6C0Mo2swlo5qfK0EUjwGzEaE2iwNwmE2eUlwhEe87q0oa2-azo7u3vwDwHg2ZwrUdUbGwmk0zU8oC1Iwqo5p0OwUQp1yU426V89F8uwm8jxK2K2G0EoKmUhw5ywtF86K",
                "__csr": "gjMjQDbbkBSCJ9trvjZUBWSOQCha4AluF7it95Kbhlx3Ap9bVAcyp98mzeiAHAzGDx2fCUyqiEkijni-F8CbwFzVES9Gi9GFAdDAAKFEydKppUjyVoSl1hXjyEKUC2uuupyp8yXyF8x4UK4Wxafz8sx2Eb8izolKmFudCyUgCx29wko01pIrK5U7m08WK0wra0Iu-rm4t1rw3rA7UW040o0xy04aO07OzUmwWwMxq544GwRBo19k0pto0zgM1lqfw4ow92jlw8K8U0Tiu8k9G2B3A6UQM1yUpzE06xa04jU7C3-0H8y0esw0SQxG",
                "__hsdp": f"gfadkM8q20axdRPgp8R7yk2y3J0ODw_hU2hV9jyci1zxC1Jzo2IzpStekEnw4mw3aUcF84G04LE1Io1IE1XEdoeE0Aa0ME20w2BE6zw5Jwi8",
                "__hblp": "0vU1eoeEfQu0Au0Eo8UbEhAK0wWAwYUSp2axi2K4UfEowmU8ElwgUdFVUS1-Cw5qwmEhwIU21g-1cwd-0cuwMwNw4UwBwkHw6Kw77wCwFyUdp9o7y0se0ME20w2gEfXzU62vweS1zxF7x-221BxC1Xwcy",
                "__sjsp": "gfadkM8q20axdRPsQ5adhUB0p43G3Z7w960yopwro10o",
                "__comet_req": "7",
                "lsd": "AdEBwV3MLIw",
                "jazoest": "2901",
                "__spin_r": "1029966864",
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "__crn": "comet.igweb.PolarisLoginTwoFactorRoute",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "QuickPromotionSupportIGSchemaBatchFetchQuery",
                "server_timestamps": "true",
                "variables": json.dumps({"scale":1,"surface_nux_ids":["INSTAGRAM_FOR_WEB_LOGIN_INTERSTITIAL_QP"],"trigger_context":None}),
                "doc_id": "24550588164597887"
            }
            
            response1 = self.session.post(
                "https://www.instagram.com/api/graphql",
                data=payload1,
                headers=headers1,
                timeout=15
            )
            
            # REQUÊTE 2: Navigation
            headers2 = {
                **self.base_headers,
                "viewport-width": str(screen_width),
                "x-asbd-id": "359341",
                "x-ig-d": "www",
                "dpr": "1",
                "x-fb-lsd": "AdEBwV3MLIw",
                "content-type": "application/x-www-form-urlencoded",
                "accept": "*/*",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/login/two_factor?next=%2F&source=mobile_nav",
                "cookie": cookies_string
            }
            
            payload2 = {
                "client_previous_actor_id": "",
                "route_url": "/accounts/login/two_factor?next=%2F&source=mobile_nav",
                "__d": "www",
                "__user": "0",
                "__a": "1",
                "__req": "16",
                "__hs": "20409.HYP:instagram_web_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "GOOD",
                "__rev": "1029966864",
                "__s": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
                "__hsi": str(random.randint(7000000000000000000, 8000000000000000000)),
                "__dyn": "7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJw5ux609vCwjE1EE2Cw8G11wBz81s8hwGxu786a3a1YwBgao6C0Mo2swlo5qfK0EUjwGzEaE2iwNwmE2eUlwhEe87q0oa2-azo7u3vwDwHg2ZwrUdUbGwmk0zU8oC1Iwqo5p0OwUQp1yU426V89F8uwm8jxK2K2G0EoKmUhw5ywtF86K",
                "__csr": "gjMjQDbbkBSCJ9trvjZUBWSOQCha4AluF7it95Kbhlx3Ap9bVAcyp98mzeiAHAzGDx2fCUyqiEkijni-F8CbwFzVES9Gi9GFAdDAAKFEydKppUjyVoSl1hXjyEKUC2uuupyp8yXyF8x4UK4Wxafz8sx2Eb8izolKmFudCyUgCx29wko01pIrK5U7m08WK0wra0Iu-rm4t1rw3rA7UW040o0xy04aO07OzUmwWwMxq544GwRBo19k0pto0zgM1lqfw4ow92jlw8K8U0Tiu8k9G2B3A6UQM1yUpzE06xa04jU7C3-0H8y0esw0SQxG",
                "__hsdp": "gfadkM8q20axdRPgp8R7yk2y3J0ODw_hU2hV9jyci1zxC1Jzo2IzpStekEnw4mw3aUcF84G04LE1Io1IE1XEdoeE0Aa0ME20w2BE6zw5Jwi8",
                "__hblp": "0vU1eoeEfQu0Au0Eo8UbEhAK0wWAwYUSp2axi2K4UfEowmU8ElwgUdFVUS1-Cw5qwmEhwIU21g-1cwd-0cuwMwNw4UwBwkHw6Kw77wCwFyUdp9o7y0se0ME20w2gEfXzU62vweS1zxF7x-221BxC1Xwcy",
                "__sjsp": "gfadkM8q20axdRPsQ5adhUB0p43G3Z7w960yopwro10o",
                "__comet_req": "7",
                "lsd": "AdEBwV3MLIw",
                "jazoest": "2901",
                "__spin_r": "1029966864",
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "__crn": "comet.igweb.PolarisLoginTwoFactorRoute"
            }
            
            response2 = self.session.post(
                "https://www.instagram.com/ajax/navigation/",
                data=payload2,
                headers=headers2,
                timeout=15
            )
            
            # Mettre à jour le device_id depuis la session si nécessaire
            if self.device_id and self.mid:
                # Utiliser le device_id depuis two_factor_info si disponible
                two_factor_device_id = self.two_factor_info.get("device_id", "")
                if two_factor_device_id:
                    # Utiliser le device_id du 2FA pour cohérence
                    pass
            
            return True
            
        except Exception as e:
            return False
    
    def submit_two_factor_code(self, code, username, cookies_string):
        """Soumettre le code 2FA"""
        try:
            screen_width = self.current_device_info.get("screen_width", 412)
            
            headers = {
                **self.base_headers,
                "viewport-width": str(screen_width),
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-instagram-ajax": "1029966864",
                "x-csrftoken": self.csrf_token,
                "x-web-device-id": self.device_id,
                "x-web-session-id": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
                "x-asbd-id": "359341",
                "dpr": "1",
                "x-ig-www-claim": "0",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/login/two_factor?next=%2F&source=mobile_nav",
                "cookie": cookies_string
            }
            
            payload = {
                "identifier": self.two_factor_identifier,
                "isPrivacyPortalReq": "false",
                "queryParams": json.dumps({"next":"/","source":"mobile_nav"}),
                "trust_signal": "true",
                "username": username,
                "verification_method": "3",  # TOTP
                "verificationCode": code,
                "jazoest": str(random.randint(20000, 30000))
            }
            
            response = self.session.post(
                "https://www.instagram.com/api/v1/web/accounts/login/ajax/two_factor/",
                data=payload,
                headers=headers,
                timeout=30
            )
            
            # Vérifier d'abord les cookies de succès même en cas de 400
            success_cookies_found = False
            for cookie in response.cookies:
                if cookie.name in ["sessionid", "ds_user_id"]:
                    success_cookies_found = True
                    break
            
            if success_cookies_found:
                print("✅ Authentification 2FA réussie!")
                return self.build_success_response(response, username)
            
            # Analyser la réponse JSON pour tous les codes de status
            try:
                data = response.json()
                
                # Succès explicite
                if data.get("authenticated") == True:
                    print("✅ Authentification 2FA réussie!")
                    return self.build_success_response(response, username)
                
                # Code incorrect - permettre une nouvelle tentative
                elif (data.get("status") == "fail" and 
                      data.get("error_type") in ["invalid_verficaition_code", "invalid_verification_code"]):
                    return {
                        "success": False,
                        "message": "Code de sécurité incorrect",
                        "invalid_code": True
                    }
                
                # Message d'erreur générique d'Instagram
                elif data.get("message"):
                    error_msg = data.get("message")
                    # Vérifier si c'est une erreur de code incorrect
                    if "code" in error_msg.lower() or "sécurité" in error_msg.lower() or "incorrect" in error_msg.lower():
                        return {
                            "success": False,
                            "message": error_msg,
                            "invalid_code": True
                        }
                    else:
                        return {
                            "success": False,
                            "message": error_msg,
                            "invalid_code": False
                        }
                
                # Autres cas de fail
                elif data.get("status") == "fail":
                    return {
                        "success": False,
                        "message": "Code incorrect ou expiré",
                        "invalid_code": True
                    }
                
                # Réponse inattendue mais pas d'erreur explicite
                else:
                    return {
                        "success": False,
                        "message": "Réponse 2FA inattendue",
                        "invalid_code": True
                    }
                
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON mais status 200, traiter comme succès
                if response.status_code == 200:
                    print("✅ Authentification 2FA réussie!")
                    return self.build_success_response(response, username)
                else:
                    return {
                        "success": False, 
                        "message": f"Réponse 2FA invalide (HTTP {response.status_code})", 
                        "invalid_code": True
                    }
                
        except Exception as e:
            return {
                "success": False, 
                "message": f"Erreur soumission 2FA: {str(e)}", 
                "invalid_code": False
            }
    
    def handle_checkpoint_router(self, checkpoint_url, cookies_string, username):
        """Router pour gérer les différents types de challenges"""
        
        # Déterminer le type de flux basé sur l'URL
        if "/challenge/action/" in checkpoint_url:
            return self.handle_traditional_challenge(checkpoint_url, cookies_string, username)
        else:
            return self.handle_checkpoint(checkpoint_url, cookies_string, username)
    
    def handle_traditional_challenge(self, checkpoint_url, cookies_string, username):
        """Gérer le flux de challenge traditionnel"""
        
        screen_width = self.current_device_info.get("screen_width", 412)
        dpr = self.current_device_info.get("dpr", 2.625)
        
        # ÉTAPE 1: GET vers checkpoint_url pour obtenir la page
        headers1 = {
            **self.base_headers,
            "dpr": str(dpr),
            "viewport-width": str(screen_width),
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "referer": "https://www.instagram.com/",
            "cookie": cookies_string
        }
        
        try:
            response1 = self.session.get(
                f"https://www.instagram.com{checkpoint_url}",
                headers=headers1,
                timeout=15
            )
            
            # Mettre à jour les cookies
            for cookie in response1.cookies:
                if cookie.name in ["ps_l", "ps_n", "csrftoken"]:
                    if cookie.name == "csrftoken":
                        self.csrf_token = cookie.value
                    
                    # Mettre à jour cookies_string
                    if f"{cookie.name}=" in cookies_string:
                        cookies_string = re.sub(f'{cookie.name}=[^;]+', f'{cookie.name}={cookie.value}', cookies_string)
                    else:
                        cookies_string += f"; {cookie.name}={cookie.value}"
            
            # ÉTAPE 2: Requête API pour obtenir les données du challenge
            api_url = checkpoint_url.replace("/challenge/action/", "/api/v1/challenge/web/")
            
            headers2 = {
                **self.base_headers,
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
                "x-bloks-version-id": "c510c52d2e632f2477f6a1cb69ca1734c0ea54d761300fa1f170bc676047eeca",
                "x-asbd-id": "359341",
                "x-ig-www-claim": "0",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": f"https://www.instagram.com{checkpoint_url}",
                "cookie": cookies_string
            }
            
            response2 = self.session.get(
                f"https://www.instagram.com{api_url}",
                headers=headers2,
                timeout=15
            )
            
            try:
                challenge_data = response2.json()
                challenge_type = challenge_data.get("challengeType", "")
                self.challenge_context = challenge_data.get("challenge_context", "")
                self.challenge_navigation = challenge_data.get("navigation", {})
                
                # Support pour SelectVerificationMethodForm
                if challenge_type == "SelectVerificationMethodForm":
                    # Sauvegarder l'URL pour ce flux
                    self.current_challenge_url = checkpoint_url
                    return self.handle_select_verification_method_form(challenge_data, cookies_string, username)
                
                # Si c'est un formulaire de sélection de contact
                elif challenge_type == "SelectContactPointRecoveryForm":
                    return self.handle_traditional_contact_selection(challenge_data, cookies_string, username)
                
                # Si c'est directement une demande de code
                elif "VerifyEmailCodeForm" in challenge_type or "VerifyPhoneCodeForm" in challenge_type or "VerifySMSCodeForm" in challenge_type:
                    return self.handle_traditional_code_entry(challenge_data, cookies_string, username)
                
                else:
                    return {"success": False, "message": f"Type de challenge non supporté: {challenge_type}"}
                    
            except json.JSONDecodeError:
                return {"success": False, "message": "Réponse challenge invalide"}
                
        except Exception as e:
            return {"success": False, "message": f"Erreur challenge traditionnel: {e}"}
    
    def handle_select_verification_method_form(self, challenge_data, cookies_string, username):
        """Gérer le nouveau flux SelectVerificationMethodForm"""
        
        fields = challenge_data.get("fields", {})
        navigation = challenge_data.get("navigation", {})
        forward_url = navigation.get("forward", "")
        
        # Afficher les informations à l'utilisateur
        print("\n" + "="*60)
        print("🔐 VÉRIFICATION DE SÉCURITÉ REQUISE")
        print("="*60)
        
        # Extraire les détails du contact depuis fields
        phone_number = fields.get("phone_number", "")
        if phone_number:
            print(f"📱 Un code sera envoyé au numéro: {phone_number}")
        
        print("1. Continuer avec cette méthode")
        print("2. Quitter")
        print("-"*60)
        
        while True:
            choice = input("Votre choix (1-2): ").strip()
            
            if choice == "1":
                # Continuer avec la méthode proposée
                return self.submit_select_verification_choice(challenge_data, cookies_string, username)
                
            elif choice == "2":
                return {"success": False, "message": "Utilisateur a annulé"}
                
            else:
                print("❌ Choix invalide")
    
    def submit_select_verification_choice(self, challenge_data, cookies_string, username):
        """Soumettre le choix pour SelectVerificationMethodForm"""
        
        navigation = challenge_data.get("navigation", {})
        forward_url = navigation.get("forward", "")
        
        if not forward_url:
            return {"success": False, "message": "URL de soumission manquante"}
        
        headers = {
            **self.base_headers,
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
            "x-csrftoken": self.csrf_token,
            "x-web-session-id": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
            "x-asbd-id": "359341",
            "sec-ch-prefers-color-scheme": "light",
            "dnt": "1",
            "x-ig-www-claim": "0",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com{self.current_challenge_url}",
            "cookie": cookies_string
        }
        
        # Utiliser choice=0 comme dans l'exemple
        payload = {"choice": "0"}
        
        try:
            response = self.session.post(
                f"https://www.instagram.com{forward_url}",
                data=payload,
                headers=headers,
                timeout=30
            )
            
            try:
                data = response.json()
                challenge_type = data.get("challengeType", "")
                
                # Si on obtient VerifySMSCodeForm ou similaire
                if "VerifySMSCodeForm" in challenge_type or "VerifyEmailCodeForm" in challenge_type or "VerifyPhoneCodeForm" in challenge_type:
                    return self.handle_traditional_code_entry(data, cookies_string, username)
                else:
                    return {"success": False, "message": f"Type de réponse inattendu: {challenge_type}"}
                    
            except json.JSONDecodeError:
                return {"success": False, "message": "Réponse invalide après soumission"}
                
        except Exception as e:
            return {"success": False, "message": f"Erreur soumission choix: {e}"}
    
    def handle_traditional_contact_selection(self, challenge_data, cookies_string, username):
        """Gérer la sélection de méthode dans le flux traditionnel"""
        
        fields = challenge_data.get("fields", {})
        
        # Afficher les options disponibles
        options = []
        if fields.get("email"):
            options.append(("Email", fields["email"], "1"))
        if fields.get("phone_number"):
            options.append(("SMS", fields["phone_number"], "0"))
        if fields.get("whatsapp"):
            options.append(("WhatsApp", fields["whatsapp"], "0"))
        
        if not options:
            return {"success": False, "message": "Aucune méthode de vérification disponible"}
        
        while True:
            print("\n" + "="*60)
            print("🔐 MÉTHODES DE VÉRIFICATION DISPONIBLES")
            print("="*60)
            
            for i, (method, contact, choice_value) in enumerate(options, 1):
                print(f"{i}. {method}: {contact}")
            
            print(f"{len(options) + 1}. Quitter")
            print("-"*60)
            
            try:
                choice = int(input("Votre choix: ").strip())
                
                if 1 <= choice <= len(options):
                    selected_method, selected_contact, choice_value = options[choice - 1]
                    print(f"📧 Envoi du code vers {selected_method}: {selected_contact}")
                    
                    # Soumettre le choix
                    return self.submit_traditional_choice(choice_value, cookies_string, username)
                    
                elif choice == len(options) + 1:
                    return {"success": False, "message": "Utilisateur a annulé"}
                    
                else:
                    print("❌ Choix invalide")
                    
            except ValueError:
                print("❌ Veuillez entrer un nombre valide")
    
    def submit_traditional_choice(self, choice_value, cookies_string, username):
        """Soumettre le choix de méthode pour le flux traditionnel"""
        
        headers = {
            **self.base_headers,
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
            "x-csrftoken": self.csrf_token,
            "x-web-session-id": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
            "x-bloks-version-id": "c510c52d2e632f2477f6a1cb69ca1734c0ea54d761300fa1f170bc676047eeca",
            "x-asbd-id": "359341",
            "x-ig-www-claim": "0",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "cookie": cookies_string
        }
        
        payload = {
            "choice": choice_value,
            "is_bloks_web": "True",
            "challenge_context": self.challenge_context,
            "has_follow_up_screens": "false",
            "nest_data_manifest": "true"
        }
        
        response = self.session.post(
            "https://www.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/",
            data=payload,
            headers=headers,
            timeout=15
        )
        
        try:
            data = response.json()
            layout_data = data.get("layout", {}).get("bloks_payload", {})
            handler = layout_data.get("tree", {}).get("bk.components.internal.Action", {}).get("handler", "")
            
            if "ig.action.challenges.OpenChallengeUrl" in handler:
                # Extraire les paramètres de l'URL
                handler_match = re.search(r'ig\.action\.challenges\.OpenChallengeUrl[^"]*"([^"]+)"[^"]*"([^"]+)"', handler)
                if handler_match:
                    param1 = handler_match.group(1)
                    param2 = handler_match.group(2)
                    
                    # Construire la nouvelle URL
                    new_url = f"/challenge/action/{param1}/{param2}/None/"
                    
                    # Naviguer vers cette URL et demander le code
                    return self.navigate_to_code_entry_traditional(new_url, cookies_string, username)
            
            return {"success": False, "message": "Impossible de continuer avec cette méthode"}
            
        except Exception as e:
            return {"success": False, "message": f"Erreur soumission choix: {e}"}
    
    def navigate_to_code_entry_traditional(self, challenge_url, cookies_string, username):
        """Naviguer vers la page de saisie de code traditionnelle"""
        
        # ÉTAPE 1: GET navigation
        screen_width = self.current_device_info.get("screen_width", 412)
        dpr = self.current_device_info.get("dpr", 2.625)
        
        headers1 = {
            **self.base_headers,
            "dpr": str(dpr),
            "viewport-width": str(screen_width),
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "cookie": cookies_string
        }
        
        response1 = self.session.get(
            f"https://www.instagram.com{challenge_url}",
            headers=headers1,
            timeout=15
        )
        
        # ÉTAPE 2: Requête API pour obtenir le formulaire de code
        api_url = challenge_url.replace("/challenge/action/", "/api/v1/challenge/web/")
        
        headers2 = {
            **self.base_headers,
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "accept": "*/*",
            "x-csrftoken": self.csrf_token,
            "x-web-session-id": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
            "x-bloks-version-id": "c510c52d2e632f2477f6a1cb69ca1734c0ea54d761300fa1f170bc676047eeca",
            "x-asbd-id": "359341",
            "x-ig-www-claim": "0",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com{challenge_url}",
            "cookie": cookies_string
        }
        
        response2 = self.session.get(
            f"https://www.instagram.com{api_url}",
            headers=headers2,
            timeout=15
        )
        
        try:
            challenge_data = response2.json()
            challenge_type = challenge_data.get("challengeType", "")
            
            if "VerifyEmailCodeForm" in challenge_type or "VerifyPhoneCodeForm" in challenge_type or "VerifySMSCodeForm" in challenge_type:
                self.challenge_context = challenge_data.get("challenge_context", "")
                self.challenge_navigation = challenge_data.get("navigation", {})
                
                # Afficher les informations
                fields = challenge_data.get("fields", {})
                contact_point = fields.get("contact_point", "votre contact")
                form_type = fields.get("form_type", "email")
                
                print(f"\n📧 Code de vérification envoyé vers ({form_type}): {contact_point}")
                print("Veuillez vérifier vos messages...")
                
                return self.handle_traditional_code_entry(challenge_data, cookies_string, username)
            else:
                return {"success": False, "message": f"Type de challenge non supporté: {challenge_type}"}
                
        except Exception as e:
            return {"success": False, "message": f"Erreur navigation code: {e}"}
    
    def handle_traditional_code_entry(self, challenge_data, cookies_string, username):
        """Gérer la saisie du code dans le flux traditionnel"""
        
        fields = challenge_data.get("fields", {})
        contact_point = fields.get("contact_point", "votre contact")
        form_type = fields.get("form_type", "email")
        navigation = challenge_data.get("navigation", {})
        forward_url = navigation.get("forward", "")
        
        while True:
            print("\n" + "="*60)
            print("🔐 VÉRIFICATION REQUISE")
            print("="*60)
            print(f"📧 Code envoyé vers ({form_type}): {contact_point}")
            print("1. Entrer le code de vérification")
            print("2. Essayer une autre méthode")
            print("3. Quitter")
            print("-"*60)
            
            choice = input("Votre choix (1-3): ").strip()
            
            if choice == "1":
                code = input("\n📱 Entrez le code de vérification: ").strip()
                
                if len(code) < 5:
                    print("❌ Le code doit contenir au moins 5 chiffres")
                    continue
                
                # Soumettre le code
                result = self.submit_traditional_code(code, forward_url, cookies_string, username)
                
                if result["success"]:
                    return result
                elif result.get("can_retry", False):
                    print(f"\n❌ {result['message']}")
                    print("Veuillez réessayer avec un autre code...")
                    continue
                else:
                    return result
                    
            elif choice == "2":
                return {"success": False, "message": "Retour au début pour changer de méthode", "retry": True}
                
            elif choice == "3":
                return {"success": False, "message": "Connexion annulée par l'utilisateur"}
                
            else:
                print("❌ Choix invalide")
    
    def submit_traditional_code(self, code, forward_url, cookies_string, username):
        """Soumettre le code dans le flux traditionnel"""
        
        if not forward_url:
            return {"success": False, "message": "URL de soumission manquante", "can_retry": False}
        
        headers = {
            **self.base_headers,
            "x-ig-app-id": "936619743392459",
            "x-requested-with": "XMLHttpRequest",
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded",
            "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
            "x-csrftoken": self.csrf_token,
            "x-web-session-id": f"{self._random_hex(6)}:{self._random_hex(6)}:{self._random_hex(6)}",
            "x-asbd-id": "359341",
            "sec-ch-prefers-color-scheme": "light",
            "dnt": "1",
            "x-ig-www-claim": "0",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com{self.current_challenge_url}",
            "cookie": cookies_string
        }
        
        payload = {"security_code": code}
        
        try:
            response = self.session.post(
                f"https://www.instagram.com{forward_url}",
                data=payload,
                headers=headers,
                timeout=30
            )
            
            try:
                # Vérifier d'abord les cookies de succès
                for cookie in response.cookies:
                    if cookie.name in ["sessionid", "ds_user_id"]:
                        return self.build_success_response(response, username)
                
                # Vérifier dans le contenu de la réponse
                response_text = response.text
                if '"authenticated":true' in response_text or '"user":true' in response_text:
                    return self.build_success_response(response, username)
                
                # Analyser la réponse JSON
                data = response.json()
                
                # Vérifier le type de redirection pour succès
                if data.get("type") == "CHALLENGE_REDIRECTION":
                    crypted_uid = data.get("cryptedUid", "")
                    location = data.get("location", "")
                    
                    if crypted_uid and location:
                        # Connexion réussie - récupérer les cookies finaux
                        return self.handle_challenge_redirection(location, cookies_string, username)
                
                # Vérifier les erreurs
                if data.get("status") == "fail":
                    challenge_info = data.get("challenge", {})
                    errors = challenge_info.get("errors", [])
                    
                    if errors:
                        error_message = errors[0] if isinstance(errors, list) else str(errors)
                        return {"success": False, "message": error_message, "can_retry": True}
                    else:
                        return {"success": False, "message": "Code incorrect ou expiré", "can_retry": True}
                
                # Si pas d'erreur explicite mais pas de succès non plus
                return {"success": False, "message": "Code incorrect ou expiré", "can_retry": True}
                
            except json.JSONDecodeError:
                if response.status_code == 200:
                    return self.build_success_response(response, username)
                else:
                    return {"success": False, "message": "Réponse invalide", "can_retry": False}
            
        except Exception as e:
            return {"success": False, "message": f"Erreur soumission code: {e}", "can_retry": False}
    
    def handle_challenge_redirection(self, location_url, cookies_string, username):
        """Gérer la redirection après un challenge réussi"""
        
        headers = {
            **self.base_headers,
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "cookie": cookies_string
        }
        
        try:
            response = self.session.get(location_url, headers=headers, timeout=15)
            
            # Vérifier les nouveaux cookies
            for cookie in response.cookies:
                if cookie.name in ["sessionid", "ds_user_id"]:
                    return self.build_success_response(response, username)
            
            # Si pas de cookies de session, continuer avec les cookies existants
            return self.build_success_response(response, username)
            
        except Exception as e:
            return {"success": False, "message": f"Erreur redirection: {e}"}
    
    # ---- FLUX GRAPHQL MODERNE ----
    
    def handle_checkpoint(self, checkpoint_url, cookies_string, username):
        """Gérer le flux checkpoint GraphQL moderne"""
        
        # Extraire l'APC initial
        if "?apc=" in checkpoint_url:
            self.apc = checkpoint_url.split("?apc=")[1]
        
        screen_width = self.current_device_info.get("screen_width", 412)
        dpr = self.current_device_info.get("dpr", 2.625)
        
        # REQUÊTE 1: GET vers checkpoint_url pour extraire le bon APC
        headers1 = {
            **self.base_headers,
            "dpr": str(dpr),
            "viewport-width": str(screen_width),
            "upgrade-insecure-requests": "1",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "referer": "https://www.instagram.com/",
            "cookie": cookies_string
        }
        
        try:
            response1 = self.session.get(
                f"https://www.instagram.com{checkpoint_url}",
                headers=headers1,
                timeout=15
            )
            
            # Mettre à jour cookies depuis la réponse
            for cookie in response1.cookies:
                if cookie.name in ["ps_l", "ps_n", "csrftoken"]:
                    if cookie.name == "csrftoken":
                        self.csrf_token = cookie.value
                    
                    # Mettre à jour cookies_string
                    if f"{cookie.name}=" in cookies_string:
                        cookies_string = re.sub(f'{cookie.name}=[^;]+', f'{cookie.name}={cookie.value}', cookies_string)
                    else:
                        cookies_string += f"; {cookie.name}={cookie.value}"
            
            # Extraire le bon APC depuis la réponse HTML
            html_content = response1.text
            apc_match = re.search(r'hreflang="fr"[^>]*href="[^"]*\?apc=([^"&]+%7Caplc)"', html_content)
            
            if not apc_match:
                apc_match = re.search(r'\?apc=([A-Za-z0-9_-]+%7Caplc)', html_content)
            
            if apc_match:
                self.apc = apc_match.group(1)
            
            # Continuer avec le flux de demande de code
            return self.request_verification_code(cookies_string, username)
            
        except Exception as e:
            return {"success": False, "message": f"Erreur checkpoint: {e}"}
    
    def request_verification_code(self, cookies_string, username):
        """Faire la requête initiale pour obtenir le code de vérification"""
        
        headers2 = {
            **self.base_headers,
            "x-csrftoken": self.csrf_token,
            "x-fb-friendly-name": "AuthPlatformCodeEntryViewQuery",
            "x-ig-app-id": "936619743392459",
            "x-asbd-id": "359341",
            "x-fb-lsd": "AdFupf2HF_k",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com/auth_platform/codeentry/?apc={self.apc}",
            "cookie": cookies_string
        }
        
        apc_decoded = unquote(self.apc)
        timestamp = int(time.time())
        
        payload2 = {
            "av": "0",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "2",
            "__hs": f"{timestamp}.HYP:instagram_web_pkg.2.1...0",
            "dpr": str(self.current_device_info.get("dpr", 2.625)),
            "__ccg": "POOR",
            "__rev": "1027717747",
            "__s": "9c67l8:ul907k:so4h9a",
            "__hsi": str(random.randint(7000000000000000000, 7999999999999999999)),
            "__comet_req": "7",
            "lsd": "AdFupf2HF_k",
            "jazoest": "2960",
            "__spin_r": "1027717747",
            "__spin_b": "trunk",
            "__spin_t": str(timestamp),
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AuthPlatformCodeEntryViewQuery",
            "variables": json.dumps({"apc": apc_decoded}),
            "server_timestamps": "true",
            "doc_id": "10020782808035518"
        }
        
        response2 = self.session.post(
            "https://www.instagram.com/api/graphql",
            data=payload2,
            headers=headers2,
            timeout=15
        )
        
        try:
            data = response2.json()
            code_content = data.get("data", {}).get("xfb_auth_platform_enter_code_content", {})
            
            if code_content:
                # Afficher les informations détaillées sur l'envoi du code
                print(f"\n📧 {code_content.get('screen_content_heading', 'Vérification requise')}")
                print(f"   {code_content.get('screen_content_body', 'Un code a été envoyé')}")
                
                # Demander à l'utilisateur de saisir le code
                return self.handle_code_entry(cookies_string, apc_decoded, username)
            else:
                return {"success": False, "message": "Impossible d'obtenir les informations de vérification"}
                
        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la demande de code: {e}"}
    
    def handle_code_entry(self, cookies_string, apc_decoded, username):
        """Gérer la saisie du code avec options"""
        
        while True:
            print("\n" + "="*60)
            print("🔐 VÉRIFICATION REQUISE")
            print("="*60)
            print("1. Entrer le code de vérification")
            print("2. Essayer une autre méthode de vérification")
            print("3. Quitter")
            print("-"*60)
            
            choice = input("Votre choix (1-3): ").strip()
            
            if choice == "1":
                code = input("\n📱 Entrez le code de vérification: ").strip()
                
                if len(code) < 5:
                    print("❌ Le code doit contenir au moins 5 chiffres")
                    continue
                
                # Soumettre le code
                result = self.submit_verification_code(code, cookies_string, apc_decoded, username)
                
                if result["success"]:
                    return result
                elif result.get("can_retry", False):
                    # Code incorrect, mais on peut réessayer
                    print(f"\n❌ {result['message']}")
                    print("Veuillez réessayer avec un autre code...")
                    continue
                else:
                    # Erreur grave, arrêter
                    return result
                    
            elif choice == "2":
                # Essayer une autre méthode
                return self.try_another_verification_method(cookies_string, apc_decoded, username)
                
            elif choice == "3":
                return {"success": False, "message": "Connexion annulée par l'utilisateur"}
                
            else:
                print("❌ Choix invalide")
    
    def submit_verification_code(self, code, cookies_string, apc_decoded, username):
        """Soumettre le code de vérification"""
        
        headers = {
            **self.base_headers,
            "x-csrftoken": self.csrf_token,
            "x-fb-friendly-name": "useAuthPlatformSubmitCodeMutation",
            "x-ig-app-id": "936619743392459",
            "x-asbd-id": "359341",
            "x-fb-lsd": "AdFupf2HF_k",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com/auth_platform/codeentry/?apc={self.apc}",
            "cookie": cookies_string
        }
        
        timestamp = int(time.time())
        
        payload = {
            "av": "0",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "76",
            "__hs": f"{timestamp}.HYP:instagram_web_pkg.2.1...0",
            "dpr": str(self.current_device_info.get("dpr", 2.625)),
            "__ccg": "MODERATE",
            "__rev": "1027760013",
            "__s": "zxrn60:lw0tbs:z8zxpc",
            "__hsi": str(random.randint(7000000000000000000, 7999999999999999999)),
            "__comet_req": "7",
            "lsd": "AdFupf2HF_k",
            "jazoest": "2960",
            "__spin_r": "1027760013",
            "__spin_b": "trunk",
            "__spin_t": str(timestamp),
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAuthPlatformSubmitCodeMutation",
            "variables": json.dumps({
                "input": {
                    "client_mutation_id": str(random.randint(100, 999)),
                    "actor_id": "0",
                    "code": code,
                    "encrypted_ap_context": apc_decoded
                }
            }),
            "server_timestamps": "true",
            "doc_id": "25017097917894476"
        }
        
        response = self.session.post(
            "https://www.instagram.com/api/graphql",
            data=payload,
            headers=headers,
            timeout=30
        )
        
        try:
            # Vérifier d'abord les cookies de succès
            for cookie in response.cookies:
                if cookie.name in ["sessionid", "ds_user_id"]:
                    # Connexion réussie !
                    return self.build_success_response(response, username)
            
            # Vérifier dans le contenu de la réponse pour succès
            response_text = response.text
            if '"authenticated":true' in response_text or '"user":true' in response_text:
                return self.build_success_response(response, username)
            
            # Analyser la réponse JSON
            try:
                data = response.json()
                submit_data = data.get("data", {}).get("xfb_auth_platform_submit_code", {})
                
                error_message = submit_data.get("error_message")
                if error_message:
                    # Code incorrect - permettre de continuer la boucle
                    return {"success": False, "message": error_message, "can_retry": True}
                
                # Si pas d'erreur explicite mais pas de succès non plus
                redirect_uri = submit_data.get("redirect_uri", "")
                if redirect_uri:
                    # Il y a peut-être une redirection - traiter comme succès potentiel
                    return self.build_success_response(response, username)
                
                return {"success": False, "message": "Code incorrect ou expiré", "can_retry": True}
                
            except json.JSONDecodeError:
                # Pas de JSON valide, mais vérifier les headers de succès
                if response.status_code == 200:
                    return self.build_success_response(response, username)
                else:
                    return {"success": False, "message": "Réponse invalide", "can_retry": False}
            
        except Exception as e:
            return {"success": False, "message": f"Erreur lors de la soumission du code: {e}", "can_retry": False}
    
    def try_another_verification_method(self, cookies_string, apc_decoded, username):
        """Essayer une autre méthode de vérification"""
        
        headers = {
            **self.base_headers,
            "x-csrftoken": self.csrf_token,
            "x-fb-friendly-name": "useAuthPlatformTryAnotherWayMutation",
            "x-ig-app-id": "936619743392459",
            "x-asbd-id": "359341",
            "x-fb-lsd": "AdGKmlMaDQ0",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com/auth_platform/codeentry/?apc={self.apc}",
            "cookie": cookies_string
        }
        
        timestamp = int(time.time())
        
        payload = {
            "av": "0",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "8j",
            "__hs": f"{timestamp}.HYP:instagram_web_pkg.2.1...0",
            "dpr": str(self.current_device_info.get("dpr", 2.625)),
            "__ccg": "MODERATE",
            "__rev": "1027760013",
            "__s": "387exr:lw0tbs:z8zxpc",
            "__hsi": str(random.randint(7000000000000000000, 7999999999999999999)),
            "__comet_req": "7",
            "lsd": "AdGKmlMaDQ0",
            "jazoest": "2899",
            "__spin_r": "1027760013",
            "__spin_b": "trunk",
            "__spin_t": str(timestamp),
            "__crn": "comet.igweb.PolarisAuthPlatformCodeEntryRoute",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAuthPlatformTryAnotherWayMutation",
            "variables": json.dumps({
                "input": {
                    "client_mutation_id": str(random.randint(100, 999)),
                    "actor_id": "0",
                    "encrypted_ap_context": apc_decoded
                }
            }),
            "server_timestamps": "true",
            "doc_id": "9378248908953318"
        }
        
        response = self.session.post(
            "https://www.instagram.com/api/graphql",
            data=payload,
            headers=headers,
            timeout=15
        )
        
        try:
            data = response.json()
            redirect_uri = data.get("data", {}).get("xfb_auth_platform_try_another_way", {}).get("redirect_uri", "")
            
            if redirect_uri:
                # Nouveau APC obtenu
                new_apc = redirect_uri.split("?apc=")[1] if "?apc=" in redirect_uri else ""
                if new_apc:
                    # Navigation vers challenge picker
                    return self.handle_challenge_picker(new_apc, cookies_string, username)
            
            return {"success": False, "message": "Impossible de changer de méthode"}
                
        except Exception as e:
            return {"success": False, "message": f"Erreur changement méthode: {e}"}
    
    def handle_challenge_picker(self, new_apc, cookies_string, username):
        """Gérer le sélecteur de méthodes de vérification"""
        
        # Navigation
        nav_headers = {
            **self.base_headers,
            "x-asbd-id": "359341",
            "x-ig-d": "www",
            "x-fb-lsd": "AdGKmlMaDQ0",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com/auth_platform/challengepicker/?apc={new_apc}",
            "cookie": cookies_string
        }
        
        timestamp = int(time.time())
        
        nav_payload = {
            "client_previous_actor_id": "",
            "route_url": f"/auth_platform/challengepicker/?apc={new_apc}",
            "routing_namespace": "igx_www$a$87a091182d5bd65bcb043a2888004e09",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "8n",
            "__hs": f"{timestamp}.HYP:instagram_web_pkg.2.1...0",
            "dpr": str(self.current_device_info.get("dpr", 2.625)),
            "__ccg": "MODERATE",
            "__rev": "1027760013",
            "__s": "387exr:lw0tbs:z8zxpc",
            "__hsi": str(random.randint(7000000000000000000, 7999999999999999999)),
            "__dyn": "7xeUmwlE7ibwKBAg5S1Dxu13w8CewSwMwNw9G2S0lW4o0B-q1ew6ywaq0yE7i0n24o5-1ywOwv89k2C1Fwc60D82Ixe0EUjwGzEaE2iwNwmE2eU5O0HU1IEGdwtU662O0Lo6-3u2WE15E6O1FwlA1HQp1yU5Oi2K7E5y1rwGwa6byohw4UwFwtE5C",
            "__csr": "hk774soBaD9RGBmKDZeiQKmrH_BKdKm9h94FQ9KppKmqq9yoixy8wKx2l5gO2Fu9Gm2uqq8K9peeDBKJ5DiiGim4bAqx6axabBwCwgoB19165XwBK9gO8xOdxe7p4i2G9x68xu5E8oC2XwzxOm0BU01mBm0c3w15y0Z809uEzg0jjg1co0zyt02lU12IM0AWho4dw3WU0263w1BK",
            "__hsdp": "gnhAgg8Pliibb2isDa6UC1Rw6pwcm0VU2Gw8K4i1VBw9W07O817qw41w1tu",
            "__hblp": "04Uw6Ew5fzU-0R-0y8lxa5o2uwjU3Fw6pw10q0J8e9o28wGyE6q0ZE0Gu0gq0nG2S1_woUK",
            "__comet_req": "7",
            "lsd": "AdGKmlMaDQ0",
            "jazoest": "2899",
            "__spin_r": "1027760013",
            "__spin_b": "trunk",
            "__spin_t": str(timestamp),
            "__crn": "comet.igweb.PolarisAuthPlatformChallengePickerRoute"
        }
        
        nav_response = self.session.post(
            "https://www.instagram.com/ajax/navigation/",
            data=nav_payload,
            headers=nav_headers,
            timeout=15
        )
        
        # Obtenir les options de vérification
        return self.get_verification_options(new_apc, cookies_string, username)
    
    def get_verification_options(self, apc, cookies_string, username):
        """Obtenir les options de vérification disponibles"""
        
        headers = {
            **self.base_headers,
            "x-csrftoken": self.csrf_token,
            "x-fb-friendly-name": "AuthPlatformChallengePickerViewQuery",
            "x-ig-app-id": "936619743392459",
            "x-asbd-id": "359341",
            "x-fb-lsd": "AdGKmlMaDQ0",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com/auth_platform/challengepicker/?apc={apc}",
            "cookie": cookies_string
        }
        
        timestamp = int(time.time())
        apc_decoded = unquote(apc)
        
        payload = {
            "av": "0",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "8p",
            "__hs": f"{timestamp}.HYP:instagram_web_pkg.2.1...0",
            "dpr": str(self.current_device_info.get("dpr", 2.625)),
            "__ccg": "MODERATE",
            "__rev": "1027760013",
            "__s": "387exr:lw0tbs:z8zxpc",
            "__hsi": str(random.randint(7000000000000000000, 7999999999999999999)),
            "__dyn": "7xeUmwlE7ibwKBAg5S1Dxu13w8CewSwMwNw9G2S0lW4o0B-q1ew6ywaq0yE7i0n24o5-1ywOwv89k2C1Fwc60D82Ixe0EUjwGzEaE2iwNwmE2eU5O0HU1IEGdwtU662O0Lo6-3u2WE15E6O1FwlA1HQp1yU5Oi2K7E5y1rwGwa6byohw4UwFwtE5C",
            "__csr": "hk774soBaD9RGBmKDZeiQKmrH_BKdKm9h94FQ9KppKmqq9yoixy8wKx2l5gO2Fu9Gm2uqq8K9peeDBKJ5DiiGim4bAqx6axabBwCwgoB19165XwBK9gO8xOdxe7p4i2G9x68xu5E8oC2XwzxOm0BU01mBm0c3w15y0Z809uEzg0-20YA0j608UDg0Bu0gHc09eAm13o0-K00xwU0prw",
            "__hsdp": "gnhAgg8Pliibb2isDa6UC1Rw6pwcm0VU2Gw8K4i1VBw9W07O817qw41w1tu",
            "__hblp": "04Uw6Ew5fzU-0R-0y8lxa5o2uwjU3Fw6pw9C0dIwbi3ym0y8aEG1Cwfq0aDw46w5WwJwvU6ebw",
            "__comet_req": "7",
            "lsd": "AdGKmlMaDQ0",
            "jazoest": "2899",
            "__spin_r": "1027760013",
            "__spin_b": "trunk",
            "__spin_t": str(timestamp),
            "__crn": "comet.igweb.PolarisAuthPlatformChallengePickerRoute",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AuthPlatformChallengePickerViewQuery",
            "variables": json.dumps({"apc": apc_decoded}),
            "server_timestamps": "true",
            "doc_id": "10027695863977233"
        }
        
        response = self.session.post(
            "https://www.instagram.com/api/graphql",
            data=payload,
            headers=headers,
            timeout=15
        )
        
        try:
            data = response.json()
            challenges = data.get("data", {}).get("xfb_auth_platform_challenges", {})
            options = challenges.get("challenge_options", [])
            
            if not options:
                return {"success": False, "message": "Aucune méthode de vérification disponible"}
            
            # Afficher les options à l'utilisateur
            return self.display_verification_options(options, apc, cookies_string, username)
            
        except Exception as e:
            return {"success": False, "message": f"Erreur options vérification: {e}"}
    
    def display_verification_options(self, options, apc, cookies_string, username):
        """Afficher les options de vérification à l'utilisateur"""
        
        while True:
            print("\n" + "="*60)
            print("🔐 MÉTHODES DE VÉRIFICATION DISPONIBLES")
            print("="*60)
            
            for i, option in enumerate(options, 1):
                header = option.get("header", "Méthode inconnue")
                description = option.get("description", "")
                print(f"{i}. {header}")
                if description:
                    print(f"   {description}")
                print()
            
            print(f"{len(options) + 1}. Quitter et essayer d'autres identifiants")
            print("-"*60)
            
            try:
                choice = int(input("Votre choix: ").strip())
                
                if 1 <= choice <= len(options):
                    selected_option = options[choice - 1]
                    challenge_index = selected_option.get("index", choice - 1)
                    
                    # Sélectionner cette méthode
                    return self.select_verification_method(challenge_index, apc, cookies_string, username)
                    
                elif choice == len(options) + 1:
                    return {"success": False, "message": "Utilisateur a choisi de changer d'identifiants"}
                    
                else:
                    print("❌ Choix invalide")
                    
            except ValueError:
                print("❌ Veuillez entrer un nombre valide")
    
    def select_verification_method(self, challenge_index, apc, cookies_string, username):
        """Sélectionner une méthode de vérification"""
        
        headers = {
            **self.base_headers,
            "x-csrftoken": self.csrf_token,
            "x-fb-friendly-name": "useAuthPlatformSelectChallengeMutation",
            "x-ig-app-id": "936619743392459",
            "x-asbd-id": "359341",
            "x-fb-lsd": "AdGKmlMaDQ0",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com/auth_platform/challengepicker/?apc={apc}",
            "cookie": cookies_string
        }
        
        timestamp = int(time.time())
        apc_decoded = unquote(apc)
        
        payload = {
            "av": "0",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "bj",
            "__hs": f"{timestamp}.HYP:instagram_web_pkg.2.1...0",
            "dpr": str(self.current_device_info.get("dpr", 2.625)),
            "__ccg": "MODERATE",
            "__rev": "1027760013",
            "__s": "mzwxa9:lw0tbs:z8zxpc",
            "__hsi": str(random.randint(7000000000000000000, 7999999999999999999)),
            "__dyn": "7xeUmwlE7ibwKBAg5S1Dxu13w8CewSwMwNw9G2S0lW4o0B-q1ew6ywaq0yE7i0n24o5-1ywOwv89k2C1Fwc60D82Ixe0EUjwGzEaE2iwNwmE2eU5O0HU1IEGdwtU662O0Lo6-3u2WE15E6O1FwlA1HQp1yU5Oi2K7E5y1rwGwa6byohw4UwFwtE5C",
            "__csr": "hk774soBaD9RGBmKDZeiQKmrH_BKdKm9h94FQ9KppKmqq9yoixy8wKx2l5gO2Fu9Gm2uqq8K9peeDBKJ5DiiGim4bAqx6axabBwCwgoB19165XwBK9gO8xOdxe7p4i2G9x68xu5E8oC2XwzxOm0BU01mBm0c3w15y0Z809uEzg0-20YA0j608UDg0Bu0gHc09eAm13o0-K00xwU0prw",
            "__hsdp": "gnhAgg8Pliibb2isDa6UC1Rw6pwcm0VU2Gw8K4i1VBw9W07O817qw41w1tu",
            "__hblp": "04Uw6Ew5fzU-0R-0y8lxa5o2uwjU3Fw6pw9C0dIwbi3ym0y8aEG1Cwfq0aDw46w5WwJwvU6ebw",
            "__comet_req": "7",
            "lsd": "AdGKmlMaDQ0",
            "jazoest": "2899",
            "__spin_r": "1027760013",
            "__spin_b": "trunk",
            "__spin_t": str(timestamp),
            "__crn": "comet.igweb.PolarisAuthPlatformChallengePickerRoute",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAuthPlatformSelectChallengeMutation",
            "variables": json.dumps({
                "input": {
                    "client_mutation_id": str(random.randint(100, 999)),
                    "actor_id": "0",
                    "challenge_index": challenge_index,
                    "contact_point_index": 0,
                    "encrypted_ap_context": apc_decoded
                }
            }),
            "server_timestamps": "true",
            "doc_id": "9771607989592788"
        }
        
        response = self.session.post(
            "https://www.instagram.com/api/graphql",
            data=payload,
            headers=headers,
            timeout=15
        )
        
        try:
            data = response.json()
            redirect_uri = data.get("data", {}).get("xfb_auth_platform_select_challenge", {}).get("redirect_uri", "")
            
            if redirect_uri:
                # Nouveau APC pour cette méthode
                new_apc = redirect_uri.split("?apc=")[1] if "?apc=" in redirect_uri else ""
                if new_apc:
                    # Continuer avec la demande de code pour cette méthode
                    return self.request_verification_code_for_method(new_apc, cookies_string, username)
            
            return {"success": False, "message": "Impossible de sélectionner cette méthode"}
            
        except Exception as e:
            return {"success": False, "message": f"Erreur sélection méthode: {e}"}
    
    def request_verification_code_for_method(self, apc_encoded, cookies_string, username):
        """Demander le code pour une méthode spécifique"""
        
        # Mettre à jour l'APC
        self.apc = apc_encoded
        apc_decoded = unquote(apc_encoded)
        
        headers = {
            **self.base_headers,
            "x-csrftoken": self.csrf_token,
            "x-fb-friendly-name": "AuthPlatformCodeEntryViewQuery",
            "x-ig-app-id": "936619743392459",
            "x-asbd-id": "359341",
            "x-fb-lsd": "AdGKmlMaDQ0",
            "content-type": "application/x-www-form-urlencoded",
            "accept": "*/*",
            "origin": "https://www.instagram.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": f"https://www.instagram.com/auth_platform/challengepicker/?apc={apc_encoded}",
            "cookie": cookies_string
        }
        
        timestamp = int(time.time())
        
        payload = {
            "av": "0",
            "__d": "www",
            "__user": "0",
            "__a": "1",
            "__req": "bm",
            "__hs": f"{timestamp}.HYP:instagram_web_pkg.2.1...0",
            "dpr": str(self.current_device_info.get("dpr", 2.625)),
            "__ccg": "MODERATE",
            "__rev": "1027760013",
            "__s": "mzwxa9:lw0tbs:z8zxpc",
            "__hsi": str(random.randint(7000000000000000000, 7999999999999999999)),
            "__dyn": "7xeUmwlE7ibwKBAg5S1Dxu13w8CewSwMwNw9G2S0lW4o0B-q1ew6ywaq0yE7i0n24o5-1ywOwv89k2C1Fwc60D82Ixe0EUjwGzEaE2iwNwmE2eU5O0HU1IEGdwtU662O0Lo6-3u2WE15E6O1FwlA1HQp1yU5Oi2K7E5y1rwGwa6byohw4UwFwtE5C",
            "__csr": "hk774soBaD9RGBmKDZeiQKmrH_BKdKm9h94FQ9KppKmqq9yoixy8wKx2l5gO2Fu9Gm2uqq8K9peeDBKJ5DiiGim4bAqx6axabBwCwgoB19165XwBK9gO8xOdxe7p4i2G9x68xu5E8oC2XwzxOm0BU01mBm0c3w15y0Z809uEzg0-20YA0j608UDg0Bu0gHc09eAm13o0-K00xwU0prw",
            "__hsdp": "gnhAgg8Pliibb2isDa6UC1Rw6pwcm0VU2Gw8K4i1VBw9W07O817qw41w1tu",
            "__hblp": "04Uw6Ew5fzU-0R-0y8lxa5o2uwjU3Fw6pw9C0dIwbi3ym0y8aEG1Cwfq0aDw46w5WwJwvU6ebw",
            "__comet_req": "7",
            "lsd": "AdGKmlMaDQ0",
            "jazoest": "2899",
            "__spin_r": "1027760013",
            "__spin_b": "trunk",
            "__spin_t": str(timestamp),
            "__crn": "comet.igweb.PolarisAuthPlatformChallengePickerRoute",
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AuthPlatformCodeEntryViewQuery",
            "variables": json.dumps({"apc": apc_decoded}),
            "server_timestamps": "true",
            "doc_id": "10020782808035518"
        }
        
        response = self.session.post(
            "https://www.instagram.com/api/graphql",
            data=payload,
            headers=headers,
            timeout=15
        )
        
        try:
            data = response.json()
            code_content = data.get("data", {}).get("xfb_auth_platform_enter_code_content", {})
            
            if code_content:
                # Afficher les informations détaillées sur l'envoi du code
                print(f"\n📧 {code_content.get('screen_content_heading', 'Vérification requise')}")
                print(f"   {code_content.get('screen_content_body', 'Un code a été envoyé')}")
                
                # Continuer avec la saisie du code
                return self.handle_code_entry(cookies_string, apc_decoded, username)
            else:
                return {"success": False, "message": "Impossible d'obtenir les informations de vérification"}
                
        except Exception as e:
            return {"success": False, "message": f"Erreur demande code: {e}"}
    
    def build_success_response(self, response, username):
        """Construire la réponse de succès et sauvegarder la session"""
        
        cookies_dict = dict(self.session.cookies)
        
        # Extraire les données utilisateur depuis les cookies ou la réponse
        user_id = cookies_dict.get("ds_user_id", "")
        sessionid = cookies_dict.get("sessionid", "")
        
        # Analyser la réponse pour des données supplémentaires
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                if data.get("user") == True:
                    user_id = data.get("userId", user_id)
        except:
            pass
        
        if user_id and sessionid:
            user_data = {
                "user_id": user_id,
                "username": username,
                "authenticated": True
            }
            
            # Construire la session complète avec device info
            session_data = self._build_session_from_cookies(cookies_dict, user_data, self.current_device_info)
            
            # Sauvegarder dans un fichier
            self._save_session_with_device(username, session_data, user_data, self.current_device_info)
            
            return {
                "success": True,
                "user_data": user_data,
                "cookies": cookies_dict,
                "session_data": session_data
            }
        
        return {"success": False, "message": "Données de session incomplètes"}
    
    def load_session(self, username: str) -> dict:
        """Charger session depuis le disque"""
        try:
            complete_filename = f"sessions/{username}_ig_complete.json"
            simple_filename = f"sessions/{username}_ig.json"
            
            filename = complete_filename if os.path.exists(complete_filename) else simple_filename
            
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                created_at = session_data.get("created_at") or session_data.get("last_login") or session_data.get("session_created", 0)
                
                if time.time() - created_at < 7 * 24 * 3600:
                    self.session_data = session_data
                    
                    # Charger aussi les infos device sauvegardées
                    device_data = session_data.get("device_info", {})
                    if device_data:
                        self.current_device_info = device_data
                        
                        # Vérifier si user_agent_mobile existe, sinon le créer
                        if not device_data.get('user_agent_mobile'):
                            # Générer des valeurs aléatoires si elles n'existent pas
                            if not device_data.get('dpi'):
                                device_data['dpi'] = f"{generate_random_dpi()}dpi"
                            if not device_data.get('resolution'):
                                device_data['resolution'] = generate_random_resolution()
                            if not device_data.get('android_release'):
                                device_data['android_release'] = device_data.get('android_version', '14')
                            if not device_data.get('cpu'):
                                device_data['cpu'] = 'mt6989'
                            if not device_data.get('version_code'):
                                device_data['version_code'] = '370711637'
                            
                            # Créer le user_agent_mobile
                            device_data['user_agent_mobile'] = (
                                f"Instagram 307.0.0.34.111 Android ({device_data.get('android_version', '14')}/"
                                f"{device_data['android_release']}; {device_data['dpi']}; "
                                f"{device_data['resolution']}; {device_data.get('manufacturer', 'samsung')}; "
                                f"{device_data.get('model', 'SM-G991B')}; {device_data.get('device', 'z3q')}; {device_data['cpu']}; "
                                f"en_US; {device_data['version_code']})"
                            )
                            
                            # Mettre à jour la session avec le nouveau user_agent_mobile
                            session_data['device_info'] = device_data
                            session_data['user_agent_mobile'] = device_data['user_agent_mobile']
                            
                            # Sauvegarder la session mise à jour
                            try:
                                with open(filename, 'w', encoding='utf-8') as f:
                                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                            except Exception as save_error:
                                print(f"⚠️ Erreur sauvegarde user_agent_mobile: {save_error}")
                    
                    cookies = session_data.get("cookies", {})
                    for name, value in cookies.items():
                        self.session.cookies.set(name, value)
                    
                    return session_data
                else:
                    print(f"⚠️ Session expirée pour {username}")
        
        except Exception as e:
            pass
        
        return {}
    
    def get_mobile_user_agent(self):
        """Retourner le user-agent mobile depuis les infos device"""
        return self.current_device_info.get('user_agent_mobile', '')

    
    def check_account_status_after_login(self, username: str, password: str, login_response: dict) -> dict:
        """Vérifier le statut du compte après la connexion"""
        try:
            if not login_response["success"]:
                return login_response
            
            user_data = login_response.get("user_data", {})
            user_id = user_data.get("user_id")
            
            if not user_id:
                return login_response
            
            session_data = login_response.get("session_data", {})
            auth_token = session_data.get("authorization", "")
            
            # Utiliser les headers Web au lieu des headers mobile
            headers = {
                "user-agent": self.current_device_info.get("user_agent"),
                "x-ig-app-id": "936619743392459",  # Web app ID
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "x-csrftoken": session_data.get("cookies", {}).get("csrftoken", ""),
                "referer": "https://www.instagram.com/",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty"
            }
            
            # Test avec une requête Web simple
            test_response = self.session.get(
                f"https://www.instagram.com/api/v1/users/{user_id}/info/",
                headers=headers,
                timeout=20
            )
            
            if test_response.status_code == 400:
                try:
                    error_data = test_response.json()
                    if "challenge_required" in str(error_data):
                        challenge = error_data.get("challenge", {})
                        url = challenge.get("url", "")
                        
                        if "/accounts/suspended/" in url:
                            return {
                                "success": True,
                                "message": "account_suspended",
                                "status": "suspended",
                                "user_data": user_data,
                                "session_data": session_data
                            }
                        elif "/accounts/disabled/" in url:
                            return {
                                "success": False,
                                "message": "account_disabled", 
                                "status": "disabled",
                                "user_data": user_data
                            }
                        else:
                            return {
                                "success": True,
                                "message": "challenge_warning",
                                "status": "active_with_challenge",
                                "user_data": user_data,
                                "session_data": session_data,
                                "challenge_info": error_data
                            }
                    
                    elif "checkpoint_required" in str(error_data):
                        url = error_data.get("checkpoint_url", "")
                        
                        if "/accounts/suspended/" in url:
                            return {
                                "success": True,
                                "message": "account_suspended",
                                "status": "suspended", 
                                "user_data": user_data,
                                "session_data": session_data
                            }
                        elif "/accounts/disabled/" in url:
                            return {
                                "success": False,
                                "message": "account_disabled",
                                "status": "disabled",
                                "user_data": user_data
                            }
                        else:
                            return {
                                "success": True,
                                "message": "checkpoint_warning",
                                "status": "active_with_checkpoint", 
                                "user_data": user_data,
                                "session_data": session_data,
                                "checkpoint_info": error_data
                            }
                            
                except:
                    pass
            
            return login_response
            
        except Exception as e:
            return login_response
    
    # Méthodes utilitaires pour cookies et session
    
    def _parse_cookie_string(self, cookies_string: str) -> dict:
        """Parser une chaîne de cookies en dictionnaire"""
        try:
            cookies_dict = {}
            # Nettoyer et séparer les cookies
            cookies_string = cookies_string.strip()
            if not cookies_string:
                return {}
            
            # Séparer par point-virgule
            cookie_pairs = cookies_string.split(';')
            
            for i, pair in enumerate(cookie_pairs):
                pair = pair.strip()
                if '=' in pair:
                    name, value = pair.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    
                    # Nettoyer les guillemets si présents
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    cookies_dict[name] = value
            
            return cookies_dict
            
        except Exception as e:
            return {}
    
    def _get_profile_info_from_cookies(self, user_id: str, cookies_dict: dict) -> dict:
        """Récupérer les informations du profil via les cookies"""
        try:
            # Utiliser User-Agent de device généré
            web_user_agent = self.current_device_info.get('user_agent')
            
            # Headers pour récupérer les infos utilisateur
            headers = {
                "accept": "*/*",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "user-agent": web_user_agent,
                "x-csrftoken": cookies_dict.get("csrftoken", ""),
                "x-ig-app-id": "936619743392459",  # App ID web standard
                "x-ig-www-claim": "0",
                "x-requested-with": "XMLHttpRequest",
                "referer": "https://www.instagram.com/",
                "origin": "https://www.instagram.com",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin"
            }
            
            # Vérifier d'abord avec une requête simple vers la page d'accueil
            test_response = self.session.get(
                "https://www.instagram.com/",
                headers={"user-agent": web_user_agent},
                timeout=10
            )
            if test_response.status_code != 200:
                return {"success": False, "error": f"Page d'accueil inaccessible: {test_response.status_code}"}
                
            response = self.session.get(
                f"https://www.instagram.com/api/v1/users/{user_id}/info/",
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"API user info échec: {response.status_code}"}
            
            try:
                data = response.json()
                
                if data.get("status") == "ok" and "user" in data:
                    user_info = data["user"]
                    
                    # Extraire les données utilisateur
                    user_data = {
                        "user_id": str(user_info.get("pk", user_id)),
                        "username": user_info.get("username", ""),
                        "full_name": user_info.get("full_name", ""),
                        "is_verified": user_info.get("is_verified", False),
                        "is_private": user_info.get("is_private", False),
                        "profile_pic_url": user_info.get("profile_pic_url", ""),
                        "follower_count": user_info.get("follower_count", 0),
                        "following_count": user_info.get("following_count", 0),
                        "media_count": user_info.get("media_count", 0),
                        "biography": user_info.get("biography", ""),
                        "is_business": user_info.get("is_business", False),
                        "account_type": user_info.get("account_type", 1),
                        "phone_number": user_info.get("phone_number", ""),
                        "country_code": user_info.get("country_code", ""),
                        "fbid_v2": str(user_info.get("fbid_v2", "")),
                        "interop_messaging_user_fbid": str(user_info.get("interop_messaging_user_fbid", ""))
                    }
                    return {"success": True, "user_data": user_data}
                else:
                    return {"success": False, "error": "Cookies invalides ou expirés"}
                    
            except json.JSONDecodeError as e:
                return {"success": False, "error": "Réponse API invalide"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur récupération profil: {str(e)}"}
    
    def _build_session_from_cookies(self, cookies_dict, user_data, device_info):
        """Construire les données de session depuis les cookies avec device info"""
        
        user_id = user_data.get("user_id")
        username = user_data.get("username") 
        sessionid = cookies_dict.get("sessionid", "")
        
        # Encoder sessionid si nécessaire
        if sessionid and '%3A' not in sessionid:
            sessionid_encoded = urllib.parse.quote(sessionid)
        else:
            sessionid_encoded = sessionid
        
        # Token d'autorisation
        token_data = {
            "ds_user_id": user_id,
            "sessionid": sessionid_encoded
        }
        
        encoded_token = base64.b64encode(json.dumps(token_data, separators=(',', ':')).encode()).decode()
        authorization_header = f"Bearer IGT:2:{encoded_token}"
        
        # Headers IG
        ig_headers = {
            "ig-u-ds-user-id": user_id,
            "x-ig-www-claim": cookies_dict.get("csrftoken", "")[:40] if cookies_dict.get("csrftoken") else ""
        }
        
        # Construire ig-u-rur
        if "rur" in cookies_dict:
            ig_headers["ig-u-rur"] = cookies_dict["rur"].replace('\\', '')
        else:
            timestamp = int(time.time() + 30 * 24 * 3600)
            random_hash = str(uuid.uuid4()).replace('-', '')[:40]
            ig_headers["ig-u-rur"] = f"RVA,{user_id},{timestamp}:01fe{random_hash}"
        
        # UUIDs basés sur device généré
        device_uuid = str(uuid.uuid4())
        android_id = f"android-{str(uuid.uuid4()).replace('-', '')[:16]}"
        
        # Session complète compatible avec device dynamique
        session_data = {
            "uuids": {
                "phone_id": str(uuid.uuid4()),
                "uuid": device_uuid,
                "client_session_id": str(uuid.uuid4()),
                "advertising_id": str(uuid.uuid4()),
                "device_id": android_id
            },
            "cookies": cookies_dict,
            "last_login": int(time.time()),
            "device_settings": device_info,
            "user_agent": device_info.get('user_agent', ''),
            "user_agent_mobile": device_info.get('user_agent_mobile', ''),  # Ajout du user-agent mobile
            "country": "MG",
            "country_code": 261,
            "locale": "fr_FR",
            "timezone_offset": 10800,
            
            # IMPORTANT: Sauvegarder toutes les infos device utilisées
            "device_info": device_info,
            
            # Données d'autorisation
            "authorization_data": {
                "ds_user_id": user_id,
                "sessionid": sessionid,
                "should_use_header_over_cookies": True,
                "authorization_header": authorization_header,
                "username": username,
                "session_flush_nonce": "",
                "credential_type": "cookies"
            },
            
            # Headers IG
            "ig_headers": ig_headers,
            
            # Données utilisateur
            "user_data": user_data,
            "session_created": int(time.time()),
            "logged_in_user": user_data,
            "account_id": user_id,
            "account_username": username,
            "rank_token": f"{user_id}_{uuid.uuid4()}",
            "csrf_token": cookies_dict.get("csrftoken", "missing"),
            
            # Métadonnées session
            "session_metadata": {
                "login_timestamp": int(time.time()),
                "session_start_time": time.time(),
                "pigeon_session_id": f"UFS-{uuid.uuid4()}-0",
                "conn_uuid_client": str(uuid.uuid4()).replace('-', ''),
                "bandwidth_test_data": {
                    "speed_kbps": random.uniform(1000, 5000),
                    "total_bytes": random.randint(500000, 5000000),
                    "total_time_ms": random.randint(300, 2000)
                },
                "salt_ids": [332011630, random.randint(220140000, 220150000)],
                "bloks_version_id": "ce555e5500576acd8e84a66018f54a05720f2dce29f0bb5a1f97f0c10d6fac48",
                "status": "ok"
            },
            
            # Device fingerprint depuis device généré
            "device_fingerprint": {
                "android_id": android_id,
                "device_uuid": device_uuid,
                "family_device_id": str(uuid.uuid4()),
                "x_mid": device_info.get('x_mid', ''),
                "attestation_data": {},
                "screen_density": device_info.get('screen_density', 320),
                "screen_width": device_info.get('screen_width', 412),
                "screen_height": device_info.get('screen_height', 915),
                "connection_type": "WIFI"
            },
            
            # Authorization header direct
            "authorization": authorization_header
        }
        
        return session_data
    
    def _save_session_with_device(self, username: str, session_data: dict, user_data: dict, device_info: dict):
        """Sauvegarder session complète AVEC les informations device utilisées"""
        try:
            os.makedirs("sessions", exist_ok=True)
            
            complete_filename = f"sessions/{username}_ig_complete.json"
            
            if not user_data.get("username"):
                user_data["username"] = username
            
            # Sauvegarder avec formatage propre
            with open(complete_filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            # Supprimer l'ancien fichier simple s'il existe
            simple_filename = f"sessions/{username}_ig.json"
            if os.path.exists(simple_filename):
                try:
                    os.remove(simple_filename)
                except:
                    pass
        
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde session: {e}")
    
    def _save_session_fixed(self, username: str, session_data: dict, user_data: dict):
        """Sauvegarder session complète (méthode de compatibilité)"""
        self._save_session_with_device(username, session_data, user_data, self.current_device_info)
