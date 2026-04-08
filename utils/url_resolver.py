# -*- coding: utf-8 -*-
"""
Résolveur d'URLs Instagram avec support liens courts - CORRIGÉ
Gestion complète des liens courts, extraction media/user IDs avec recherche similaire
"""

import re
import requests
import time
import random
from .license import validate_license
from .encryption import InstagramEncryption

class URLResolver:
    """Résolveur d'URLs Instagram avec support complet des liens courts et recherche similaire"""
    
    def __init__(self):
        # Validation licence obligatoire
        if not validate_license():
            raise PermissionError("Ce script n'est pas autorisé à utiliser cette bibliothèque. Veuillez contacter le créateur via: 0389561802 ou https://t.me/Kenny5626")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        })
    
    def resolve_short_url(self, url: str) -> str:
        """Résoudre un lien court vers l'URL complète"""
        try:
            # Patterns de liens courts Instagram et autres
            short_url_patterns = [
                r'https?://instagr\.am/p/([A-Za-z0-9_-]+)',
                r'https?://ig\.me/([A-Za-z0-9_-]+)',
                r'https?://bit\.ly/([A-Za-z0-9_-]+)',
                r'https?://tinyurl\.com/([A-Za-z0-9_-]+)',
                r'https?://t\.co/([A-Za-z0-9_-]+)',
                r'https?://vt\.tiktok\.com/([A-Za-z0-9_-]+)',
                r'https?://vm\.tiktok\.com/([A-Za-z0-9_-]+)'
            ]
            
            # Vérifier si c'est un lien court
            is_short_url = any(re.match(pattern, url) for pattern in short_url_patterns)
            
            if is_short_url:
                print(f"🔗 Résolution du lien court: {url}")
                
                # Suivre les redirections
                response = self.session.head(url, allow_redirects=True, timeout=10)
                
                if response.status_code in [200, 301, 302]:
                    resolved_url = response.url
                    print(f"✅ URL résolue: {resolved_url}")
                    return resolved_url
                else:
                    print(f"⚠️ Erreur résolution: HTTP {response.status_code}")
                    return url
            
            # Si ce n'est pas un lien court, retourner tel quel
            return url
            
        except Exception as e:
            print(f"⚠️ Erreur résolution URL: {e}")
            return url
    
    def extract_media_id_from_url(self, url: str) -> str:
        """Extraire media ID depuis URL Instagram (avec résolution liens courts)"""
        try:
            # D'abord résoudre les liens courts
            resolved_url = self.resolve_short_url(url)
            
            # Pattern pour les URLs Instagram post
            patterns = [
                r'/p/([A-Za-z0-9_-]+)/',  # Format /p/CODE/
                r'/reel/([A-Za-z0-9_-]+)/',  # Format /reel/CODE/
                r'/tv/([A-Za-z0-9_-]+)/',  # Format /tv/CODE/
                r'media_id=([0-9]+)',  # Format direct media_id
            ]
            
            for pattern in patterns:
                match = re.search(pattern, resolved_url)
                if match:
                    code = match.group(1)
                    
                    # Si c'est déjà un media ID numérique
                    if code.isdigit():
                        return code
                    
                    # Sinon convertir shortcode en media ID
                    media_id = self.shortcode_to_media_id(code)
                    if media_id:
                        return media_id
            
            # Si pas de pattern trouvé, essayer de récupérer via scraping
            response = self.session.get(resolved_url, headers={
                "user-agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36"
            }, timeout=10)
            
            if response.status_code == 200:
                content = InstagramEncryption.safe_decode_response(response)
                
                # Chercher media ID dans le HTML
                media_id_patterns = [
                    r'"media_id":"([0-9]+)"',
                    r'"id":"([0-9]+_[0-9]+)"',
                    r'"shortcode_media":{"__typename":"GraphImage","id":"([0-9]+)"',
                ]
                
                for pattern in media_id_patterns:
                    match = re.search(pattern, content)
                    if match:
                        media_id = match.group(1).split('_')[0]  # Prendre seulement la première partie
                        return media_id
            
            return None
            
        except Exception as e:
            return None
    
    def extract_user_id_from_url(self, url: str, api_session=None) -> str:
        """Extraire user ID depuis URL de profil avec recherche similaire EXACTEMENT comme script original"""
        try:
            # D'abord résoudre les liens courts
            resolved_url = self.resolve_short_url(url)
            
            # Extraire username depuis l'URL
            match = re.search(r'instagram\.com/([^/?]+)', resolved_url)
            if match:
                username = match.group(1).replace('@', '').strip()
                
                # Si on a une session API, utiliser la recherche avancée
                if api_session:
                    return self._username_to_user_id_with_similarity(username, api_session)
                else:
                    return self._username_to_user_id_basic(username)
            
            return None
            
        except Exception as e:
            return None
    
    def _username_to_user_id_with_similarity(self, username: str, api_session) -> str:
        """Convertir username en user ID avec recherche de similarité EXACTEMENT comme script original"""
        try:
            username = username.replace('@', '').strip()
            
            # Headers pour requête API
            headers = {
                "user-agent": api_session.device_manager.device_info['user_agent'],
                "x-ig-app-id": "567067343352427",
                "x-ig-android-id": api_session.device_manager.device_info['android_id'],
                "x-ig-device-id": api_session.device_manager.device_info['device_uuid'],
                "accept-language": "fr-FR, en-US",
                "authorization": getattr(api_session, 'auth_token', '') if hasattr(api_session, 'auth_token') else "",
            }
            
            # Méthode 1: Search users API - recherche exacte
            search_params = {
                "timezone_offset": "10800",
                "q": username,
                "count": "30"
            }
            
            response = api_session.session.get(
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
                            if user.get("username", "").lower() == username.lower():
                                user_id = str(user.get("pk"))
                                print(f"👥 User trouvé (exact): @{username} -> {user_id}")
                                return user_id
                        
                        # Si pas trouvé exact, chercher des similitudes EXACTEMENT comme script original
                        target_lower = username.lower()
                        best_matches = []
                        
                        # Recherche par préfixe
                        for user in users:
                            user_username = user.get("username", "").lower()
                            if user_username.startswith(target_lower) and user_username != target_lower:
                                best_matches.append((user.get("pk"), user_username))
                        
                        if best_matches:
                            # Prendre le plus court (plus proche)
                            best_matches.sort(key=lambda x: len(x[1]))
                            user_id = str(best_matches[0][0])
                            found_username = best_matches[0][1]
                            print(f"👥 User similaire trouvé: @{username} -> @{found_username} -> {user_id}")
                            return user_id
                        
                        # Recherche par parties de nom EXACTEMENT comme script original
                        username_parts = target_lower.split('_') + target_lower.split('.')
                        for user in users:
                            user_username = user.get("username", "").lower()
                            if any(part in user_username for part in username_parts if len(part) > 2):
                                user_id = str(user.get("pk"))
                                found_username = user.get("username", "")
                                print(f"👥 User similaire trouvé (partie): @{username} -> @{found_username} -> {user_id}")
                                return user_id
                        
                except Exception:
                    pass
            
            # Méthode 2: Web scraping fallback
            return self._username_to_user_id_basic(username)
            
        except Exception as e:
            return None
    
    def _username_to_user_id_basic(self, username: str) -> str:
        """Méthode basique de conversion username -> user ID"""
        try:
            # Web scraping basique
            web_response = self.session.get(
                f"https://www.instagram.com/{username}/",
                headers={"user-agent": "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36"},
                timeout=10
            )
            
            if web_response.status_code == 200:
                content = InstagramEncryption.safe_decode_response(web_response)
                
                # Extraire user ID depuis le HTML
                user_id_patterns = [
                    r'"profilePage_([0-9]+)"',
                    r'"user_id":"([0-9]+)"',
                    r'"owner":{"id":"([0-9]+)"'
                ]
                
                for pattern in user_id_patterns:
                    match = re.search(pattern, content)
                    if match:
                        user_id = match.group(1)
                        print(f"👥 User trouvé (web): @{username} -> {user_id}")
                        return user_id
            
            return None
            
        except Exception as e:
            return None
    
    def shortcode_to_media_id(self, shortcode: str) -> str:
        """Convertir shortcode Instagram en media ID (algorithme exact)"""
        try:
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
            decoded = 0
            multi = 1
            
            for char in reversed(shortcode):
                try:
                    decoded += multi * alphabet.index(char)
                    multi *= 64
                except ValueError:
                    return None
            
            return str(decoded)
            
        except Exception as e:
            return None
    
    def is_instagram_url(self, url: str) -> bool:
        """Vérifier si une URL est un lien Instagram valide"""
        try:
            # Résoudre les liens courts d'abord
            resolved_url = self.resolve_short_url(url)
            
            # Patterns Instagram valides
            instagram_patterns = [
                r'https?://(www\.)?instagram\.com/p/[A-Za-z0-9_-]+',
                r'https?://(www\.)?instagram\.com/reel/[A-Za-z0-9_-]+',
                r'https?://(www\.)?instagram\.com/tv/[A-Za-z0-9_-]+',
                r'https?://(www\.)?instagram\.com/[^/?]+/?$',  # Profil
                r'https?://instagr\.am/p/[A-Za-z0-9_-]+',
            ]
            
            return any(re.match(pattern, resolved_url) for pattern in instagram_patterns)
            
        except Exception:
            return False
    
    def get_url_type(self, url: str) -> str:
        """Déterminer le type d'URL Instagram"""
        try:
            resolved_url = self.resolve_short_url(url)
            
            if '/p/' in resolved_url:
                return 'post'
            elif '/reel/' in resolved_url:
                return 'reel'
            elif '/tv/' in resolved_url:
                return 'igtv'
            elif re.search(r'instagram\.com/[^/?]+/?$', resolved_url):
                return 'profile'
            else:
                return 'unknown'
                
        except Exception:
            return 'unknown'
