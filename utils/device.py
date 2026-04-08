# -*- coding: utf-8 -*-
"""
Gestionnaire de device Android réel avec MID Instagram
Extraction complète des informations du device via Termux/Android
"""

import os
import json
import time
import hashlib
import hmac
import base64
import uuid
import random
import subprocess
import requests
import re
from .encryption import InstagramEncryption
from .license import validate_license

def detect_termux_environment():
    """Détecter si on est dans Termux pour adapter les headers"""
    try:
        if os.environ.get('TERMUX_VERSION') or os.environ.get('PREFIX', '').startswith('/data/data/com.termux'):
            return True
        
        try:
            result = subprocess.run(['termux-info'], capture_output=True, timeout=3)
            if result.returncode == 0:
                return True
        except:
            pass
        
        if os.path.exists('/data/data/com.termux/files/usr'):
            return True
            
        return False
    except:
        return False

def get_optimal_encoding_for_environment():
    """Retourner l'encodage optimal selon l'environnement"""
    if detect_termux_environment():
        return "gzip, deflate"
    else:
        return "gzip, deflate, zstd"

class DeviceManager:
    """Gestionnaire des informations du device Android réel avec MID Instagram récupération améliorée"""
    
    def __init__(self):
        # Validation licence obligatoire
        if not validate_license():
            raise PermissionError("Ce script n'est pas autorisé à utiliser cette bibliothèque. Veuillez contacter le créateur via: 0389561802 ou https://t.me/Kenny5626")
        
        self.device_file = "ig_device.json"
        self.device_info = {}
        self.load_or_create_device_info()
    
    def get_real_android_device_info(self):
        """Récupérer les vraies informations du device Android depuis Termux"""
        device_info = {}
        
        try:
            # Android ID - Méthode corrigée et stable
            try:
                android_id = subprocess.run(['settings', 'get', 'secure', 'android_id'], 
                                          capture_output=True, text=True, timeout=5).stdout.strip()
                
                # Vérifier si la commande a échoué (contient des mots d'erreur)
                if android_id and not any(error_keyword in android_id.lower() for error_keyword in 
                                        ['failure', 'error', 'cmd:', 'failed', 'transaction']):
                    device_info['android_id'] = f"android-{android_id}"
                else:
                    # Utiliser la méthode alternative stable basée sur l'ICCID et build ID
                    iccid = subprocess.run(['getprop', 'persist.radio.volte0.iccid'], capture_output=True, text=True, timeout=3).stdout.strip()
                    build_id = subprocess.run(['getprop', 'ro.build.id'], capture_output=True, text=True, timeout=3).stdout.strip()
                    
                    # Créer un hash stable basé sur l'ICCID et build ID
                    device_string = f"{iccid}{build_id}"
                    stable_hash = hashlib.md5(device_string.encode()).hexdigest()[:16]
                    device_info['android_id'] = f"android-{stable_hash}"
                    
            except:
                device_info['android_id'] = f"android-{hashlib.md5(str(time.time()).encode()).hexdigest()[:16]}"
            
            # Device UUID basé sur Android ID
            device_info['device_uuid'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, device_info['android_id']))
            
            # Propriétés du build Android
            build_props = {
                'model': 'ro.product.model',
                'brand': 'ro.product.brand', 
                'manufacturer': 'ro.product.manufacturer',
                'device': 'ro.product.device',
                'android_version': 'ro.build.version.release',
                'sdk_version': 'ro.build.version.sdk',
                'build_id': 'ro.build.id',
                'fingerprint': 'ro.build.fingerprint'
            }
            
            for key, prop in build_props.items():
                try:
                    value = subprocess.run(['getprop', prop], capture_output=True, text=True, timeout=3).stdout.strip()
                    if value:
                        device_info[key] = value
                except:
                    pass
            
            # Écran et densité
            try:
                wm_size = subprocess.run(['wm', 'size'], capture_output=True, text=True, timeout=3).stdout
                if 'Physical size:' in wm_size:
                    import re
                    size_match = re.search(r'(\d+)x(\d+)', wm_size)
                    if size_match:
                        device_info['screen_width'] = int(size_match.group(1))
                        device_info['screen_height'] = int(size_match.group(2))
            except:
                pass
            
            try:
                wm_density = subprocess.run(['wm', 'density'], capture_output=True, text=True, timeout=3).stdout
                if 'Physical density:' in wm_density:
                    import re
                    density_match = re.search(r'(\d+)', wm_density)
                    if density_match:
                        device_info['screen_density'] = int(density_match.group(1))
            except:
                pass
                
            # Informations réseau
            try:
                result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and 'wlan' in result.stdout:
                    device_info['connection_type'] = 'WIFI'
                else:
                    device_info['connection_type'] = 'MOBILE'
            except:
                device_info['connection_type'] = 'WIFI'
            
        except Exception as e:
            pass
        
        # Fallbacks réalistes si récupération échoue
        fallbacks = {
            'model': 'SM-G991B',
            'brand': 'samsung', 
            'manufacturer': 'samsung',
            'device': 'z3q',
            'android_version': '12',
            'sdk_version': '32',
            'build_id': 'SP1A.210812.016',
            'screen_width': 900,
            'screen_height': 1600,
            'screen_density': 320,
            'connection_type': 'WIFI'
        }
        
        for key, default in fallbacks.items():
            if key not in device_info:
                device_info[key] = default
        
        # Générer family_device_id stable
        device_info['family_device_id'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, 
                                                        f"{device_info.get('android_id', '')}-family"))
        
        # User-Agent Instagram réaliste
        device_info['user_agent'] = (
            f"Instagram 307.0.0.34.111 Android "
            f"({device_info['sdk_version']}/{device_info['android_version']}; "
            f"{device_info['screen_density']}dpi; "
            f"{device_info['screen_width']}x{device_info['screen_height']}; "
            f"{device_info['manufacturer']}; {device_info['model']}; "
            f"{device_info['device']}; en_US; 370711637)"
        )
        
        return device_info
    
    def get_instagram_mid_from_web(self, device_info: dict) -> str:
        """Récupérer MID Instagram depuis le web avec méthodes améliorées"""
        # Session temporaire pour récupérer le MID
        import requests
        temp_session = requests.Session()
        
        # Étape 1: Essayer avec l'endpoint direct des données partagées
        try:
            
            shared_headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "accept-encoding": "gzip, deflate",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "user-agent": f"Mozilla/5.0 (Linux; Android {device_info['android_version']}; {device_info['model']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "cache-control": "no-cache"
            }
            
            response = temp_session.get(
                "https://www.instagram.com/data/shared_data/",
                headers=shared_headers,
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                
                # Utiliser le décodage unifié
                content = InstagramEncryption.safe_decode_response(response)
                
                # Chercher MID dans les données JSON
                try:
                    data = json.loads(content)
                    
                    # Chercher dans différents emplacements possibles
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
                    # Si ce n'est pas du JSON, chercher avec regex
                    pass
                
                # Patterns regex pour MID dans shared_data
                mid_patterns = [
                    r'"machine_id"\s*:\s*"([A-Za-z0-9+/=_-]{20,})"',
                    r'"mid"\s*:\s*"([A-Za-z0-9+/=_-]{20,})"',
                    r'"rollout_hash"\s*:\s*"([A-Za-z0-9+/=_-]{20,})"',
                    r'machine_id["\s]*:["\s]*([A-Za-z0-9+/=_-]{20,})'
                ]
                
                for pattern in mid_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        mid_candidate = matches[0].strip()
                        if len(mid_candidate) > 15:
                            return mid_candidate
        
        except Exception as e:
            print(f"⚠️ Méthode 1 échouée: {e}")
        
        # Étape 2: Page d'accueil Instagram avec cookies
        try:
            
            web_headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "cache-control": "max-age=0",
                "dnt": "1",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Android WebView";v="120"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": f"Mozilla/5.0 (Linux; Android {device_info['android_version']}; {device_info['model']}) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.210 Mobile Safari/537.36",
                "viewport-width": str(device_info['screen_width'])
            }
            
            response = temp_session.get(
                "https://www.instagram.com/", 
                headers=web_headers,
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                for cookie in response.cookies:
                    if cookie.name == 'mid':
                        return cookie.value
                
                # Utiliser le décodage unifié pour le contenu
                content = InstagramEncryption.safe_decode_response(response)
                
                # Patterns regex plus complets pour le HTML
                mid_patterns = [
                    r'"mid":"([A-Za-z0-9+/=_-]{15,})"',
                    r'"machine_id":"([A-Za-z0-9+/=_-]{15,})"',
                    r'"deviceId":"([A-Za-z0-9+/=_-]{15,})"',
                    r'mid=([A-Za-z0-9+/=_-]{15,})[;&,]',
                    r'machine_id["\s]*:["\s]*([A-Za-z0-9+/=_-]{15,})',
                    r'window\._sharedData[^}]*"mid":"([^"]+)"',
                    r'{"mid":"([A-Za-z0-9+/=_-]{15,})"}',
                    r'"rollout_hash":"([A-Za-z0-9+/=_-]{15,})"'
                ]
                
                for i, pattern in enumerate(mid_patterns):
                    matches = re.findall(pattern, content)
                    if matches:
                        for match in matches:
                            mid_candidate = match.strip()
                            if len(mid_candidate) >= 15 and not mid_candidate.startswith('null'):
                                return mid_candidate
        
        except Exception as e:
            print(f"⚠️ Méthode 2 échouée: {e}")
        
        # Étape 3: Endpoint graphql avec session établie
        try:
            graphql_headers = {
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "fr-FR,fr;q=0.9,en;q=0.8",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://www.instagram.com",
                "referer": "https://www.instagram.com/",
                "user-agent": web_headers["user-agent"],
                "x-asbd-id": "129477",
                "x-csrftoken": "missing",
                "x-ig-app-id": "936619743392459",
                "x-ig-www-claim": "0",
                "x-requested-with": "XMLHttpRequest"
            }
            
            # Essayer de faire une requête GraphQL simple qui retourne des métadonnées
            response = temp_session.get(
                "https://www.instagram.com/web/search/topsearch/?context=blended&query=&rank_token=&count=0",
                headers=graphql_headers,
                timeout=20
            )
            
            if response.status_code == 200:
                content = InstagramEncryption.safe_decode_response(response)
                
                # Chercher dans les headers de réponse d'abord
                for header_name, header_value in response.headers.items():
                    if 'mid' in header_name.lower() or 'machine' in header_name.lower():
                        if len(header_value) > 15:
                            return header_value
                
                # Puis dans le JSON de réponse
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if ('mid' in key.lower() or 'machine' in key.lower()) and isinstance(value, str) and len(value) > 15:
                                return value
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Méthode 3 échouée: {e}")
        
        try:
            # Utiliser des données réelles du device pour créer un MID cohérent
            device_string = f"{device_info['android_id']}{device_info['device_uuid']}{int(time.time())}"
            device_hash = hashlib.sha256(device_string.encode()).hexdigest()
            
            # Encoder en base64 pour ressembler à un vrai MID Instagram
            mid_bytes = device_hash[:32].encode()
            mid_b64 = base64.b64encode(mid_bytes).decode().rstrip('=')
            
            # Ajouter préfixe réaliste
            realistic_mid = f"aK{mid_b64}AABAABAAGr1cGeLxBgxSR2V-Nk"[:30]
            return realistic_mid
            
        except Exception as e:
            print(f"⚠️ Erreur génération MID: {e}")
        
        # Fallback ultime
        fallback_mid = f"aK{hashlib.md5(str(time.time()).encode()).hexdigest()[:20]}AABAA"
        return fallback_mid
    
    def load_or_create_device_info(self):
        """Charger ou créer les infos device avec MID réel"""
        if os.path.exists(self.device_file):
            try:
                with open(self.device_file, 'r', encoding='utf-8') as f:
                    loaded_info = json.load(f)
                
                # Vérifier si le MID existe et n'est pas le défaut statique
                current_mid = loaded_info.get('x_mid', '')
                if current_mid and len(current_mid) > 15 and not current_mid.startswith('aKqYqAABAAG'):
                    self.device_info = loaded_info
                    return
                else:
                    print("⚠️ MID invalide ou statique détecté, régénération...")
                    
            except Exception as e:
                print(f"⚠️ Erreur chargement device: {e}")
        
        # Créer nouvelles infos device avec MID réel
        device_info = self.get_real_android_device_info()
        
        # Récupérer le MID réel depuis Instagram avec méthode améliorée
        real_mid = self.get_instagram_mid_from_web(device_info)
        device_info['x_mid'] = real_mid
        
        self.device_info = device_info
        self.save_device_info()
    
    def save_device_info(self):
        """Sauvegarder les infos device"""
        try:
            with open(self.device_file, 'w', encoding='utf-8') as f:
                json.dump(self.device_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde device: {e}")
    
    def get_x_mid(self) -> str:
        """Récupérer le x-mid pour les headers"""
        mid = self.device_info.get('x_mid', '')
        if mid and len(mid) > 15:
            return mid
        
        # Si pas de MID valide, en récupérer un nouveau
        new_mid = self.get_instagram_mid_from_web(self.device_info)
        self.device_info['x_mid'] = new_mid
        self.save_device_info()
        return new_mid
    
    def refresh_mid_if_needed(self):
        """Rafraîchir le MID si nécessaire (après erreurs Instagram)"""
        try:
            current_mid = self.device_info.get('x_mid', '')
            
            # Si le MID est invalide, statique ou trop court
            if not current_mid or len(current_mid) < 15 or current_mid.startswith('aKqYqAABAAG') or current_mid.startswith('aKsWZwABAAG'):
                new_mid = self.get_instagram_mid_from_web(self.device_info)
                self.device_info['x_mid'] = new_mid
                self.save_device_info()
                return new_mid
            
            return current_mid
            
        except Exception as e:
            print(f"⚠️ Erreur rafraîchissement MID: {e}")
            return self.device_info.get('x_mid', 'fallback_mid')
