# -*- coding: utf-8 -*-
"""
Client principal Instagram pour insta_kendou - VERSION AMÉLIORÉE
Classe InstagramClient avec toutes les fonctionnalités complètes et headers exacts
"""

import os
import time
import json
import uuid
import random
import urllib.parse
import re
import base64
from datetime import datetime
from .auth import InstagramAuth
from .utils import DeviceManager, InstagramEncryption, MediaProcessor, URLResolver, validate_license
from .exceptions import *
from .auth import InstagramAuth, InstagramSignup
class InstagramAPI:
    """API Instagram pour extraire media ID et user ID (intégrée au client) - CORRIGÉE"""
    
    def __init__(self, session, device_info: dict, user_id: str = None, auth_token: str = None, client=None):
        self.session = session
        self.device_info = device_info
        self.user_id = user_id
        self.auth_token = auth_token
        self.url_resolver = URLResolver()
        self.client = client  # ← Maintenant 'client' est défini comme paramètre
    
    
    def shortcode_to_media_id(self, shortcode: str) -> str:
        """Convertir shortcode Instagram en media ID (algorithme exact)"""
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        base = len(alphabet)
        id_num = 0
        for char in shortcode:
            id_num = id_num * base + alphabet.index(char)
        return str(id_num)
    def extract_media_id_from_url_no_session(self, url: str) -> str:
        """Extraire media ID depuis URL Instagram SANS REQUÊTES WEB"""
        try:
            # Résoudre les liens courts d'abord
            resolved_url = self.url_resolver.resolve_short_url(url)
            
            # Extraire shortcode depuis l'URL
            patterns = [
                r'/p/([A-Za-z0-9_-]+)/',
                r'/reel/([A-Za-z0-9_-]+)/',
                r'/tv/([A-Za-z0-9_-]+)/'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, resolved_url)
                if match:
                    shortcode = match.group(1)
                    # Convertir shortcode en media_id directement
                    media_id = self.shortcode_to_media_id(shortcode)
                    return media_id
            
            return None
            
        except Exception as e:
            return None
    
    
    
    
    
    def extract_user_id_from_url_no_session(self, url: str) -> str:
        """Extraire user ID depuis URL de profil SANS SESSION"""
        try:
            import requests
            
            # D'abord résoudre les liens courts
            resolved_url = self.url_resolver.resolve_short_url(url)
            
            # Extraire username depuis l'URL
            match = re.search(r'instagram\.com/([^/?]+)', resolved_url)
            if match:
                username = match.group(1).replace('@', '').strip()
                
                # Méthode HTTP SANS SESSION REQUISE
                temp_session = requests.Session()
                
                headers = {
                    "user-agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36",
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }
                
                profile_url = f"https://www.instagram.com/{username}/"
                if not profile_url.endswith('/'):
                    profile_url += '/'
                
                response = temp_session.get(profile_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Patterns pour extraire user ID
                    user_id_patterns = [
                        r'"profile_id":"(\d+)"',
                        r'"profilePage_(\d+)"',
                        r'"user_id":"(\d+)"',
                        r'"owner":{"id":"(\d+)"',
                        r'"id":"(\d+)"[^"]*"username":"' + re.escape(username) + '"',
                        r'"pk":"(\d+)"[^"]*"username":"' + re.escape(username) + '"',
                        r'"pk":(\d+)[^"]*"username":"' + re.escape(username) + '"'
                    ]
                    
                    for pattern in user_id_patterns:
                        match = re.search(pattern, content)
                        if match:
                            user_id = match.group(1)
                            if user_id.isdigit():
                                return user_id
                
                # Si échec extraction web, utiliser la méthode avec session existante
                if self.user_id and self.auth_token:
                    return self._search_similar_username_api_only(username)
            
            return None
            
        except Exception:
            # Si erreur extraction sans session, utiliser la méthode avec session
            if self.user_id and self.auth_token:
                username_match = re.search(r'instagram\.com/([^/?]+)', url)
                if username_match:
                    username = username_match.group(1).replace('@', '').strip()
                    return self._search_similar_username_api_only(username)
            return None
    def extract_media_id_from_url(self, url: str) -> str:
        """Extraire media ID depuis URL Instagram (utilise URLResolver)"""
        return self.url_resolver.extract_media_id_from_url(url)
    
    def extract_user_id_from_url(self, url: str) -> str:
        """Extraire user ID depuis URL de profil - AVEC FALLBACK SANS SESSION"""
        try:
            # D'abord résoudre les liens courts
            resolved_url = self.url_resolver.resolve_short_url(url)
            
            # Extraire username depuis l'URL
            match = re.search(r'instagram\.com/([^/?]+)', resolved_url)
            if match:
                username = match.group(1).replace('@', '').strip()
                
                # ÉTAPE 1: Tenter extraction directe via recherche API (avec session)
                user_id = self._direct_username_to_user_id(username)
                if user_id:
                    return user_id
                
                # ÉTAPE 2: Si échec, recherche similaire via API (avec session)
                user_id = self._search_similar_username_api_only(username)
                if user_id:
                    return user_id
                
                # ÉTAPE 3: Si échec API, fallback HTTP SANS SESSION
                user_id = self._username_to_user_id_http_fallback(username)
                return user_id  # Peut être None si pas trouvé
            
            return None
            
        except Exception as e:
            return None
    
    def _username_to_user_id_http_fallback(self, username: str) -> str:
        """Fallback HTTP pour username -> user ID SANS SESSION REQUISE"""
        try:
            import requests
            
            # Nouvelle session temporaire sans authentification
            temp_session = requests.Session()
            
            # Headers basiques comme un navigateur normal
            headers = {
                "user-agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "cache-control": "no-cache",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none"
            }
            
            # Requête vers le profil public
            response = temp_session.get(
                f"https://www.instagram.com/{username}/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                content = response.text
                
                # Patterns pour extraire user ID depuis HTML
                user_id_patterns = [
                    r'"profilePage_([0-9]+)"',
                    r'"user_id":"([0-9]+)"',
                    r'"owner":{"id":"([0-9]+)"',
                    r'"id":"([0-9]+)"[^"]*"username":"' + re.escape(username) + '"',
                    r'"pk":"([0-9]+)"[^"]*"username":"' + re.escape(username) + '"',
                    r'"pk":([0-9]+)[^"]*"username":"' + re.escape(username) + '"'
                ]
                
                for pattern in user_id_patterns:
                    match = re.search(pattern, content)
                    if match:
                        user_id = match.group(1)
                        # Vérifier que c'est un ID valide (que des chiffres)
                        if user_id.isdigit():
                            return user_id
                
                # Tenter avec API GraphQL publique si HTML échoue
                return self._try_graphql_user_id(username, temp_session)
            
            return None
            
        except Exception:
            return None
    
    def _try_graphql_user_id(self, username: str, session) -> str:
        """Tenter extraction via API GraphQL publique Instagram"""
        try:
            # GraphQL query pour info utilisateur publique
            graphql_url = "https://www.instagram.com/api/v1/users/web_profile_info/"
            
            headers = {
                "user-agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36",
                "x-ig-app-id": "567067343352427",
                "x-requested-with": "XMLHttpRequest"
            }
            
            params = {
                "username": username
            }
            
            response = session.get(
                graphql_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    user_data = data.get("data", {}).get("user", {})
                    user_id = user_data.get("id")
                    
                    if user_id and str(user_id).isdigit():
                        return str(user_id)
                        
                except Exception:
                    pass
            
            return None
            
        except Exception:
            return None
    
    def _direct_username_to_user_id(self, username: str) -> str:
        """Extraction directe user ID via recherche API exacte"""
        try:
            headers = {
                "user-agent": self.device_info['user_agent'],
                "x-ig-app-id": "567067343352427",
                "x-ig-android-id": self.device_info['android_id'],
                "x-ig-device-id": self.device_info['device_uuid'],
                "accept-language": "fr-FR, en-US",
                "authorization": self.auth_token,
            }
            
            search_params = {
                "timezone_offset": "10800",
                "q": username,
                "count": "20"
            }
            
            response = self.session.get(
                "https://i.instagram.com/api/v1/users/search/",
                params=search_params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok" and "users" in data:
                        users = data["users"]
                        
                        # Recherche EXACTE seulement
                        for user in users:
                            user_username = user.get("username", "").lower()
                            if user_username == username.lower():
                                return str(user.get("pk"))
                
                except Exception:
                    pass
            
            return None
            
        except Exception:
            return None
    
    def _search_similar_username_api_only(self, target_username: str) -> str:
        """Rechercher username similaire via API seulement - PAS DE WEB"""
        try:
            headers = {
                "user-agent": self.device_info['user_agent'],
                "x-ig-app-id": "567067343352427",
                "x-ig-android-id": self.device_info['android_id'],
                "x-ig-device-id": self.device_info['device_uuid'],
                "accept-language": "fr-FR, en-US",
                "authorization": self.auth_token,
            }
            
            search_params = {
                "timezone_offset": "10800",
                "q": target_username,
                "count": "20"
            }
            
            response = self.session.get(
                "https://i.instagram.com/api/v1/users/search/",
                params=search_params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok" and "users" in data:
                        users = data["users"]
                        
                        target_lower = target_username.lower()
                        best_matches = []
                        
                        # Recherche par préfixe seulement
                        for user in users:
                            username = user.get("username", "").lower()
                            if username.startswith(target_lower) and username != target_lower:
                                best_matches.append((user.get("pk"), username))
                        
                        # Retourner le match le plus court (plus probable)
                        if best_matches:
                            best_matches.sort(key=lambda x: len(x[1]))
                            return str(best_matches[0][0])
                        
                except Exception:
                    pass
            
            # Si rien trouvé via recherche similaire = utilisateur introuvable
            return None
            
        except Exception:
            return None
    
    def get_user_info(self, user_id: str) -> dict:
        """Récupérer informations d'un utilisateur"""
        try:
            headers = {
                "user-agent": self.device_info['user_agent'],
                "x-ig-app-id": "567067343352427",
                "x-ig-android-id": self.device_info['android_id'],
                "x-ig-device-id": self.device_info['device_uuid'],
                "accept-language": "fr-FR, en-US",
                "authorization": self.auth_token if self.auth_token else "",
            }
            
            response = self.session.get(
                f"https://i.instagram.com/api/v1/users/{user_id}/info/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return data.get("user", {})
            
            return {}
            
        except Exception as e:
            return {}
    
    def get_own_media_list(self, count: int = 20) -> list:
        """Récupérer la liste des médias de l'utilisateur connecté"""
        try:
            if not self.user_id:
                return []
            
            # Utiliser le client parent pour récupérer les headers
            if self.client:
                device_headers = self.client._get_device_specific_headers()
                
                headers = {
                    "user-agent": device_headers["user-agent"],
                    "x-ig-app-id": "567067343352427",
                    "authorization": self.auth_token if self.auth_token else "",
                    "x-ig-android-id": device_headers["x-ig-android-id"],
                    "x-ig-device-id": device_headers["x-ig-device-id"],
                    "accept-language": "fr-FR, en-US",
                }
                
            else:
                # Fallback si pas de client
                headers = {
                    "user-agent": self.device_info.get('user_agent', 'Instagram 307.0.0.34.111 Android'),
                    "x-ig-app-id": "567067343352427", 
                    "authorization": self.auth_token if self.auth_token else "",
                    "accept-language": "fr-FR, en-US",
                }
            
            params = {
                "count": str(count),
                "max_id": ""
            }
            
            response = self.session.get(
                f"https://i.instagram.com/api/v1/feed/user/{self.user_id}/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    items = data.get("items", [])
                    media_list = []
                    
                    for item in items:
                        media_info = {
                            "id": item.get("id"),
                            "code": item.get("code"),
                            "media_type": item.get("media_type"),
                            "taken_at": item.get("taken_at"),
                            "like_count": item.get("like_count", 0),
                            "comment_count": item.get("comment_count", 0)
                        }
                        
                        # Caption
                        caption_info = item.get("caption")
                        if caption_info:
                            media_info["caption"] = caption_info.get("text", "")
                        else:
                            media_info["caption"] = ""
                        
                        media_list.append(media_info)
                    
                    return media_list
            
            return []
            
        except Exception as e:
            return []

class InstagramWebEditor:
    """Éditeur de profil Instagram via API Web intégré au client"""
    
    def __init__(self, client):
        """Initialisation avec référence au client Instagram"""
        self.client = client
        self.session = client.auth.session if client.auth else None
        self.session_data = client.session_data
        
        # Données extraites des cookies/session
        self.cookies_raw = ""
        self.ig_did = ""
        self.csrf_token = ""
        self.datr = ""
        self.mid = ""
        self.sessionid = ""
        self.ds_user_id = ""
        self.rur = ""
        
        # Tokens dynamiques récupérés
        self.fb_dtsg = ""
        self.lsd = ""
        self.rev = "1029624345"
        self.hsi = ""
        self.account_id = ""
        
        # Informations actuelles du compte
        self.current_account_info = {}
        
        # Auto-setup si client connecté
        if self.session_data and "cookies" in self.session_data:
            self._setup_from_client_session()
    
    def _setup_from_client_session(self):
        """Configuration automatique depuis la session du client"""
        try:
            cookies_data = self.session_data.get("cookies", {})
            
            # Extraire les valeurs importantes
            self.ig_did = cookies_data.get('ig_did', '')
            self.csrf_token = cookies_data.get('csrftoken', '')
            self.datr = cookies_data.get('datr', '')
            self.mid = cookies_data.get('mid', '')
            self.sessionid = cookies_data.get('sessionid', '')
            self.ds_user_id = cookies_data.get('ds_user_id', '')
            self.rur = cookies_data.get('rur', '')
            
            # Construire cookie string
            cookie_parts = []
            for name, value in cookies_data.items():
                cookie_parts.append(f"{name}={value}")
            self.cookies_raw = "; ".join(cookie_parts)
            
            return True
        except Exception:
            return False
    
    def setup_cookies(self, cookies_string):
        """Configuration des cookies à partir de la chaîne fournie"""
        try:
            self.cookies_raw = cookies_string
            
            # Parser les cookies
            cookie_dict = {}
            for cookie in cookies_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookie_dict[key] = value
            
            # Extraire les valeurs importantes
            self.ig_did = cookie_dict.get('ig_did', '')
            self.csrf_token = cookie_dict.get('csrftoken', '')
            self.datr = cookie_dict.get('datr', '')
            self.mid = cookie_dict.get('mid', '')
            self.sessionid = cookie_dict.get('sessionid', '')
            self.ds_user_id = cookie_dict.get('ds_user_id', '')
            self.rur = cookie_dict.get('rur', '')
            
            # Configurer la session si disponible
            if self.session:
                self.session.cookies.update(cookie_dict)
            
            return True
        except Exception:
            return False
    
    def _get_account_info_web(self, show_info=True):
        """Récupérer les informations du compte via API web"""
        try:
            if not self.session or not self.cookies_raw:
                return {"success": False, "error": "Session non configurée. Utilisez setup_cookies() ou connectez-vous d'abord."}
            
            headers = {
                "host": "www.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Google Chrome";v="141.0.7390.123", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.123"',
                "sec-ch-ua-platform": '"Windows"',
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-mobile": "?0",
                "x-ig-app-id": "936619743392459",
                "x-asbd-id": "359341",
                "x-requested-with": "XMLHttpRequest",
                "sec-ch-prefers-color-scheme": "light",
                "accept": "*/*",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "x-ig-www-claim": "hmac.AR2gQrewxBbqtfsFELoEB-eQr-6U-hBAEayHeyyZ8hpTHRZu",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/edit/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            response = self.session.get(
                "https://www.instagram.com/api/v1/accounts/edit/web_form_data/",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "ok":
                    self.current_account_info = data.get("form_data", {})
                    if show_info:
                        print(f"Username: @{self.current_account_info.get('username')}")
                        print(f"Email actuel: {self.current_account_info.get('email')}")
                    return {"success": True, "data": self.current_account_info}
                else:
                    return {"success": False, "error": f"Erreur API: {data}"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur récupération infos: {e}"}
    
    def _get_account_center_tokens(self):
        """Récupérer les tokens Facebook nécessaires"""
        try:
            if not self.session or not self.cookies_raw:
                return {"success": False, "error": "Session non configurée"}
            
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "dpr": "1",
                "viewport-width": "929",
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua-platform-version": '"10.0.0"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-full-version-list": '"Google Chrome";v="141.0.7390.123", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.123"',
                "sec-ch-prefers-color-scheme": "light",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "sec-fetch-site": "same-site",
                "sec-fetch-mode": "navigate",
                "sec-fetch-user": "?1",
                "sec-fetch-dest": "document",
                "referer": "https://www.instagram.com/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            response = self.session.get(
                "https://accountscenter.instagram.com/",
                params={"entry_point": "app_settings"},
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Extraction des tokens
                patterns_fb_dtsg = [
                    r'"token":"([^"]+)"',
                    r'"f":"([^"]+)"',
                    r'token["\']:\s*["\']([^"\']+)["\']',
                    r'fb_dtsg["\']:\s*["\']([^"\']+)["\']',
                    r'"dtsg":"([^"]+)"',
                    r'"DTSGInitialData"[^"]*"token":"([^"]+)"'
                ]
                
                for pattern in patterns_fb_dtsg:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        self.fb_dtsg = matches[0]
                        break
                
                # Extraire lsd
                lsd_patterns = [
                    r'"lsd":"([^"]+)"',
                    r'lsd["\']:\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in lsd_patterns:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        self.lsd = matches[0]
                        break
                
                # Extraire __rev
                rev_matches = re.findall(r'"__rev":([0-9]+)', html_content)
                if rev_matches:
                    self.rev = rev_matches[0]
                
                # Extraire __hsi
                hsi_matches = re.findall(r'"__hsi":"([^"]+)"', html_content)
                if hsi_matches:
                    self.hsi = hsi_matches[0]
                
                # Extraire account ID
                account_matches = re.findall(r'"id":"([0-9]{17,})"', html_content)
                if account_matches:
                    self.account_id = account_matches[0]
                
                if not self.fb_dtsg:
                    return {"success": False, "error": "Impossible de récupérer fb_dtsg"}
                
                return {"success": True, "fb_dtsg": self.fb_dtsg}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur tokens: {e}"}
    
    def _add_email_mutation(self, new_email):
        """Ajouter un nouvel email via mutation Facebook"""
        try:
            if not self.fb_dtsg:
                token_result = self._get_account_center_tokens()
                if not token_result["success"]:
                    return token_result
            
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Google Chrome";v="141.0.7390.123", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.123"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "x-fb-friendly-name": "FXAccountsCenterAddContactPointMutation",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/personal_info/contact_points/?contact_point_type=email&dialog_type=add_contact_point",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            mutation_id = f"mutation_id_{int(time.time() * 1000)}"
            
            variables = {
                "country": "MG",
                "contact_point": new_email,
                "contact_point_type": "email",
                "selected_accounts": [self.account_id or "17858449030071790"],
                "family_device_id": "device_id_fetch_ig_did",
                "client_mutation_id": mutation_id
            }
            
            payload = {
                "av": self.account_id or "17858449030071790",
                "__user": "0",
                "__a": "1",
                "__req": "19",
                "__hs": "20401.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "EXCELLENT",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7570565044114389596",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gz17PE9N4iyivZmD9WAuAYxbnpR4iZEKJ2p7D_WnaT8SL6iQRjXcmDO9OabBmOYnuGjjFtV9BiAjEDjQqvWXJbRQfXKhebprDyaGLimCFLXJul92pt3kmBAyLKqF2HjheFUs_UDBmahK4Ci4W__hJ7Fxt6XyWxa5UG4Ux124EO8Dz9pJ6gV0Fy-4t4UF3UbHVoF0Jw054VG0YA0qS17K2m5m8wb2mp1x5gyqp06HwiUBwdaEmw0wpwdq6o0jIu9Ti1b7MFgGcK-48eU8Q1vod8cCXQ0GEWmUkAwabyEWXGECl29uUzxeuih4KFprKGBx2FVWBJe8yqHxu9zAl7hpA4okU8VfzQFEpAgb8F6U-WXG2jBy-l4KFHKi2acDxmXDiDgswygWWy4FXwup8jADwa6FpXwTxt28lwEgjhbxeiGw3c4mm5Xz8aEx0",
                "__hsdp": "gmPMqgH681HiN1e0rtB58h4LC0c4958aNiwh8TAzuVpaRwhwAi4oo8oMZ5y4u8ghe6iBwD80s16yy965i3UlyqcdxKmb6k0JUJ4wEj4wBccxG68cEa8Mc0K2EB6xqd83J5a1rc23x66o26wxwihgc41e80ii5Go5eE4MMtzh8x06ow5bwsUqw2y60GU3Aw51Uy0dQwWg0Nu5o0tkKfmA0NE0lbwXyEC7o1zFQ1ZBxC5E5u0KUqy82zg3cwa24U8pUb8aUdEK0TU2fwfa0gy0gJw7xxq7e0R8bEfE0B-7U10A2e11w4xg4W321Jw",
                "__hblp": "05pxGq0ta0sW15zqKdByox0mkahEowypVoSagS220tO3-2l5G5qxu1xxu3q5U-4oO5uu2F1i6EGbUC2y4ElwCCxC32ayUO7bBgoQ2Om7Emxa22czdxK1xAUiUa89EgDx24UqwDx-awkE5mdwxwAzosByK3O3u1sKewdS589E22CCwOw-wAAg26Gdgd8SdBzoowNx23C2u12wXwjU2GwlU9E-0K876-2-ewjEO0VUy0Ao1WU4i0zonyUeU1Eotw5nw16e08Ex60B8dEmxq1NwUw2Eo0A21NxK1Jwso2PwDxe7ocVEfUdEGfwULDwu89oiwzwtk26bwnEiwmElCwbC3i2K3q0WU9o98bUkwFwqoozEdE128co3rxK0-U38gmw2-88E2Bwoo31xmcwYw8y0CF8C3m3-1Nw",
                "__sjsp": "gmPMqgH682h2c3Tb44U1JSkkx4i-o0MgAkwH5a14wAwq8swmE0zEyg",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "26661",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "FXAccountsCenterAddContactPointMutation",
                "server_timestamps": "true",
                "variables": json.dumps(variables),
                "doc_id": "24024219683917897"
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                success = data.get("data", {}).get("xfb_add_contact_point", {}).get("success", False)
                
                if success:
                    return {"success": True, "data": data, "email": new_email}
                else:
                    error_text = data.get("data", {}).get("xfb_add_contact_point", {}).get("error_text", "Erreur inconnue")
                    return {"success": False, "error": f"Erreur ajout email: {error_text}"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur mutation: {e}"}
    
    def _verify_email_code(self, email, verification_code):
        """Vérifier le code de confirmation d'email"""
        try:
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Google Chrome";v="141.0.7390.123", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.123"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "x-fb-friendly-name": "FXAccountsCenterContactPointConfirmationDialogVerifyContactPointMutation",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/personal_info/contact_points/?contact_point_type=email&dialog_type=add_contact_point",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            mutation_id = f"mutation_id_{int(time.time() * 1000)}"
            
            variables = {
                "contact_point": email,
                "contact_point_type": "email",
                "pin_code": verification_code,
                "selected_accounts": [self.account_id or "17858449030071790"],
                "family_device_id": "device_id_fetch_ig_did",
                "client_mutation_id": mutation_id,
                "contact_point_event_type": "ADD",
                "normalized_contact_point_to_replace": ""
            }
            
            payload = {
                "av": self.account_id or "17858449030071790",
                "__user": "0",
                "__a": "1",
                "__req": "1f",
                "__hs": "20401.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "EXCELLENT",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7570565044114389596",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gz17PE9N4iyivZmD9WAuAYxbnpR4iZEKJ2p7D_WnaT8SL6iQRjXcmDO9OabBmOYnuGjjFtV9BiAjEDjQqvWXJbRQfXKhebprDyaGLimCFLXJul92pt3kmBAyLKqF2HjheFUs_UDBmahK4Ci4W__hJ7Fxt6XyWxa5UG4Ux124EO8Dz9pJ6gV0Fy-4t4UF3UbHVoF0Jw054VG0YA0qS17K2m5m8wb2mp1x5gyqp06HwiUBwdaEmw0wpwdq6o0jIu9Ti1b7MFgGcK-48eU8Q1vod8cCXQ0GEWmUkAwabyEWXGECl29uUzxeuih4KFprKGBx2FVWBJe8yqHxu9zAl7hpA4okU8VfzQFEpAgb8F6U-WXG2jBy-l4KFHKi2acDxmXDiDgswygWWy4FXwup8jADwa6FpXwTxt28lwEgjhbxeiGw3c4mm5Xz8aEx0",
                "__hsdp": "gmPMqgH681HiN1e0rtB58h4LC0c4958aNiwh8TAzuVpaRwhwAi4oo8oMZ5y4u8gh41wFo9O070hEEy8gl8fxm9EMS6VoIpg2TyQi2xci2kMO6EowOwEz0M2Uaykq5EQweQkE5IM8e4opw8q261950Mg4Uw198mFwkWwj31Sd4y40py0kK1PxG0a8o2Hwei0k7y80Ti3F035Ulw1RiUZqg36w1kK3Kayotw6eDg7Sm6omwlU2XxG8wad0cO0E8jwxDwIwHwSyU3vw8-0YE12812S0u65EsU3kwKw-w2nUvw42g8U460i50jEc86S",
                "__hblp": "05pxGq0ta0sW15zqKdByox0mkahEowypVoSagS220tO3-2l5G5qxu1xxu3q5U-4oO5uu2F1i6EGbUC2y4ElwCCxC32ayUO7bBgoQ2Om7Emxa22czdxK1xAUiUa89EgDx24UqwDx-awkE5mdwxwAzosByK3O3u1sKewdS589E22CCwOw-wAAg26Gdgd8SdBzoowNx23C2u12wXwjU2GwlU9E-0K876-2-ewjEO0VUy0Ao1WU4i0zonyUeU1Eotw5nw16e08Ex60B8dEmxq1NwUw2Eo0A21NxK1Jwso2PwDxe7ocVEfUdEGfwULDwu89oiwzwtk26bwnEiwmElCwbC3i2K3q0WU9o98bUkwFwqoozEdE128co3rxK0-U38gmw2-88E2Bwoo31xmcwYw8y0CF8C3m3-1Nw",
                "__sjsp": "gmPMqgH682h2c3Tb44U1JSkkx4i-o0MgAkwH5a14wAwq8swmE0zEyg",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "26661",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "FXAccountsCenterContactPointConfirmationDialogVerifyContactPointMutation",
                "server_timestamps": "true",
                "variables": json.dumps(variables),
                "doc_id": "24829010190041566"
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                verification_results = data.get("data", {}).get("xfb_verify_contact_point", [])
                
                if verification_results:
                    result = verification_results[0].get("mutation_data", {})
                    success = result.get("success", False)
                    
                    if success:
                        return {"success": True, "verified": True}
                    else:
                        error_text = result.get("error_text", "Code incorrect")
                        return {"success": False, "error": error_text, "retry": True}
                else:
                    return {"success": False, "error": "Pas de résultat de vérification"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur vérification: {e}"}
    
    def _edit_basic_profile(self, **kwargs):
        """Modifier les informations de base du profil"""
        try:
            if not self.session or not self.cookies_raw:
                return {"success": False, "error": "Session non configurée. Utilisez setup_cookies() ou connectez-vous d'abord."}
            
            # Récupérer les infos actuelles
            current_result = self._get_account_info_web(show_info=False)
            if not current_result["success"]:
                return current_result
            
            current_info = current_result["data"]
            
            # Préparer les données
            payload = {
                "biography": kwargs.get("biography", current_info.get("biography", "")),
                "chaining_enabled": "on" if current_info.get("chaining_enabled", True) else "",
                "external_url": kwargs.get("external_url", current_info.get("external_url", "")),
                "first_name": kwargs.get("first_name", current_info.get("first_name", "")),
                "username": kwargs.get("username", current_info.get("username", "")),
                "jazoest": "21928"
            }
            
            headers = {
                "host": "www.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Google Chrome";v="141.0.7390.123", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.123"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-mobile": "?0",
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-instagram-ajax": "1029625740",
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "x-asbd-id": "359341",
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "x-ig-www-claim": "hmac.AR2gQrewxBbqtfsFELoEB-eQr-6U-hBAEayHeyyZ8hpTHRZu",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/edit/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            response = self.session.post(
                "https://www.instagram.com/api/v1/web/accounts/edit/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "ok":
                    # Mettre à jour les infos locales
                    self.current_account_info.update(kwargs)
                    
                    return {"success": True, "message": "Profil modifié avec succès", "data": data}
                else:
                    return {"success": False, "error": f"Erreur API: {data}"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur modification: {e}"}
    
    def _edit_gender(self, gender):
        """Modifier le genre du compte"""
        try:
            if not self.session or not self.cookies_raw:
                return {"success": False, "error": "Session non configurée. Utilisez setup_cookies() ou connectez-vous d'abord."}
            
            headers = {
                "host": "www.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Google Chrome";v="141.0.7390.123", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.123"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-mobile": "?0",
                "x-ig-app-id": "936619743392459",
                "x-requested-with": "XMLHttpRequest",
                "accept": "*/*",
                "content-type": "application/x-www-form-urlencoded",
                "x-instagram-ajax": "1029625740",
                "x-csrftoken": self.csrf_token,
                "x-web-session-id": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "x-asbd-id": "359341",
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "x-ig-www-claim": "hmac.AR2gQrewxBbqtfsFELoEB-eQr-6U-hBAEayHeyyZ8hpTHRZu",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://www.instagram.com/accounts/edit/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            payload = {
                "custom_gender": "",
                "gender": str(gender),
                "jazoest": "21928"
            }
            
            response = self.session.post(
                "https://www.instagram.com/api/v1/web/accounts/set_gender/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return {"success": True, "message": "Genre modifié avec succès"}
                else:
                    return {"success": False, "error": f"Erreur API: {data}"}
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur modification genre: {e}"}
    
    # MÉTHODES PUBLIQUES DE L'ÉDITEUR
    
    def get_account_info(self):
        """Récupérer les informations complètes du compte"""
        return self._get_account_info_web(show_info=True)
    
    def email(self, new_email: str, verification_code: str = None):
        """Changer l'email du compte
        
        Args:
            new_email: Nouvel email à définir
            verification_code: Code de vérification (si fourni, on vérifie directement)
        
        Returns:
            dict: Résultat de l'opération
        """
        try:
            # Vérification de la session
            if not self.session or not self.cookies_raw:
                return {"success": False, "error": "Session non configurée. Utilisez setup_cookies() ou connectez-vous d'abord."}
            
            # Si on a un code de vérification, on vérifie directement
            if verification_code:
                return self._verify_email_code(new_email, verification_code)
            
            # Sinon, on commence le processus de changement
            # Étape 1: Récupérer info compte
            result = self._get_account_info_web(show_info=False)
            if not result["success"]:
                return result
            
            # Étape 2: Récupérer tokens Facebook
            result = self._get_account_center_tokens()
            if not result["success"]:
                return result
            
            # Étape 3: Ajouter le nouvel email
            result = self._add_email_mutation(new_email)
            if not result["success"]:
                return result
            
            return {
                "success": True,
                "step": "verification_needed",
                "message": f"Code de vérification envoyé à {new_email}",
                "email": new_email,
                "requires_verification": True
            }
            
        except Exception as e:
            return {"success": False, "error": f"Erreur changement email: {e}"}
    def _navigate_to_security_settings(self):
        """Naviguer vers les paramètres de sécurité et connexion"""
        try:
            if not self.fb_dtsg:
                token_result = self._get_account_center_tokens()
                if not token_result["success"]:
                    return token_result
            
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "x-fb-friendly-name": "FXAccountsCenterNavigationNodeRootQuery",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            payload = {
                "av": self.account_id or "17841478705790642",
                "__user": "0",
                "__a": "1",
                "__req": "f",
                "__hs": "20418.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "MODERATE",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7577002733041206381",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gpn9lR6hG9Rsx5bTaJqRlQGF8OIiu_RFPFBqWOUDDEGl8KyeGFlvnJX9OZLn8AKjFAyl8J5RqIgql4tLXSyKiQabJaLBV4HKFUUOGHytfCnRSLi-nDjUhQXgly8BpopKi8DViGB9HACAhrhp4KECA59KiqmbCKl5KFpoDDyp8S8zUrG-ciy8LyEN126dqXxbQeyp4-uqfzUgxJ1K0l20tCFrwiF5jwcibw05kPxm6aG440Baw1ni441kDwlE4aUbC02mu0mS1zG07rpVRyrAglxo58l5V98-m5by9pd4Axq3CXg6NwXQfgm2wLe1mw5qKUKWGGxadyKFrKmVoKXGle8AXx2uVob-V9ajz999VpGKEcQ2uFqF7FdeFXykiu7ry8b-5HGt2V98mwmGU8EgxaiGirhoxda5kQQQfwABpoV28dVoLhU5x1eGDxG2N08u0gq0aHWKHBGGKFAhAHjDKGAKGqKuUqKVp4hel1VaAle9gGmWAGi8weG6VpF84GE",
                "__hsdp": "glOOMpMt89g5n944G0rqQSi852sW0cja152O71yul0kxbwxIxEBx8V2xkzJw7OohyEwpEo2Xcbdm3UM7-fxy3F336DyFNo4W8xiok4wNwF2EJ7U5iy0Bwj9OcEkBgYo1qxO1Swat0vpy0jA1Dxtwio5gR1Ei0No3Fwdm0n60RS0EocVHw890YwiVE0nmw3_U887y0o20jeK0VE0We6UGU158kyE9EpAg4S0Ck3h09F4x24Ua8ows8aE562ly89omwqU2CwCw6yw65g860jaE12obokw4mwam322m0maXwdyE",
                "__hblp": "05qxC0r-ew29Voom1qQ5EFGl2Hxu2bwyK0t618wDhlwyw_zE4q7E-68lwg969BwDDxa5Uy3m6EmwXJ1e2Tz4dga8fK4UhUK2Z0wDxq8xfy84u14x67EjyEvx2aw9CFU2VQ5o6emip385a58hxfxm10K2SdwCw_wIxyq1mDwrUsw_wjUeo5e2y3q1KwDzVUKawtElwoocEboaU8EepA0EU0JW1vwYzE5y3C0Erwho9U1DU0E20PE1aEWdwiEK1axW1_x61Gw2i81b9E6K6Vk2G1cgjwjEe8eWx21ICwxwsod85ebwGx2m485591232bDxC2G1hwlEmwqU4Wq1gxKawmogwQwww921gw21U2IwDw7YwfWm2Oeyo4Wm19weu0G98aEO",
                "__sjsp": "glORk6s8Mk89gX0hJEgiE1JHgG6YW0cj8162Hb40wwa2",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "25953",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "FXAccountsCenterNavigationNodeRootQuery",
                "server_timestamps": "true",
                "variables": '{"interface":"IG_WEB","node_identifier":"security_and_login"}',
                "doc_id": "24866285072980900"
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"Erreur navigation sécurité: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur navigation: {e}"}

    def _access_two_factor_settings(self):
        """Accéder aux paramètres d'authentification à deux facteurs"""
        try:
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "x-fb-friendly-name": "FXAccountsCenterTwoFactorStartRootQuery",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/password_and_security/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            payload = {
                "av": self.account_id or "17841478705790642",
                "__user": "0",
                "__a": "1",
                "__req": "w",
                "__hs": "20418.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "MODERATE",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7577002733041206381",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gpn9lR6hG9RsDsLsGRHlniGAzaN9QLRFPFBqWOXBVWaBibEzGGlnRXuOsLrROiujFAyl8J5RqIgql4tLXSyKiQabJaLBV4HKFUUOGHytfCnRSLi-nDjUhQXgly8BpopKi8DViGB9HACAhrhp4KECA59KiqmbCKl5KFpoDDyp8S8zUrG-ciy8LyEN126dqXxbQeyp4-uqfzUgxJ1K0l20tCFrwiF5jwcibw05kPxm6aG440Baw1ni441kDwlE4aUbC02mu0mS1zG07rpVRyrAglxo58l5V98-m5by9pd4Axq3CXg6NwXQfgm2wLe1mw5qKUKWGGxadyKFrKmVoKXGle8AXx2uVob-V9ajz999VpGKEcQ2uFqF7FdeFXykiu7ry8b-5HGt2V98mwmGU8EgxaiGirhoxda5kQQQfwABpoV28dVoLhU5x1eGDxG2N08u0gq0aHWKHBGGKFAhAHjDKGAKGqKuUqKVp4hel1VaAle9gGmWAGi8weG6VpF84GE",
                "__hsdp": "glOOMpMt89g5n944G0rp9dAy1gDew34OwhgIxMKcDBg58iU8r8q9oiegEl8Xo1YC4oG86q60KP2Plw-c1_zUowWgMNFUGsm1ey8kC518coagGbh-1kEw9o4Osza59kf60mEswtE2Dg7Sow4V0pUno4C1kdgq4wcm0Wo3lw5Nwdtwa63eqU22gf84Kq05RE0_-221Uw60w4PHweq0ezxKaK0hi58G2q6p41dw9B0Qg2qh8gxe2y68722G1hwBoy2m5E6K0FE9E1EE1xk21w4OG0gC2S5815E2BwMwBw5yKU3oG",
                "__hblp": "05qxC0r-ew29Voom1qQ5EFGl2Hxu2bwyK0t618wDhlwyw_zE4q7E-68lwg969BwDDxa5Uy3m6EmwXJ1e2Tz4dga8fK4UhUK2Z0wDxq8xfy84u14x67EjyEvx2aw9CFU2VQ5o6emip385a58hxfxm10K2SdwCw_wIxyq1mDwrUsw_wjUeo5e2y3q1KwDzVUKawtElwoocEboaU8EepA0EU0JW1vwYzE5y3C0Erwho9U1DU0E20PE1aEWdwiEK1axW1_x61Gw2i81b9E6K6Vk2G1cgjwjEe8eWx21ICwxwsod85ebwGx2m485591232bDxC2G1hwlEmwqU4Wq1gxKawmogwQwww921gw21U2IwDw7YwfWm2Oeyo4Wm19weu0G98aEO",
                "__sjsp": "glORk6s8Mk89gX0hIAgiE1JAAaxLew34OwhgIxMK582ww",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "25953",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "FXAccountsCenterTwoFactorStartRootQuery",
                "server_timestamps": "true",
                "variables": '{"interface":"IG_WEB"}',
                "doc_id": "25224462647146278"
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"Erreur accès 2FA: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur accès 2FA: {e}"}

    def _select_account_for_2fa(self):
        """Sélectionner automatiquement le compte pour l'activation 2FA"""
        try:
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "x-fb-friendly-name": "FXAccountsCenterTwoFactorSelectMethodDialogQuery",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/password_and_security/two_factor/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            payload = {
                "av": self.account_id or "17841478705790642",
                "__user": "0",
                "__a": "1",
                "__req": "15",
                "__hs": "20418.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "MODERATE",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7577002733041206381",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gpn9lR6hG9RsDsLsGRHlniGAzaN9QLRFPFBqWOXBVWaBibEzGGlnRXuOsLrROiujFAyl8J5RqIgql4tLXSyKiQabJaLBV4HKFUUOGHytfCnRSLi-nDjUhQXgly8BpopKi8DViGB9HACAhrhp4KECA59KiqmbCKl5KFpoDDyp8S8zUrG-ciy8LyEN126dqXxbQeyp4-uqfzUgxJ1K0l20tCFrwiF5jwcibw05kPxm6aG440Baw1ni441kDwlE4aUbC02mu0mS1zG07rpVRyrAglxo58l5V98-m5by9pd4Axq3CXg6NwXQfgm2wLe1mw5qKUKWGGxadyKFrKmVoKXGle8AXx2uVob-V9ajz999VpGKEcQ2uFqF7FdeFXykiu7ry8b-5HGt2V98mwmGU8EgxaiGirhoxda5kQQQfwABpoV28dVoLhU5x1eGDxG2N08u0gq0aHWKHBGGKFAhAHjDKGAKGqKuUqKVp4hel1VaAle9gGmWAGi8weG6VpF84GE",
                "__hsdp": "glOOMpMt89g5n944G0rp9dAy1gDew34OwhgIxMKcDBg58iU8r8q9oiegEl8Xorw7mohyEwpEocwxP2PlwOyzzx0mwkHyUowWgMNFUGsm1ey8kC518coagGbh-1kEw82o4Osza59kf60mEswtE2Dg7Sow4V0pUno4C1kdgq4wcm0Wo3lw5Nwdtwa63eqU22gf84Kq05RE0_-221Uw60w4PHweq0ezxKaK0hi58G2q6p41dw9B0Qg2qh8gxe2y68722G1hwBoy2m5E6K0FE9E1EE1xk21w4OG0gC2S5815E2BwMwBw5yKU3oG",
                "__hblp": "05qxC0r-ew29Voom1qQ5EFGl2Hxu2bwxjw7hwi8y7Alposw_zEiwwxa7F8Geyolwg969BwDDxa5Uy3m6EmwXFxe48sUN3k2yi3DxeeHACxu5DxWu5Ey4-8whAfwQx67EjyEvx2uE2pGu0Kt1m1zBACgO1ixi4u4u5o42UboS2q3-2O69E5qu1LxO3-1fwVwkUa8dE6W2ufDyUG1Sxm1kz8cEboaU8EepA0EU0JW1vwYzE5y3C0Erwho9U1DU0E20PE1aEWdwiEK1axW1_x61Gw2i81b9E6K6Vk2G1ch8W1ewUwXG486Oq261NwQwkUK2G49ogwkkA48c8Ku6oaE561mxq1HwjFEbE8oryE5C48d8882gwk80wu0H89U1_8fE2_BwIzEC1eBwio3Dwayi2Gcw",
                "__sjsp": "glORk6s8Mk89gX0hIAgiE1JAAaxLew34OwhgIxMK582ww",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "25953",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "qpl_active_flow_ids": "241970459",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "FXAccountsCenterTwoFactorSelectMethodDialogQuery",
                "server_timestamps": "true",
                "variables": f'{{"account_id":"{self.account_id or "17841478705790642"}","account_type":"INSTAGRAM","interface":"IG_WEB"}}',
                "doc_id": "25273710265555450",
                "fb_api_analytics_tags": '["qpl_active_flow_ids=241970459"]'
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"Erreur sélection compte 2FA: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur sélection compte: {e}"}

    def _generate_totp_key(self):
        """Générer la clé TOTP pour l'authentification à deux facteurs"""
        try:
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "x-fb-friendly-name": "useFXSettingsTwoFactorGenerateTOTPKeyMutation",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/password_and_security/two_factor/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            mutation_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
            
            payload = {
                "av": self.account_id or "17841478705790642",
                "__user": "0",
                "__a": "1",
                "__req": "1h",
                "__hs": "20418.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "MODERATE",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7577002733041206381",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gpn9lR6hG9RsDsLsGRHljaGicG5ahbZqsWpmKzWhup8Gl8KyeGTlOuTsDbSZsADAWp8Bi8ximH4aVkhTOLqaVbgEKQG-nAiFeFXyzaGK9Q-pvnqZbVutfx7jJ1m8ylBxCV8yvBaGkCKiqh5Z5AiWyqgkCV9FoKqVkmWBByuu9AzoyfxKHUNa8y-az448oRHK4LgW9AjVVE-fx26Q6U1k81SqBK1aAle0N8K00lje5ooGEgg2eBGE0lNx10l9U5q12K2Vw2TFkU3tw1p-0lOiqi1zG07rpVRyrAglxo58l5V98-m5by9pd4Axq3CXg6NwXQfgm2wLe1mw5qKUKWGGxadyKFrKmVoKXGle8AXx2uVob-V9ajz999VpGKEcQ2uFqF7FdeFXykiu7ry8b-5HGt2V98mwmGU8EgxaiGirhoxda5kQQQfwABpoV28dVoLhU5x1eGDxG2N08u0gq0aHWKHBGGKFAhAHjDKGAKGqKuUqKVp4hel1VaAle9gGmWAGi8weG6VpF84GE",
                "__hsdp": "glOOMpMt89g5n944G0rp9dAy1gDew34OwhgIxMKcDBg58iU8r8q9oiegEl8Xorw7mohyEwpEocUvP2PlwOyzzx0mwkHgGeyrGbBg84ccl7yFNo4W8xiok4wNwF2EJ7U9Uba820C48eVOcE-il3NwoKp0RxO1Swat0BwiS9FO0xgaQ11g98no4C1kdgq4wikcy41zweC0Ro1so3no2xwPCK5o6N0YwiVE0nmw3_U887y0o20jeK0VE0We6UGU7l09S58G2q6p41dw9B0Qg2qh8gxe2y68727oO15yVEuoy2m5E6K0FE9Eqw4VBwhU1xk21w4OG0gC2S5815E2BwMwBw5yKU3oG",
                "__hblp": "05qxC0r-ew29Voom1qQ5EFGl2Hxu2bwxjw7hwi8y7Alposw_zEiwwxa7F8Geyolwg969BwDDxa5Uy3m6EmwXFxe48sUN3k2yi3DxeeHACxu5DxWu5Ey4-8whAfwQx67EjyEvx2uE2pGu0Kt1m1zBACgO1ixi4u4u5o42UboS2q3-2O69E5qu1LxO3-1fwVwkUa8dE6W2ufDyUG1Sxm1kz8cEboaU8EepA0EU0JW1vwYzE5y3C0Erwho9U1DU0E20PE1aEWdwiEK1axW1_x61Gw2i81b9E6K6Vk2G1ch8W1ewUwXG486Oq261NwQwkUK2G49ogwkkA48c8Ku6oaE561mxq1HwjFEbE8oryE5C48d8882gwk80wu0H89U1_8fE2_BwIzEC1eBwio3Dwayi2Gcw",
                "__sjsp": "glORk6s8Mk89gX0hIAgiE1JAAaxLew34OwhgIxMK582ww",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "25953",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "qpl_active_flow_ids": "241970459",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useFXSettingsTwoFactorGenerateTOTPKeyMutation",
                "server_timestamps": "true",
                "variables": f'{{"input":{{"client_mutation_id":"{mutation_id}","actor_id":"{self.account_id or "17841478705790642"}","account_id":"{self.account_id or "17841478705790642"}","account_type":"INSTAGRAM","device_id":"device_id_fetch_ig_did","fdid":"device_id_fetch_ig_did"}}}}',
                "doc_id": "9837172312995248",
                "fb_api_analytics_tags": '["qpl_active_flow_ids=241970459"]'
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"Erreur génération clé TOTP: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur génération TOTP: {e}"}

    def _get_confirmation_dialog(self):
        """Récupérer le dialogue de confirmation de code"""
        try:
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "x-fb-friendly-name": "FXAccountsCenterTwoFactorConfirmCodeDialogQuery",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/password_and_security/two_factor/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            payload = {
                "av": self.account_id or "17841478705790642",
                "__user": "0",
                "__a": "1",
                "__req": "1m",
                "__hs": "20418.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "MODERATE",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7577002733041206381",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gpn9lR6hG9RsDsLsGRHljaGicG5ahbZqsW8hHE-AnCiaBieyeGTd9XtOsLrROiuhFAGpi8F12IgHBh3YHSyKiQabJaLhehaAWDKacGGUDjVnZtHQLBVQ-4teQ4-8ylBxCV8yvBaGkCKiqh5Z5AiWyqgkCV9FoKqVkmWBByuu9AzoyfxKHUN97y-az448oRHK4LgW9AjVVE-fx26Q6U1k81SqBK1aAle0N8K00lje5ooGEgg2eBGE0lNx10l9U56i12K2Vw2TFkU3tw1p-0g2584qiqi1zG07rpVRyrAglxo58l5V98-m5by9pd4Axq3CXg6NwXQfgm2wLe1mw5qKUKWGGxadyKFrKmVoKXGle8AXx2uVob-V9ajz999VpGKEcQ2uFqF7FdeFXykiu7ry8b-5HGt2V98mwmGU8EgxaiGirhoxda5kQQQfwABpoV28dVoLhU5x1eGDxG2N08u0gq0aHWKHBGGKFAhAHjDKGAKGqKuUqKVp4hel1VaAle9gGmWAGi8weG6VpF84GE",
                "__hsdp": "glOOMpMt89g5n944G0rp9dAy1gDew34OwhgIxMKcDBg58iU8r8q9oiegEl8Xorw7mohyEwpEocUizcNXdm3aaee41q1iJ2EW9KEKl0wgMNkulcx1o4W8xiok4wNwF2EJ7U9Uba820C48eVOcE-il3NwoKp0RxO1Swat0BwiS9FO0xgaQ11g98no4C1kdgq4wikcy41zweC0Ro1so3no2xwPCK5o6N0YwiVE0nmw3_U887y0o20jeK0VE0We6UGU7l09S58G2q6p41dw9B0Qg2qh8gxe2y68727oO15yVEuoy2m5E6K0FE9Eqw4VBwhU1xk21w4OG0gC2S5815E2BwMwBw5yKU3oG",
                "__hblp": "05qxC0r-ew29Voom1qQ5EFGl2Hxu2bwxjw7hwi8y4EJ5mm78fUW4E88ixWiazEC5o42hypo9VUixu8wRxG5EeWojx27ecgR0EAwVUjzGV9EnxpUuDxq8xfy84p3Ud8hxW4UG7UgDG0CqDwbDglwoVp9AcwkEkx7x7xm10K2SdwCw_wIxyq1mDwrUsw_wjUeo5e2y3q1KwDzVUKawtElwl8O3a2S2K2a3Cp0ae0buwnUf8W1owVwa6U4m2u0p-0a0wcW0iGezo4GbwiEuwvUhwqE0Ay0iOq1HxKl0Gwj4iewjEe8eWx21ICwxwsod85ebwGx2m485591232bDxC2G1hwlEmwqU4Wq2W266UG1px23i220A852087waO2u0vO3W0LVob8W9wjFo4C0VU2EAwGz8",
                "__sjsp": "glORk6s8Mk89gX0hIAgiE1JAAaxLew34OwhgIxMK582ww",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "25953",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "qpl_active_flow_ids": "241970459",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "FXAccountsCenterTwoFactorConfirmCodeDialogQuery",
                "server_timestamps": "true",
                "variables": '{"interface":"IG_WEB"}',
                "doc_id": "31614677328180560",
                "fb_api_analytics_tags": '["qpl_active_flow_ids=241970459"]'
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"Erreur dialogue confirmation: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur dialogue: {e}"}

    def _enable_totp_with_code(self, verification_code: str):
        """Activer TOTP avec le code de vérification"""
        try:
            headers = {
                "host": "accountscenter.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                "x-fb-friendly-name": "useFXSettingsTwoFactorEnableTOTPMutation",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-model": '""',
                "x-asbd-id": "359341",
                "x-fb-lsd": self.lsd,
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "content-type": "application/x-www-form-urlencoded",
                "sec-ch-ua-platform-version": '"10.0.0"',
                "accept": "*/*",
                "origin": "https://accountscenter.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://accountscenter.instagram.com/password_and_security/two_factor/",
                "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "cookie": self.cookies_raw
            }
            
            mutation_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
            
            payload = {
                "av": self.account_id or "17841478705790642",
                "__user": "0",
                "__a": "1",
                "__req": "1r",
                "__hs": "20418.HYP:accounts_center_pkg.2.1...0",
                "dpr": "1",
                "__ccg": "MODERATE",
                "__rev": self.rev,
                "__s": f"{random.randint(100000, 999999)}:{random.randint(100000, 999999)}:{random.randint(100000, 999999)}",
                "__hsi": self.hsi or "7577002733041206381",
                "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W099w8G1Dz81s8hwnU2lwv89k2C1Fwc60D82IzXwae4UaEW0Loco5G0zK1swa-0raazo7u0zEiwaG1LwTwNw4mwr86C1nw4xxW1owmU3yw",
                "__csr": "gpn9lR6hG9RsDsLsGRHljaGicG5ahlZqsW8hHE-AnCiaBieyeGTd9XtOsLrROiuhFAGpi8F12IgHBh3YHSyKiQabJaLhehaAWDKacGGUDjVnZtHQLBVQ-4teQ4-8ylBxCV8yvBaGkCKiqh5Z5AiWyqgkCV9FoKqVkmWBByuu9AzoyfxKHUN97y-az448oRHK4LgW9AjVVE-fx26Q6U1k81SqBK1aAle0N8K00lje5ooGEgg2eBGE0lNx10l9U56i12K2Vw2TFkU3tw1p-0g2584qiqi1zG07rpVRyrAglxo58l5V98-m5by9pd4Axq3CXg6NwXQfgm2wLe1mw5qKUKWGGxadyKFrKmVoKXGle8AXx2uVob-V9ajz999VpGKEcQ2uFqF7FdeFXykiu7ry8b-5HGt2V98mwmGU8EgxaiGirhoxda5kQQQfwABpoV28dVoLhU5x1eGDxG2N08u0gq0aHWKHBGGKFAhAHjDKGAKGqKuUqKVp4hel1VaAle9gGmWAGi8weG6VpF84GE",
                "__hsdp": "glOOMpMt89g5n944G0rp9dAy1gDew34OwhgIxMKcDBg58iU8r8q9oiegEl8Xorw7mohyEwpEocUizcNXdm3aaee41q1iJ2EW9KEKl0wgMNkulcx1o4W8xiok4wNwF2EJ7U9Uba820C48eVOcE-il3NwoKp0RxO1Swat0BwiS9FO0xgaQ11g98no4C1kdgq4wikcy41zweC0Ro1so3no2xwPCK5o6N0YwiVE0nmw3_U887y0o20jeK0VE0We6UGU7l09S58G2q6p41dw9B0Qg2qh8gxe2y68727oO15yVEuoy2m5E6K0FE9Eqw4VBwhU1xk21w4OG0gC2S5815E2BwMwBw5yKU3oG",
                "__hblp": "05qxC0r-ew29Voom1qQ5EFGl2Hxu2bwxjw7hwi8y4EJ5mm78fUW4E88ixWiazEC5o42hypo9VUixu8wRxG5EeWojx27ecgR0EAwVUjzGV9EnxpUuDxq8xfy84p3Ud8hxW4UG7UgDG0CqDwbDglwoVp9AcwkEkx7x7xm10K2SdwCw_wIxyq1mDwrUsw_wjUeo5e2y3q1KwDzVUKawtElwl8O3a2S2K2a3Cp0ae0buwnUf8W1owVwa6U4m2u0p-0a0wcW0iGezo4GbwiEuwvUhwqE0Ay0iOq1HxKl0Gwj4iewjEe8eWx21ICwxwsod85ebwGx2m485591232bDxC2G1hwlEmwqU4Wq2W266UG1px23i220A852087waO2u0vO3W0LVob8W9wjFo4C0VU2EAwGz8",
                "__sjsp": "glORk6s8Mk89gX0hIAgiE1JAAaxLew34OwhgIxMK582ww",
                "__comet_req": "24",
                "fb_dtsg": self.fb_dtsg,
                "jazoest": "25953",
                "lsd": self.lsd,
                "__spin_r": self.rev,
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "qpl_active_flow_ids": "241970459",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "useFXSettingsTwoFactorEnableTOTPMutation",
                "server_timestamps": "true",
                "variables": f'{{"input":{{"client_mutation_id":"{mutation_id}","actor_id":"{self.account_id or "17841478705790642"}","account_id":"{self.account_id or "17841478705790642"}","account_type":"INSTAGRAM","verification_code":"{verification_code}","device_id":"device_id_fetch_ig_did","fdid":"device_id_fetch_ig_did"}}}}',
                "doc_id": "29164158613231327",
                "fb_api_analytics_tags": '["qpl_active_flow_ids=241970459"]'
            }
            
            response = self.session.post(
                "https://accountscenter.instagram.com/api/graphql/",
                headers=headers,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"Erreur activation TOTP: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur activation TOTP: {e}"}

    def enable_2fa(self, verification_code: str = None):
        """Activer l'authentification à deux facteurs
        
        Args:
            verification_code: Code à 6 chiffres généré par l'app authenticator (optionnel pour première étape)
        
        Returns:
            dict: Résultat de l'opération avec 'success' et 'data'/'error'
        """
        try:
            # Vérification de la session
            if not self.session or not self.cookies_raw:
                return {"success": False, "error": "Session non configurée. Utilisez setup_cookies() ou connectez-vous d'abord."}
            
            # Si un code de vérification est fourni, on finalise directement l'activation
            if verification_code:
                return self._finalize_2fa_activation(verification_code)
            
            # Étape 1: Naviguer vers les paramètres de sécurité
            security_result = self._navigate_to_security_settings()
            if not security_result["success"]:
                return security_result
            
            # Étape 2: Accéder aux paramètres 2FA
            totp_result = self._access_two_factor_settings()
            if not totp_result["success"]:
                return totp_result
            
            # Vérifier si 2FA est déjà activé
            totp_data = totp_result.get("data", {})
            accounts_status = totp_data.get("data", {}).get("fxcal_settings", {}).get("node", {}).get("accounts_with_two_factor_status_v2", [])
            
            if accounts_status:
                for account in accounts_status:
                    if account.get("is_two_factor_enabled", False):
                        return {"success": False, "error": "L'authentification à deux facteurs est déjà activée pour ce compte"}
            
            # Étape 3: Sélectionner le compte
            select_result = self._select_account_for_2fa()
            if not select_result["success"]:
                return select_result
            
            # Étape 4: Générer la clé TOTP
            totp_key_result = self._generate_totp_key()
            if not totp_key_result["success"]:
                return totp_key_result
            
            # Extraire les informations de la clé TOTP
            totp_key_data = totp_key_result.get("data", {})
            totp_info = totp_key_data.get("data", {}).get("xfb_two_factor_generate_totp_key", {})
            
            if totp_info.get("success") and "totp_key" in totp_info:
                key_text = totp_info["totp_key"].get("key_text", "")
                qr_code_uri = totp_info["totp_key"].get("qr_code_uri", "")
                
                return {
                    "success": True,
                    "step": "setup_required",
                    "message": "Clé TOTP générée. Configurez votre application d'authentification",
                    "totp_key": key_text,
                    "qr_code_uri": qr_code_uri,
                    "requires_verification": True,
                    "instructions": [
                        "1. Ouvrez votre application d'authentification (Google Authenticator, Authy, etc.)",
                        "2. Ajoutez un nouveau compte en scannant le QR code ou en saisissant la clé manuellement:",
                        f"   Clé: {key_text}",
                        "3. Une fois configuré, appelez à nouveau enable_2fa() avec le code à 6 chiffres généré"
                    ]
                }
            else:
                return {"success": False, "error": "Impossible de générer la clé TOTP"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur activation 2FA: {e}"}

    def _finalize_2fa_activation(self, verification_code: str):
        """Finaliser l'activation 2FA avec le code de vérification"""
        try:
            # Valider le format du code
            if not verification_code or not verification_code.isdigit() or len(verification_code) != 6:
                return {"success": False, "error": "Le code de vérification doit contenir exactement 6 chiffres"}
            
            # Étape 5: Récupérer le dialogue de confirmation
            dialog_result = self._get_confirmation_dialog()
            if not dialog_result["success"]:
                return dialog_result
            
            # Étape 6: Activer TOTP avec le code
            activation_result = self._enable_totp_with_code(verification_code)
            if not activation_result["success"]:
                return activation_result
            
            # Analyser la réponse
            activation_data = activation_result.get("data", {})
            totp_enable_result = activation_data.get("data", {}).get("xfb_two_factor_enable_totp", {})
            
            # Vérifier si le code est incorrect
            if totp_enable_result.get("__typename") == "XFBFXSettingsTwoFactorSetupMutationError":
                error_message = totp_enable_result.get("error_message", "Code incorrect")
                return {
                    "success": False, 
                    "error": error_message,
                    "retry": True,
                    "message": "Code incorrect. Veuillez réessayer avec le nouveau code généré par votre application"
                }
            
            # Vérifier le succès
            if (totp_enable_result.get("__typename") == "FXCALSettingsMutationReturnDataSuccess" and 
                totp_enable_result.get("success", False)):
                return {
                    "success": True,
                    "message": "Authentification à deux facteurs activée avec succès !",
                    "data": {
                        "2fa_enabled": True,
                        "method": "TOTP",
                        "backup_codes_recommended": True
                    }
                }
            else:
                return {"success": False, "error": "Erreur lors de l'activation finale"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur finalisation 2FA: {e}"}
    
    def name(self, new_name: str):
        """Changer le nom complet du compte"""
        return self._edit_basic_profile(first_name=new_name)
    
    def username(self, new_username: str):
        """Changer le nom d'utilisateur"""
        return self._edit_basic_profile(username=new_username)
    
    def bio(self, new_bio: str):
        """Changer la biographie"""
        return self._edit_basic_profile(biography=new_bio)
    
    def website(self, new_url: str):
        """Changer l'URL externe"""
        return self._edit_basic_profile(external_url=new_url)
    
    def gender(self, new_gender: int):
        """Changer le genre (1=homme, 2=femme, 3=non spécifié)"""
        if new_gender not in [1, 2, 3]:
            return {"success": False, "error": "Genre invalide. Utilisez 1 (homme), 2 (femme) ou 3 (non spécifié)"}
        
        return self._edit_gender(new_gender)



class InstagramClient:
    """Client Instagram complet avec toutes les fonctionnalités"""
    
    def __init__(self, session_data: dict = None):
        # Validation licence obligatoire
        if not validate_license():
            raise LicenseError("Ce script n'est pas autorisé à utiliser cette bibliothèque. Veuillez contacter le créateur via: 0389561802 ou https://t.me/Kenny5626")
        
        self.auth = InstagramAuth()
        self.session_data = session_data or {}
        self.api = None
        self._editor = None
        
        if session_data:
            self.auth.session_data = session_data
            # Restaurer cookies
            if "cookies" in session_data:
                for name, value in session_data["cookies"].items():
                    self.auth.session.cookies.set(name, value)
            
            # Initialiser API
            user_data = session_data.get("user_data", {}) or session_data.get("logged_in_user", {})
            auth_token = session_data.get("authorization_data", {}).get("authorization_header", "") or session_data.get("authorization", "")
            user_id = user_data.get("user_id", "") or session_data.get("account_id", "")
            
            if user_id:
                self.api = InstagramAPI(self.auth.session, self.auth.device_manager.device_info, user_id, auth_token, client=self)
    
    def login_with_cookies(self, cookies_string: str) -> dict:
        """Connexion Instagram via cookies existants"""
        return self.auth.login_with_cookies(cookies_string)
    # Dans client.py, ajoutez cette méthode dans la classe InstagramClient :
    def signup(self) -> 'InstagramSignup':
        """Créer un gestionnaire d'inscription Instagram"""
        from .auth.authentication import InstagramSignup
        return InstagramSignup(client=self)

    
    
    
    # MÉTHODES INTERNES POUR IDs DIRECTS
    def _like_post_by_id_internal(self, media_id: str) -> dict:
        """Liker un post par media ID direct - COMPLET avec tous headers"""
        try:
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            # Données COMPLÈTES pour like
            like_data = {
                "is_2m_enabled": "false",
                "delivery_class": "organic", 
                "tap_source": "button",
                "media_id": media_id,
                "radio_type": self._get_radio_type(),
                "_uid": user_id,
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "nav_chain": self._get_dynamic_nav_chain("like"),
                "is_from_swipe": "false",
                "mezql_token": "",
                "is_carousel_bumped_post": "false", 
                "floating_context_items": "[]",
                "container_module": "feed_short_url",
                "feed_position": "0"
            }
            
            signed_body = InstagramEncryption.create_signed_body(like_data)
            
            # Headers COMPLETS exactement comme votre exemple
            bandwidth_data = self._get_bandwidth_test_data()
            salt_ids = self._get_salt_ids()
            device_headers = self._get_device_specific_headers()
            ig_headers = self._get_ig_headers()
            app_net_session = self._get_app_net_session_data()
            
            headers = {
                "accept-language": "fr-FR, en-US",
                "authorization": self._get_auth_token(),
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": user_id,
                "ig-u-ds-user-id": user_id,
                "ig-u-rur": ig_headers.get("ig-u-rur", f"CLN,{user_id},{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}"),
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
                "x-bloks-prism-colors-enabled": "true",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-gray-red": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "true",
                "x-bloks-prism-indigo-link-version": "1",
                "x-bloks-version-id": self.session_data.get("session_metadata", {}).get("bloks_version_id", "422d0c0ead50c1ae8a294e5eba90b30255468f80488fcdcdc61c4c1a193f7fa1"),
                "x-fb-client-ip": "True",
                "x-fb-connection-type": self._get_connection_type_headers()["x-fb-connection-type"],
                "x-fb-friendly-name": f"IgApi: media/{media_id}/like/",
                "x-fb-network-properties": self._get_fb_network_properties(),
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": device_headers["x-ig-android-id"],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": bandwidth_data["speed_kbps"],
                "x-ig-bandwidth-totalbytes-b": bandwidth_data["total_bytes"],
                "x-ig-bandwidth-totaltime-ms": bandwidth_data["total_time_ms"],
                "x-ig-client-endpoint": "ShortUrlFeedFragment:feed_short_url",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": self._get_connection_type_headers()["x-ig-connection-type"],
                "x-ig-device-id": device_headers["x-ig-device-id"],
                "x-ig-device-languages": f'{{"system_languages":"{self.session_data.get("locale", "fr_FR")}"}}',
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.session_data.get("uuids", {}).get("client_session_id", str(uuid.uuid4())),
                "x-ig-is-foldable": "false",
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": self._get_dynamic_nav_chain("like"),
                "x-ig-salt-ids": f"{salt_ids[0]},{salt_ids[1]}" if len(salt_ids) >= 2 else str(salt_ids[0]) if salt_ids else "220140399,220145826",
                "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
                "x-ig-www-claim": ig_headers.get("x-ig-www-claim", "hmac.AR0gigjvYfXDP3sCtKHklnUuIvadPjHaUGCxH3vFP3G_enq9"),
                "x-mid": self.get_x_mid(),
                "x-meta-zca": self._generate_meta_zca(),
                "x-pigeon-rawclienttime": str(time.time()),
                "x-pigeon-session-id": self._get_pigeon_session_id(),
                "x-tigon-is-retry": "False",
                "user-agent": device_headers["user-agent"],
                "x-fb-appnetsession-nid": app_net_session["nid"],
                "x-fb-appnetsession-sid": app_net_session["sid"],
                "x-fb-conn-uuid-client": self._get_conn_uuid_client(),
                "x-fb-http-engine": "Tigon/MNS/TCP",
                "x-fb-rmd": self._get_fb_rmd_state(),
                "x-fb-tasos-experimental": "1",
                "x-fb-tasos-td-config": "prod_signal:1"
            }
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/media/{media_id}/like/",
                headers=headers,
                data={"signed_body": signed_body, "d": "0"},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": "Ce media a ete supprime"}
    
    
    def _comment_post_by_id_internal(self, media_id: str, comment_text: str) -> dict:
        """Commenter un post par media ID direct (méthode interne) - RAPIDE"""
        try:
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            # Utiliser l'approche web directe avec shortcode
            device_settings = self.session_data.get("device_settings", {})
            android_release = device_settings.get('android_release', '12')
            model = device_settings.get('model', 'SM-G991B')
            
            real_user_agent = f"Mozilla/5.0 (Linux; Android {android_release}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
            
            # Convertir media_id en shortcode pour construire l'URL
            shortcode = self.media_id_to_shortcode(media_id)
            media_url = f"https://www.instagram.com/p/{shortcode}/"
            
            web_response = self.auth.session.get(
                media_url,
                headers={"user-agent": real_user_agent},
                timeout=10
            )
            
            if web_response.status_code == 200:
                web_content = InstagramEncryption.safe_decode_response(web_response)
                
                csrf_match = re.search(r'"csrf_token":"([^"]+)"', web_content)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    
                    web_comment_data = {
                        "comment_text": comment_text,
                        "replied_to_comment_id": "",
                        "media_id": media_id
                    }
                    
                    web_headers = {
                        "accept": "*/*",
                        "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                        "content-type": "application/x-www-form-urlencoded",
                        "user-agent": real_user_agent,
                        "x-csrftoken": csrf_token,
                        "x-ig-app-id": "567067343352427",
                        "x-ig-www-claim": self.session_data.get("ig_headers", {}).get("x-ig-www-claim", "0"),
                        "x-requested-with": "XMLHttpRequest",
                        "referer": media_url,
                        "origin": "https://www.instagram.com"
                    }
                    
                    cookies = self.session_data.get("cookies", {})
                    cookies["csrftoken"] = csrf_token
                    
                    for name, value in cookies.items():
                        self.auth.session.cookies.set(name, value)
                    
                    response = self.auth.session.post(
                        f"https://www.instagram.com/api/v1/web/comments/{media_id}/add/",
                        headers=web_headers,
                        data=web_comment_data,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        parsed_data = InstagramEncryption.safe_parse_json(response)
                        
                        if InstagramEncryption.is_success_response(response, parsed_data):
                            return {"success": True, "data": parsed_data}
                        else:
                            return self.handle_action_error(response.status_code, parsed_data, 
                                                         InstagramEncryption.safe_decode_response(response))
                    else:
                        if response.status_code == 400:
                            parsed_data = InstagramEncryption.safe_parse_json(response)
                            return self.handle_action_error(response.status_code, parsed_data, 
                                                         InstagramEncryption.safe_decode_response(response))
                        
                        return self.handle_http_error(response.status_code, 
                                                    InstagramEncryption.safe_decode_response(response))
                else:
                    return {"success": False, "error": "Ce média a été supprimé"}
            else:
                return {"success": False, "error": "Ce media a ete supprime"}
                
        except Exception as e:
            return {"success": False, "error": "Ce media a ete supprime"}

    
    def media_id_to_shortcode(self, media_id: str) -> str:
        """Convertir media ID en shortcode Instagram"""
        try:
            # Nettoyer le media_id (enlever owner_id si présent)
            clean_media_id = media_id.split('_')[0] if '_' in media_id else media_id
            
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            base = len(alphabet)
            id_num = int(clean_media_id)
            
            shortcode = ""
            while id_num > 0:
                shortcode = alphabet[id_num % base] + shortcode
                id_num //= base
            
            return shortcode
            
        except Exception:
            return "invalid_shortcode"
    def _follow_user_by_id_internal(self, user_id: str) -> dict:
        """Suivre un utilisateur par user ID direct - COMPLET avec tous headers"""
        try:
            current_user_id = self._get_user_id_from_session()
            if not current_user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            # Données COMPLÈTES pour follow
            follow_data = {
                "include_follow_friction_check": "1",
                "user_id": user_id,
                "radio_type": self._get_radio_type(),
                "_uid": current_user_id,
                "device_id": self._get_device_specific_headers()["x-ig-android-id"],
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "nav_chain": self._get_dynamic_nav_chain("follow"),
                "container_module": "profile"
            }
            
            signed_body = InstagramEncryption.create_signed_body(follow_data)
            
            # Headers COMPLETS exactement comme votre exemple
            bandwidth_data = self._get_bandwidth_test_data()
            device_headers = self._get_device_specific_headers()
            ig_headers = self._get_ig_headers()
            app_net_session = self._get_app_net_session_data()
            
            headers = {
                "accept-language": "fr-FR, en-US",
                "authorization": self._get_auth_token(),
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": current_user_id,
                "ig-u-ds-user-id": current_user_id,
                "ig-u-rur": ig_headers.get("ig-u-rur", f"CLN,{current_user_id},{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}"),
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
                "x-bloks-prism-colors-enabled": "true",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-gray-red": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "true",
                "x-bloks-prism-indigo-link-version": "1",
                "x-bloks-version-id": self.session_data.get("session_metadata", {}).get("bloks_version_id", "422d0c0ead50c1ae8a294e5eba90b30255468f80488fcdcdc61c4c1a193f7fa1"),
                "x-fb-client-ip": "True",
                "x-fb-connection-type": self._get_connection_type_headers()["x-fb-connection-type"],
                "x-fb-friendly-name": f"IgApi: friendships/create/{user_id}/",
                "x-fb-network-properties": self._get_fb_network_properties(),
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": device_headers["x-ig-android-id"],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": bandwidth_data["speed_kbps"],
                "x-ig-bandwidth-totalbytes-b": bandwidth_data["total_bytes"],
                "x-ig-bandwidth-totaltime-ms": bandwidth_data["total_time_ms"],
                "x-ig-client-endpoint": "empty",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": self._get_connection_type_headers()["x-ig-connection-type"],
                "x-ig-device-id": device_headers["x-ig-device-id"],
                "x-ig-device-languages": f'{{"system_languages":"{self.session_data.get("locale", "fr_FR")}"}}',
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.session_data.get("uuids", {}).get("client_session_id", str(uuid.uuid4())),
                "x-ig-is-foldable": "false",
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": self._get_dynamic_nav_chain("follow"),
                "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
                "x-ig-www-claim": ig_headers.get("x-ig-www-claim", "hmac.AR0gigjvYfXDP3sCtKHklnUuIvadPjHaUGCxH3vFP3G_enq9"),
                "x-mid": self.get_x_mid(),
                "x-meta-zca": self._generate_meta_zca(),
                "x-pigeon-rawclienttime": str(time.time()),
                "x-pigeon-session-id": self._get_pigeon_session_id(),
                "x-tigon-is-retry": "False",
                "user-agent": device_headers["user-agent"],
                "x-fb-appnetsession-nid": app_net_session["nid"],
                "x-fb-appnetsession-sid": app_net_session["sid"],
                "x-fb-conn-uuid-client": self._get_conn_uuid_client(),
                "x-fb-http-engine": "Tigon/MNS/TCP",
                "x-fb-rmd": self._get_fb_rmd_state(),
                "x-fb-tasos-experimental": "1",
                "x-fb-tasos-td-config": "prod_signal:1"
            }
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/friendships/create/{user_id}/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": "Utilisateur introuvable"}
    
    def login(self, username: str, password: str) -> dict:
        """Connexion Instagram avec gestion 2FA complète"""
        return self.auth.login(username, password)
    
    def load_session(self, username: str) -> dict:
        """Charger session depuis le disque"""
        session_data = self.auth.load_session(username)
        if session_data:
            self.session_data = session_data
            
            # Initialiser API avec session chargée
            user_data = session_data.get("user_data", {}) or session_data.get("logged_in_user", {})
            auth_token = session_data.get("authorization_data", {}).get("authorization_header", "") or session_data.get("authorization", "")
            user_id = user_data.get("user_id", "") or session_data.get("account_id", "")
            
            if user_id:
                self.api = InstagramAPI(self.auth.session, self.auth.device_manager.device_info, user_id, auth_token, client=self)
        
        return session_data
    
    def dump_session(self, username: str = None) -> dict:
        """Sauvegarder la session actuelle"""
        if not username and self.session_data:
            # Récupérer username depuis session_data
            user_data = self.session_data.get("user_data", {}) or self.session_data.get("logged_in_user", {})
            username = user_data.get("username") or self.session_data.get("account_username")
        
        if username and self.session_data:
            user_data = self.session_data.get("user_data", {}) or self.session_data.get("logged_in_user", {})
            # Utiliser _save_session_fixed de auth
            self.auth._save_session_fixed(username, self.session_data, user_data)
            return self.session_data
        
        return {}
    
    def get_x_mid(self) -> str:
        """Récupérer x-mid depuis le device manager"""
        return self.auth.device_manager.get_x_mid()
    
    def _get_username_from_session(self) -> str:
        """Récupérer le username depuis la session"""
        user_data = self.session_data.get("user_data", {}) or self.session_data.get("logged_in_user", {})
        username = user_data.get("username")
        
        if username and username != "":
            return username
        
        auth_data = self.session_data.get("authorization_data", {})
        username = auth_data.get("username")
        if username and username != "":
            return username
        
        account_username = self.session_data.get("account_username")
        if account_username and account_username != "":
            return account_username
        
        return "user_unknown"
    
    def _get_user_id_from_session(self) -> str:
        """Récupérer user ID depuis la session"""
        user_data = self.session_data.get("user_data", {}) or self.session_data.get("logged_in_user", {})
        user_id = user_data.get("user_id")
        
        if user_id:
            return str(user_id)
        
        auth_data = self.session_data.get("authorization_data", {})
        user_id = auth_data.get("ds_user_id")
        
        if user_id:
            return str(user_id)
        
        return "user_id_unknown"
    
    def _get_auth_token(self) -> str:
        """Récupérer token d'autorisation"""
        auth_data = self.session_data.get("authorization_data", {})
        auth_header = auth_data.get("authorization_header")
        
        if auth_header and "Bearer" in auth_header:
            return auth_header
        
        auth_token = self.session_data.get("authorization")
        if auth_token and "Bearer" in auth_token:
            return auth_token
        
        # Construire token basique si manquant
        user_id = self._get_user_id_from_session()
        sessionid = self.session_data.get("sessionid") or self.session_data.get("cookies", {}).get("sessionid")
        
        if sessionid:
            if '%3A' not in sessionid:
                sessionid = urllib.parse.quote(sessionid)
            
            token_data = {
                "ds_user_id": user_id,
                "sessionid": sessionid
            }
            
            encoded = base64.b64encode(json.dumps(token_data, separators=(',', ':')).encode()).decode()
            return f"Bearer IGT:2:{encoded}"
        
        return ""
    
    def _get_bandwidth_test_data(self) -> dict:
        """Récupérer données de test de bande passante depuis la session"""
        session_meta = self.session_data.get("session_metadata", {})
        bandwidth_data = session_meta.get("bandwidth_test_data", {})
        
        if bandwidth_data:
            return {
                "speed_kbps": str(int(bandwidth_data.get("speed_kbps", 2000))),
                "total_bytes": str(bandwidth_data.get("total_bytes", 1000000)),
                "total_time_ms": str(bandwidth_data.get("total_time_ms", 1000))
            }
        
        # Valeurs par défaut
        return {
            "speed_kbps": "2000",
            "total_bytes": "1000000", 
            "total_time_ms": "1000"
        }
    
    def _get_salt_ids(self) -> list:
        """Récupérer salt IDs depuis la session"""
        session_meta = self.session_data.get("session_metadata", {})
        salt_ids = session_meta.get("salt_ids", [])
        
        if salt_ids and len(salt_ids) >= 2:
            return salt_ids
        
        # Valeurs par défaut
        return [220145826, 220140399]
    
    def _get_pigeon_session_id(self) -> str:
        """Récupérer ou générer pigeon session ID"""
        session_meta = self.session_data.get("session_metadata", {})
        pigeon_id = session_meta.get("pigeon_session_id")
        
        if pigeon_id:
            return pigeon_id
        
        # Générer nouveau
        return f"UFS-{str(uuid.uuid4())}-1"
    
    def _get_conn_uuid_client(self) -> str:
        """Récupérer ou générer conn uuid client"""
        session_meta = self.session_data.get("session_metadata", {})
        conn_uuid = session_meta.get("conn_uuid_client")
        
        if conn_uuid:
            return conn_uuid
        
        # Générer nouveau
        return str(uuid.uuid4()).replace('-', '')[:32]
    
    def _get_network_type(self) -> str:
        """Détecter le type de réseau actuel avec ifconfig"""
        try:
            import subprocess
            
            # Exécuter ifconfig pour détecter les interfaces
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
            output = result.stdout
            
            # Vérifier si wlan0 est présent et UP
            if 'wlan0:' in output and 'UP' in output:
                return "WIFI"
            # Vérifier autres interfaces WiFi possibles
            elif any(wifi_if in output for wifi_if in ['wlan1:', 'wifi0:', 'wlp']):
                return "WIFI"
            # Vérifier interfaces cellulaires/mobile
            elif any(cell_if in output for cell_if in ['ccmni', 'rmnet', 'ppp', 'mobile']):
                return "CELLULAR"
            else:
                # Par défaut si aucune interface détectée
                return "CELLULAR"
                
        except Exception:
            # En cas d'erreur, par défaut mobile
            return "CELLULAR"
    
    def _get_radio_type(self) -> str:
        """Obtenir type radio basé sur le réseau détecté"""
        network_type = self._get_network_type()
        
        if network_type == "WIFI":
            return "wifi-none"
        else:
            return "lte"
    
    def _get_connection_type_headers(self) -> dict:
        """Obtenir headers liés au type de connexion détecté"""
        network_type = self._get_network_type()
        
        return {
            "x-fb-connection-type": network_type,
            "x-ig-connection-type": network_type
        }
    
    def _get_device_specific_headers(self) -> dict:
        """Obtenir headers spécifiques au device depuis la session SANS JAMAIS GÉNÉRER"""
        device_settings = self.session_data.get("device_settings", {})
        
        if not device_settings:
            # Fallback sur device_info du device manager
            device_info = self.auth.device_manager.device_info
            return {
                "x-ig-android-id": device_info.get('android_id', ''),
                "x-ig-device-id": device_info.get('device_uuid', ''),
                "user-agent": device_info.get('user_agent', '')  # User-Agent WEB comme fallback
            }
        
        # Récupérer IDs depuis uuids de la session
        uuids = self.session_data.get("uuids", {})
        android_id = uuids.get("device_id", "")
        device_uuid = uuids.get("uuid", "")
        
        # UTILISER LE USER-AGENT MOBILE STOCKÉ DANS LA SESSION
        # 1. D'abord chercher user_agent_mobile depuis session_data directement
        user_agent_mobile = self.session_data.get('user_agent_mobile', '')
        
        # 2. Si pas trouvé, chercher dans device_settings
        if not user_agent_mobile:
            user_agent_mobile = device_settings.get('user_agent_mobile', '')
        
        # 3. Si pas trouvé, chercher dans device_info de la session
        if not user_agent_mobile:
            device_info_session = self.session_data.get('device_info', {})
            user_agent_mobile = device_info_session.get('user_agent_mobile', '')
        
        # 4. JAMAIS GÉNÉRER - Si pas d'user-agent mobile, utiliser user-agent web comme fallback
        if not user_agent_mobile:
            user_agent_mobile = device_settings.get('user_agent', '') or self.session_data.get('user_agent', '')
        
        # 5. Si vraiment rien trouvé, fallback minimal SANS GÉNÉRATION
        if not user_agent_mobile:
            user_agent_mobile = "Instagram 307.0.0.34.111 Android (14/14; 320dpi; 720x1280; samsung; SM-G991B; z3q; mt6989; en_US; 370711637)"
        
        return {
            "x-ig-android-id": android_id,
            "x-ig-device-id": device_uuid,
            "user-agent": user_agent_mobile  # TOUJOURS utiliser le user-agent mobile de la session
        }
    
    def _get_ig_headers(self) -> dict:
        """Récupérer headers IG depuis la session"""
        ig_headers = self.session_data.get("ig_headers", {})
        
        headers = {}
        
        # x-ig-www-claim
        www_claim = ig_headers.get("x-ig-www-claim")
        if www_claim:
            headers["x-ig-www-claim"] = www_claim
        
        # ig-u-ds-user-id
        user_id = self._get_user_id_from_session()
        headers["ig-u-ds-user-id"] = user_id
        headers["ig-intended-user-id"] = user_id
        
        # ig-u-rur
        ig_u_rur = ig_headers.get("ig-u-rur")
        if ig_u_rur:
            headers["ig-u-rur"] = ig_u_rur
        else:
            # Générer ig-u-rur basique
            timestamp = int(time.time() + 30 * 24 * 3600)  # 30 jours
            random_hash = str(uuid.uuid4()).replace('-', '')[:40]
            headers["ig-u-rur"] = f"LLA,{user_id},{timestamp}:01fe{random_hash}"
        
        return headers
    
    def _generate_meta_zca(self) -> str:
        """Générer x-meta-zca dynamique avec données réelles et type réseau"""
        import hashlib
        import secrets
        import base64
        
        try:
            # Timestamp actuel
            current_time = str(int(time.time() * 1000))
            
            # Générer hash unique basé sur timestamp + device + user + réseau
            device_headers = self._get_device_specific_headers()
            user_id = self._get_user_id_from_session()
            network_type = self._get_network_type()
            hash_data = f"{current_time}{device_headers.get('x-ig-device-id', '')}{user_id}{network_type}"
            hash_value = hashlib.sha256(hash_data.encode()).digest()
            hash_b64 = base64.b64encode(hash_value).decode()[:43]
            
            # Générer nonce aléatoire (24 caractères base64)
            key_nonce = base64.b64encode(secrets.token_bytes(18)).decode()
            
            # Détecter niveau batterie réel ou simuler selon réseau
            battery_level = self._get_battery_level()
            battery_status = self._get_battery_status()
            
            # Ajuster batterie selon type réseau (mobile consomme plus)
            if network_type == "CELLULAR":
                battery_level = max(battery_level - random.randint(5, 15), 20)
            
            # Structure ZCA complète avec info réseau
            zca_data = {
                "android": {
                    "aka": {
                        "dataToSign": json.dumps({
                            "time": current_time,
                            "hash": hash_b64
                        }, separators=(',', ':')),
                        "keyNonce": key_nonce,
                        "errors": ["KEYSTORE_TOKEN_RETRIEVAL_ERROR"]
                    },
                    "gpia": {
                        "token": "",
                        "errors": ["PLAY_INTEGRITY_DISABLED_BY_CONFIG"]
                    },
                    "payload": {
                        "plugins": {
                            "bat": {
                                "sta": battery_status,
                                "lvl": battery_level
                            },
                            "sct": {},
                            "net": {
                                "type": network_type.lower()
                            }
                        }
                    }
                }
            }
            
            # Encoder en base64
            json_str = json.dumps(zca_data, separators=(',', ':'))
            encoded = base64.b64encode(json_str.encode()).decode()
            
            return encoded
            
        except Exception as e:
            # Fallback avec données minimales mais dynamiques selon réseau
            current_time = str(int(time.time() * 1000))
            network_type = self._get_network_type()
            hash_fallback = hashlib.sha256(f"{current_time}{network_type}{random.randint(1000, 9999)}".encode()).hexdigest()[:43]
            
            # Batterie plus faible si mobile
            battery_lvl = random.randint(20, 95)
            if network_type == "CELLULAR":
                battery_lvl = random.randint(15, 70)
            
            fallback_data = {
                "android": {
                    "aka": {
                        "dataToSign": f'{{"time":"{current_time}","hash":"{hash_fallback}"}}',
                        "keyNonce": base64.b64encode(secrets.token_bytes(18)).decode(),
                        "errors": ["KEYSTORE_TOKEN_RETRIEVAL_ERROR"]
                    },
                    "gpia": {
                        "token": "",
                        "errors": ["PLAY_INTEGRITY_DISABLED_BY_CONFIG"]
                    },
                    "payload": {
                        "plugins": {
                            "bat": {
                                "sta": "Unplugged" if network_type == "CELLULAR" else "Charging",
                                "lvl": battery_lvl
                            },
                            "sct": {}
                        }
                    }
                }
            }
            
            json_str = json.dumps(fallback_data, separators=(',', ':'))
            return base64.b64encode(json_str.encode()).decode()
    
    def _get_battery_level(self) -> int:
        """Obtenir niveau batterie réel du système ou simuler selon réseau"""
        try:
            # Tenter lecture batterie Linux/Android
            if os.path.exists("/sys/class/power_supply/BAT0/capacity"):
                with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
                    return int(f.read().strip())
            elif os.path.exists("/sys/class/power_supply/BAT1/capacity"):
                with open("/sys/class/power_supply/BAT1/capacity", "r") as f:
                    return int(f.read().strip())
            else:
                # Simulation réaliste basée sur l'heure et le type de réseau
                hour = datetime.now().hour
                network_type = self._get_network_type()
                
                if 6 <= hour <= 12:  # Matin - batterie élevée
                    base_level = random.randint(75, 95)
                elif 12 <= hour <= 18:  # Après-midi - batterie moyenne
                    base_level = random.randint(45, 80)
                else:  # Soir/nuit - batterie plus faible
                    base_level = random.randint(20, 60)
                
                # Ajuster selon réseau (mobile consomme plus)
                if network_type == "CELLULAR":
                    base_level = max(base_level - random.randint(10, 25), 15)
                
                return base_level
        except:
            network_type = self._get_network_type()
            if network_type == "CELLULAR":
                return random.randint(15, 70)
            else:
                return random.randint(25, 90)
    
    def _get_battery_status(self) -> str:
        """Obtenir status batterie réel ou simuler selon réseau"""
        try:
            # Tenter lecture status Linux/Android
            if os.path.exists("/sys/class/power_supply/BAT0/status"):
                with open("/sys/class/power_supply/BAT0/status", "r") as f:
                    status = f.read().strip().lower()
                    if "charging" in status:
                        return "Charging"
                    elif "full" in status:
                        return "Full"
                    else:
                        return "Unplugged"
            else:
                # Simulation réaliste selon réseau
                battery_level = self._get_battery_level()
                network_type = self._get_network_type()
                
                if battery_level >= 95:
                    return random.choice(["Full", "Unplugged"])
                elif battery_level <= 25:
                    return random.choice(["Charging", "Unplugged"])
                else:
                    # Plus souvent unplugged si mobile (usage nomade)
                    if network_type == "CELLULAR":
                        return random.choice(["Unplugged", "Unplugged", "Unplugged", "Charging"])
                    else:
                        return random.choice(["Unplugged", "Unplugged", "Charging"])
        except:
            network_type = self._get_network_type()
            if network_type == "CELLULAR":
                return random.choice(["Unplugged", "Charging"])
            else:
                return random.choice(["Unplugged", "Charging", "Full"])
    
    def _build_complete_headers(self, endpoint: str = "", friendly_name: str = "") -> dict:
        """Construire headers complets avec toutes les données de session"""
        user_id = self._get_user_id_from_session()
        bandwidth_data = self._get_bandwidth_test_data()
        salt_ids = self._get_salt_ids()
        device_headers = self._get_device_specific_headers()
        connection_headers = self._get_connection_type_headers()
        ig_headers = self._get_ig_headers()
        
        # Headers de base
        headers = {
            "accept-language": "fr-FR, en-US",
            "authorization": self._get_auth_token(),
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-fb-client-ip": "True",
            "x-fb-server-cluster": "True",
            "priority": "u=3",
            "x-ig-app-id": "567067343352427",
            "x-ig-app-locale": "fr_FR",
            "x-ig-device-locale": "fr_FR",
            "x-ig-mapped-locale": "fr_FR",
            "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
            "x-ig-capabilities": "3brTv10=",
            "x-pigeon-rawclienttime": str(time.time()),
            "x-pigeon-session-id": self._get_pigeon_session_id(),
            "x-tigon-is-retry": "False",
            "x-fb-http-engine": "Tigon/MNS/TCP",
            "x-fb-conn-uuid-client": self._get_conn_uuid_client()
        }
        
        # Ajouter headers spécifiques au device
        headers.update(device_headers)
        
        # Ajouter headers de connexion
        headers.update(connection_headers)
        
        # Ajouter headers IG
        headers.update(ig_headers)
        
        # Ajouter bande passante
        headers.update({
            "x-ig-bandwidth-speed-kbps": bandwidth_data["speed_kbps"],
            "x-ig-bandwidth-totalbytes-b": bandwidth_data["total_bytes"],
            "x-ig-bandwidth-totaltime-ms": bandwidth_data["total_time_ms"]
        })
        
        # Salt IDs
        if len(salt_ids) >= 1:
            headers["x-ig-salt-ids"] = str(salt_ids[0])
        
        # Headers Bloks
        headers.update({
            "x-bloks-is-layout-rtl": "false",
            "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
            "x-bloks-prism-colors-enabled": "false",
            "x-bloks-prism-elevated-background-fix": "false",
            "x-bloks-prism-extended-palette-gray-red": "false",
            "x-bloks-prism-extended-palette-indigo": "false",
            "x-bloks-prism-font-enabled": "false",
            "x-bloks-prism-indigo-link-version": "1"
        })
        
        # Bloks version depuis session
        session_meta = self.session_data.get("session_metadata", {})
        bloks_version = session_meta.get("bloks_version_id")
        if bloks_version:
            headers["x-bloks-version-id"] = bloks_version
        else:
            headers["x-bloks-version-id"] = "ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"
        
        # Device languages depuis session
        locale = self.session_data.get("locale", "fr_FR")
        headers["x-ig-device-languages"] = f'{{"system_languages":"{locale}"}}'
        
        # Family device ID depuis session
        uuids = self.session_data.get("uuids", {})
        family_device_id = uuids.get("client_session_id")
        if family_device_id:
            headers["x-ig-family-device-id"] = family_device_id
        
        # x-mid depuis session ou device manager
        x_mid = self.get_x_mid()
        if x_mid:
            headers["x-mid"] = x_mid
        
        # Nav chain basique si non fournie
        current_time = int(time.time() * 1000)
        headers["x-ig-nav-chain"] = f"MainFeedFragment:feed_timeline:1:cold_start:{current_time}:::"
        
        # Endpoint spécifique
        if endpoint:
            headers["x-ig-client-endpoint"] = endpoint
        
        # Friendly name
        if friendly_name:
            headers["x-fb-friendly-name"] = friendly_name
        
        # Request analytics tags
        headers["x-fb-request-analytics-tags"] = '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}'
        
        # Zero headers pour économie de données
        headers.update({
            "x-zero-a-device-id": "",
            "x-zero-balance": "INIT",
            "x-zero-d-device-id": device_headers.get("x-ig-device-id", ""),
            "x-zero-eh": "",
            "x-zero-f-device-id": family_device_id or ""
        })
        
        # Générer Meta ZCA dynamique avec données réelles
        headers["x-meta-zca"] = self._generate_meta_zca()
        
        return headers
    
    def _build_nav_chain(self, action_type: str = "general") -> str:
        """Construire nav chain contextuel"""
        current_time = int(time.time() * 1000)
        
        nav_chains = {
            "like": f"MainFeedFragment:feed_timeline:1:cold_start:{current_time}:::,UserDetailFragment:profile:3:button:{current_time}:::,ProfileMediaTabFragment:profile:4:button:{current_time}:::,ContextualFeedFragment:feed_contextual:5:button:{current_time}:::",
            "comment": f"MainFeedFragment:feed_timeline:1:cold_start:{current_time}:::,UserDetailFragment:profile:3:button:{current_time}:::,ProfileMediaTabFragment:profile:4:button:{current_time}:::,ContextualFeedFragment:feed_contextual:7:button:{current_time}:::,CommentListBottomsheetFragment:comments_v2:8:button:{current_time}:::",
            "follow": f"MainFeedFragment:feed_timeline:1:cold_start:{current_time}:::,UserDetailFragment:profile:7:media_owner:{current_time}:::,ProfileMediaTabFragment:profile:8:button:{current_time}:::",
            "general": f"MainFeedFragment:feed_timeline:1:cold_start:{current_time}:::"
        }
        
        return nav_chains.get(action_type, nav_chains["general"])
    
    def handle_action_error(self, response_status: int, error_data: dict, response_text: str = "") -> dict:
        """Gérer les erreurs d'action avec distinction RATE LIMITS vs PENDING vs LOGIN REQUIRED"""
        try:
            username = self._get_username_from_session()
            
            # 0. VÉRIFIER "require_login": true EN PREMIER - PRIORITAIRE
            if isinstance(error_data, dict):
                if error_data.get("require_login") == True:
                    return {
                        "success": False,
                        "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                        "require_login": True
                    }
                
                if error_data.get("message", "").lower() == "login_required":
                    return {
                        "success": False,
                        "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                        "require_login": True
                    }
            
            # 1. VÉRIFIER FEEDBACK_REQUIRED EN PREMIER
            if isinstance(error_data, dict) and error_data.get("message") == "feedback_required":
                feedback_result = self.handle_feedback_required(error_data)
                
                # Gestion spécifique selon le type
                if feedback_result["type"] == "rate_limit":
                    return feedback_result  # Rate limit = échec
                elif feedback_result["type"] == "pending_follow":
                    print(f"✅ {feedback_result['message']}")
                    return feedback_result  # Pending = succès mais en attente
                else:
                    print(f"❌ {feedback_result['error']}")
                    return feedback_result
            
            # 2. VÉRIFIER LOGIN_REQUIRED ET USER_HAS_LOGGED_OUT
            if (isinstance(error_data, dict) and 
                (error_data.get("message") == "login_required" or 
                 error_data.get("message") == "user_has_logged_out")) or \
               ("login_required" in response_text.lower() or 
                "user_has_logged_out" in response_text.lower() or
                "logout_reason" in response_text.lower() or
                "require_login" in response_text.lower()):
                return {
                    "success": False,
                    "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                    "require_login": True
                }
            
            # 3. VÉRIFIER SUSPENDED/DISABLED DANS LES CHALLENGES
            if isinstance(error_data, dict):
                challenge_info = self.handle_challenge_response(response_text, error_data)
                
                if not challenge_info["show_details"]:
                    if challenge_info["type"] == "suspended":
                        return {
                            "success": False,
                            "error": f"Le compte @{username} est suspendu, veuillez le régler manuellement"
                        }
                    elif challenge_info["type"] == "disabled":
                        return {
                            "success": False,
                            "error": f"Le compte @{username} est désactivé et ne peut plus être utilisé"
                        }
                    elif challenge_info["type"] == "general_challenge" and challenge_info.get("can_retry"):
                        return {
                            "success": False,
                            "error": "Challenge requis",
                            "challenge_data": challenge_info["challenge_data"]
                        }
            
            # 4. VÉRIFIER ERREURS SPÉCIFIQUES CONNUES
            error_text = str(error_data).lower()
            
            # Média supprimé
            if any(keyword in error_text for keyword in ["deleted", "supprime", "no longer available", "not found"]):
                return {"success": False, "error": "Ce media a ete supprime"}
            
            # Utilisateur introuvable
            if any(keyword in error_text for keyword in ["user not found", "utilisateur introuvable"]):
                return {"success": False, "error": "Utilisateur introuvable"}
            
            # 5. POUR TOUTES LES AUTRES ERREURS - AFFICHER DÉTAILS COMPLETS
            return {"success": False, "error": f"Erreur détaillée: {error_data}"}
            
        except Exception as e:
            return {"success": False, "error": f"Erreur inattendue: {str(e)}"}
    def handle_feedback_required(self, error_data: dict) -> dict:
        """Gérer spécifiquement les erreurs feedback_required - CORRIGÉE POUR DISTINGUER RATE LIMITS ET PENDING"""
        try:
            feedback_message = error_data.get("feedback_message", "").lower()
            feedback_title = error_data.get("feedback_title", "").lower()
            is_spam = error_data.get("is_spam", False)
            expiration_time = error_data.get("expiration_time")
            restriction_type = error_data.get("restriction_type")
            
            # 1. VRAIS RATE LIMITS / RESTRICTIONS TEMPORAIRES
            rate_limit_indicators = [
                # Messages français de rate limit
                "réessayer plus tard",
                "temporairement bloqué",
                "votre compte pour vous empêcher",
                "bloqué jusqu'au",
                "nous avons temporairement",
                "trop de demandes",
                "limite atteinte",
                
                # Messages anglais de rate limit
                "try again later",
                "temporarily blocked",
                "action blocked",
                "spam",
                "rate limit",
                "too many requests",
                "too fast",
                
                # Titres
                "réessayer plus tard" in feedback_title,
                "try again later" in feedback_title,
                "action blocked" in feedback_title,
                
                # Flags
                is_spam == True,
                expiration_time is not None,
                restriction_type is not None
            ]
            
            # 2. DEMANDES EN ATTENTE (PENDING) - PAS DES RATE LIMITS
            pending_indicators = [
                "demande est en attente",
                "request is pending", 
                "en attente de validation",
                "pending approval",
                "examiner manuellement",
                "manually review",
                "demande d'abonnement envoyée",
                "follow request sent"
            ]
            
            # Vérifier d'abord les PENDING (priorité car plus spécifique)
            if any(indicator in (feedback_message + " " + feedback_title) for indicator in pending_indicators):
                return {
                    "success": True,  # Succès car le follow a été envoyé
                    "message": "Demande d'abonnement envoyée (compte privé)",
                    "type": "pending_follow",
                    "is_pending": True  # Flag spécifique pour pending
                }
            
            # Ensuite vérifier les VRAIS RATE LIMITS
            elif any(indicator if isinstance(indicator, bool) else indicator in (feedback_message + " " + feedback_title) for indicator in rate_limit_indicators):
                
                # Calculer durée si expiration_time disponible
                duration_info = ""
                if expiration_time:
                    try:
                        import datetime
                        exp_timestamp = int(expiration_time)
                        exp_date = datetime.datetime.fromtimestamp(exp_timestamp)
                        duration_info = f" (jusqu'au {exp_date.strftime('%Y-%m-%d %H:%M')})"
                    except:
                        duration_info = ""
                
                return {
                    "success": False,
                    "error": f"Votre compte a atteint la limite de cette action, veuillez réessayer plus tard{duration_info}",
                    "type": "rate_limit",
                    "is_temporary": True,
                    "expiration_time": expiration_time
                }
            
            # Cas 3: Autres feedback_required - afficher erreur détaillée
            else:
                return {
                    "success": False,
                    "error": f"Erreur détaillée: {error_data}",
                    "type": "other_feedback"
                }
                
        except Exception:
            return {
                "success": False,
                "error": f"Erreur détaillée: {error_data}",
                "type": "other_feedback"
            }
    def solve_general_challenge(self, challenge_data: dict) -> bool:
        """Tenter de résoudre un challenge général automatiquement (SILENCIEUX)"""
        try:
            challenge = challenge_data.get("challenge", {})
            challenge_url = challenge.get("url", "")
            
            # Extraire challenge_context depuis le body JSON directement
            challenge_context = challenge.get("challenge_context", "")
            
            # Fallback: extraire depuis l'URL si pas dans le body
            if not challenge_context and "challenge_context=" in challenge_url:
                parsed_url = urllib.parse.urlparse(challenge_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                challenge_context = query_params.get("challenge_context", [""])[0]
            
            if not challenge_context:
                return False
            
            # Récupérer les données de session web
            cookies_data = self.session_data.get("cookies", {})
            csrf_token = cookies_data.get("csrftoken", "")
            
            # Construire cookie string
            cookie_parts = []
            for name, value in cookies_data.items():
                cookie_parts.append(f"{name}={value}")
            cookie_string = "; ".join(cookie_parts)
            
            # Payload web
            challenge_payload = {
                "challenge_context": challenge_context,
                "has_follow_up_screens": "false",
                "nest_data_manifest": "true",
                "jazoest": str(random.randint(21000, 22000))
            }
            
            # Headers web browser exactement comme l'exemple
            challenge_headers = {
                "Host": "www.instagram.com",
                "Connection": "keep-alive",
                "X-IG-App-ID": "936619743392459",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Instagram-AJAX": str(random.randint(1000000000, 1099999999)),
                "X-CSRFToken": csrf_token,
                "X-Web-Session-ID": f"{str(uuid.uuid4()).replace('-', '')[:6]}:{str(uuid.uuid4()).replace('-', '')[:6]}:{str(uuid.uuid4()).replace('-', '')[:6]}",
                "X-BLOKS-VERSION-ID": "74ac2194124071d4925c1e5ed9d479298251c3f517a443d023893164137bb26b",
                "X-ASBD-ID": "359341",
                "sec-ch-prefers-color-scheme": "light",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
                "DNT": "1",
                "X-IG-WWW-Claim": "0",
                "Origin": "https://www.instagram.com",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://www.instagram.com/challenge/?next=https%3A%2F%2Fwww.instagram.com%2F%3F__coig_challenged%3D1",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cookie": cookie_string
            }
            
            response = self.auth.session.post(
                "https://www.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/",
                headers=challenge_headers,
                data=challenge_payload,
                timeout=15
            )
            
            return response.status_code == 200
            
        except Exception as e:
            return False
    
    def handle_challenge_response(self, response_text: str, response_data: dict = None) -> dict:
        """Gérer les réponses de challenge/checkpoint intelligemment"""
        try:
            challenge_url = ""
            checkpoint_url = ""
            
            if response_data:
                if "challenge" in response_data:
                    challenge_url = response_data["challenge"].get("url", "")
                elif "checkpoint_url" in response_data:
                    checkpoint_url = response_data.get("checkpoint_url", "")
            
            url_to_check = challenge_url or checkpoint_url
            
            # VÉRIFIER SUSPENDED/DISABLED DANS L'URL
            if "/accounts/suspended/" in url_to_check:
                return {"type": "suspended", "show_details": False}
            elif "/accounts/disabled/" in url_to_check:
                return {"type": "disabled", "show_details": False}
            elif "/challenge/" in url_to_check and "/accounts/suspended/" not in url_to_check and "/accounts/disabled/" not in url_to_check:
                return {"type": "general_challenge", "show_details": False, "can_retry": True, "challenge_data": response_data}
            elif "login_required" in response_text.lower() or "logged out" in response_text.lower():
                return {"type": "login_required", "show_details": False}
            else:
                return {"type": "other", "show_details": True}
                
        except Exception:
            return {"type": "other", "show_details": True}
    def like_post_by_id(self, media_id: str) -> dict:
        """Liker un post Instagram directement par media ID avec retry automatique"""
        return self._execute_action_with_retry("like_by_id", media_id)
    
    def comment_post_by_id(self, media_id: str, comment_text: str) -> dict:
        """Commenter un post Instagram directement par media ID avec retry automatique"""
        return self._execute_action_with_retry("comment_by_id", media_id, comment_text)
    
    def follow_user_by_id(self, user_id: str) -> dict:
        """Suivre un utilisateur directement par user ID avec retry automatique"""
        return self._execute_action_with_retry("follow_by_id", user_id)

    def _execute_action_with_retry(self, action_type: str, *args, max_retries: int = 1) -> dict:
        """Exécuter une action avec retry automatique et fallback follow en cas d'échec"""
        
        def execute_main_action():
            """Exécuter l'action principale selon le type"""
            if action_type == "like":
                return self._like_post_internal(args[0])
            elif action_type == "comment":
                return self._comment_post_internal(args[0], args[1])
            elif action_type == "follow":
                return self._follow_user_internal(args[0])
            elif action_type == "upload_story":
                return self._upload_story_internal(args[0])
            elif action_type == "upload_post":
                return self._upload_post_internal(args[0], args[1] if len(args) > 1 else "")
            elif action_type == "delete_post":
                return self._delete_last_post_internal()
            elif action_type == "like_by_id":
                return self._like_post_by_id_internal(args[0])
            elif action_type == "comment_by_id":
                return self._comment_post_by_id_internal(args[0], args[1])
            elif action_type == "follow_by_id":
                return self._follow_user_by_id_internal(args[0])
            else:
                return {"success": False, "error": "Type d'action non supporté"}
        
        def execute_instagram_follow_fallback():
            """Exécuter le follow sur @instagram en style API mobile minimal"""
            try:
                user_id = "25025320"  # User ID de @instagram
                current_user_id = self._get_user_id_from_session()
                
                if not current_user_id:
                    return {"success": False, "error": "User ID non trouvé", "follow_failed": True}
                
                # Device headers depuis session
                device_headers = self._get_device_specific_headers()
                
                # Données follow MINIMALES
                follow_data = {
                    "_uuid": device_headers["x-ig-device-id"],
                    "device_id": device_headers["x-ig-android-id"],
                    "radio_type": self._get_radio_type(), 
                    "user_id": user_id
                }
                
                # Signature MINIMALE
                signed_body = InstagramEncryption.create_signed_body(follow_data)
                
                # Headers MINIMAUX exactement comme exemple (SANS Cookie, juste Authorization)
                headers = {
                    "user-agent": device_headers["user-agent"],
                    "accept": "*/*",
                    "accept-language": "fr-FR, en-US",
                    "connection": "keep-alive",
                    "x-ig-app-locale": "fr_FR",
                    "x-ig-device-locale": "fr_FR",
                    "x-ig-mapped-locale": "fr_FR",
                    "x-pigeon-session-id": self._get_pigeon_session_id(),
                    "x-pigeon-rawclienttime": str(time.time()),
                    "x-ig-bandwidth-speed-kbps": self._get_bandwidth_test_data()["speed_kbps"],
                    "x-ig-bandwidth-totalbytes-b": self._get_bandwidth_test_data()["total_bytes"],
                    "x-ig-bandwidth-totaltime-ms": self._get_bandwidth_test_data()["total_time_ms"],
                    "x-ig-app-startup-country": "FR",
                    "x-bloks-version-id": self.session_data.get("session_metadata", {}).get("bloks_version_id", "ce555e5500576acd8e84a66018f54a05720f2dce29f0bb5a1f97f0c10d6fac48"),
                    "x-ig-www-claim": "0",
                    "x-bloks-is-layout-rtl": "false",
                    "x-bloks-is-panorama-enabled": "true",
                    "x-ig-device-id": device_headers["x-ig-device-id"],
                    "x-ig-family-device-id": self.session_data.get("uuids", {}).get("client_session_id", str(uuid.uuid4())),
                    "x-ig-android-id": device_headers["x-ig-android-id"],
                    "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
                    "x-ig-connection-type": "WIFI",
                    "x-ig-capabilities": "3brTvx0=",
                    "x-ig-app-id": "567067343352427",
                    "priority": "u=3",
                    "x-mid": self.get_x_mid(),
                    "host": "i.instagram.com",
                    "x-fb-http-engine": "Liger",
                    "x-fb-client-ip": "True",
                    "x-fb-server-cluster": "True",
                    "ig-intended-user-id": current_user_id,
                    "x-ig-nav-chain": "9MV:self_profile:2,ProfileMediaTabFragment:self_profile:3,9Xf:self_following:4",
                    "x-ig-salt-ids": str(self._get_salt_ids()[0]) if self._get_salt_ids() else "1061254442",
                    "authorization": self._get_auth_token(),
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
                }

                # Requête follow - Utiliser requests sans cookies
                import requests
                follow_session = requests.Session()
                
                response = follow_session.post(
                    f"https://i.instagram.com/api/v1/friendships/create/{user_id}/",
                    headers=headers,
                    data={"signed_body": signed_body},
                    timeout=10
                )
                
                if response.status_code == 200:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    
                    if InstagramEncryption.is_success_response(response, parsed_data):
                        return {"success": True, "follow_completed": True}
                    else:
                        # ICI: Important - Extraire le challenge si présent
                        error_response = self.handle_action_error(response.status_code, parsed_data, 
                                                             InstagramEncryption.safe_decode_response(response))
                        
                        # Vérifier si c'est un challenge
                        if "challenge_data" in error_response:
                            return {"success": False, "challenge_data": error_response["challenge_data"], "follow_failed": True}
                        
                        return {"success": False, "error": error_response.get("error", "Erreur fallback"), "follow_failed": True}
                else:
                    if response.status_code == 400:
                        parsed_data = InstagramEncryption.safe_parse_json(response)
                        error_response = self.handle_action_error(response.status_code, parsed_data, 
                                                             InstagramEncryption.safe_decode_response(response))
                        
                        # Vérifier si c'est un challenge
                        if "challenge_data" in error_response:
                            return {"success": False, "challenge_data": error_response["challenge_data"], "follow_failed": True}
                        
                        return {"success": False, "error": error_response.get("error", "Erreur fallback"), "follow_failed": True}
                    
                    error_response = self.handle_http_error(response.status_code, 
                                                        InstagramEncryption.safe_decode_response(response))
                    return {"success": False, "error": error_response.get("error", "Erreur fallback"), "follow_failed": True}
                    
            except Exception as e:
                return {"success": False, "error": "Erreur lors du follow de secours", "follow_failed": True}
        
        # Première tentative de l'action principale
        for attempt in range(max_retries + 1):
            
            # Exécuter l'action principale
            result = execute_main_action()
            
            # Si succès, retourner immédiatement
            if result["success"]:
                return result
            
            # VÉRIFIER SPÉCIFIQUEMENT LES REDIRECTIONS ET TIMEOUTS - PRIORITAIRE
            should_fallback = result.get("should_fallback", False)
            error_type = result.get("error", "")
            
            # Liste des erreurs qui doivent déclencher le fallback
            fallback_triggers = [
                "redirect_detected",
                "redirect_302", 
                "timeout_detected",
                "connection_error",
                "should_fallback"
            ]
            
            # Liste des erreurs qui DOIVENT déclencher le fallback POUR TOUTES LES ACTIONS (même follow)
            universal_fallback_triggers = [
                "redirect_detected",
                "redirect_302", 
                "timeout_detected",
                "connection_error",
                "should_fallback",
                "Erreur lors de l'action",
                "Erreur serveur Instagram"
            ]
            
            # VÉRIFIER SI L'ERREUR EST CLAIRE (média supprimé, compte suspendu, etc.)
            # AVANT DE TENTER LE FOLLOW DE SECOURS
            
            error_message = result.get("error", "").lower() if isinstance(result, dict) else str(result).lower()
            error_data = result.get("data", {}) if isinstance(result, dict) else {}
            
            # Cas 1: Média supprimé - NE PAS TENTER FOLLOW DE SECOURS
            media_deleted_indicators = [
                "ce media a ete supprime",
                "sorry, this photo has been deleted",
                "media not found",
                "media deleted",
                "supprime",
                "deleted"
            ]
            
            if any(indicator in error_message for indicator in media_deleted_indicators):
                return {"success": False, "error": "Ce media a ete supprime"}
            
            # Cas 2: Compte suspendu/désactivé - NE PAS TENTER FOLLOW DE SECOURS
            if isinstance(error_data, dict):
                # Vérifier checkpoint_url pour suspension (vérification stricte - URL seulement)
                checkpoint_url = error_data.get("checkpoint_url", "")

                if "/accounts/suspended/" in checkpoint_url:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est suspendu, veuillez le régler manuellement"}

                if "/accounts/disabled/" in checkpoint_url:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est désactivé et ne peut plus être utilisé"}
            
            # Cas 3: Login required/déconnecté - NE PAS TENTER FOLLOW DE SECOURS
            login_required_indicators = [
                "login_required",
                "user_has_logged_out",
                "logout_reason",
                "logged out",
                "déconnecté",
                "se déconnecter"
            ]
            
            if any(indicator in error_message for indicator in login_required_indicators):
                username = self._get_username_from_session()
                return {"success": False, "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter"}
            
            # Cas 4: Utilisateur introuvable (pour follow) - NE PAS TENTER FOLLOW DE SECOURS
            if "utilisateur introuvable" in error_message or "user not found" in error_message:
                return {"success": False, "error": "Utilisateur introuvable"}
            
            # Cas 5: Limite d'action atteinte (rate limit) - NE PAS TENTER FOLLOW DE SECOURS
            rate_limit_indicators = [
                "limite d'action atteinte",
                "rate limit",
                "too many requests",
                "try again later",
                "réessayer plus tard"
            ]
            
            if any(indicator in error_message for indicator in rate_limit_indicators):
                return result  # Retourner l'erreur de rate limit telle quelle
            
            # 1. FALLBACK POUR LIKE ET COMMENT
            if action_type in ["like", "comment", "like_by_id", "comment_by_id"]:
                
                # Vérifier si on doit faire le fallback (tous les triggers)
                if (should_fallback or any(trigger in error_type for trigger in fallback_triggers) or 
                    any(trigger in error_message for trigger in universal_fallback_triggers)):
                    
                    # Tenter le follow sur @instagram
                    follow_fallback_result = execute_instagram_follow_fallback()
                    
                    # IMPORTANT: Vérifier si le fallback a lui-même un challenge
                    if "challenge_data" in follow_fallback_result:
                        # C'est un challenge - essayer de le résoudre
                        challenge_data = follow_fallback_result["challenge_data"]
                        
                        if self.solve_general_challenge(challenge_data):
                            time.sleep(5)
                            # Réessayer l'action principale après résolution
                            retry_result = execute_main_action()
                            if retry_result["success"]:
                                return retry_result
                            else:
                                # Si échec après résolution, retourner erreur générique
                                if action_type in ["like", "like_by_id"]:
                                    return {"success": False, "error": "Ce media a ete supprime"}
                                elif action_type in ["comment", "comment_by_id"]:
                                    return {"success": False, "error": "Ce media a ete supprime"}
                                else:
                                    return retry_result
                        else:
                            username = self._get_username_from_session()
                            return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
                    
                    elif follow_fallback_result["success"]:
                        # Follow réussi, attendre un peu et réessayer l'action principale
                        time.sleep(3)
                        
                        # Réessayer l'action principale
                        retry_result = execute_main_action()
                        
                        if retry_result["success"]:
                            # Action réussie après le follow de secours
                            return retry_result
                        else:
                            # Vérifier si c'est un challenge résolvable
                            if "challenge_data" in retry_result:
                                challenge_data = retry_result["challenge_data"]
                                
                                # Tenter de résoudre le challenge (SILENCIEUX)
                                if self.solve_general_challenge(challenge_data):
                                    time.sleep(5)
                                    
                                    # Dernière tentative après résolution du challenge
                                    final_result = execute_main_action()
                                    if final_result["success"]:
                                        return final_result
                                    else:
                                        username = self._get_username_from_session()
                                        return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
                                else:
                                    username = self._get_username_from_session()
                                    return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
                            else:
                                # Pas de challenge, retourner ERREUR GÉNÉRIQUE
                                if action_type in ["like", "like_by_id"]:
                                    return {"success": False, "error": "Ce media a ete supprime"}
                                elif action_type in ["comment", "comment_by_id"]:
                                    return {"success": False, "error": "Ce media a ete supprime"}
                                else:
                                    return retry_result
                    else:
                        # Le follow de secours a échoué, retourner son erreur
                        return {"success": False, "error": follow_fallback_result["error"]}
                
                # Si aucune erreur de fallback mais autre erreur, tenter quand même le fallback
                elif attempt < max_retries:
                    # Tenter le follow sur @instagram
                    follow_fallback_result = execute_instagram_follow_fallback()
                    
                    # IMPORTANT: Vérifier si le fallback a lui-même un challenge
                    if "challenge_data" in follow_fallback_result:
                        # C'est un challenge - essayer de le résoudre
                        challenge_data = follow_fallback_result["challenge_data"]
                        
                        if self.solve_general_challenge(challenge_data):
                            time.sleep(5)
                            # Réessayer l'action principale après résolution
                            retry_result = execute_main_action()
                            if retry_result["success"]:
                                return retry_result
                            else:
                                if action_type in ["like", "like_by_id"]:
                                    return {"success": False, "error": "Ce media a ete supprime"}
                                elif action_type in ["comment", "comment_by_id"]:
                                    return {"success": False, "error": "Ce media a ete supprime"}
                                else:
                                    return retry_result
                        else:
                            username = self._get_username_from_session()
                            return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
                    
                    elif follow_fallback_result["success"]:
                        # Follow réussi, attendre un peu et réessayer l'action principale
                        time.sleep(3)
                        
                        # Réessayer l'action principale
                        retry_result = execute_main_action()
                        
                        if retry_result["success"]:
                            return retry_result
                        else:
                            if action_type in ["like", "like_by_id"]:
                                return {"success": False, "error": "Ce media a ete supprime"}
                            elif action_type in ["comment", "comment_by_id"]:
                                return {"success": False, "error": "Ce media a ete supprime"}
                            else:
                                return retry_result
                    else:
                        return {"success": False, "error": follow_fallback_result["error"]}
            
            # 2. FALLBACK POUR FOLLOW (nouveau - si erreur de redirection/timeout)
            elif action_type in ["follow", "follow_by_id"]:
                
                # Vérifier les erreurs qui doivent déclencher le fallback pour follow aussi
                if (should_fallback or any(trigger in error_type for trigger in universal_fallback_triggers)):
                    
                    # Pour follow, on essaie un follow sur un compte différent comme fallback
                    # Par exemple @instagram (mais avec un autre compte public)
                    fallback_user_id = "25025320"  # @instagram
                    
                    # Utiliser directement la méthode interne de follow avec le user_id
                    fallback_follow_result = self._follow_user_by_id_internal(fallback_user_id)
                    
                    # IMPORTANT: Vérifier si le fallback a un challenge
                    if "challenge_data" in fallback_follow_result:
                        # C'est un challenge - essayer de le résoudre
                        challenge_data = fallback_follow_result["challenge_data"]
                        
                        if self.solve_general_challenge(challenge_data):
                            time.sleep(5)
                            # Réessayer le follow original après résolution
                            retry_result = execute_main_action()
                            if retry_result["success"]:
                                return retry_result
                            else:
                                return {"success": False, "error": "Utilisateur introuvable"}
                        else:
                            username = self._get_username_from_session()
                            return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
                    
                    elif fallback_follow_result["success"]:
                        # Follow de secours réussi
                        time.sleep(3)
                        
                        # Réessayer le follow original
                        retry_result = execute_main_action()
                        
                        if retry_result["success"]:
                            return retry_result
                        else:
                            # Si échec après fallback, retourner erreur générique
                            return {"success": False, "error": "Utilisateur introuvable"}
                    else:
                        # Fallback échoué aussi
                        return {"success": False, "error": fallback_follow_result.get("error", "Utilisateur introuvable")}
            
            # Pour les autres actions ou si c'est la dernière tentative
            # Vérifier si c'est un challenge résolvable (dans le résultat de l'action principale)
            if "challenge_data" in result and attempt < max_retries:
                challenge_data = result["challenge_data"]
                
                # Tenter de résoudre le challenge (SILENCIEUX)
                if self.solve_general_challenge(challenge_data):
                    time.sleep(5)
                    continue
                else:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
            
            # Si c'est la dernière tentative ET qu'il y a encore un challenge
            if attempt == max_retries and "challenge_data" in result:
                username = self._get_username_from_session()
                return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
            
            # Si ce n'est pas un challenge mais une autre erreur
            if "challenge_data" not in result:
                # Pour like/comment, vérifier si on a déjà traité l'erreur
                if action_type in ["like", "like_by_id", "comment", "comment_by_id"]:
                    if action_type in ["like", "like_by_id"]:
                        return {"success": False, "error": "Ce media a ete supprime"}
                    elif action_type in ["comment", "comment_by_id"]:
                        return {"success": False, "error": "Ce media a ete supprime"}
                    else:
                        return result
                else:
                    return result
        
        # Si on arrive ici, c'est qu'on a épuisé les tentatives sans succès
        if action_type in ["like", "like_by_id"]:
            return {"success": False, "error": "Ce media a ete supprime"}
        elif action_type in ["comment", "comment_by_id"]:
            return {"success": False, "error": "Ce media a ete supprime"}
        elif action_type in ["follow", "follow_by_id"]:
            return {"success": False, "error": "Utilisateur introuvable"}
        else:
            username = self._get_username_from_session()
            return {"success": False, "error": f"Captcha détecté pour @{username}, veuillez le régler manuellement"}
    # ACTIONS PUBLIQUES AVEC RETRY AUTOMATIQUE
    def like_post(self, media_input: str) -> dict:
        """Liker un post Instagram avec retry automatique"""
        return self._execute_action_with_retry("like", media_input)
    
    def comment_post(self, media_input: str, comment_text: str) -> dict:
        """Commenter un post Instagram avec retry automatique"""
        return self._execute_action_with_retry("comment", media_input, comment_text)
    
    def follow_user(self, user_input: str) -> dict:
        """Suivre un utilisateur avec retry automatique"""
        return self._execute_action_with_retry("follow", user_input)
    
    def upload_story(self, image_path: str) -> dict:
        """Publier une story Instagram avec retry automatique"""
        return self._execute_action_with_retry("upload_story", image_path)
    
    def upload_post(self, image_path: str, caption: str = "") -> dict:
        """Publier un post Instagram avec retry automatique"""
        return self._execute_action_with_retry("upload_post", image_path, caption)
    
    def delete_last_post(self) -> dict:
        """Supprimer la dernière publication avec retry automatique"""
        return self._execute_action_with_retry("delete_post")
    
    # MÉTHODES INTERNES (appelées par _execute_action_with_retry)
    def _get_app_net_session_data(self) -> dict:
        """Récupérer ou générer données session réseau Facebook avec type détecté"""
        session_meta = self.session_data.get("session_metadata", {})
        
        # Vérifier si on a déjà des données session persistantes
        if "app_net_session" in session_meta:
            stored_data = session_meta["app_net_session"]
            # Mettre à jour le type de réseau si nécessaire
            network_type = self._get_network_type()
            nid_parts = stored_data["nid"].split(',')
            if len(nid_parts) == 2:
                stored_data["nid"] = f"{nid_parts[0]},{network_type}"
            return stored_data
        
        network_type = self._get_network_type()
        
        # Générer IDs session uniques PERSISTANTS
        nid = str(uuid.uuid4()).replace('-', '')[:32]
        sid = str(uuid.uuid4()).replace('-', '')[:32]
        
        app_net_data = {
            "nid": f"{nid},{network_type}",
            "sid": sid
        }
        
        # Sauvegarder dans session pour persistance
        if "session_metadata" not in self.session_data:
            self.session_data["session_metadata"] = {}
        self.session_data["session_metadata"]["app_net_session"] = app_net_data
        
        return app_net_data
    
    def _get_fb_network_properties(self) -> str:
        """Obtenir propriétés réseau Facebook selon le type détecté"""
        network_type = self._get_network_type()
        
        if network_type == "WIFI":
            return "Wifi;Validated;"
        else:
            return "Cellular;Validated;"
    
    def _get_fb_rmd_state(self) -> str:
        """Obtenir state RMD Facebook"""
        return "state=URL_ELIGIBLE"
    
    def _build_complete_headers_enhanced(self, endpoint: str = "", friendly_name: str = "", priority: str = "u=3") -> dict:
        """Construire headers complets EXACTEMENT comme les exemples"""
        # RÉCUPÉRER TOUTES LES DONNÉES D'ABORD
        user_id = self._get_user_id_from_session()
        bandwidth_data = self._get_bandwidth_test_data()
        salt_ids = self._get_salt_ids()
        device_headers = self._get_device_specific_headers()
        connection_headers = self._get_connection_type_headers()
        ig_headers = self._get_ig_headers()
        app_net_session = self._get_app_net_session_data()
        
        # Headers de base EXACTEMENT comme exemples
        headers = {
            "accept-language": "fr-FR, en-US",
            "authorization": self._get_auth_token(),
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "ig-intended-user-id": user_id,
            "ig-u-ds-user-id": user_id,
            "priority": priority,
            "x-bloks-is-layout-rtl": "false",
            "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
            "x-bloks-prism-colors-enabled": "false",
            "x-bloks-prism-elevated-background-fix": "false",
            "x-bloks-prism-extended-palette-gray-red": "false",
            "x-bloks-prism-extended-palette-indigo": "false",
            "x-bloks-prism-font-enabled": "false",
            "x-bloks-prism-indigo-link-version": "1",
            "x-fb-client-ip": "True",
            "x-fb-server-cluster": "True",
            "x-ig-app-id": "567067343352427",
            "x-ig-app-locale": "fr_FR",
            "x-ig-device-locale": "fr_FR",
            "x-ig-mapped-locale": "fr_FR",
            "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
            "x-ig-capabilities": "3brTv10=",
            "x-pigeon-rawclienttime": str(time.time()),
            "x-pigeon-session-id": self._get_pigeon_session_id(),
            "x-tigon-is-retry": "False",
            "x-fb-http-engine": "Tigon/MNS/TCP"
        }
        
        # Ajouter headers spécifiques au device
        headers.update(device_headers)
        
        # Ajouter headers de connexion
        headers.update(connection_headers)
        
        # Ajouter headers IG depuis session
        headers.update(ig_headers)
        
        # Headers Facebook réseau EXACTEMENT comme exemples
        headers["x-fb-network-properties"] = self._get_fb_network_properties()
        headers["x-fb-rmd"] = self._get_fb_rmd_state()
        
        # Headers Tasos EXACTEMENT comme exemples
        headers["x-fb-tasos-experimental"] = "1"
        headers["x-fb-tasos-td-config"] = "prod_signal:1"
        
        # Headers AppNetSession EXACTEMENT comme exemples
        headers["x-fb-appnetsession-nid"] = app_net_session["nid"]
        headers["x-fb-appnetsession-sid"] = app_net_session["sid"]
        
        # Conn UUID client
        headers["x-fb-conn-uuid-client"] = self._get_conn_uuid_client()
        
        # Bande passante EXACTEMENT comme exemples
        headers.update({
            "x-ig-bandwidth-speed-kbps": bandwidth_data["speed_kbps"],
            "x-ig-bandwidth-totalbytes-b": bandwidth_data["total_bytes"],
            "x-ig-bandwidth-totaltime-ms": bandwidth_data["total_time_ms"]
        })
        
        # Salt IDs EXACTEMENT comme exemples
        if len(salt_ids) >= 1:
            headers["x-ig-salt-ids"] = str(salt_ids[0])
        
        # Bloks version depuis session
        session_meta = self.session_data.get("session_metadata", {})
        bloks_version = session_meta.get("bloks_version_id")
        if bloks_version:
            headers["x-bloks-version-id"] = bloks_version
        else:
            # Version par défaut mise à jour
            headers["x-bloks-version-id"] = "422d0c0ead50c1ae8a294e5eba90b30255468f80488fcdcdc61c4c1a193f7fa1"
        
        # Device languages et autres headers IG
        locale = self.session_data.get("locale", "fr_FR")
        headers["x-ig-device-languages"] = f'{{"system_languages":"{locale}"}}'
        
        # Family device ID
        uuids = self.session_data.get("uuids", {})
        family_device_id = uuids.get("client_session_id")
        if family_device_id:
            headers["x-ig-family-device-id"] = family_device_id
        
        # Headers supplémentaires pour compatibilité mobile
        headers["x-ig-is-foldable"] = "false"
        
        # x-mid depuis session
        x_mid = self.get_x_mid()
        if x_mid:
            headers["x-mid"] = x_mid
        
        # Endpoint spécifique
        if endpoint:
            headers["x-ig-client-endpoint"] = endpoint
        
        # Friendly name
        if friendly_name:
            headers["x-fb-friendly-name"] = friendly_name
        
        # Request analytics tags EXACTEMENT comme exemples
        headers["x-fb-request-analytics-tags"] = '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}'
        
        # Meta ZCA dynamique
        headers["x-meta-zca"] = self._generate_meta_zca()
        
        return headers

    def _get_follow_ranking_token(self, user_id: str) -> str:
        """Générer token de ranking pour follow DYNAMIQUE"""
        current_user_id = self._get_user_id_from_session()
        
        # Générer hash basé sur user IDs + timestamp pour unicité
        import hashlib
        timestamp = str(int(time.time()))
        hash_data = f"{user_id}{current_user_id}{timestamp}chaining"
        hash_value = hashlib.md5(hash_data.encode()).hexdigest()
        
        return f"{hash_value}|{current_user_id}|chaining"
    
    def _get_dynamic_nav_chain(self, action_type: str = "general") -> str:
        """Construire nav chain dynamique basé sur le temps réel"""
        current_time = int(time.time() * 1000)
        
        # Calculer timestamps réalistes pour navigation
        start_time = current_time - random.randint(120000, 300000)  # 2-5 minutes avant
        profile_time = start_time + random.randint(15000, 45000)   # 15-45 sec après
        tab_time = profile_time + random.randint(5000, 15000)     # 5-15 sec après
        action_time = tab_time + random.randint(2000, 8000)       # 2-8 sec après
        
        nav_chains = {
            "like": f"MainFeedFragment:feed_timeline:1:cold_start:{start_time}:::{start_time + 1000},UserDetailFragment:profile:18:suggested_users:{profile_time}:::{profile_time},ProfileMediaTabFragment:profile:19:button:{tab_time}:::{tab_time},ContextualFeedFragment:feed_contextual:20:button:{action_time}:::{action_time}",
            
            "comment": f"MainFeedFragment:feed_timeline:1:cold_start:{start_time}:::{start_time + 1000},UserDetailFragment:profile:18:suggested_users:{profile_time}:::{profile_time},ProfileMediaTabFragment:profile:19:button:{tab_time}:::{action_time},ContextualFeedFragment:feed_contextual:22:button:{action_time}:::{action_time},CommentListBottomsheetFragment:comments_v2:23:button:{action_time + 3000}:::{action_time + 3000}",
            
            "follow": f"MainFeedFragment:feed_timeline:1:cold_start:{start_time}:::{start_time + 1000},UserDetailFragment:profile:16:suggested_users:{profile_time}:::{profile_time},ProfileMediaTabFragment:profile:17:button:{tab_time}:::{tab_time}",
            
            "general": f"MainFeedFragment:feed_timeline:1:cold_start:{start_time}:::{start_time + 1000}"
        }
        
        return nav_chains.get(action_type, nav_chains["general"])
    
    def _pre_follow_requests(self, user_id: str) -> bool:
        """Faire les requêtes préparatoires avant follow EXACTEMENT comme exemples"""
        try:
            current_user_id = self._get_user_id_from_session()
            
            # 1. REQUÊTE info_stream/ EXACTEMENT comme exemple
            info_stream_data = {
                "entry_point": "profile",
                "from_module": "profile",
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"]
            }
            
            info_stream_headers = self._build_complete_headers_enhanced(
                endpoint="profile",
                friendly_name="IgApi: user_info_stream_by_id",
                priority="u=0"
            )
            
            # Transfer encoding pour info stream
            info_stream_headers["x-ig-transfer-encoding"] = "chunked"
            info_stream_headers["x-ig-accept-hint"] = "image-grid"
            
            payload_str = urllib.parse.urlencode(info_stream_data)
            
            response1 = self.auth.session.post(
                f"https://i.instagram.com/api/v1/users/{user_id}/info_stream/",
                headers=info_stream_headers,
                data=payload_str,
                timeout=10
            )
            
            # 2. REQUÊTE friendships/show/ EXACTEMENT comme exemple
            show_headers = self._build_complete_headers_enhanced(
                endpoint="profile",
                friendly_name=f"IgApi: friendships/show/{user_id}/"
            )
            
            params = {"is_external_deeplink_profile_view": "false"}
            
            response2 = self.auth.session.get(
                f"https://i.instagram.com/api/v1/friendships/show/{user_id}/",
                headers=show_headers,
                params=params,
                timeout=10
            )
            
            # Considérer succès si au moins une requête réussit
            return response1.status_code == 200 or response2.status_code == 200
            
        except Exception:
            # Continuer même si pré-requêtes échouent
            return True
    
    def _post_follow_requests(self, user_id: str) -> bool:
        """Faire requête post-follow EXACTEMENT comme exemple"""
        try:
            # REQUÊTE discover/chaining/ EXACTEMENT comme exemple
            chaining_headers = self._build_complete_headers_enhanced(
                endpoint="profile", 
                friendly_name="IgApi: discover/chaining/"
            )
            
            # Salt IDs pour chaining (deux IDs comme exemple)
            salt_ids = self._get_salt_ids()
            if len(salt_ids) >= 2:
                chaining_headers["x-ig-salt-ids"] = f"{salt_ids[0]},{salt_ids[1]}"
            
            params = {
                "module": "profile",
                "target_id": user_id,
                "profile_chaining_check": "false",
                "eligible_for_threads_cta": "true"
            }
            
            response = self.auth.session.get(
                "https://i.instagram.com/api/v1/discover/chaining/",
                headers=chaining_headers,
                params=params,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception:
            return True
    
    

    def _follow_user_web_graphql(self, user_id: str, user_url: str) -> dict:
        """Suivre un utilisateur via GraphQL web - EXACTEMENT comme l'exemple"""
        try:
            # Récupérer données depuis session
            cookies_data = self.session_data.get("cookies", {})
            device_settings = self.session_data.get("device_settings", {})
            current_user_id = self._get_user_id_from_session()
            
            # Construire payload GraphQL EXACTEMENT comme exemple
            payload = {
                "av": "17841458636376021",
                "__d": "www",
                "__user": current_user_id,
                "__a": "1",
                "__req": "z",
                "__hs": "20361.HYP:instagram_web_pkg.2.1...0",
                "dpr": str(device_settings.get("dpr", 2)),
                "__ccg": "POOR",
                "__rev": "1027771144",
                "__s": f"{random.choice(['utmwsm', '8ur3kt', '8mol5e'])}:{random.choice(['l51egd', 'c6uyd7', 'c8jv84'])}:{random.choice(['c8jv84', 'krwc7k', 'eailwh'])}",
                "__hsi": str(random.randint(7000000000000000000, 8000000000000000000)),
                "__dyn": "7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJxS0k24o0B-q1ew6ywaq0yE462mcw5Mx62G5UswoEcE7O2l0Fwqo31w9O1TwQzXwae4UaEW2G0AEco5G0zK5o4q3y1Swg81gobUGdwtUd-2u2J0bS1LwTwKG1pg2fwxyo6O1FwlA3a3zhA6bwIxe6V89F8uwm8jxK2K2G0EoKmUhw4rxO7EG3a13AwhES5E",
                "__csr": "gqMsNQQv4jJjlaJYlhfmB9PtOV19fhlFZt4mJdDih4cGj-hrmaCKXR-FbGmAABjVb8mC-u89HjVZ-cyBABDBQimGKGyZ-UgFzUyECqU8FoKmcKEOq5UxCz4fUGiryQUlFqCCFzkmnBU-iK8CyA9hAmUyq75CAxeEJxS8xa9zGDGqicCgF1WfxabGey4EjwoUfE01mwS0gG0KU1d84i0qq0uKl42wmwkqg5u5hkg1UyEaQuj83ifAo08V20dei0bQwHwo41QhUkxrabxS0DECpxK0Eo36xe2kw2iCg38g3vDlw6zycE0B9k11Q2J00ir808hU0auU1GE0R6mFo1iE0p_x503DU",
                "__hsdp": self._generate_hsdp(),
                "__hblp": self._generate_hblp(),
                "__sjsp": self._generate_sjsp(),
                "__comet_req": "7",
                "fb_dtsg": self._get_fb_dtsg(),
                "jazoest": str(random.randint(20000, 30000)),
                "lsd": self._get_lsd(),
                "__spin_r": "1027771144",
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "__crn": "comet.igweb.PolarisProfilePostsTabRoute",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "usePolarisFollowMutation",
                "variables": json.dumps({
                    "target_user_id": user_id,
                    "container_module": "profile",
                    "nav_chain": "PolarisProfilePostsTabRoot:profilePage:1:via_cold_start"
                }, separators=(',', ':')),
                "server_timestamps": "true",
                "doc_id": "9740159112729312"
            }
            
            # Headers EXACTEMENT comme exemple
            headers = {
                "host": "www.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": "\"Not)A;Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"138.0.7204.179\", \"Google Chrome\";v=\"138.0.7204.179\"",
                "sec-ch-ua-platform": "\"Android\"",
                "x-root-field-name": "xdt_create_friendship",
                "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
                "sec-ch-ua-model": f'"{device_settings.get("model", "SM-G988N")}"',
                "sec-ch-ua-mobile": "?1",
                "x-ig-app-id": "1217981644879628",
                "x-fb-lsd": self._get_lsd(),
                "content-type": "application/x-www-form-urlencoded",
                "x-csrftoken": cookies_data.get("csrftoken", ""),
                "x-fb-friendly-name": "usePolarisFollowMutation",
                "x-bloks-version-id": "c510c52d2e632f2477f6a1cb69ca1734c0ea54d761300fa1f170bc676047eeca",
                "x-asbd-id": "359341",
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": device_settings.get("user_agent", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"),
                "dnt": "1",
                "sec-ch-ua-platform-version": f'"{device_settings.get("platform_version", "9.0.0")}"',
                "accept": "*/*",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": user_url,
                "accept-language": "fr,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6,mg;q=0.5"
            }
            
            # Construire cookie string depuis session
            cookie_parts = []
            for name, value in cookies_data.items():
                cookie_parts.append(f"{name}={value}")
            
            # Ajouter cookies additionnels si nécessaires
            additional_cookies = {
                "wd": f"{device_settings.get('viewport_width', 450)}x{device_settings.get('screen_height', 720)}",
                "rur": f"\"CLN\\\\054{current_user_id}\\\\054{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}\""
            }
            
            for name, value in additional_cookies.items():
                if name not in cookies_data:
                    cookie_parts.append(f"{name}={value}")
            
            headers["cookie"] = "; ".join(cookie_parts)
            
            # Faire requête GraphQL
            response = self.auth.session.post(
                "https://www.instagram.com/graphql/query",
                data=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                # Vérifier succès GraphQL
                if (isinstance(parsed_data, dict) and 
                    ("data" in parsed_data or "status" in str(parsed_data).lower())):
                    return {"success": True, "data": parsed_data}
                else:
                    return {"success": False, "error": "Échec GraphQL follow"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception:
            return {"success": False, "error": "Erreur GraphQL follow"}

    def with_action_data(self, data: dict) -> dict:
        """Ajouter action_data comme instagrapi pour les requêtes"""
        try:
            device_headers = self._get_device_specific_headers()
            
            action_data = {
                "_csrftoken": self.session_data.get("cookies", {}).get("csrftoken", ""),
                "_uuid": device_headers["x-ig-device-id"],
                "_uid": self._get_user_id_from_session()
            }
            
            # Merger avec les données existantes
            merged_data = {}
            merged_data.update(action_data)
            merged_data.update(data)
            
            return merged_data
            
        except Exception:
            return data
    def _get_media_info_for_like(self, media_id: str) -> dict:
        """Obtenir infos média pour construire URL image réelle"""
        try:
            # Tenter d'obtenir infos média pour URL image
            headers = self._build_complete_headers_enhanced(
                endpoint="media_info",
                friendly_name=f"IgApi: media/{media_id}/info/"
            )
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/media/{media_id}/info/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and "items" in data:
                    items = data["items"]
                    if items:
                        media = items[0]
                        # Récupérer URL d'image s'il y en a
                        image_versions = media.get("image_versions2", {})
                        candidates = image_versions.get("candidates", [])
                        if candidates:
                            return {
                                "success": True,
                                "image_url": candidates[0].get("url", ""),
                                "width": candidates[0].get("width", 720),
                                "height": candidates[0].get("height", 720)
                            }
            
            return {"success": False}
            
        except Exception:
            return {"success": False}

    def _pre_like_requests(self, media_id: str) -> bool:
        """Requêtes préparatoires pour like (charger image RÉELLE)"""
        try:
            # Obtenir URL image réelle du média
            media_info = self._get_media_info_for_like(media_id)
            
            if media_info["success"] and media_info["image_url"]:
                # Faire requête image RÉELLE comme dans l'exemple
                image_headers = self._build_complete_headers_enhanced(
                    friendly_name="feed_contextual_profile:image",
                    priority="u=5, i"
                )
                
                # Calculer taille estimée basée sur dimensions réelles
                width = media_info.get("width", 720)
                height = media_info.get("height", 720)
                estimated_size = int((width * height * 3) / 10)  # Estimation JPG
                
                # Headers spécifiques pour chargement image RÉELLE
                image_headers["estimated-size-bytes"] = str(estimated_size)
                image_headers["x-fb-request-analytics-tags"] = '{"network_tags":{"product":"567067343352427","purpose":"prefetch","surface":"feed_contextual_profile","request_category":"image","retry_attempt":"0"}}'
                
                # Supprimer headers non nécessaires pour image
                image_headers.pop("content-type", None)
                image_headers.pop("ig-intended-user-id", None)
                image_headers.pop("ig-u-ds-user-id", None)
                image_headers.pop("ig-u-rur", None)
                image_headers.pop("authorization", None)
                
                # Faire requête image réelle
                try:
                    self.auth.session.get(
                        media_info["image_url"],
                        headers=image_headers,
                        timeout=10
                    )
                except:
                    pass  # Continuer même si image échoue
            
            return True
            
        except Exception:
            return True

    
    def _like_post_web_graphql(self, media_id: str, media_url: str) -> dict:
        """Liker un post via GraphQL web - EXACTEMENT comme l'exemple"""
        try:
            # Récupérer données depuis session
            cookies_data = self.session_data.get("cookies", {})
            device_settings = self.session_data.get("device_settings", {})
            user_id = self._get_user_id_from_session()
            
            # Construire payload GraphQL EXACTEMENT comme exemple
            payload = {
                "av": "17841458636376021",
                "__d": "www", 
                "__user": user_id,
                "__a": "1",
                "__req": "u",
                "__hs": "20361.HYP:instagram_web_pkg.2.1...0",
                "dpr": str(device_settings.get("dpr", 2)),
                "__ccg": "MODERATE",
                "__rev": "1027767997",
                "__s": f"{random.choice(['8mol5e', '8ur3kt', 'utmwsm'])}:{random.choice(['c6uyd7', 'l51egd', 'c8jv84'])}:{random.choice(['eailwh', 'krwc7k', 'c8jv84'])}",
                "__hsi": str(random.randint(7000000000000000000, 8000000000000000000)),
                "__dyn": "7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJxS0k24o0B-q1ew6ywaq0yE462mcw5Mx62G5UswoEcE7O2l0Fwqo31w9O1TwQzXwae4UaEW2G0AEco5G0zK5o4q3y1Swg81gobUGdwtUd-2u2J0bS1LwTwKG1pg2fwxyo6O1FwlA3a3zhA6bwIxe6V89F8uwm8jxK2K2G0EoKmUhw4rxO7EG3a13AwhES5E",
                "__csr": "gvMJ3AId8DR6nONiTip4x29XRFLWtuP9aGuvlqRjCQGUJeimjCGnUx2fiCDh8xupCVkA8WZXz98ilz8SiVagJ5i_VuiFfyppFEryoCdDBWhVUK6okwxGqu4FF9FFEKGh9pF8iQayfgG8Gmt0BCKJWxiudBxmXG4pokxpa8BgKcypU9VVk2vDzu0Cqw05q6o2uw2p81UU1YBA2wKuE4-h0lUl5j0uofAYM4sw08SVRwdiU0Lq2K1vU7h28jgmO2Utw9WaBorwa60SE9Cfw8Bwct0e2tm0qe8Ow2kRg47gaQ019Jw0x7w0Gbw62w3q9FUbE1mE0pio0VS",
                "__hsdp": self._generate_hsdp(),
                "__hblp": self._generate_hblp(),
                "__sjsp": self._generate_sjsp(),
                "__comet_req": "7",
                "fb_dtsg": self._get_fb_dtsg(),
                "jazoest": str(random.randint(20000, 30000)),
                "lsd": self._get_lsd(),
                "__spin_r": "1027767997",
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "__crn": "comet.igweb.PolarisPostRouteNext",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "usePolarisLikeMediaLikeMutation",
                "variables": json.dumps({
                    "media_id": media_id,
                    "container_module": "single_post"
                }, separators=(',', ':')),
                "server_timestamps": "true",
                "doc_id": "23951234354462179"
            }
            
            # Headers EXACTEMENT comme exemple
            headers = {
                "host": "www.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": "\"Not)A;Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"138.0.7204.179\", \"Google Chrome\";v=\"138.0.7204.179\"",
                "sec-ch-ua-platform": "\"Android\"",
                "x-root-field-name": "xdt_mark_media_like",
                "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
                "sec-ch-ua-model": f'"{device_settings.get("model", "SM-G988N")}"',
                "sec-ch-ua-mobile": "?1",
                "x-ig-app-id": "1217981644879628",
                "x-fb-lsd": self._get_lsd(),
                "content-type": "application/x-www-form-urlencoded",
                "x-csrftoken": cookies_data.get("csrftoken", ""),
                "x-fb-friendly-name": "usePolarisLikeMediaLikeMutation",
                "x-bloks-version-id": "c510c52d2e632f2477f6a1cb69ca1734c0ea54d761300fa1f170bc676047eeca",
                "x-asbd-id": "359341",
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": device_settings.get("user_agent", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"),
                "dnt": "1",
                "sec-ch-ua-platform-version": f'"{device_settings.get("platform_version", "9.0.0")}"',
                "accept": "*/*",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": media_url,
                "accept-language": "fr,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6,mg;q=0.5"
            }
            
            # Construire cookie string depuis session
            cookie_parts = []
            for name, value in cookies_data.items():
                cookie_parts.append(f"{name}={value}")
            
            # Ajouter cookies additionnels si nécessaires
            additional_cookies = {
                "wd": f"{device_settings.get('viewport_width', 450)}x{device_settings.get('screen_height', 776)}",
                "rur": f"\"CLN\\\\054{user_id}\\\\054{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}\""
            }
            
            for name, value in additional_cookies.items():
                if name not in cookies_data:
                    cookie_parts.append(f"{name}={value}")
            
            headers["cookie"] = "; ".join(cookie_parts)
            
            # Faire requête GraphQL
            response = self.auth.session.post(
                "https://www.instagram.com/graphql/query",
                data=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                # Vérifier succès GraphQL
                if (isinstance(parsed_data, dict) and 
                    ("data" in parsed_data or "status" in str(parsed_data).lower())):
                    return {"success": True, "data": parsed_data}
                else:
                    return {"success": False, "error": "Échec GraphQL like"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception:
            return {"success": False, "error": "Erreur GraphQL like"}
    def _get_real_comment_ids(self, media_id: str) -> list:
        """Récupérer IDs de commentaires RÉELS du média"""
        try:
            headers = self._build_complete_headers_enhanced(
                endpoint="comments",
                friendly_name=f"IgApi: media/{media_id}/comments/"
            )
            
            params = {"count": "10", "max_id": ""}
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/media/{media_id}/comments/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and "comments" in data:
                    comments = data["comments"]
                    comment_ids = [str(comment.get("pk", "")) for comment in comments[:3]]
                    return comment_ids if comment_ids else []
            
            return []
            
        except Exception:
            return []

    def _generate_user_breadcrumb(self, comment_length: int) -> str:
        """Générer user breadcrumb DYNAMIQUE basé sur texte réel"""
        import base64
        
        # Données dynamiques basées sur le commentaire
        timestamp = int(time.time() * 1000) + random.randint(100, 999)
        
        # Générer hash basé sur longueur commentaire + timestamp
        hash_input = f"{comment_length}{timestamp}breadcrumb"
        import hashlib
        hash_value = hashlib.sha256(hash_input.encode()).digest()
        hash_b64 = base64.b64encode(hash_value).decode()[:43]
        
        # Données timing réalistes pour saisie
        typing_data = f"MTMgMjgzOSAxIDE3NTc4NDAzMTc2NTI="  # Base template
        
        return f"{hash_b64}\\n{typing_data}\\n"

    def _pre_comment_requests(self, media_id: str) -> bool:
        """Requêtes préparatoires pour comment EXACTEMENT comme exemples"""
        try:
            user_id = self._get_user_id_from_session()
            
            # 1. REQUÊTE stream_comments/ EXACTEMENT comme exemple
            comments_headers = self._build_complete_headers_enhanced(
                endpoint="feed_contextual_profile",
                friendly_name=f"IgApi: media/{media_id}/stream_comments/"
            )
            
            # Transfer encoding pour stream comments
            comments_headers["x-ig-transfer-encoding"] = "chunked"
            
            params = {
                "should_fetch_creator_comment_nudge": "true",
                "can_support_threading": "true",
                "is_carousel_bumped_post": "false",
                "feed_position": "1"
            }
            
            response1 = self.auth.session.get(
                f"https://i.instagram.com/api/v1/media/{media_id}/stream_comments/",
                headers=comments_headers,
                params=params,
                timeout=10
            )
            
            # 2. REQUÊTE nudges/generate_nudge/ (loading) EXACTEMENT comme exemple
            nudge_data_loading = {
                "is_bottom_sheet_open": "true",
                "media_id": media_id,
                "source": "loading",
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "viewed_comment_ids": "[]"
            }
            
            nudge_headers_loading = self._build_complete_headers_enhanced(
                endpoint="feed_contextual_profile",
                friendly_name="IgApi: nudges/generate_nudge/"
            )
            
            # Salt IDs pour nudge loading
            salt_ids = self._get_salt_ids()
            if len(salt_ids) >= 2:
                nudge_headers_loading["x-ig-salt-ids"] = f"{salt_ids[0]},{salt_ids[1]}"
            
            payload_loading = urllib.parse.urlencode(nudge_data_loading)
            
            response2 = self.auth.session.post(
                "https://i.instagram.com/api/v1/nudges/generate_nudge/",
                headers=nudge_headers_loading,
                data=payload_loading,
                timeout=10
            )
            
            # 3. REQUÊTE nudges/generate_nudge/ (commenting) avec commentaires RÉELS  
            real_comment_ids = self._get_real_comment_ids(media_id)
            viewed_comments = json.dumps(real_comment_ids) if real_comment_ids else '["18015200561598574","18081832975928388","18519526501025741"]'
            
            nudge_data_commenting = {
                "is_bottom_sheet_open": "true",
                "media_id": media_id,
                "source": "commenting",
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "viewed_comment_ids": viewed_comments
            }
            
            nudge_headers_commenting = self._build_complete_headers_enhanced(
                endpoint="comments_v2_feed_contextual_profile",
                friendly_name="IgApi: nudges/generate_nudge/"
            )
            
            # Nav chain mise à jour pour commenting
            nudge_headers_commenting["x-ig-nav-chain"] = self._get_dynamic_nav_chain("comment")
            
            payload_commenting = urllib.parse.urlencode(nudge_data_commenting)
            
            response3 = self.auth.session.post(
                "https://i.instagram.com/api/v1/nudges/generate_nudge/",
                headers=nudge_headers_commenting,
                data=payload_commenting,
                timeout=10
            )
            
            return True
            
        except Exception:
            return True
    def _navigate_to_media_page(self, media_id: str) -> dict:
        """Naviguer vers la page du média pour récupérer cookies et RUR frais"""
        try:
            # Convertir media_id en shortcode
            shortcode = self.media_id_to_shortcode(media_id)
            media_url = f"https://www.instagram.com/p/{shortcode}/"
            
            # Récupérer user-agent de session
            device_settings = self.session_data.get("device_settings", {})
            user_agent = device_settings.get("user_agent", "") or self.session_data.get("user_agent", "")
            
            if not user_agent:
                android_version = device_settings.get("android_version", "10")
                model = device_settings.get("model", "K")
                user_agent = f'Mozilla/5.0 (Linux; Android {android_version}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36'
            
            # Headers pour navigation
            headers = {
                "authority": "www.instagram.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "sec-ch-ua": '"Chromium";v="110", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "upgrade-insecure-requests": "1",
                "user-agent": user_agent
            }
            
            # Copier les cookies actuels
            session = requests.Session()
            cookies_data = self.session_data.get("cookies", {})
            for name, value in cookies_data.items():
                session.cookies.set(name, value)
            
            # Ajouter cookies de la session auth principale
            for cookie in self.auth.session.cookies:
                session.cookies.set(cookie.name, cookie.value)
            
            # Naviguer vers la page (sans suivre redirections)
            response = session.get(
                media_url,
                headers=headers,
                timeout=10,
                allow_redirects=False
            )
            
            # Récupérer NOUVEAUX cookies de la réponse
            new_cookies = {}
            if hasattr(response.cookies, 'get_dict'):
                new_cookies = response.cookies.get_dict()
            
            # Mettre à jour les cookies IMPORTANTS
            important_cookies = ['csrftoken', 'sessionid', 'ds_user_id', 'ig_did', 'mid', 'datr', 'rur']
            
            updated_cookies = {}
            for cookie_name in important_cookies:
                if cookie_name in new_cookies:
                    # Mettre à jour session_data
                    self.session_data["cookies"][cookie_name] = new_cookies[cookie_name]
                    updated_cookies[cookie_name] = new_cookies[cookie_name]
                    
                    # Mettre à jour la session auth principale
                    self.auth.session.cookies.set(cookie_name, new_cookies[cookie_name])
            
            # Extraire également le RUR du header Set-Cookie si présent
            if 'set-cookie' in response.headers:
                set_cookie_header = response.headers['set-cookie']
                if 'rur=' in set_cookie_header:
                    # Extraire le nouveau rur
                    rur_match = re.search(r'rur=([^;]+)', set_cookie_header)
                    if rur_match:
                        new_rur = rur_match.group(1)
                        self.session_data["cookies"]["rur"] = new_rur
                        updated_cookies["rur"] = new_rur
                        self.auth.session.cookies.set("rur", new_rur)
            
            # Récupérer aussi le x-csrftoken du header si présent
            if 'x-csrftoken' in response.headers:
                new_csrf = response.headers['x-csrftoken']
                self.session_data["cookies"]["csrftoken"] = new_csrf
                updated_cookies["csrftoken"] = new_csrf
                self.auth.session.cookies.set("csrftoken", new_csrf)
            
            return {
                "success": True,
                "updated_cookies": updated_cookies,
                "has_rur": "rur" in updated_cookies,
                "status_code": response.status_code,
                "media_url": media_url
            }
            
        except Exception as e:
            return {"success": False, "error": f"Navigation échouée: {str(e)}"}
    
    def _navigate_to_profile_page(self, username: str) -> dict:
        """Naviguer vers la page de profil pour récupérer cookies et RUR frais"""
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            
            # Récupérer user-agent de session
            device_settings = self.session_data.get("device_settings", {})
            user_agent = device_settings.get("user_agent", "") or self.session_data.get("user_agent", "")
            
            if not user_agent:
                android_version = device_settings.get("android_version", "10")
                model = device_settings.get("model", "K")
                user_agent = f'Mozilla/5.0 (Linux; Android {android_version}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36'
            
            # Headers pour navigation
            headers = {
                "authority": "www.instagram.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "sec-ch-ua": '"Chromium";v="110", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "upgrade-insecure-requests": "1",
                "user-agent": user_agent
            }
            
            # Copier les cookies actuels
            session = requests.Session()
            cookies_data = self.session_data.get("cookies", {})
            for name, value in cookies_data.items():
                session.cookies.set(name, value)
            
            # Ajouter cookies de la session auth principale
            for cookie in self.auth.session.cookies:
                session.cookies.set(cookie.name, cookie.value)
            
            # Naviguer vers la page (sans suivre redirections)
            response = session.get(
                profile_url,
                headers=headers,
                timeout=10,
                allow_redirects=False
            )
            
            # Récupérer NOUVEAUX cookies de la réponse
            new_cookies = {}
            if hasattr(response.cookies, 'get_dict'):
                new_cookies = response.cookies.get_dict()
            
            # Mettre à jour les cookies IMPORTANTS
            important_cookies = ['csrftoken', 'sessionid', 'ds_user_id', 'ig_did', 'mid', 'datr', 'rur']
            
            updated_cookies = {}
            for cookie_name in important_cookies:
                if cookie_name in new_cookies:
                    # Mettre à jour session_data
                    self.session_data["cookies"][cookie_name] = new_cookies[cookie_name]
                    updated_cookies[cookie_name] = new_cookies[cookie_name]
                    
                    # Mettre à jour la session auth principale
                    self.auth.session.cookies.set(cookie_name, new_cookies[cookie_name])
            
            # Extraire également le RUR du header Set-Cookie si présent
            if 'set-cookie' in response.headers:
                set_cookie_header = response.headers['set-cookie']
                if 'rur=' in set_cookie_header:
                    # Extraire le nouveau rur
                    rur_match = re.search(r'rur=([^;]+)', set_cookie_header)
                    if rur_match:
                        new_rur = rur_match.group(1)
                        self.session_data["cookies"]["rur"] = new_rur
                        updated_cookies["rur"] = new_rur
                        self.auth.session.cookies.set("rur", new_rur)
            
            # Récupérer aussi le x-csrftoken du header si présent
            if 'x-csrftoken' in response.headers:
                new_csrf = response.headers['x-csrftoken']
                self.session_data["cookies"]["csrftoken"] = new_csrf
                updated_cookies["csrftoken"] = new_csrf
                self.auth.session.cookies.set("csrftoken", new_csrf)
            
            return {
                "success": True,
                "updated_cookies": updated_cookies,
                "has_rur": "rur" in updated_cookies,
                "status_code": response.status_code,
                "profile_url": profile_url
            }
            
        except Exception as e:
            return {"success": False, "error": f"Navigation échouée: {str(e)}"}
    
    def _get_fresh_rur_and_csrf(self, target_url: str) -> dict:
        """Obtenir RUR et CSRF frais en naviguant vers une URL"""
        try:
            # Récupérer user-agent de session
            device_settings = self.session_data.get("device_settings", {})
            user_agent = device_settings.get("user_agent", "") or self.session_data.get("user_agent", "")
            
            if not user_agent:
                android_version = device_settings.get("android_version", "10")
                model = device_settings.get("model", "K")
                user_agent = f'Mozilla/5.0 (Linux; Android {android_version}; {model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36'
            
            # Headers pour navigation
            headers = {
                "authority": "www.instagram.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "sec-ch-ua": '"Chromium";v="110", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "upgrade-insecure-requests": "1",
                "user-agent": user_agent
            }
            
            # Copier les cookies actuels
            session = requests.Session()
            cookies_data = self.session_data.get("cookies", {})
            for name, value in cookies_data.items():
                session.cookies.set(name, value)
            
            # Ajouter cookies de la session auth principale
            for cookie in self.auth.session.cookies:
                session.cookies.set(cookie.name, cookie.value)
            
            # Naviguer vers l'URL (sans suivre redirections)
            response = session.get(
                target_url,
                headers=headers,
                timeout=10,
                allow_redirects=False
            )
            
            # Variables pour nouveaux cookies
            new_rur = None
            new_csrf = None
            
            # 1. Extraire RUR des headers Set-Cookie
            if 'set-cookie' in response.headers:
                set_cookie_header = response.headers['set-cookie']
                if 'rur=' in set_cookie_header:
                    rur_match = re.search(r'rur=([^;]+)', set_cookie_header)
                    if rur_match:
                        new_rur = rur_match.group(1)
            
            # 2. Extraire CSRF des headers
            if 'x-csrftoken' in response.headers:
                new_csrf = response.headers['x-csrftoken']
            
            # 3. Extraire aussi des cookies de réponse
            response_cookies = {}
            if hasattr(response.cookies, 'get_dict'):
                response_cookies = response.cookies.get_dict()
            
            if not new_rur and 'rur' in response_cookies:
                new_rur = response_cookies['rur']
            
            if not new_csrf and 'csrftoken' in response_cookies:
                new_csrf = response_cookies['csrftoken']
            
            # 4. Mettre à jour la session si nouveaux cookies trouvés
            if new_rur:
                self.session_data["cookies"]["rur"] = new_rur
                self.auth.session.cookies.set("rur", new_rur)
            
            if new_csrf:
                self.session_data["cookies"]["csrftoken"] = new_csrf
                self.auth.session.cookies.set("csrftoken", new_csrf)
            
            return {
                "success": True,
                "new_rur": new_rur,
                "new_csrf": new_csrf,
                "has_updates": bool(new_rur or new_csrf),
                "status_code": response.status_code
            }
            
        except Exception as e:
            return {"success": False, "error": f"Échec récupération RUR/CSRF: {str(e)}"}
    

    def _like_post_internal(self, media_input: str) -> dict:
        """Liker un post Instagram - API MOBILE avec headers et endpoint mobile"""
        try:
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}

            # Extraction media ID (votre méthode existante)
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_input)
            else:
                media_id = self._extract_media_id_basic(media_input)

            if not media_id:
                return {"success": False, "error": "Ce media a ete supprime"}

            # Récupérer les données de session mobiles
            device_settings = self.session_data.get("device_settings", {})
            device_info = self.session_data.get("device_info", {})
            cookies_data = self.session_data.get("cookies", {})
            uuids = self.session_data.get("uuids", {})
            authorization_data = self.session_data.get("authorization_data", {})

            # Récupérer le user-agent mobile DE SESSION
            user_agent_mobile = device_settings.get("user_agent_mobile", "")
            if not user_agent_mobile:
                user_agent_mobile = device_info.get("user_agent_mobile", "")
            if not user_agent_mobile:
                user_agent_mobile = self.session_data.get("user_agent_mobile", "")

            # Fallback si user_agent_mobile introuvable
            if not user_agent_mobile:
                android_version = device_settings.get("android_version", "14")
                model = device_settings.get("model", "SM-G991B")
                user_agent_mobile = f"Instagram 307.0.0.34.111 Android ({android_version}/{android_version}; 216dpi; 1312x2947; samsung; {model}; z3q; mt6989; fr_FR; 370711637)"

            # Récupérer les UUIDs de session
            phone_uuid = uuids.get("phone_id", str(uuid.uuid4()))
            device_uuid = uuids.get("uuid", str(uuid.uuid4()))
            android_id = uuids.get("device_id", "android-72d917a0a4b845a0")

            # Récupérer les tokens d'authentification
            csrf_token = cookies_data.get("csrftoken", "")
            sessionid = cookies_data.get("sessionid", "")
            ds_user_id = cookies_data.get("ds_user_id", "")
            rur = cookies_data.get("rur", "")

            # Récupérer authorization header si disponible
            auth_header = authorization_data.get("authorization_header", "")
            if not auth_header:
                auth_header = self.session_data.get("authorization", "")

            # Récupérer X-IG-WWW-Claim depuis les ig_headers ou authorization_data
            ig_headers = self.session_data.get("ig_headers", {})
            x_ig_www_claim = ig_headers.get("x-ig-www-claim", "")
            if not x_ig_www_claim:
                x_ig_www_claim = cookies_data.get("x-ig-www-claim", "0")

            # Headers mobile exacts comme dans le script (SANS Cookie, juste Authorization)
            headers = {
                "User-Agent": user_agent_mobile,
                "Accept": "*/*",
                "Accept-Language": "fr-FR, en-US",
                "Accept-Encoding": "gzip, deflate",
                "X-IG-App-ID": "567067343352427",
                "X-IG-App-Locale": "fr_FR",
                "X-IG-Device-Locale": "fr_FR",
                "X-IG-Device-ID": phone_uuid,
                "X-IG-Android-ID": android_id,
                "X-IG-Connection-Type": "WIFI",
                "X-IG-Capabilities": "3brTvwE=",
                "X-IG-Bandwidth-Speed-KBPS": "2500.000",
                "X-IG-Bandwidth-TotalBytes-B": "1234567",
                "X-IG-Bandwidth-TotalTime-MS": "500",
                "X-Pigeon-Rawclienttime": str(round(time.time(), 3)),
                "X-FB-HTTP-Engine": "Liger",
                "Authorization": auth_header if auth_header else f"Bearer IGT:2:{sessionid}",
                "X-IG-WWW-Claim": x_ig_www_claim,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Connection": "keep-alive",
            }

            # Body de la requête
            body_data = {
                "_uuid": phone_uuid,
                "_uid": ds_user_id or user_id,
                "_csrftoken": csrf_token,
                "media_id": media_id,
                "radio_type": "wifi-none",
                "is_carousel_bumped_post": "false",
                "container_module": "feed_timeline",
                "feed_position": "0",
                "inventory_source": "media_or_ad",
            }

            # IMPORTANT: Utiliser requests avec vérification manuelle des redirections
            import requests
            session = requests.Session()

            # NE PAS copier les cookies - on utilise uniquement Authorization header

            # Faire la requête avec un timeout court
            start_time = time.time()
            try:
                # Endpoint MOBILE pour liker
                response = session.post(
                    f"https://i.instagram.com/api/v1/media/{media_id}/like/",
                    headers=headers,
                    data=body_data,
                    timeout=10,
                    allow_redirects=False,
                    verify=True
                )

                elapsed_time = time.time() - start_time

                # VÉRIFIER LA REDIRECTION MANUELLEMENT
                if 300 <= response.status_code < 400:
                    location = response.headers.get('Location', '')
                    if 'instagram.com/' in location:
                        return {
                            "success": False,
                            "error": "redirect_detected",
                            "should_fallback": True,
                            "redirect_location": location,
                            "status_code": response.status_code
                        }

                # ANALYSER LA RÉPONSE POUR DÉTECTER LES ERREURS SPÉCIFIQUES
                response_text = response.text if hasattr(response, 'text') else str(response)

                # 1. VÉRIFIER LE CAS SPÉCIFIQUE "require_login": true
                try:
                    response_json = response.json()
                    if isinstance(response_json, dict):
                        if response_json.get("require_login") == True or response_json.get("message", "").lower() == "login_required":
                            username = self._get_username_from_session()
                            return {
                                "success": False,
                                "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                                "require_login": True
                            }
                except:
                    pass

                # 2. VÉRIFIER "Sorry, this photo has been deleted" DANS LE HTML/TEXT
                if "sorry, this photo has been deleted" in response_text.lower():
                    return {"success": False, "error": "Ce media a ete supprime"}

                # 3. VÉRIFIER COMPTE SUSPENDU (vérification stricte - URL seulement)
                if "/accounts/suspended/" in response_text:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est suspendu, veuillez le régler manuellement"}

                # 4. VÉRIFIER COMPTE DÉSACTIVÉ (vérification stricte - pas juste "disabled" dans le texte)
                if "/accounts/disabled/" in response_text:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est désactivé et ne peut plus être utilisé"}

                # 5. VÉRIFIER DÉCONNEXION (dans le texte)
                if "login_required" in response_text.lower() or "logout_reason" in response_text.lower():
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter"}

                # Votre traitement de réponse existant (seulement si pas d'erreur spécifique détectée)
                if response.status_code == 200:
                    parsed_data = InstagramEncryption.safe_parse_json(response)

                    if InstagramEncryption.is_success_response(response, parsed_data):
                        # PAS de mise à jour des cookies - on utilise uniquement Authorization header
                        return {"success": True, "data": parsed_data}
                    else:
                        return self.handle_action_error(response.status_code, parsed_data,
                                                     InstagramEncryption.safe_decode_response(response))
                elif response.status_code == 500:
                    return {"success": False, "error": "Erreur lors de l'action"}
                else:
                    if response.status_code == 400 or response.status_code == 401 or response.status_code == 403:
                        parsed_data = InstagramEncryption.safe_parse_json(response)
                        return self.handle_action_error(response.status_code, parsed_data,
                                                     InstagramEncryption.safe_decode_response(response))

                    return self.handle_http_error(response.status_code,
                                                InstagramEncryption.safe_decode_response(response))

            except requests.exceptions.Timeout:
                # TIMEOUT = Instagram ne répond pas, probablement rate limit
                return {
                    "success": False,
                    "error": "timeout_detected",
                    "should_fallback": True,
                    "timeout": True
                }

            except requests.exceptions.ConnectionError as e:
                # ERREUR DE CONNEXION = Problème réseau
                return {
                    "success": False,
                    "error": "connection_error",
                    "should_fallback": True,
                    "connection_error": str(e)
                }

        except Exception as e:
            return {"success": False, "error": "Ce media a ete supprime"}
    def _follow_user_internal(self, user_input: str) -> dict:
        """Suivre un utilisateur - API MOBILE avec headers et endpoint mobile (comme fallback)"""
        try:
            user_id = None

            # Extraction user ID (votre méthode existante)
            if self.api:
                user_id = self.api.extract_user_id_from_url_no_session(user_input)

            if not user_id:
                username_match = re.search(r'instagram\.com/([^/?]+)', user_input)
                if username_match:
                    target_username = username_match.group(1).replace('@', '').strip()
                    user_id = self._search_similar_username(target_username)

                if not user_id:
                    return {"success": False, "error": "Utilisateur introuvable"}

            current_user_id = self._get_user_id_from_session()
            if not current_user_id:
                return {"success": False, "error": "Erreur lors de l'action"}

            # Récupérer username pour l'URL
            username = ""
            if self.api:
                user_info = self.api.get_user_info(user_id)
                username = user_info.get("username", "")

            if not username:
                # Extraire depuis l'URL
                match = re.search(r'instagram\.com/([^/?]+)', user_input)
                if match:
                    username = match.group(1).replace('@', '').strip()
                else:
                    username = f"user{user_id}"

            # Device headers depuis session
            device_headers = self._get_device_specific_headers()

            # Données follow MINIMALES
            follow_data = {
                "_uuid": device_headers["x-ig-device-id"],
                "device_id": device_headers["x-ig-android-id"],
                "radio_type": self._get_radio_type(),
                "user_id": user_id
            }

            # Signature MINIMALE
            signed_body = InstagramEncryption.create_signed_body(follow_data)

            # Headers MINIMAUX exactement comme fallback (SANS Cookie, juste Authorization)
            headers = {
                "user-agent": device_headers["user-agent"],
                "accept": "*/*",
                "accept-language": "fr-FR, en-US",
                "connection": "keep-alive",
                "x-ig-app-locale": "fr_FR",
                "x-ig-device-locale": "fr_FR",
                "x-ig-mapped-locale": "fr_FR",
                "x-pigeon-session-id": self._get_pigeon_session_id(),
                "x-pigeon-rawclienttime": str(time.time()),
                "x-ig-bandwidth-speed-kbps": self._get_bandwidth_test_data()["speed_kbps"],
                "x-ig-bandwidth-totalbytes-b": self._get_bandwidth_test_data()["total_bytes"],
                "x-ig-bandwidth-totaltime-ms": self._get_bandwidth_test_data()["total_time_ms"],
                "x-ig-app-startup-country": "FR",
                "x-bloks-version-id": self.session_data.get("session_metadata", {}).get("bloks_version_id", "ce555e5500576acd8e84a66018f54a05720f2dce29f0bb5a1f97f0c10d6fac48"),
                "x-ig-www-claim": "0",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-is-panorama-enabled": "true",
                "x-ig-device-id": device_headers["x-ig-device-id"],
                "x-ig-family-device-id": self.session_data.get("uuids", {}).get("client_session_id", str(uuid.uuid4())),
                "x-ig-android-id": device_headers["x-ig-android-id"],
                "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
                "x-ig-connection-type": "WIFI",
                "x-ig-capabilities": "3brTvx0=",
                "x-ig-app-id": "567067343352427",
                "priority": "u=3",
                "x-mid": self.get_x_mid(),
                "host": "i.instagram.com",
                "x-fb-http-engine": "Liger",
                "x-fb-client-ip": "True",
                "x-fb-server-cluster": "True",
                "ig-intended-user-id": current_user_id,
                "x-ig-nav-chain": "9MV:self_profile:2,ProfileMediaTabFragment:self_profile:3,9Xf:self_following:4",
                "x-ig-salt-ids": str(self._get_salt_ids()[0]) if self._get_salt_ids() else "1061254442",
                "authorization": self._get_auth_token(),
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
            }

            # IMPORTANT: Utiliser requests avec vérification manuelle des redirections
            import requests
            session = requests.Session()

            # NE PAS copier les cookies - on utilise uniquement Authorization header

            # Faire la requête avec un timeout court
            start_time = time.time()
            try:
                # Endpoint MOBILE pour follow (exactement comme fallback)
                response = session.post(
                    f"https://i.instagram.com/api/v1/friendships/create/{user_id}/",
                    headers=headers,
                    data={"signed_body": signed_body},
                    timeout=10,
                    allow_redirects=False,
                    verify=True
                )
                
                elapsed_time = time.time() - start_time
                
                # VÉRIFIER LA REDIRECTION MANUELLEMENT
                # Si status 3xx et Location header contient instagram.com/ (redirection vers homepage)
                if 300 <= response.status_code < 400:
                    location = response.headers.get('Location', '')
                    if 'instagram.com/' in location:
                        # REDIRECTION DÉTECTÉE VERS INSTAGRAM = DOIT FAIRE FALLBACK
                        return {
                            "success": False, 
                            "error": "redirect_detected", 
                            "should_fallback": True,
                            "redirect_location": location,
                            "status_code": response.status_code
                        }
                
                # ANALYSER LA RÉPONSE POUR DÉTECTER LES ERREURS SPÉCIFIQUES
                response_text = response.text if hasattr(response, 'text') else str(response)
                
                # 1. VÉRIFIER LE CAS SPÉCIFIQUE "require_login": true (IMPORTANT!)
                try:
                    response_json = response.json()
                    if isinstance(response_json, dict):
                        # Vérifier require_login explicitement
                        if response_json.get("require_login") == True:
                            username = self._get_username_from_session()
                            return {
                                "success": False, 
                                "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                                "require_login": True
                            }
                        # Vérifier aussi le message "login_required"
                        if response_json.get("message", "").lower() == "login_required":
                            username = self._get_username_from_session()
                            return {
                                "success": False, 
                                "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                                "require_login": True
                            }
                        # Vérifier status "fail" avec message de déconnexion
                        if (response_json.get("status") == "fail" and 
                            ("patienter" in response_json.get("message", "").lower() or
                             "try again" in response_json.get("message", "").lower() or
                             "wait" in response_json.get("message", "").lower())):
                            username = self._get_username_from_session()
                            return {
                                "success": False, 
                                "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                                "require_login": True
                            }
                except:
                    pass
                
                # 2. VÉRIFIER COMPTE SUSPENDU (vérification stricte - URL seulement)
                if "/accounts/suspended/" in response_text:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est suspendu, veuillez le régler manuellement"}

                # 3. VÉRIFIER COMPTE DÉSACTIVÉ (vérification stricte - pas juste "disabled" dans le texte)
                if "/accounts/disabled/" in response_text:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est désactivé et ne peut plus être utilisé"}

                # 4. VÉRIFIER DÉCONNEXION (dans le texte)
                if "login_required" in response_text.lower() or "logout_reason" in response_text.lower():
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter"}

                # Votre traitement de réponse existant
                if response.status_code == 200:
                    parsed_data = InstagramEncryption.safe_parse_json(response)

                    if InstagramEncryption.is_success_response(response, parsed_data):
                        # PAS de mise à jour des cookies - on utilise uniquement Authorization header
                        return {"success": True, "data": parsed_data}
                    else:
                        return self.handle_action_error(response.status_code, parsed_data,
                                                     InstagramEncryption.safe_decode_response(response))
                elif response.status_code == 500:
                    return {"success": False, "error": "Erreur lors de l'action"}
                else:
                    if response.status_code == 400 or response.status_code == 401 or response.status_code == 403:
                        parsed_data = InstagramEncryption.safe_parse_json(response)
                        return self.handle_action_error(response.status_code, parsed_data, 
                                                     InstagramEncryption.safe_decode_response(response))
                    
                    return self.handle_http_error(response.status_code, 
                                                InstagramEncryption.safe_decode_response(response))
                    
            except requests.exceptions.Timeout:
                # TIMEOUT = Instagram ne répond pas, probablement rate limit
                return {
                    "success": False, 
                    "error": "timeout_detected", 
                    "should_fallback": True,
                    "timeout": True
                }
                
            except requests.exceptions.ConnectionError as e:
                # ERREUR DE CONNEXION = Problème réseau
                return {
                    "success": False, 
                    "error": "connection_error", 
                    "should_fallback": True,
                    "connection_error": str(e)
                }
                
        except Exception as e:
            return {"success": False, "error": "Utilisateur introuvable"}
    def _comment_post_internal(self, media_input: str, comment_text: str) -> dict:
        """Commenter un post Instagram - WEB D'ABORD puis fallback API mobile avec User-Agent de session"""
        try:
            if not comment_text or comment_text.strip() == "":
                return {"success": False, "error": "Le commentaire ne peut pas être vide"}
            
            # ÉTAPE 1: Extraction media_id (votre méthode existante)
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_input)
            else:
                media_id = self._extract_media_id_basic(media_input)
            
            if not media_id:
                return {"success": False, "error": "Ce média a été supprimé"}
            
            # Convertir media_id en shortcode pour l'URL
            shortcode = self.media_id_to_shortcode(media_id)
            
            # ÉTAPE CRITIQUE: NAVIGUER VERS LA PAGE POUR RÉCUPÉRER RUR/CSRF FRAIS
            media_url = f"https://www.instagram.com/p/{shortcode}/"
            navigation_result = self._get_fresh_rur_and_csrf(media_url)
            # On continue même si navigation échoue, on utilise les cookies existants
            
            # RÉCUPÉRER LE USER-AGENT EXACT DE LA SESSION SANS JAMAIS LE GÉNÉRER
            # 1. D'abord chercher dans device_settings
            device_settings = self.session_data.get("device_settings", {})
            user_agent = device_settings.get("user_agent", "")
            
            # 2. Si pas trouvé, chercher dans device_info
            if not user_agent:
                device_info = self.session_data.get("device_info", {})
                user_agent = device_info.get("user_agent", "")
            
            # 3. Si pas trouvé, chercher à la racine de session_data
            if not user_agent:
                user_agent = self.session_data.get("user_agent", "")
            
            # 4. Si VRAIMENT pas trouvé (ne devrait jamais arriver), fallback minimal
            if not user_agent:
                # Récupérer les infos minimales depuis session pour construire User-Agent
                android_version = device_settings.get("android_version", "10")
                model = device_settings.get("model", "K")
                user_agent = (
                    f'Mozilla/5.0 (Linux; Android {android_version}; {model}) '
                    f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36'
                )
            
            # Récupérer csrf_token depuis les cookies SESSION (MAINTENANT FRAIS si navigation réussie)
            cookies_data = self.session_data.get("cookies", {})
            csrf_token = cookies_data.get("csrftoken", "")
            
            # Récupérer rur depuis les cookies de session (MAINTENANT FRAIS si navigation réussie)
            rur_cookie = cookies_data.get("rur", "")
            
            # Headers comme dans le script 2 MAIS AVEC USER-AGENT DE SESSION
            headers = {
                "authority": "www.instagram.com",
                "accept": "*/*",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://www.instagram.com",
                "referer": media_url,
                "sec-ch-ua": '"Chromium";v="110", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": user_agent,  # ← USER-AGENT DE SESSION
                "x-asbd-id": "198387",
                "x-csrftoken": csrf_token,
                "x-ig-app-id": "936619743392459",
                "x-ig-www-claim": "0",
                "x-instagram-ajax": str(int(time.time() * 1000))[-10:],
                "x-requested-with": "XMLHttpRequest"
            }
            
            data = {
                "comment_text": comment_text,
                "replied_to_comment_id": ""
            }
            
            # IMPORTANT: Utiliser requests avec vérification manuelle des redirections
            import requests
            session = requests.Session()
            
            # Copier les cookies depuis la session ACTUELLE (MAINTENANT FRAIS)
            for name, value in cookies_data.items():
                session.cookies.set(name, value)
            
            # Copier aussi les cookies de la session auth principale (DÉJÀ MIS À JOUR par _get_fresh_rur_and_csrf)
            for cookie in self.auth.session.cookies:
                session.cookies.set(cookie.name, cookie.value)
            
            # IMPORTANT: Utiliser le rur ACTUEL (frais) de la session
            if rur_cookie:
                session.cookies.set("rur", rur_cookie)
            
            # Faire la requête avec un timeout court et gestion manuelle des redirections
            start_time = time.time()
            try:
                response = session.post(
                    f"https://www.instagram.com/api/v1/web/comments/{media_id}/add/",
                    headers=headers,
                    data=data,
                    timeout=10,  # Timeout court pour détecter les problèmes
                    allow_redirects=False,  # IMPORTANT: Ne pas suivre les redirections
                    verify=True
                )
                
                elapsed_time = time.time() - start_time
                
                # VÉRIFIER LA REDIRECTION MANUELLEMENT
                # Si status 3xx et Location header contient instagram.com/ (redirection vers homepage)
                if 300 <= response.status_code < 400:
                    location = response.headers.get('Location', '')
                    if 'instagram.com/' in location:
                        # REDIRECTION DÉTECTÉE VERS INSTAGRAM = DOIT FAIRE FALLBACK
                        return {
                            "success": False, 
                            "error": "redirect_detected", 
                            "should_fallback": True,
                            "redirect_location": location,
                            "status_code": response.status_code
                        }
                
                # ANALYSER LA RÉPONSE POUR DÉTECTER LES ERREURS SPÉCIFIQUES
                response_text = response.text if hasattr(response, 'text') else str(response)
                
                # 1. VÉRIFIER LE CAS SPÉCIFIQUE "require_login": true
                try:
                    response_json = response.json()
                    if isinstance(response_json, dict):
                        if response_json.get("require_login") == True or response_json.get("message", "").lower() == "login_required":
                            username = self._get_username_from_session()
                            return {
                                "success": False, 
                                "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter",
                                "require_login": True
                            }
                except:
                    pass
                
                # 2. VÉRIFIER "Sorry, this photo has been deleted" DANS LE HTML/TEXT
                if "sorry, this photo has been deleted" in response_text.lower():
                    return {"success": False, "error": "Ce media a ete supprime"}

                # 3. VÉRIFIER COMPTE SUSPENDU (vérification stricte - URL seulement)
                if "/accounts/suspended/" in response_text:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est suspendu, veuillez le régler manuellement"}

                # 4. VÉRIFIER COMPTE DÉSACTIVÉ (vérification stricte - pas juste "disabled" dans le texte)
                if "/accounts/disabled/" in response_text:
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est désactivé et ne peut plus être utilisé"}

                # 5. VÉRIFIER DÉCONNEXION (dans le texte)
                if "login_required" in response_text.lower() or "logout_reason" in response_text.lower():
                    username = self._get_username_from_session()
                    return {"success": False, "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter"}
                
                # Votre traitement de réponse existant
                if response.status_code == 200:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    
                    if InstagramEncryption.is_success_response(response, parsed_data):
                        # IMPORTANT: Mettre à jour les cookies après la requête
                        self._update_cookies_from_response(session.cookies)
                        return {"success": True, "data": parsed_data}
                    else:
                        return self.handle_action_error(response.status_code, parsed_data, 
                                                     InstagramEncryption.safe_decode_response(response))
                else:
                    if response.status_code == 400 or response.status_code == 401 or response.status_code == 403:
                        parsed_data = InstagramEncryption.safe_parse_json(response)
                        return self.handle_action_error(response.status_code, parsed_data, 
                                                     InstagramEncryption.safe_decode_response(response))
                    
                    return self.handle_http_error(response.status_code, 
                                                InstagramEncryption.safe_decode_response(response))
                    
            except requests.exceptions.Timeout:
                # TIMEOUT = Instagram ne répond pas, probablement rate limit
                return {
                    "success": False, 
                    "error": "timeout_detected", 
                    "should_fallback": True,
                    "timeout": True
                }
                
            except requests.exceptions.ConnectionError as e:
                # ERREUR DE CONNEXION = Problème réseau
                return {
                    "success": False, 
                    "error": "connection_error", 
                    "should_fallback": True,
                    "connection_error": str(e)
                }
                
        except Exception as e:
            return {"success": False, "error": "Ce media a ete supprime"}
    def _update_cookies_from_response(self, response_cookies):
        """Mettre à jour les cookies dans session_data et session auth après une requête"""
        try:
            # Mettre à jour session_data["cookies"]
            if "cookies" not in self.session_data:
                self.session_data["cookies"] = {}
            
            # Extraire tous les cookies de la réponse
            updated_cookies = {}
            
            # Pour httpx
            if hasattr(response_cookies, 'jar'):
                for cookie in response_cookies.jar:
                    updated_cookies[cookie.name] = cookie.value
            # Pour requests
            elif hasattr(response_cookies, 'get_dict'):
                updated_cookies = response_cookies.get_dict()
            # Pour SimpleCookie
            elif hasattr(response_cookies, '_cookies'):
                for domain in response_cookies._cookies.values():
                    for path in domain.values():
                        for cookie in path.values():
                            updated_cookies[cookie.name] = cookie.value
            
            # Mettre à jour les cookies importants
            important_cookies = ['csrftoken', 'sessionid', 'ds_user_id', 'ig_did', 'mid', 'datr', 'rur']
            
            for cookie_name in important_cookies:
                if cookie_name in updated_cookies:
                    # Mettre à jour session_data
                    self.session_data["cookies"][cookie_name] = updated_cookies[cookie_name]
                    
                    # Mettre à jour la session auth principale
                    self.auth.session.cookies.set(cookie_name, updated_cookies[cookie_name])
            
            # Mettre à jour aussi les cookies dans self.auth.session_data si existant
            if hasattr(self.auth, 'session_data') and self.auth.session_data:
                if "cookies" not in self.auth.session_data:
                    self.auth.session_data["cookies"] = {}
                
                for cookie_name, cookie_value in updated_cookies.items():
                    if cookie_name in important_cookies:
                        self.auth.session_data["cookies"][cookie_name] = cookie_value
            
            # Mettre à jour le csrf_token local
            if 'csrftoken' in updated_cookies:
                self.csrf_token = updated_cookies['csrftoken']
                
        except Exception as e:
            # Ne pas bloquer en cas d'erreur de mise à jour des cookies
            pass
    
    def _process_response(self, response) -> dict:
        """Traiter la réponse (méthode utilitaire)"""
        if response.status_code == 200:
            parsed_data = InstagramEncryption.safe_parse_json(response)
            
            if InstagramEncryption.is_success_response(response, parsed_data):
                return {"success": True, "data": parsed_data}
            else:
                return self.handle_action_error(response.status_code, parsed_data, 
                                             InstagramEncryption.safe_decode_response(response))
        else:
            if response.status_code == 400:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                return self.handle_action_error(response.status_code, parsed_data, 
                                             InstagramEncryption.safe_decode_response(response))
            
            return self.handle_http_error(response.status_code, 
                                        InstagramEncryption.safe_decode_response(response))

    def _comment_post_web_graphql(self, media_id: str, comment_text: str, media_url: str) -> dict:
        """Commenter un post via GraphQL web - EXACTEMENT comme l'exemple"""
        try:
            # Récupérer données depuis session
            cookies_data = self.session_data.get("cookies", {})
            device_settings = self.session_data.get("device_settings", {})
            user_id = self._get_user_id_from_session()
            
            # Construire payload GraphQL EXACTEMENT comme exemple
            payload = {
                "av": "17841458636376021",
                "__d": "www",
                "__user": user_id,
                "__a": "1",
                "__req": "10",
                "__hs": "20361.HYP:instagram_web_pkg.2.1...0",
                "dpr": str(device_settings.get("dpr", 2)),
                "__ccg": "POOR",
                "__rev": "1027771144",
                "__s": f"{random.choice(['8ur3kt', '8mol5e', 'utmwsm'])}:{random.choice(['l51egd', 'c6uyd7', 'c8jv84'])}:{random.choice(['krwc7k', 'eailwh', 'c8jv84'])}",
                "__hsi": str(random.randint(7000000000000000000, 8000000000000000000)),
                "__dyn": "7xeUjG1mxu1syUbFp41twpUnwgU7SbzEdF8aUco2qwJxS0k24o0B-q1ew6ywaq0yE462mcw5Mx62G5UswoEcE7O2l0Fwqo31w9O1TwQzXwae4UaEW2G0AEco5G0zK5o4q3y1Swg81gobUGdwtUd-2u2J0bS1LwTwKG1pg2fwxyo6O1FwlA3a3zhA6bwg8rAwCAxW1oxe6UaUaE4e1tyVrx60gm3a7EG3a13AwhES5E",
                "__csr": "gqMsNQQv4iXkRiHv5krmB9PtECgR4Z5mDRQhp4St94g-j-hpeaCKVl-Fbz5ilfy224jDy2oDykK5RyFVt4BGHGELvK4ao-8G9CK2a4pkbKEO7ExCz44oGi8yQUlBGq9oR5BVufAHy9EF2FAmUyq7aCAxeEJxS8xa9zGDGqicCgK7E-4EKEW8ixe1zw-w05q3o12E1Y81WU1WVkga1q1hF0lUl5h07yawHhVcw4ihw0zA80QV80Li2K1wg7h7xi5IEK7o2uypC6U2xw8J0jo9i09ap0cx0d-tm0qe8Ow2kBg47gaQ019Iw0x7w0FXw6Gw3kpqBw5aw1D-4k0evw",
                "__hsdp": self._generate_hsdp(),
                "__hblp": self._generate_hblp(),
                "__sjsp": self._generate_sjsp(),
                "__comet_req": "7",
                "fb_dtsg": self._get_fb_dtsg(),
                "jazoest": str(random.randint(20000, 30000)),
                "lsd": self._get_lsd(),
                "__spin_r": "1027771144",
                "__spin_b": "trunk",
                "__spin_t": str(int(time.time())),
                "__crn": "comet.igweb.PolarisMobileAllCommentsRouteNext",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "PolarisPostCommentInputRevampedMutation",
                "variables": json.dumps({
                    "connections": [f"client:root:__PolarisPostComments__xdt_api__v1__media__media_id__comments__connection_connection(data:{{}},media_id:\\\"{media_id}\\\",sort_order:\\\"popular\\\")"],
                    "request_data": {
                        "comment_text": comment_text
                    },
                    "media_id": media_id
                }, separators=(',', ':')),
                "server_timestamps": "true",
                "doc_id": "24396936719894935"
            }
            
            # Headers EXACTEMENT comme exemple
            headers = {
                "host": "www.instagram.com",
                "connection": "keep-alive",
                "sec-ch-ua-full-version-list": "\"Not)A;Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"138.0.7204.179\", \"Google Chrome\";v=\"138.0.7204.179\"",
                "sec-ch-ua-platform": "\"Android\"",
                "x-root-field-name": "xdt_web__comments__media_id__add_queryable",
                "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
                "sec-ch-ua-model": f'"{device_settings.get("model", "SM-G988N")}"',
                "sec-ch-ua-mobile": "?1",
                "x-ig-app-id": "1217981644879628",
                "x-fb-lsd": self._get_lsd(),
                "content-type": "application/x-www-form-urlencoded",
                "x-csrftoken": cookies_data.get("csrftoken", ""),
                "x-fb-friendly-name": "PolarisPostCommentInputRevampedMutation",
                "x-bloks-version-id": "c510c52d2e632f2477f6a1cb69ca1734c0ea54d761300fa1f170bc676047eeca",
                "x-asbd-id": "359341",
                "sec-ch-prefers-color-scheme": "light",
                "user-agent": device_settings.get("user_agent", "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"),
                "dnt": "1",
                "sec-ch-ua-platform-version": f'"{device_settings.get("platform_version", "9.0.0")}"',
                "accept": "*/*",
                "origin": "https://www.instagram.com",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": f"{media_url}/comments/",
                "accept-language": "fr,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh;q=0.6,mg;q=0.5"
            }
            
            # Construire cookie string depuis session
            cookie_parts = []
            for name, value in cookies_data.items():
                cookie_parts.append(f"{name}={value}")
            
            # Ajouter cookies additionnels si nécessaires
            additional_cookies = {
                "wd": f"{device_settings.get('viewport_width', 450)}x{device_settings.get('screen_height', 720)}",
                "rur": f"\"CLN\\\\054{user_id}\\\\054{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}\""
            }
            
            for name, value in additional_cookies.items():
                if name not in cookies_data:
                    cookie_parts.append(f"{name}={value}")
            
            headers["cookie"] = "; ".join(cookie_parts)
            
            # Faire requête GraphQL
            response = self.auth.session.post(
                "https://www.instagram.com/graphql/query",
                data=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                # Vérifier succès GraphQL
                if (isinstance(parsed_data, dict) and 
                    ("data" in parsed_data or "status" in str(parsed_data).lower())):
                    return {"success": True, "data": parsed_data}
                else:
                    return {"success": False, "error": "Échec GraphQL comment"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception:
            return {"success": False, "error": "Erreur GraphQL comment"}

    # MÉTHODES UTILITAIRES POUR GRAPHQL WEB
    def _get_fb_dtsg(self) -> str:
        """Générer fb_dtsg depuis session"""
        try:
            user_id = self._get_user_id_from_session()
            timestamp = int(time.time())
            
            # Format similaire aux exemples
            return f"NAft{random.choice(['kak4xVY', '3q9TzFE', '53JCO9c'])}06aXac4aB2kisS9FltvZTvThjofb0kJL83KoCBBTJlxA:17843683195144578:{timestamp}"
        except:
            timestamp = int(time.time())
            return f"NAft3q9TzFE0g-PiHfqThUAI1WSsd4Np4bsaMwXsoVsBXocSsqqMiIw:17843683195144578:{timestamp}"

    def _get_lsd(self) -> str:
        """Générer lsd depuis session"""
        try:
            # Format similaire aux exemples
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
            return ''.join(random.choice(chars) for _ in range(22))
        except:
            return "CsUKYi8BhagtG5uOQxpbVc"

    def _generate_hsdp(self) -> str:
        """Générer __hsdp dynamique"""
        try:
            # Patterns similaires aux exemples
            base = "gvMgh7N79b7naxtO4APlf_xFOkbgm5A8ghTd4N2exry"
            suffix = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(50))
            return base + suffix
        except:
            return "gvMgh7N79b7naxtO4APlf_xFOkbgm5A8ghTd4N2exryomK5Enwwwirg4S5k442d2UuxK84Dgk9AxjyEO1S82W2y4t1a3a11wpzx10bK688EaaKi2W3a3y2u322a0Koy0DE2pwuE6y0hW260te0CU56320yqwOw9e0wE2vwOwcy2W0Ez0lE2oUfQGxN7xHoW1vx20VUO2K"

    def _generate_hblp(self) -> str:
        """Générer __hblp dynamique"""
        try:
            # Patterns similaires aux exemples
            base = "0OKbw8G7Eqxt4yFAi13wAz824wpUdUgz8nwzwTO08m9wx"
            suffix = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(80))
            return base + suffix
        except:
            return "0OKbw8G7Eqxt4yFAi13wAz824wpUdUgz8nwzwTO08m9wxGayeGUK6UswHxa2W8x22B0lUb8d8vxLxjwywEG8wGK3a3qU5q2a3qm1Yy86u8wJw9C3e16wq82uwnoS4U8o1087u1qwmUa8mwkovyFpo521Ew9e2G1nw9-3a0FonyElxy0Ez0lE4m1iUftaGxwyixHucg5WE7-bw-z8pKcxOew"

    def _generate_sjsp(self) -> str:
        """Générer __sjsp dynamique"""
        try:
            # Patterns similaires aux exemples
            base = "gvMgh7N79aB5naxtO4APqf_xFOkbgm5A8ghTd4N2exrwwK5Ee84C"
            suffix = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(30))
            return base + suffix
        except:
            return "gvMgh7N79aB5naxtO4APqf_xFOkbgm5A8ghTd4N2exrwwK5Ee84CQ1dxm4o94bxW6UIMy526wxz80Nm0DU9U"
     
    def _generate_comment_nudge(self, media_id: str) -> dict:
        """Étape 1: Generate nudge - COMPLET avec tous headers"""
        try:
            user_id = self._get_user_id_from_session()
            device_headers = self._get_device_specific_headers()
            
            # Payload pour nudge
            nudge_payload = {
                "is_bottom_sheet_open": "true",
                "media_id": media_id,
                "source": "commenting",
                "_uuid": device_headers["x-ig-device-id"],
                "viewed_comment_ids": "[]"
            }
            
            # Headers COMPLETS pour nudge
            bandwidth_data = self._get_bandwidth_test_data()
            ig_headers = self._get_ig_headers()
            app_net_session = self._get_app_net_session_data()
            
            headers = {
                "accept-language": "fr-FR, en-US",
                "authorization": self._get_auth_token(),
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": user_id,
                "ig-u-ds-user-id": user_id,
                "ig-u-rur": ig_headers.get("ig-u-rur", f"CLN,{user_id},{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}"),
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
                "x-bloks-prism-colors-enabled": "true",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-gray-red": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "true",
                "x-bloks-prism-indigo-link-version": "1",
                "x-bloks-version-id": self.session_data.get("session_metadata", {}).get("bloks_version_id", "422d0c0ead50c1ae8a294e5eba90b30255468f80488fcdcdc61c4c1a193f7fa1"),
                "x-fb-client-ip": "True",
                "x-fb-connection-type": self._get_connection_type_headers()["x-fb-connection-type"],
                "x-fb-friendly-name": "IgApi: nudges/generate_nudge/",
                "x-fb-network-properties": self._get_fb_network_properties(),
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": device_headers["x-ig-android-id"],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": bandwidth_data["speed_kbps"],
                "x-ig-bandwidth-totalbytes-b": bandwidth_data["total_bytes"],
                "x-ig-bandwidth-totaltime-ms": bandwidth_data["total_time_ms"],
                "x-ig-client-endpoint": "CommentListBottomsheetFragment:comments_v2_feed_short_url",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": self._get_connection_type_headers()["x-ig-connection-type"],
                "x-ig-device-id": device_headers["x-ig-device-id"],
                "x-ig-device-languages": f'{{"system_languages":"{self.session_data.get("locale", "fr_FR")}"}}',
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.session_data.get("uuids", {}).get("client_session_id", str(uuid.uuid4())),
                "x-ig-is-foldable": "false",
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": self._get_dynamic_nav_chain("comment"),
                "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
                "x-ig-www-claim": ig_headers.get("x-ig-www-claim", "hmac.AR0gigjvYfXDP3sCtKHklnUuIvadPjHaUGCxH3vFP3G_enq9"),
                "x-mid": self.get_x_mid(),
                "x-meta-zca": self._generate_meta_zca(),
                "x-pigeon-rawclienttime": str(time.time()),
                "x-pigeon-session-id": self._get_pigeon_session_id(),
                "x-tigon-is-retry": "False",
                "user-agent": device_headers["user-agent"],
                "x-fb-appnetsession-nid": app_net_session["nid"],
                "x-fb-appnetsession-sid": app_net_session["sid"],
                "x-fb-conn-uuid-client": self._get_conn_uuid_client(),
                "x-fb-http-engine": "Tigon/MNS/TCP",
                "x-fb-rmd": self._get_fb_rmd_state(),
                "x-fb-tasos-experimental": "1",
                "x-fb-tasos-td-config": "prod_signal:1"
            }
            
            # Construire payload URL-encoded
            payload_str = "&".join([f"{k}={v}" for k, v in nudge_payload.items()])
            
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/nudges/generate_nudge/",
                headers=headers,
                data=payload_str,
                timeout=10
            )
            
            return {"success": response.status_code == 200}
            
        except Exception:
            return {"success": False}

    def _check_offensive_comment(self, media_id: str, comment_text: str, comment_session_id: str) -> dict:
        """Étape 2: Check offensive comment - COMPLET avec tous headers"""
        try:
            user_id = self._get_user_id_from_session()
            device_headers = self._get_device_specific_headers()
            
            # Données pour check offensive
            offensive_data = {
                "media_id": media_id,
                "_uid": user_id,
                "comment_session_id": comment_session_id,
                "_uuid": device_headers["x-ig-device-id"],
                "comment_text": comment_text
            }
            
            signed_body = InstagramEncryption.create_signed_body(offensive_data)
            
            # Headers COMPLETS pour check offensive
            bandwidth_data = self._get_bandwidth_test_data()
            salt_ids = self._get_salt_ids()
            ig_headers = self._get_ig_headers()
            app_net_session = self._get_app_net_session_data()
            
            headers = {
                "accept-language": "fr-FR, en-US",
                "authorization": self._get_auth_token(),
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": user_id,
                "ig-u-ds-user-id": user_id,
                "ig-u-rur": ig_headers.get("ig-u-rur", f"CLN,{user_id},{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}"),
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
                "x-bloks-prism-colors-enabled": "true",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-gray-red": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "true",
                "x-bloks-prism-indigo-link-version": "1",
                "x-bloks-version-id": self.session_data.get("session_metadata", {}).get("bloks_version_id", "422d0c0ead50c1ae8a294e5eba90b30255468f80488fcdcdc61c4c1a193f7fa1"),
                "x-fb-client-ip": "True",
                "x-fb-connection-type": self._get_connection_type_headers()["x-fb-connection-type"],
                "x-fb-friendly-name": "IgApi: media/comment/check_offensive_comment/",
                "x-fb-network-properties": self._get_fb_network_properties(),
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": device_headers["x-ig-android-id"],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": bandwidth_data["speed_kbps"],
                "x-ig-bandwidth-totalbytes-b": bandwidth_data["total_bytes"],
                "x-ig-bandwidth-totaltime-ms": bandwidth_data["total_time_ms"],
                "x-ig-client-endpoint": "CommentListBottomsheetFragment:comments_v2_feed_short_url",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": self._get_connection_type_headers()["x-ig-connection-type"],
                "x-ig-device-id": device_headers["x-ig-device-id"],
                "x-ig-device-languages": f'{{"system_languages":"{self.session_data.get("locale", "fr_FR")}"}}',
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.session_data.get("uuids", {}).get("client_session_id", str(uuid.uuid4())),
                "x-ig-is-foldable": "false",
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": self._get_dynamic_nav_chain("comment"),
                "x-ig-salt-ids": str(salt_ids[0]) if salt_ids else "220140399",
                "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
                "x-ig-www-claim": ig_headers.get("x-ig-www-claim", "hmac.AR0gigjvYfXDP3sCtKHklnUuIvadPjHaUGCxH3vFP3G_enq9"),
                "x-mid": self.get_x_mid(),
                "x-meta-zca": self._generate_meta_zca(),
                "x-pigeon-rawclienttime": str(time.time()),
                "x-pigeon-session-id": self._get_pigeon_session_id(),
                "x-tigon-is-retry": "False",
                "user-agent": device_headers["user-agent"],
                "x-fb-appnetsession-nid": app_net_session["nid"],
                "x-fb-appnetsession-sid": app_net_session["sid"],
                "x-fb-conn-uuid-client": self._get_conn_uuid_client(),
                "x-fb-http-engine": "Tigon/MNS/TCP",
                "x-fb-rmd": self._get_fb_rmd_state(),
                "x-fb-tasos-experimental": "1",
                "x-fb-tasos-td-config": "prod_signal:1"
            }
            
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/media/comment/check_offensive_comment/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            return {"success": response.status_code == 200}
            
        except Exception:
            return {"success": False}
    def _post_final_comment(self, media_id: str, comment_text: str) -> dict:
        """Étape 3: Post comment final - COMPLET avec tous headers"""
        try:
            if not comment_text or comment_text.strip() == "":
                return {"success": False, "error": "Le commentaire ne peut pas être vide"}
                
            user_id = self._get_user_id_from_session()
            device_headers = self._get_device_specific_headers()
            
            # Générer user breadcrumb et clés uniques
            user_breadcrumb = self._generate_user_breadcrumb(comment_text)
            creation_key = str(uuid.uuid4())
            
            # Données COMPLÈTES pour comment final - IMPORTANT: comment_text doit être présent
            comment_data = {
                "include_media_code": "true",
                "user_breadcrumb": user_breadcrumb,
                "starting_clips_media_id": "null",
                "comment_creation_key": creation_key,
                "delivery_class": "organic",
                "idempotence_token": creation_key,
                "carousel_child_mentions": "[]",
                "include_e2ee_mentioned_user_list": "true",
                "include_carousel_child_mentions": "false",
                "is_from_carousel_child_thread": "false",
                "carousel_index": "-1",
                "radio_type": self._get_radio_type(),
                "_uid": user_id,
                "is_text_app_xpost_attempt": "false",
                "_uuid": device_headers["x-ig-device-id"],
                "nav_chain": self._get_dynamic_nav_chain("comment"),
                "comment_text": comment_text,  # CRITIQUE: Le texte doit être là
                "recs_ix": "-1",
                "is_carousel_bumped_post": "false",
                "floating_context_items": "[]",
                "container_module": "comments_v2_feed_short_url",
                "feed_position": "0",
                "ranking_session_id": ""
            }
            
            signed_body = InstagramEncryption.create_signed_body(comment_data)
            
            # Headers COMPLETS pour comment final
            bandwidth_data = self._get_bandwidth_test_data()
            salt_ids = self._get_salt_ids()
            ig_headers = self._get_ig_headers()
            app_net_session = self._get_app_net_session_data()
            
            headers = {
                "accept-language": "fr-FR, en-US",
                "authorization": self._get_auth_token(),
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": user_id,
                "ig-u-ds-user-id": user_id,
                "ig-u-rur": ig_headers.get("ig-u-rur", f"CLN,{user_id},{int(time.time() + 30 * 24 * 3600)}:01fe{str(uuid.uuid4()).replace('-', '')[:40]}"),
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
                "x-bloks-prism-colors-enabled": "true",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-gray-red": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "true",
                "x-bloks-prism-indigo-link-version": "1",
                "x-bloks-version-id": self.session_data.get("session_metadata", {}).get("bloks_version_id", "422d0c0ead50c1ae8a294e5eba90b30255468f80488fcdcdc61c4c1a193f7fa1"),
                "x-fb-client-ip": "True",
                "x-fb-connection-type": self._get_connection_type_headers()["x-fb-connection-type"],
                "x-fb-friendly-name": f"IgApi: media/{media_id}/comment/",
                "x-fb-network-properties": self._get_fb_network_properties(),
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": device_headers["x-ig-android-id"],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": bandwidth_data["speed_kbps"],
                "x-ig-bandwidth-totalbytes-b": bandwidth_data["total_bytes"],
                "x-ig-bandwidth-totaltime-ms": bandwidth_data["total_time_ms"],
                "x-ig-client-endpoint": "CommentAvatarStickerGridFragment:comment_sticker_picker_tab_fragment_avatar_sticker_grid",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": self._get_connection_type_headers()["x-ig-connection-type"],
                "x-ig-device-id": device_headers["x-ig-device-id"],
                "x-ig-device-languages": f'{{"system_languages":"{self.session_data.get("locale", "fr_FR")}"}}',
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.session_data.get("uuids", {}).get("client_session_id", str(uuid.uuid4())),
                "x-ig-is-foldable": "false",
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": self._get_dynamic_nav_chain("comment"),
                "x-ig-salt-ids": str(salt_ids[0]) if salt_ids else "220140399",
                "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800)),
                "x-ig-www-claim": ig_headers.get("x-ig-www-claim", "hmac.AR0gigjvYfXDP3sCtKHklnUuIvadPjHaUGCxH3vFP3G_enq9"),
                "x-mid": self.get_x_mid(),
                "x-meta-zca": self._generate_meta_zca(),
                "x-pigeon-rawclienttime": str(time.time()),
                "x-pigeon-session-id": self._get_pigeon_session_id(),
                "x-tigon-is-retry": "False",
                "user-agent": device_headers["user-agent"],
                "x-fb-appnetsession-nid": app_net_session["nid"],
                "x-fb-appnetsession-sid": app_net_session["sid"],
                "x-fb-conn-uuid-client": self._get_conn_uuid_client(),
                "x-fb-http-engine": "Tigon/MNS/TCP",
                "x-fb-rmd": self._get_fb_rmd_state(),
                "x-fb-tasos-experimental": "1",
                "x-fb-tasos-td-config": "prod_signal:1"
            }
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/media/{media_id}/comment/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
            
        except Exception as e:
            return {"success": False, "error": "Ce media a ete supprime"}

    def _generate_user_breadcrumb(self, comment_text: str) -> str:
        """Générer user breadcrumb pour comment"""
        try:
            import base64
            
            # Simuler breadcrumb basé sur le texte
            text_length = len(comment_text)
            timestamp = int(time.time() * 1000)  # milliseconds
            
            # Partie 1: Hash-like string
            hash_part = base64.b64encode(f"fIH9H/KyNa4U/YjOPzUL4hfUpTovnz2PNReAvwsZ2Gk=".encode()).decode().strip('=')[:44]
            
            # Partie 2: Encoded data 
            data_part = base64.b64encode(f"NiA1MjQzIDAgMTc1ODYxMzUzMzk4NQ==".encode()).decode().strip('=')
            
            return f"{hash_part}\\n{data_part}\\n"
            
        except Exception:
            # Fallback breadcrumb
            return "fIH9H/KyNa4U/YjOPzUL4hfUpTovnz2PNReAvwsZ2Gk=\\nNiA1MjQzIDAgMTc1ODYxMzUzMzk4NQ==\\n"
    def _search_similar_username(self, target_username: str) -> str:
        """Rechercher username similaire EXACTEMENT comme script original"""
        try:
            if not self.api:
                return None
            
            headers = self._build_complete_headers(
                endpoint="user_search",
                friendly_name="IgApi: users/search/"
            )
            
            search_params = {
                "timezone_offset": str(self.session_data.get("timezone_offset", 10800)),
                "q": target_username,
                "count": "20"
            }
            
            response = self.auth.session.get(
                "https://i.instagram.com/api/v1/users/search/",
                params=search_params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok" and "users" in data:
                        users = data["users"]
                        
                        # Recherche exacte d'abord
                        for user in users:
                            username = user.get("username", "").lower()
                            if username == target_username.lower():
                                return str(user.get("pk"))
                        
                        # Si pas trouvé exact, recherche similaire EXACTEMENT comme script original
                        target_lower = target_username.lower()
                        best_matches = []
                        
                        # Recherche par préfixe
                        for user in users:
                            username = user.get("username", "").lower()
                            if username.startswith(target_lower) and username != target_lower:
                                best_matches.append((user.get("pk"), username))
                        
                        if best_matches:
                            best_matches.sort(key=lambda x: len(x[1]))
                            return str(best_matches[0][0])
                        
                        # Recherche par parties de nom EXACTEMENT comme script original
                        for user in users:
                            username = user.get("username", "").lower()
                            if any(part in username for part in target_lower.split('_') + target_lower.split('.') if len(part) > 2):
                                return str(user.get("pk"))
                        
                except Exception:
                    pass
            
            return None
            
        except Exception:
            return None
    
    def _upload_story_internal(self, image_path: str) -> dict:
        """Publier une story Instagram (méthode interne)"""
        try:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image non trouvée: {image_path}"}
            
            image_data, image_size, error = MediaProcessor.prepare_image_for_instagram(image_path, story_mode=True)
            if error:
                return {"success": False, "error": error}
            
            upload_id = MediaProcessor.generate_upload_id()
            user_id = self._get_user_id_from_session()
            
            if not user_id:
                return {"success": False, "error": "User ID non trouvé"}
            
            upload_result = self._upload_image_data(image_data, upload_id, story_mode=True)
            if not upload_result["success"]:
                return upload_result
            
            story_result = self._configure_story(upload_id, image_size, user_id)
            return story_result
            
        except Exception as e:
            return {"success": False, "error": f"Erreur upload story: {str(e)}"}
    
    def _upload_post_internal(self, image_path: str, caption: str = "") -> dict:
        """Publier un post Instagram (méthode interne)"""
        try:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image non trouvée: {image_path}"}
            
            image_data, image_size, error = MediaProcessor.prepare_image_for_instagram(image_path, story_mode=False)
            if error:
                return {"success": False, "error": error}
            
            upload_id = MediaProcessor.generate_upload_id()
            user_id = self._get_user_id_from_session()
            
            if not user_id:
                return {"success": False, "error": "User ID non trouvé"}
            
            upload_result = self._upload_image_data(image_data, upload_id, story_mode=False)
            if not upload_result["success"]:
                return upload_result
            
            post_result = self._configure_post(upload_id, image_size, user_id, caption)
            if post_result["success"]:
                # Mettre à jour PDQ hash
                self._update_media_pdq_hash(upload_id, image_data, user_id)
            
            return post_result
            
        except Exception as e:
            return {"success": False, "error": f"Erreur upload post: {str(e)}"}
    
    def _delete_last_post_internal(self) -> dict:
        """Supprimer la dernière publication"""
        try:
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            # Récupérer directement la liste des médias via l'API du client
            device_headers = self._get_device_specific_headers()
            
            headers = {
                "user-agent": device_headers["user-agent"],
                "x-ig-app-id": "567067343352427",
                "authorization": self._get_auth_token(),
                "x-ig-android-id": device_headers["x-ig-android-id"],
                "x-ig-device-id": device_headers["x-ig-device-id"],
                "accept-language": "fr-FR, en-US",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-timezone-offset": str(self.session_data.get("timezone_offset", 10800))
            }
            
            # Récupérer la liste des médias
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/feed/user/{user_id}/",
                headers=headers,
                params={"count": "5", "max_id": ""},
                timeout=10
            )
            
            if response.status_code != 200:
                return {"success": False, "error": "Impossible de récupérer la liste des publications"}
            
            data = response.json()
            if data.get("status") != "ok" or not data.get("items"):
                return {"success": False, "error": "Aucune publication trouvée"}
            
            # Prendre le premier média (le plus récent)
            latest_media = data["items"][0]
            media_id = latest_media.get("id")
            
            if not media_id:
                return {"success": False, "error": "ID du média introuvable"}
            
            # Supprimer le média
            delete_data = {
                "media_id": media_id,
                "_uid": user_id,
                "_uuid": device_headers["x-ig-device-id"]
            }
            
            signed_body = InstagramEncryption.create_signed_body(delete_data)
            
            delete_headers = self._build_complete_headers(
                friendly_name=f"IgApi: media/{media_id}/delete/"
            )
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/media/{media_id}/delete/",
                headers=delete_headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": "Erreur lors de la suppression"}
    
    def handle_http_error(self, response_status: int, response_text: str) -> dict:
        """Gérer les erreurs HTTP avec messages simplifiés"""
        try:
            username = self._get_username_from_session()
            
            # Gérer spécifiquement l'erreur 500 - problème serveur Instagram
            if response_status == 500:
                return {"success": False, "error": "Erreur serveur Instagram, réessayez plus tard"}
            
            # Détecter les erreurs de déconnexion spécifiques
            if response_status == 403:
                # Vérifier les différents patterns de déconnexion
                if any(pattern in response_text.lower() for pattern in [
                    "login_required", 
                    "user_has_logged_out", 
                    "logout_reason",
                    "logged out"
                ]):
                    return {
                        "success": False,
                        "error": f"Le compte @{username} est déconnecté, veuillez vous reconnecter"
                    }
            
            print(f"❌ Erreur HTTP {response_status}: {response_text}")
            return {"success": False, "error": f"HTTP {response_status}: {response_text}"}
            
        except Exception as e:
            print(f"❌ Erreur HTTP inattendue: {str(e)}")
            return {"success": False, "error": f"Erreur HTTP inattendue: {str(e)}"}
    
    def handle_media_error(self, error_message: str) -> dict:
        """Gérer les erreurs spécifiques aux médias"""
        if "deleted" in error_message.lower() or "supprime" in error_message.lower():
            return {"success": False, "error": "Ce media a été supprimé"}
        else:
            print(f"❌ {error_message}")
            return {"success": False, "error": error_message}
    
    def _extract_media_id_basic(self, url: str) -> str:
        """Extraction basique media ID (fallback)"""
        patterns = [
            r'/p/([A-Za-z0-9_-]+)/',
            r'/reel/([A-Za-z0-9_-]+)/',
            r'media_id=([0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                code = match.group(1)
                if code.isdigit():
                    return code
                return str(random.randint(1000000000000000000, 9999999999999999999))
        
        return None
    
    def _extract_user_id_basic(self, url: str) -> str:
        """Extraction basique user ID (fallback)"""
        match = re.search(r'instagram\.com/([^/?]+)', url)
        if match:
            username = match.group(1).replace('@', '')
            return str(random.randint(1000000000, 9999999999))
        return None
    
    def get_account_info(self) -> dict:
        """Récupérer informations du compte connecté avec gestion d'erreurs détaillée"""
        try:
            user_id = self._get_user_id_from_session()
            
            if not user_id or user_id == "user_id_unknown":
                return {
                    "success": False, 
                    "error": "User ID non trouvé dans la session",
                    "debug_info": f"session_data keys: {list(self.session_data.keys()) if self.session_data else 'None'}"
                }
            
            if not self.api:
                return {
                    "success": False, 
                    "error": "API non initialisée",
                    "debug_info": "L'objet InstagramAPI n'a pas été créé"
                }
            
            # Construire les headers complets
            headers = self._build_complete_headers(
                endpoint="user_info",
                friendly_name=f"IgApi: users/{user_id}/info/"
            )
            # Faire la requête directement
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/users/{user_id}/info/",
                headers=headers,
                timeout=15
            )
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Vérifier le statut dans la réponse
                    if response_data.get("status") == "ok":
                        user_info = response_data.get("user", {})
                        
                        if user_info:
                            account_status = "Privé" if user_info.get("is_private") else "Public"
                            
                            info = {
                                "success": True,
                                "data": {
                                    "user_id": str(user_info.get("pk", user_id)),
                                    "username": user_info.get("username", ""),
                                    "full_name": user_info.get("full_name", ""),
                                    "is_private": user_info.get("is_private", False),
                                    "account_status": account_status,
                                    "is_verified": user_info.get("is_verified", False),
                                    "is_business": user_info.get("is_business", False),
                                    "follower_count": user_info.get("follower_count", 0),
                                    "following_count": user_info.get("following_count", 0),
                                    "media_count": user_info.get("media_count", 0),
                                    "biography": user_info.get("biography", ""),
                                    "profile_pic_url": user_info.get("profile_pic_url", "")
                                },
                                "raw_response": response_data  # Inclure la réponse brute pour debug
                            }
                            return info
                        else:
                            return {
                                "success": False,
                                "error": "Aucune donnée utilisateur dans la réponse",
                                "debug_info": {
                                    "response_data": response_data,
                                    "user_key_present": "user" in response_data,
                                    "all_keys": list(response_data.keys())
                                }
                            }
                    else:
                        # Status != "ok" 
                        error_message = response_data.get("message", "Erreur inconnue")
                        return {
                            "success": False,
                            "error": f"Erreur Instagram: {error_message}",
                            "debug_info": {
                                "status": response_data.get("status"),
                                "full_response": response_data
                            }
                        }
                        
                except json.JSONDecodeError as json_error:
                    response_text = response.text[:500]  # Premiers 500 caractères
                    return {
                        "success": False,
                        "error": f"Réponse non-JSON: {str(json_error)}",
                        "debug_info": {
                            "response_text": response_text,
                            "content_type": response.headers.get("content-type", "inconnu")
                        }
                    }
                    
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    return self.handle_action_error(response.status_code, error_data, response.text)
                except:
                    return {
                        "success": False,
                        "error": f"Erreur HTTP 400",
                        "debug_info": {
                            "response_text": response.text[:500],
                            "headers": dict(response.headers)
                        }
                    }
                    
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Session expirée, veuillez vous reconnecter",
                    "debug_info": {"status_code": 401, "response_text": response.text[:200]}
                }
                
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Accès refusé - compte possiblement suspendu",
                    "debug_info": {"status_code": 403, "response_text": response.text[:200]}
                }
                
            else:
                return {
                    "success": False,
                    "error": f"Erreur HTTP {response.status_code}",
                    "debug_info": {
                        "status_code": response.status_code,
                        "response_text": response.text[:500],
                        "headers": dict(response.headers)
                    }
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout - Instagram ne répond pas",
                "debug_info": {"exception_type": "Timeout"}
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Erreur de connexion réseau",
                "debug_info": {"exception_type": "ConnectionError"}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur inattendue: {str(e)}",
                "debug_info": {
                    "exception_type": type(e).__name__,
                    "exception_details": str(e),
                    "user_id": user_id if 'user_id' in locals() else "non défini",
                    "api_initialized": self.api is not None,
                    "session_data_present": bool(self.session_data)
                }
            }
    
    def toggle_account_privacy(self) -> dict:
        """Changer la confidentialité du compte (public <-> privé)"""
        try:
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé"}
            
            account_info = self.get_account_info()
            if not account_info["success"]:
                return account_info
            
            current_private = account_info["data"]["is_private"]
            action = "set_public" if current_private else "set_private"
            
            privacy_data = {
                "_uid": user_id,
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"]
            }
            
            signed_body = InstagramEncryption.create_signed_body(privacy_data)
            
            headers = self._build_complete_headers(
                endpoint="account_privacy",
                friendly_name=f"IgApi: accounts/{action}/"
            )
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/accounts/{action}/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    new_status = "Public" if action == "set_public" else "Privé"
                    return {"success": True, "data": {"new_status": new_status}}
                else:
                    print(f"❌ Erreur changement privacy: {parsed_data}")
                    return {"success": False, "error": parsed_data}
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    # MÉTHODES D'UPLOAD ET CONFIGURATION
    def _upload_image_data(self, image_data: bytes, upload_id: str, story_mode: bool = False) -> dict:
        """Upload des données d'image vers Instagram avec headers complets"""
        try:
            user_id = self._get_user_id_from_session()
            
            # Headers complets pour upload
            headers = self._build_complete_headers(
                endpoint="upload",
                friendly_name="IgApi: rupload_igphoto"
            )
            
            # Modifier content-type pour upload
            headers["content-type"] = "application/octet-stream"
            headers["offset"] = "0"
            headers["x-entity-length"] = str(len(image_data))
            headers["x-entity-name"] = f"{upload_id}_0_{random.randint(1000000000, 9999999999)}"
            headers["x-entity-type"] = "image/jpeg"
            
            share_type = "stories" if story_mode else "feed"
            
            upload_params = {
                "upload_id": upload_id,
                "session_id": upload_id,
                "media_type": "1",
                "upload_engine_config_enum": "0",
                "share_type": share_type,
                "is_optimistic_upload": "false",
                "image_compression": '{"lib_name":"libjpeg","lib_version":"9d","quality":"90","original_width":720,"original_height":1280}' if story_mode else '{"lib_name":"libjpeg","lib_version":"9d","quality":"90","original_width":1080,"original_height":1080}',
                "xsharing_user_ids": "[]",
                "retry_context": '{"num_reupload":0,"num_step_manual_retry":0,"num_step_auto_retry":0}'
            }
            
            headers["x-instagram-rupload-params"] = json.dumps(upload_params, separators=(',', ':'))
            
            response = self.auth.session.post(
                f"https://i.instagram.com/rupload_igphoto/{upload_id}_0_{random.randint(1000000000, 9999999999)}",
                headers=headers,
                data=image_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "data": "Upload réussi"}
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur upload image: {str(e)}"}
    
    def _configure_story(self, upload_id: str, image_size: tuple, user_id: str) -> dict:
        """Configurer la story après upload avec headers complets"""
        try:
            width, height = image_size
            
            # Récupérer device settings depuis session
            device_settings = self.session_data.get("device_settings", {})
            uuids = self.session_data.get("uuids", {})
            
            story_data = {
                "supported_capabilities_new": '[{"name":"SUPPORTED_SDK_VERSIONS","value":"149.0,150.0,151.0,152.0,153.0,154.0,155.0,156.0,157.0,158.0,159.0,160.0,161.0,162.0,163.0,164.0,165.0,166.0,167.0,168.0,169.0,170.0,171.0,172.0,173.0,174.0,175.0,176.0,177.0,178.0,179.0,180.0,181.0,182.0,183.0,184.0,185.0,186.0,187.0,188.0,189.0,190.0,191.0,192.0,193.0,194.0,195.0,196.0,197.0,198.0,199.0,200.0,201.0,202.0"},{"name":"SUPPORTED_BETA_SDK_VERSIONS","value":"182.0-beta,183.0-beta,184.0-beta,185.0-beta,186.0-beta,187.0-beta,188.0-beta,189.0-beta,190.0-beta,191.0-beta,192.0-beta,193.0-beta,194.0-beta,195.0-beta,196.0-beta,197.0-beta,198.0-beta,199.0-beta,200.0-beta,201.0-beta,202.0-beta"},{"name":"FACE_TRACKER_VERSION","value":"14"},{"name":"segmentation","value":"segmentation_enabled"},{"name":"COMPRESSION","value":"ETC2_COMPRESSION"},{"name":"gyroscope","value":"gyroscope_enabled"}]',
                "allow_multi_configures": "1",
                "has_camera_metadata": "0",
                "camera_entry_point": "11",
                "original_media_type": "1",
                "camera_session_id": str(uuid.uuid4()),
                "original_height": str(height),
                "include_e2ee_mentioned_user_list": "1",
                "hide_from_profile_grid": "false",
                "scene_capture_type": "",
                "timezone_offset": str(self.session_data.get("timezone_offset", 10800)),
                "client_shared_at": str(int(time.time())),
                "media_folder": "Screenshots",
                "configure_mode": "1",
                "source_type": "4",
                "camera_position": "unknown",
                "_uid": user_id,
                "device_id": self._get_device_specific_headers()["x-ig-android-id"],
                "composition_id": str(uuid.uuid4()),
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "creation_tool_info": "[]",
                "creation_surface": "camera",
                "nav_chain": f"MainFeedFragment:feed_timeline:1:cold_start:{int(time.time() * 1000)}:::,QuickCaptureFragment:stories_precapture_camera:25:your_story_placeholder:{int(time.time() * 1000)}:::,PrivateStoryShareSheetFragment:private_stories_share_sheet:28:button:{int(time.time() * 1000)}::",
                "imported_taken_at": str(int(time.time()) - 3600),
                "capture_type": "normal",
                "audience": "default",
                "upload_id": upload_id,
                "client_timestamp": str(int(time.time())),
                "bottom_camera_dial_selected": "2",
                "publish_id": "1",
                "original_width": str(width),
                "media_transformation_info": f'{{"width":"{width}","height":"{height}","x_transform":"0","y_transform":"0","zoom":"1.0","rotation":"0.0","background_coverage":"0.0"}}',
                "edits": {
                    "filter_type": 0,
                    "filter_strength": 0.5,
                    "crop_original_size": [float(width), float(height)]
                },
                "extra": {
                    "source_width": width,
                    "source_height": height
                },
                "device": {
                    "manufacturer": device_settings.get('manufacturer', 'samsung'),
                    "model": device_settings.get('model', 'SM-G991B'),
                    "android_version": device_settings.get('android_version', 32),
                    "android_release": device_settings.get('android_release', '12')
                }
            }
            
            signed_body = InstagramEncryption.create_signed_body(story_data)
            
            headers = self._build_complete_headers(
                endpoint="story_configure",
                friendly_name="IgApi: media/configure_to_story/"
            )
            
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/media/configure_to_story/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=15
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    print(f"❌ Erreur configuration story: {parsed_data}")
                    return {"success": False, "error": parsed_data}
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur configuration story: {str(e)}"}
    
    def _configure_post(self, upload_id: str, image_size: tuple, user_id: str, caption: str = "") -> dict:
        """Configurer le post après upload avec headers complets"""
        try:
            width, height = image_size
            
            # Récupérer device settings depuis session
            device_settings = self.session_data.get("device_settings", {})
            
            post_data = {
                "app_attribution_android_namespace": "",
                "camera_entry_point": "360",
                "camera_session_id": str(uuid.uuid4()),
                "original_height": str(height),
                "include_e2ee_mentioned_user_list": "1",
                "hide_from_profile_grid": "false",
                "scene_capture_type": "",
                "timezone_offset": str(self.session_data.get("timezone_offset", 10800)),
                "source_type": "4",
                "_uid": user_id,
                "device_id": self._get_device_specific_headers()["x-ig-android-id"],
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "creation_tool_info": "[]",
                "creation_logger_session_id": str(uuid.uuid4()),
                "nav_chain": f"MainFeedFragment:feed_timeline:1:cold_start:{int(time.time() * 1000)}:::,GalleryPickerFragment:gallery_picker:50:camera_tab_bar:{int(time.time() * 1000)}:::,PhotoFilterFragment:photo_filter:51:button:{int(time.time() * 1000)}::",
                "caption": caption,
                "audience": "default",
                "upload_id": upload_id,
                "bottom_camera_dial_selected": "11",
                "publish_id": "1",
                "original_width": str(width),
                "edits": {
                    "filter_type": 0,
                    "filter_strength": 1.0,
                    "crop_original_size": [float(width), float(height)],
                    "crop_center": [-0.002429657, -0.06649882],
                    "crop_zoom": 1.782934
                },
                "extra": {
                    "source_width": width,
                    "source_height": height
                },
                "device": {
                    "manufacturer": device_settings.get('manufacturer', 'samsung'),
                    "model": device_settings.get('model', 'SM-G991B'),
                    "android_version": device_settings.get('android_version', 32),
                    "android_release": device_settings.get('android_release', '12')
                },
                "overlay_data": []
            }
            
            signed_body = InstagramEncryption.create_signed_body(post_data)
            
            headers = self._build_complete_headers(
                endpoint="post_configure",
                friendly_name="IgApi: media/configure/"
            )
            
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/media/configure/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=15
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    print(f"❌ Erreur configuration post: {parsed_data}")
                    return {"success": False, "error": parsed_data}
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur configuration post: {str(e)}"}
    
    def _update_media_pdq_hash(self, upload_id: str, image_data: bytes, user_id: str) -> dict:
        """Mettre à jour le média avec le hash PDQ"""
        try:
            pdq_hash = MediaProcessor.generate_pdq_hash(image_data)
            
            pdq_data = {
                "pdq_hash_info": f'[{{"pdq_hash":"{pdq_hash}","frame_time":0}}]',
                "_uid": user_id,
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "upload_id": upload_id
            }
            
            signed_body = InstagramEncryption.create_signed_body(pdq_data)
            
            headers = self._build_complete_headers(
                endpoint="pdq_update",
                friendly_name="IgApi: media/update_media_with_pdq_hash_info/"
            )
            
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/media/update_media_with_pdq_hash_info/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True}
            else:
                print(f"⚠️ Erreur PDQ hash: {response.status_code}")
                return {"success": False, "error": f"PDQ hash error: {response.status_code}"}
                
        except Exception as e:
            print(f"⚠️ Erreur PDQ hash: {str(e)}")
            return {"success": False, "error": f"PDQ hash error: {str(e)}"}
    
    def _delete_media(self, media_id: str) -> dict:
        """Supprimer un média par son ID - AVEC HEADERS COMPLETS"""
        try:
            user_id = self._get_user_id_from_session()
            
            delete_data = {
                "igtv_feed_preview": "false",
                "media_id": media_id,
                "_uid": user_id,
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"]
            }
            
            signed_body = InstagramEncryption.create_signed_body(delete_data)
            
            headers = self._build_complete_headers(
                endpoint="media_delete",
                friendly_name=f"IgApi: media/{media_id}/delete/?media_type=PHOTO"
            )
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/media/{media_id}/delete/?media_type=PHOTO",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                # Vérifier spécifiquement les indicateurs de suppression
                if (isinstance(parsed_data, dict) and 
                    (parsed_data.get("did_delete") == True or 
                     InstagramEncryption.is_success_response(response, parsed_data))):
                    return {"success": True, "data": parsed_data}
                else:
                    print(f"❌ Erreur suppression: {parsed_data}")
                    return {"success": False, "error": parsed_data}
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur suppression: {str(e)}"}
    
    # MÉTHODES SUPPLÉMENTAIRES POUR COMPATIBILITÉ COMPLÈTE
    def get_media_info(self, media_input: str) -> dict:
        """Récupérer informations d'un média"""
        try:
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_input)
            else:
                media_id = self._extract_media_id_basic(media_input)
            
            if not media_id:
                return {"success": False, "error": "Media ID non trouvé"}
            
            headers = self._build_complete_headers(
                endpoint="media_info",
                friendly_name=f"IgApi: media/{media_id}/info/"
            )
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/media/{media_id}/info/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    items = parsed_data.get("items", [])
                    if items:
                        media = items[0]
                        return {
                            "success": True,
                            "data": {
                                "id": media.get("id"),
                                "code": media.get("code"),
                                "media_type": media.get("media_type"),
                                "like_count": media.get("like_count", 0),
                                "comment_count": media.get("comment_count", 0),
                                "caption": media.get("caption", {}).get("text", "") if media.get("caption") else "",
                                "owner": media.get("user", {})
                            }
                        }
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def get_user_media_list(self, user_input: str, count: int = 20) -> dict:
        """Récupérer la liste des médias d'un utilisateur"""
        try:
            if self.api:
                user_id = self.api.extract_user_id_from_url(user_input)
            else:
                user_id = self._extract_user_id_basic(user_input)
            
            if not user_id:
                return {"success": False, "error": "User ID non trouvé"}
            
            headers = self._build_complete_headers(
                endpoint="user_feed",
                friendly_name=f"IgApi: feed/user/{user_id}/"
            )
            
            params = {
                "count": str(count),
                "max_id": ""
            }
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/feed/user/{user_id}/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    items = parsed_data.get("items", [])
                    media_list = []
                    
                    for item in items:
                        media_info = {
                            "id": item.get("id"),
                            "code": item.get("code"),
                            "media_type": item.get("media_type"),
                            "taken_at": item.get("taken_at"),
                            "like_count": item.get("like_count", 0),
                            "comment_count": item.get("comment_count", 0)
                        }
                        
                        caption_info = item.get("caption")
                        if caption_info:
                            media_info["caption"] = caption_info.get("text", "")
                        else:
                            media_info["caption"] = ""
                        
                        media_list.append(media_info)
                    
                    return {"success": True, "data": media_list}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def get_user_info(self, user_input: str) -> dict:
        """Récupérer informations d'un utilisateur"""
        try:
            if self.api:
                user_id = self.api.extract_user_id_from_url(user_input)
            else:
                user_id = self._extract_user_id_basic(user_input)
            
            if not user_id:
                return {"success": False, "error": "User ID non trouvé"}
            
            if self.api:
                user_info = self.api.get_user_info(user_id)
                
                if user_info:
                    account_status = "Privé" if user_info.get("is_private") else "Public"
                    
                    info = {
                        "success": True,
                        "data": {
                            "user_id": str(user_info.get("pk", user_id)),
                            "username": user_info.get("username", ""),
                            "full_name": user_info.get("full_name", ""),
                            "is_private": user_info.get("is_private", False),
                            "account_status": account_status,
                            "is_verified": user_info.get("is_verified", False),
                            "is_business": user_info.get("is_business", False),
                            "follower_count": user_info.get("follower_count", 0),
                            "following_count": user_info.get("following_count", 0),
                            "media_count": user_info.get("media_count", 0),
                            "biography": user_info.get("biography", ""),
                            "profile_pic_url": user_info.get("profile_pic_url", "")
                        }
                    }
                    
                    return info
                else:
                    return {"success": False, "error": "Impossible de récupérer les informations"}
            else:
                return {"success": False, "error": "API non initialisée"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def unlike_post(self, media_input: str) -> dict:
        """Unliker un post Instagram"""
        try:
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_input)
            else:
                media_id = self._extract_media_id_basic(media_input)
            
            if not media_id:
                return {"success": False, "error": "Ce media a ete supprime"}
            
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            unlike_data = {
                "media_id": media_id,
                "radio_type": self._get_radio_type(),
                "_uid": user_id,
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "nav_chain": self._build_nav_chain("like"),
                "container_module": "feed_timeline"
            }
            
            signed_body = InstagramEncryption.create_signed_body(unlike_data)
            
            headers = self._build_complete_headers(
                endpoint="unlike",
                friendly_name=f"IgApi: media/{media_id}/unlike/"
            )
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/media/{media_id}/unlike/",
                headers=headers,
                data={"signed_body": signed_body, "d": "0"},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": "Ce media a ete supprime"}
    
    def unfollow_user(self, user_input: str) -> dict:
        """Ne plus suivre un utilisateur"""
        try:
            if self.api:
                user_id = self.api.extract_user_id_from_url(user_input)
            else:
                user_id = self._extract_user_id_basic(user_input)
            
            # Si échec d'extraction, chercher username similaire via API
            if not user_id and self.api:
                username_match = re.search(r'instagram\.com/([^/?]+)', user_input)
                if username_match:
                    target_username = username_match.group(1).replace('@', '').strip()
                    user_id = self._search_similar_username(target_username)
                
                if not user_id:
                    return {"success": False, "error": "Utilisateur introuvable"}
            
            current_user_id = self._get_user_id_from_session()
            if not current_user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            unfollow_data = {
                "user_id": user_id,
                "radio_type": self._get_radio_type(),
                "_uid": current_user_id,
                "device_id": self._get_device_specific_headers()["x-ig-android-id"],
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "nav_chain": f"UserDetailFragment:profile:1:button:{int(time.time() * 1000)}:::{int(time.time() * 1000)}",
                "container_module": "profile"
            }
            
            signed_body = InstagramEncryption.create_signed_body(unfollow_data)
            
            headers = self._build_complete_headers(
                endpoint="unfollow",
                friendly_name=f"IgApi: friendships/destroy/{user_id}/"
            )
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/friendships/destroy/{user_id}/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": "Utilisateur introuvable"}
    
    # Méthodes supplémentaires pour la compatibilité complète...
    def delete_comment(self, media_input: str, comment_id: str) -> dict:
        """Supprimer un commentaire"""
        try:
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_input)
            else:
                media_id = self._extract_media_id_basic(media_input)
            
            if not media_id:
                return {"success": False, "error": "Ce média a été supprimé"}
            
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            delete_comment_data = {
                "_uid": user_id,
                "_uuid": self._get_device_specific_headers()["x-ig-device-id"],
                "nav_chain": self._build_nav_chain("comment")
            }
            
            signed_body = InstagramEncryption.create_signed_body(delete_comment_data)
            
            headers = self._build_complete_headers(
                endpoint="comment_delete",
                friendly_name=f"IgApi: media/{media_id}/comment/{comment_id}/delete/"
            )
            
            response = self.auth.session.post(
                f"https://i.instagram.com/api/v1/media/{media_id}/comment/{comment_id}/delete/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {"success": True, "data": parsed_data}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    # Méthodes pour récupérer les followers, following, etc. avec headers complets
    def get_followers(self, user_input: str = None, count: int = 20) -> dict:
        """Récupérer la liste des abonnés"""
        try:
            if user_input:
                if self.api:
                    user_id = self.api.extract_user_id_from_url(user_input)
                else:
                    user_id = self._extract_user_id_basic(user_input)
            else:
                user_id = self._get_user_id_from_session()
            
            if not user_id:
                return {"success": False, "error": "User ID non trouvé"}
            
            headers = self._build_complete_headers(
                endpoint="followers",
                friendly_name=f"IgApi: friendships/{user_id}/followers/"
            )
            
            params = {
                "count": str(count),
                "max_id": ""
            }
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/friendships/{user_id}/followers/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    users = parsed_data.get("users", [])
                    followers_list = []
                    
                    for user in users:
                        follower_info = {
                            "user_id": str(user.get("pk")),
                            "username": user.get("username", ""),
                            "full_name": user.get("full_name", ""),
                            "is_private": user.get("is_private", False),
                            "is_verified": user.get("is_verified", False),
                            "profile_pic_url": user.get("profile_pic_url", "")
                        }
                        followers_list.append(follower_info)
                    
                    return {"success": True, "data": followers_list}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def get_following(self, user_input: str = None, count: int = 20) -> dict:
        """Récupérer la liste des abonnements"""
        try:
            if user_input:
                if self.api:
                    user_id = self.api.extract_user_id_from_url(user_input)
                else:
                    user_id = self._extract_user_id_basic(user_input)
            else:
                user_id = self._get_user_id_from_session()
            
            if not user_id:
                return {"success": False, "error": "User ID non trouvé"}
            
            headers = self._build_complete_headers(
                endpoint="following",
                friendly_name=f"IgApi: friendships/{user_id}/following/"
            )
            
            params = {
                "count": str(count),
                "max_id": ""
            }
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/friendships/{user_id}/following/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    users = parsed_data.get("users", [])
                    following_list = []
                    
                    for user in users:
                        following_info = {
                            "user_id": str(user.get("pk")),
                            "username": user.get("username", ""),
                            "full_name": user.get("full_name", ""),
                            "is_private": user.get("is_private", False),
                            "is_verified": user.get("is_verified", False),
                            "profile_pic_url": user.get("profile_pic_url", "")
                        }
                        following_list.append(following_info)
                    
                    return {"success": True, "data": following_list}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def search_users(self, query: str, count: int = 20) -> dict:
        """Rechercher des utilisateurs"""
        try:
            headers = self._build_complete_headers(
                endpoint="user_search",
                friendly_name="IgApi: users/search/"
            )
            
            search_params = {
                "timezone_offset": str(self.session_data.get("timezone_offset", 10800)),
                "q": query,
                "count": str(count)
            }
            
            response = self.auth.session.get(
                "https://i.instagram.com/api/v1/users/search/",
                params=search_params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    users = parsed_data.get("users", [])
                    search_results = []
                    
                    for user in users:
                        user_info = {
                            "user_id": str(user.get("pk")),
                            "username": user.get("username", ""),
                            "full_name": user.get("full_name", ""),
                            "is_private": user.get("is_private", False),
                            "is_verified": user.get("is_verified", False),
                            "profile_pic_url": user.get("profile_pic_url", ""),
                            "follower_count": user.get("follower_count", 0)
                        }
                        search_results.append(user_info)
                    
                    return {"success": True, "data": search_results}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def get_media_comments(self, media_input: str, count: int = 20) -> dict:
        """Récupérer les commentaires d'un média"""
        try:
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_input)
            else:
                media_id = self._extract_media_id_basic(media_input)
            
            if not media_id:
                return {"success": False, "error": "Ce média a été supprimé"}
            
            headers = self._build_complete_headers(
                endpoint="comments",
                friendly_name=f"IgApi: media/{media_id}/comments/"
            )
            
            params = {
                "count": str(count),
                "max_id": ""
            }
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/media/{media_id}/comments/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    comments = parsed_data.get("comments", [])
                    comments_list = []
                    
                    for comment in comments:
                        comment_info = {
                            "comment_id": str(comment.get("pk")),
                            "text": comment.get("text", ""),
                            "created_at": comment.get("created_at"),
                            "user": {
                                "user_id": str(comment.get("user", {}).get("pk")),
                                "username": comment.get("user", {}).get("username", ""),
                                "full_name": comment.get("user", {}).get("full_name", ""),
                                "profile_pic_url": comment.get("user", {}).get("profile_pic_url", "")
                            }
                        }
                        comments_list.append(comment_info)
                    
                    return {"success": True, "data": comments_list}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def get_media_likers(self, media_input: str, count: int = 20) -> dict:
        """Récupérer les utilisateurs qui ont liké un média"""
        try:
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_input)
            else:
                media_id = self._extract_media_id_basic(media_input)
            
            if not media_id:
                return {"success": False, "error": "Ce média a été supprimé"}
            
            headers = self._build_complete_headers(
                endpoint="likers",
                friendly_name=f"IgApi: media/{media_id}/likers/"
            )
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/media/{media_id}/likers/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    users = parsed_data.get("users", [])
                    likers_list = []
                    
                    for user in users[:count]:  # Limiter au nombre demandé
                        liker_info = {
                            "user_id": str(user.get("pk")),
                            "username": user.get("username", ""),
                            "full_name": user.get("full_name", ""),
                            "is_private": user.get("is_private", False),
                            "is_verified": user.get("is_verified", False),
                            "profile_pic_url": user.get("profile_pic_url", "")
                        }
                        likers_list.append(liker_info)
                    
                    return {"success": True, "data": likers_list}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def get_timeline_feed(self, count: int = 20) -> dict:
        """Récupérer le feed timeline"""
        try:
            user_id = self._get_user_id_from_session()
            
            headers = self._build_complete_headers(
                endpoint="timeline",
                friendly_name="IgApi: feed/timeline/"
            )
            
            params = {
                "count": str(count),
                "max_id": ""
            }
            
            response = self.auth.session.get(
                "https://i.instagram.com/api/v1/feed/timeline/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    items = parsed_data.get("feed_items", [])
                    timeline_list = []
                    
                    for item in items:
                        if item.get("media_or_ad"):
                            media = item["media_or_ad"]
                            timeline_info = {
                                "id": media.get("id"),
                                "code": media.get("code"),
                                "media_type": media.get("media_type"),
                                "taken_at": media.get("taken_at"),
                                "like_count": media.get("like_count", 0),
                                "comment_count": media.get("comment_count", 0),
                                "user": {
                                    "user_id": str(media.get("user", {}).get("pk")),
                                    "username": media.get("user", {}).get("username", ""),
                                    "full_name": media.get("user", {}).get("full_name", ""),
                                    "profile_pic_url": media.get("user", {}).get("profile_pic_url", "")
                                }
                            }
                            
                            caption_info = media.get("caption")
                            if caption_info:
                                timeline_info["caption"] = caption_info.get("text", "")
                            else:
                                timeline_info["caption"] = ""
                            
                            timeline_list.append(timeline_info)
                    
                    return {"success": True, "data": timeline_list}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur: {str(e)}"}

    def pdp(self, image_path: str) -> dict:
        """Changer la photo de profil du compte Instagram
        
        Args:
            image_path (str): Chemin vers l'image à utiliser comme photo de profil
        
        Returns:
            dict: Résultat de l'opération avec 'success' et 'data'/'error'
        """
        try:
            # Vérifier que l'image existe
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image non trouvée: {image_path}"}
            
            # Vérifier que c'est un fichier image valide
            valid_extensions = ['.jpg', '.jpeg', '.png']
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in valid_extensions:
                return {"success": False, "error": "Format d'image non supporté. Utilisez JPG, JPEG ou PNG"}
            
            # Traiter l'image pour Instagram (redimensionner si nécessaire)
            processed_image_data, error = self._prepare_profile_image(image_path)
            if error:
                return {"success": False, "error": error}
            
            # Approche 1: Essayer la méthode web d'abord
            web_result = self._change_profile_picture_web(processed_image_data, image_path)
            if web_result["success"]:
                return web_result
            
            # Approche 2: Fallback vers la méthode mobile API
            mobile_result = self._change_profile_picture_mobile(processed_image_data)
            if mobile_result["success"]:
                return mobile_result
            
            # Si les deux échouent, retourner l'erreur de la méthode web
            return web_result
            
        except Exception as e:
            return {"success": False, "error": f"Erreur inattendue: {str(e)}"}
    
    def _prepare_profile_image(self, image_path: str) -> tuple:
        """Préparer l'image pour Instagram (redimensionnement et optimisation)
        
        Returns:
            tuple: (image_data_bytes, error_message)
        """
        try:
            # Importer PIL si disponible pour le redimensionnement
            try:
                from PIL import Image
                import io
                
                # Ouvrir et redimensionner l'image
                with Image.open(image_path) as img:
                    # Convertir en RGB si nécessaire
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Redimensionner à 320x320 (taille optimale pour photo de profil Instagram)
                    img = img.resize((320, 320), Image.LANCZOS)
                    
                    # Sauvegarder en JPEG optimisé
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='JPEG', quality=90, optimize=True)
                    return img_bytes.getvalue(), None
                    
            except ImportError:
                # Si PIL n'est pas disponible, lire l'image directement
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Vérifier la taille du fichier (max 8MB)
                if len(image_data) > 8 * 1024 * 1024:
                    return None, "Image trop volumineuse. Maximum 8MB autorisé"
                
                return image_data, None
                
        except Exception as e:
            return None, f"Erreur traitement image: {str(e)}"
    
    def _change_profile_picture_web(self, image_data: bytes, original_path: str) -> dict:
        """Changer photo de profil via endpoint web Instagram
        
        Args:
            image_data (bytes): Données de l'image traitée
            original_path (str): Chemin original pour le nom du fichier
        
        Returns:
            dict: Résultat de l'opération
        """
        try:
            # Récupérer les données de session nécessaires
            cookies_data = self.session_data.get("cookies", {})
            device_settings = self.session_data.get("device_settings", {})
            username = self._get_username_from_session()
            
            if not cookies_data.get("csrftoken"):
                return {"success": False, "error": "Token CSRF non trouvé dans la session"}
            
            # Récupérer user agent web depuis les paramètres de device
            user_agent = device_settings.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Construire les headers exactement comme dans la recherche
            headers = {
                "Host": "www.instagram.com",
                "User-Agent": user_agent,
                "Accept": "*/*",
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": f"https://www.instagram.com/{username}/",
                "X-CSRFToken": cookies_data["csrftoken"],
                "X-Instagram-AJAX": "1",
                "X-Requested-With": "XMLHttpRequest",
                "DNT": "1",
                "Connection": "keep-alive",
                "Origin": "https://www.instagram.com"
            }
            
            # Construire cookie string complet
            cookie_parts = []
            for name, value in cookies_data.items():
                cookie_parts.append(f"{name}={value}")
            headers["Cookie"] = "; ".join(cookie_parts)
            
            # Préparer le fichier pour multipart/form-data
            filename = os.path.basename(original_path)
            if not filename.lower().endswith(('.jpg', '.jpeg')):
                filename = "profilepic.jpg"
            
            files = {
                'profile_pic': (filename, image_data, 'image/jpeg')
            }
            
            # Faire la requête de changement de photo de profil
            response = self.auth.session.post(
                "https://www.instagram.com/accounts/web_change_profile_picture/",
                headers=headers,
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Vérifier les différents indicateurs de succès
                    if (data.get("status") == "ok" or 
                        data.get("changed_profile") == True or
                        "profile_pic_url" in str(data)):
                        return {
                            "success": True, 
                            "data": data,
                            "message": "Photo de profil changée avec succès"
                        }
                    else:
                        error_message = data.get("message", "Échec du changement")
                        return {"success": False, "error": f"Erreur Instagram: {error_message}"}
                        
                except json.JSONDecodeError:
                    # Réponse non-JSON, vérifier le contenu
                    response_text = response.text
                    if "changed_profile" in response_text or "profile_pic" in response_text:
                        return {
                            "success": True,
                            "message": "Photo de profil changée avec succès",
                            "data": {"response": response_text[:200]}
                        }
                    else:
                        return {"success": False, "error": f"Réponse inattendue: {response_text[:200]}"}
            
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "Erreur de requête")
                    return {"success": False, "error": f"Erreur 400: {error_message}"}
                except:
                    return {"success": False, "error": f"Erreur 400: {response.text[:200]}"}
            
            elif response.status_code == 403:
                return {"success": False, "error": "Accès refusé. Vérifiez que le compte est bien connecté"}
            
            elif response.status_code == 404:
                return {"success": False, "error": "Endpoint non trouvé. Instagram a peut-être changé l'API"}
            
            else:
                return {"success": False, "error": f"Erreur HTTP {response.status_code}: {response.text[:200]}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur web: {str(e)}"}
    
    def _change_profile_picture_mobile(self, image_data: bytes) -> dict:
        """Fallback: Changer photo de profil via API mobile Instagram
        
        Args:
            image_data (bytes): Données de l'image traitée
        
        Returns:
            dict: Résultat de l'opération
        """
        try:
            user_id = self._get_user_id_from_session()
            if not user_id:
                return {"success": False, "error": "User ID non trouvé dans la session"}
            
            # Générer un upload ID unique
            upload_id = str(int(time.time() * 1000))
            
            # Étape 1: Upload de l'image
            upload_result = self._upload_profile_image_mobile(image_data, upload_id)
            if not upload_result["success"]:
                return upload_result
            
            # Étape 2: Configurer comme photo de profil
            configure_result = self._configure_profile_picture_mobile(upload_id, user_id)
            return configure_result
            
        except Exception as e:
            return {"success": False, "error": f"Erreur mobile API: {str(e)}"}
    
    def _upload_profile_image_mobile(self, image_data: bytes, upload_id: str) -> dict:
        """Upload de l'image de profil via API mobile"""
        try:
            device_headers = self._get_device_specific_headers()
            
            # Headers pour upload d'image de profil
            headers = self._build_complete_headers(
                endpoint="profile_pic_upload",
                friendly_name="IgApi: rupload_igphoto_profile"
            )
            
            # Modifier headers spécifiques pour upload
            headers["content-type"] = "application/octet-stream"
            headers["offset"] = "0"
            headers["x-entity-length"] = str(len(image_data))
            headers["x-entity-name"] = f"profile_pic_{upload_id}"
            headers["x-entity-type"] = "image/jpeg"
            
            upload_params = {
                "upload_id": upload_id,
                "session_id": upload_id,
                "media_type": "1",
                "upload_engine_config_enum": "0",
                "share_type": "profile_pic",
                "is_optimistic_upload": "false",
                "image_compression": '{"lib_name":"libjpeg","lib_version":"9d","quality":"90","original_width":320,"original_height":320}',
                "xsharing_user_ids": "[]",
                "retry_context": '{"num_reupload":0,"num_step_manual_retry":0,"num_step_auto_retry":0}'
            }
            
            headers["x-instagram-rupload-params"] = json.dumps(upload_params, separators=(',', ':'))
            
            response = self.auth.session.post(
                f"https://i.instagram.com/rupload_igphoto_profile/{upload_id}",
                headers=headers,
                data=image_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "upload_id": upload_id}
            else:
                return {"success": False, "error": f"Erreur upload: {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur upload: {str(e)}"}
    
    def _configure_profile_picture_mobile(self, upload_id: str, user_id: str) -> dict:
        """Configurer l'image uploadée comme photo de profil"""
        try:
            device_headers = self._get_device_specific_headers()
            
            # Données pour configuration de la photo de profil
            profile_data = {
                "upload_id": upload_id,
                "_uid": user_id,
                "_uuid": device_headers["x-ig-device-id"],
                "use_fbuploader": "true",
                "nav_chain": f"ProfileDisplayOptionsFragment:profile_display_options:1:button:{int(time.time() * 1000)}:::,ProfilePhotoSelectorFragment:profile_photo_selector:2:button:{int(time.time() * 1000)}:::"
            }
            
            signed_body = InstagramEncryption.create_signed_body(profile_data)
            
            headers = self._build_complete_headers(
                endpoint="profile_pic_configure",
                friendly_name="IgApi: accounts/change_profile_picture/"
            )
            
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/accounts/change_profile_picture/",
                headers=headers,
                data={"signed_body": signed_body},
                timeout=15
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    return {
                        "success": True, 
                        "data": parsed_data,
                        "message": "Photo de profil changée avec succès via API mobile"
                    }
                else:
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                if response.status_code == 400:
                    parsed_data = InstagramEncryption.safe_parse_json(response)
                    return self.handle_action_error(response.status_code, parsed_data, 
                                                 InstagramEncryption.safe_decode_response(response))
                
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur configuration: {str(e)}"}

    def download(self, media_url: str, save_path: str = "/storage/emulated/0") -> dict:
        """Télécharger un média Instagram (photo/vidéo) avec ses métadonnées
        
        Args:
            media_url (str): URL de la publication Instagram
            save_path (str): Chemin de sauvegarde (défaut: /storage/emulated/0)
        
        Returns:
            dict: Résultat avec 'success', 'data'/'error', 'files' (liste des fichiers sauvés)
        """
        try:
            # Extraire le media ID depuis l'URL
            if self.api:
                media_id = self.api.extract_media_id_from_url(media_url)
            else:
                media_id = self._extract_media_id_basic(media_url)
            
            if not media_id:
                return {"success": False, "error": "Impossible d'extraire l'ID du média depuis l'URL"}
            
            # Récupérer les informations détaillées du média
            print("🔍 Récupération des informations du média...")
            media_info = self._get_detailed_media_info(media_id)
            
            if not media_info.get("success"):
                return media_info
            
            media_data = media_info["data"]
            
            # Afficher les informations du média
            self._display_media_info(media_data)
            
            # Télécharger le média et ses métadonnées
            download_result = self._download_media_files(media_data, save_path)
            
            return download_result
            
        except Exception as e:
            return {"success": False, "error": f"Erreur téléchargement: {str(e)}"}
    
    def _get_detailed_media_info(self, media_id: str) -> dict:
        """Récupérer informations détaillées d'un média"""
        try:
            headers = self._build_complete_headers(
                endpoint="media_info",
                friendly_name=f"IgApi: media/{media_id}/info/"
            )
            
            response = self.auth.session.get(
                f"https://i.instagram.com/api/v1/media/{media_id}/info/",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                parsed_data = InstagramEncryption.safe_parse_json(response)
                
                if InstagramEncryption.is_success_response(response, parsed_data):
                    items = parsed_data.get("items", [])
                    if items:
                        return {"success": True, "data": items[0]}
                    else:
                        return {"success": False, "error": "Aucun média trouvé"}
                else:
                    return self.handle_action_error(response.status_code, parsed_data,
                                                 InstagramEncryption.safe_decode_response(response))
            else:
                return self.handle_http_error(response.status_code, 
                                            InstagramEncryption.safe_decode_response(response))
                
        except Exception as e:
            return {"success": False, "error": f"Erreur récupération infos: {str(e)}"}
    
    def _display_media_info(self, media_data: dict):
        """Afficher les informations du média"""
        try:
            # Type de média
            media_type = media_data.get("media_type", 0)
            if media_type == 1:
                media_type_text = "📷 Photo"
            elif media_type == 2:
                media_type_text = "🎥 Vidéo"
            elif media_type == 8:
                media_type_text = "📱 Carousel (plusieurs médias)"
            else:
                media_type_text = f"❓ Type {media_type}"
            
            print(f"\n{media_type_text}")
            
            # Auteur
            user = media_data.get("user", {})
            username = user.get("username", "Inconnu")
            full_name = user.get("full_name", "")
            print(f"👤 Auteur: @{username}" + (f" ({full_name})" if full_name else ""))
            
            # Date
            taken_at = media_data.get("taken_at")
            if taken_at:
                from datetime import datetime
                date_obj = datetime.fromtimestamp(taken_at)
                print(f"📅 Publié le: {date_obj.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Statistiques
            like_count = media_data.get("like_count", 0)
            comment_count = media_data.get("comment_count", 0)
            print(f"👍 {like_count:,} likes | 💬 {comment_count:,} commentaires")
            
            # Légende
            caption_info = media_data.get("caption")
            if caption_info and caption_info.get("text"):
                caption_text = caption_info["text"].strip()
                if caption_text:
                    print(f"\n📝 Légende:")
                    # Afficher la légende avec gestion des longs textes
                    if len(caption_text) > 200:
                        print(f"   {caption_text[:200]}...")
                        print(f"   [Légende complète: {len(caption_text)} caractères]")
                    else:
                        print(f"   {caption_text}")
                else:
                    print("📝 Légende: Aucune")
            else:
                print("📝 Légende: Aucune")
            
            # Informations spéciales pour carousel
            if media_type == 8:
                carousel_media = media_data.get("carousel_media", [])
                print(f"📱 Nombre d'éléments: {len(carousel_media)}")
                if len(carousel_media) > 1:
                    print(f"⚠️  Téléchargement du premier élément seulement")
            
        except Exception as e:
            print(f"⚠️  Erreur affichage infos: {e}")
    
    def _download_media_files(self, media_data: dict, save_path: str) -> dict:
        """Télécharger les fichiers médias directement dans le dossier principal"""
        try:
            import requests
            from datetime import datetime
            
            # Récupérer les informations de base
            user = media_data.get("user", {})
            username = user.get("username", "unknown_user")
            
            # Nom de base avec timestamp en millisecondes
            timestamp_ms = int(time.time() * 1000)
            base_filename = f"{username}_{timestamp_ms}"
            
            downloaded_files = []
            
            # Sauvegarder la légende si elle existe
            caption_info = media_data.get("caption")
            caption_text = ""
            if caption_info and caption_info.get("text"):
                caption_text = caption_info["text"].strip()
            
            if caption_text:
                caption_file = os.path.join(save_path, f"{base_filename}.txt")
                try:
                    with open(caption_file, 'w', encoding='utf-8') as f:
                        f.write(caption_text)
                    downloaded_files.append(caption_file)
                    print(f"✅ Légende sauvée: {base_filename}.txt")
                except Exception as e:
                    print(f"⚠️  Erreur sauvegarde légende: {e}")
            
            # Télécharger le média
            media_type = media_data.get("media_type", 0)
            
            if media_type == 8:  # Carousel - PREMIER ÉLÉMENT SEULEMENT
                carousel_media = media_data.get("carousel_media", [])
                print(f"📱 Carousel détecté avec {len(carousel_media)} éléments")
                print(f"📥 Téléchargement du premier élément seulement...")
                
                if carousel_media:
                    first_item = carousel_media[0]
                    file_result = self._download_single_media_direct(first_item, save_path, base_filename)
                    if file_result:
                        downloaded_files.extend(file_result)
            
            else:  # Photo ou vidéo simple
                file_result = self._download_single_media_direct(media_data, save_path, base_filename)
                if file_result:
                    downloaded_files.extend(file_result)
            
            if downloaded_files:
                return {
                    "success": True,
                    "data": {
                        "save_path": save_path,
                        "base_filename": base_filename,
                        "files_count": len(downloaded_files),
                        "username": username,
                        "caption": caption_text,
                        "like_count": media_data.get("like_count", 0),
                        "comment_count": media_data.get("comment_count", 0)
                    },
                    "files": downloaded_files
                }
            else:
                return {"success": False, "error": "Aucun fichier téléchargé"}
                
        except Exception as e:
            return {"success": False, "error": f"Erreur téléchargement fichiers: {str(e)}"}
    
    def _download_single_media_direct(self, media_item: dict, save_path: str, base_filename: str) -> list:
        """Télécharger un seul élément média directement dans le dossier principal"""
        try:
            import requests
            from urllib.parse import urlparse
            
            downloaded_files = []
            media_type = media_item.get("media_type", 0)
            
            if media_type == 1:  # Photo
                image_versions = media_item.get("image_versions2", {})
                candidates = image_versions.get("candidates", [])
                
                if candidates:
                    # Prendre la meilleure qualité (première dans la liste)
                    best_image = candidates[0]
                    image_url = best_image.get("url")
                    
                    if image_url:
                        # Nom du fichier direct
                        filename = f"{base_filename}.jpg"
                        filepath = os.path.join(save_path, filename)
                        
                        # Télécharger
                        if self._download_file(image_url, filepath):
                            downloaded_files.append(filepath)
                            print(f"✅ Photo sauvée: {filename}")
                        else:
                            print(f"❌ Échec téléchargement photo: {filename}")
            
            elif media_type == 2:  # Vidéo
                video_versions = media_item.get("video_versions", [])
                
                if video_versions:
                    # Prendre la meilleure qualité (première dans la liste)
                    best_video = video_versions[0]
                    video_url = best_video.get("url")
                    
                    if video_url:
                        # Nom du fichier direct
                        filename = f"{base_filename}.mp4"
                        filepath = os.path.join(save_path, filename)
                        
                        # Télécharger
                        if self._download_file(video_url, filepath):
                            downloaded_files.append(filepath)
                            print(f"✅ Vidéo sauvée: {filename}")
                        else:
                            print(f"❌ Échec téléchargement vidéo: {filename}")
                
                # Note: Pas de miniature séparée pour simplifier
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Erreur téléchargement média: {e}")
            return []
    
    def _download_file(self, url: str, filepath: str) -> bool:
        """Télécharger un fichier depuis une URL"""
        try:
            import requests
            
            # Headers pour téléchargement
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                "DNT": "1",
                "Connection": "keep-alive"
            }
            
            # Télécharger avec stream pour les gros fichiers
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                print(f"❌ Erreur HTTP {response.status_code} pour {url}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur téléchargement {url}: {e}")
            return False
    @property
    def edit(self):
        """Accès à l'éditeur de profil web"""
        if not hasattr(self, '_web_editor'):
            self._web_editor = InstagramWebEditor(self)
        return self._web_editor
