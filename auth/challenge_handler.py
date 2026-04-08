# -*- coding: utf-8 -*-
"""
Gestionnaire de Challenge/Checkpoint pour Instagram
Gestion complète des challenges génériques et résolution automatique
"""

import time
import json
import uuid
import random
import urllib.parse
import re
from ..utils.encryption import InstagramEncryption
from ..utils.device import get_optimal_encoding_for_environment

class ChallengeHandler:
    """Gestionnaire des challenges et checkpoints Instagram"""
    
    def __init__(self, auth_instance):
        self.auth = auth_instance
        self.challenge_data = {}
    
    def handle_challenge_flow(self, challenge_data: dict) -> dict:
        """Gérer le flux de challenge complet"""
        try:
            print("\n🔐 CHALLENGE DE SÉCURITÉ DÉTECTÉ")
            print("=" * 50)
            
            # Analyser le type de challenge
            challenge_type = self._analyze_challenge_type(challenge_data)
            
            if challenge_type == "select_verify_method":
                return self._handle_verify_method_selection(challenge_data.get("step_data", {}))
            elif challenge_type == "verify_code":
                return self._handle_code_verification(challenge_data.get("step_data", {}))
            else:
                return self._handle_generic_challenge(challenge_data)
                
        except Exception as e:
            return {"success": False, "error": f"Erreur challenge: {str(e)}"}
    
    def _analyze_challenge_type(self, challenge_data: dict) -> str:
        """Analyser le type de challenge"""
        try:
            challenge = challenge_data.get("challenge", {})
            step_name = challenge.get("step_name", "")
            
            if step_name:
                return step_name
            
            # Analyse du contenu pour déterminer le type
            data_str = str(challenge_data).lower()
            
            if any(word in data_str for word in ["select", "choose", "method", "option"]):
                return "select_verify_method"
            elif any(word in data_str for word in ["code", "verify", "enter", "6"]):
                return "verify_code"
            else:
                return "generic"
                
        except Exception:
            return "generic"
    
    def _handle_verify_method_selection(self, step_data: dict) -> dict:
        """Gérer la sélection de méthode de vérification avec gestion des méthodes temporairement indisponibles"""
        try:
            print("\n📱 MÉTHODES DE VÉRIFICATION DISPONIBLES:")
            print("=" * 60)
            
            # Extraire directement depuis step_data
            methods = step_data.get("methods", [])
            
            if not methods:
                # Extraire depuis step_data réel
                phone_number = step_data.get("phone_number", "")
                email = step_data.get("email", "")
                google_oauth_token = step_data.get("google_oauth_token", "false")
                
                methods = []
                
                # Ajouter SMS si numéro disponible
                if phone_number and phone_number != "None":
                    methods.append({
                        "id": "0",
                        "type": "sms",
                        "label": f"SMS au {phone_number}",
                        "description": "Code envoyé par SMS",
                        "value": phone_number
                    })
                
                # Ajouter Email si disponible
                if email and email != "None":
                    methods.append({
                        "id": "1", 
                        "type": "email",
                        "label": f"Email à {email}",
                        "description": "Code envoyé par email",
                        "value": email
                    })
                
                # Ajouter WhatsApp SEULEMENT si google_oauth_token="true"
                if google_oauth_token == "true" and phone_number and phone_number != "None":
                    methods.append({
                        "id": "2",
                        "type": "whatsapp", 
                        "label": f"WhatsApp au {phone_number}",
                        "description": "Code envoyé via WhatsApp",
                        "value": phone_number
                    })
            
            if not methods:
                print("❌ Aucune méthode trouvée - fallback")
                return self._request_verification_code_modern()
            
            # Gestion des méthodes temporairement indisponibles
            blocked_methods = set()
            
            while True:
                # Filtrer les méthodes bloquées temporairement
                available_methods = [m for m in methods if m["id"] not in blocked_methods]
                
                if not available_methods:
                    print("❌ Toutes les méthodes sont temporairement indisponibles")
                    print("⏳ Attendez quelques minutes et reconnectez-vous")
                    return {"success": False, "error": "Toutes les méthodes temporairement indisponibles"}
                
                # Afficher les choix disponibles
                print(f"✅ {len(available_methods)} méthode(s) disponible(s):")
                for i, method in enumerate(available_methods):
                    print(f"{i+1}. {method['label']}")
                    if method.get('description'):
                        print(f"   → {method['description']}")
                
                print(f"{len(available_methods)+1}. 🔄 Réessayer toutes les méthodes")
                print(f"{len(available_methods)+2}. 🚪 Quitter et changer de compte")
                
                # Demander le choix
                try:
                    max_choice = len(available_methods) + 2
                    choice_input = input(f"\n🎯 Choisissez une méthode (1-{max_choice}): ").strip()
                    choice_index = int(choice_input) - 1
                    
                    if choice_index == len(available_methods):  # Réessayer toutes
                        print("🔄 Réinitialisation des méthodes bloquées")
                        blocked_methods.clear()
                        continue
                    elif choice_index == len(available_methods) + 1:  # Quitter
                        print("🚪 Changement de compte")
                        return {"success": False, "error": "restart_login"}
                    elif 0 <= choice_index < len(available_methods):
                        selected_method = available_methods[choice_index]
                        print(f"✅ Méthode sélectionnée: {selected_method['label']}")
                        
                        # Envoyer la sélection
                        result = self._submit_verify_method_choice_modern(selected_method["id"])
                        
                        # Vérifier si cette méthode est temporairement bloquée
                        if not result["success"] and result.get("retry_method_selection"):
                            blocked_method_id = result.get("blocked_method")
                            if blocked_method_id:
                                blocked_methods.add(blocked_method_id)
                            continue  # Redemander le choix
                        
                        return result
                    else:
                        print("❌ Choix invalide, réessayez")
                        
                except ValueError:
                    print("❌ Veuillez entrer un numéro valide")
                except KeyboardInterrupt:
                    return {"success": False, "error": "restart_login"}
                    
        except Exception as e:
            print(f"❌ Erreur sélection méthode: {e}")
            return {"success": False, "error": f"Erreur sélection méthode: {str(e)}"}
    
    def _submit_verify_method_choice_modern(self, choice_value: str) -> dict:
        """Soumettre le choix de méthode avec gestion complète des retours"""
        try:
            print(f"\n🚀 SOUMISSION DU CHOIX: {choice_value}")
            print("=" * 60)
            
            challenge_data = self.challenge_data
            challenge_context = challenge_data.get("challenge_context", "")
            challenge_url = challenge_data.get("challenge_url", "")
    
            print(f"🎯 Choix sélectionné: {choice_value}")
            # Construire l'URL API pour la soumission
            if "/challenge/" in challenge_url:
                path_match = re.search(r'/challenge/([^/]+/[^/?]+)', challenge_url)
                if path_match:
                    challenge_path = path_match.group(1)
                    api_url = f"https://i.instagram.com/api/v1/challenge/{challenge_path}/"
                else:
                    return {"success": False, "error": "Path de challenge introuvable"}
            else:
                return {"success": False, "error": "URL de challenge invalide"}
          
            # Paramètres de requête POST
            params = {
                "guid": self.auth.device_manager.device_info['device_uuid'],
                "device_id": self.auth.device_manager.device_info['android_id'], 
                "challenge_context": challenge_context,
                "choice": choice_value
            }
            # Headers pour POST
            headers = {
                "accept-language": "fr-FR, en-US",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": "0",
                "priority": "u=3", 
                "x-bloks-version-id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
                "x-fb-client-ip": "True",
                "x-fb-connection-type": "WIFI",
                "x-fb-friendly-name": f"IgApi: challenge/{challenge_path}/",
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "user-agent": self.auth.device_manager.device_info['user_agent'],
            }
          
            # Envoyer la requête POST
            response = self.auth.session.post(api_url, headers=headers, data=params, timeout=15)
            
            # Décoder et analyser la réponse
            response_text = InstagramEncryption.safe_decode_response(response)
            
            try:
                result = json.loads(response_text)
                
                if response.status_code == 200:
                    # Vérifier le status de la réponse
                    if result.get("status") == "ok":
                        print("✅ Code de vérification envoyé avec succès!")
                        
                        # Extraire où le code a été envoyé
                        step_data = result.get("step_data", {})
                        phone_sent = step_data.get("phone_number", "")
                        email_sent = step_data.get("email", "")
                        
                        if phone_sent:
                            print(f"📱 Code envoyé par SMS au: {phone_sent}")
                        if email_sent:
                            print(f"📧 Code envoyé par email à: {email_sent}")
                        
                        # Passer à la demande de code
                        return self._request_verification_code_modern()
                    else:
                        return {"success": False, "error": f"Erreur réponse: {result}"}
                else:
                    return {"success": False, "error": f"Erreur HTTP {response.status_code}: {result}"}
                    
            except json.JSONDecodeError:
                print("❌ Réponse non-JSON:")
                print(response_text)
                
                # Parfois le code est envoyé même si la réponse n'est pas JSON
                if response.status_code == 200:
                    print("✅ Code probablement envoyé (réponse non-JSON mais status 200)")
                    return self._request_verification_code_modern()
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}: {response_text}"}
                    
        except Exception as e:
            print(f"❌ Erreur soumission choix: {e}")
            return {"success": False, "error": f"Erreur soumission choix: {str(e)}"}
    
    def _handle_code_verification(self, step_data: dict) -> dict:
        """Gérer la vérification de code directe"""
        try:
            # Analyser où le code a été envoyé
            phone_number = step_data.get("phone_number", "")
            email = step_data.get("email", "")
            contact_point = step_data.get("contact_point", "")
            
            if phone_number:
                formatted = self._format_phone_number(phone_number)
                print(f"📱 Code envoyé par SMS au: {formatted}")
            elif email:
                formatted = self._format_email(email)
                print(f"📧 Code envoyé par email à: {formatted}")
            elif contact_point:
                if "@" in contact_point:
                    formatted = self._format_email(contact_point)
                    print(f"📧 Code envoyé par email à: {formatted}")
                else:
                    formatted = self._format_phone_number(contact_point)
                    print(f"📱 Code envoyé par SMS au: {formatted}")
            else:
                print("📲 Code de vérification envoyé")
            
            # Demander directement le code
            return self._request_verification_code_modern()
            
        except Exception as e:
            return {"success": False, "error": f"Erreur vérification code: {str(e)}"}
    
    def _handle_generic_challenge(self, challenge_data: dict) -> dict:
        """Gérer un challenge générique avec analyse améliorée"""
        try:
            print("🔐 Challenge de sécurité détecté")
            
            # Analyser plus en profondeur les données
            data_str = str(challenge_data).lower()
            raw_response = challenge_data.get("raw_response", "").lower()
            
            # Chercher des indices plus spécifiques
            verification_hints = []
            
            if any(word in data_str + raw_response for word in ["email", "@", "e-mail", "courriel"]):
                verification_hints.append("email")
            
            if any(word in data_str + raw_response for word in ["phone", "sms", "text", "numero", "téléphone"]):
                verification_hints.append("sms")
            
            if any(word in data_str + raw_response for word in ["whatsapp", "wa"]):
                verification_hints.append("whatsapp")
            
            # Afficher les indices trouvés
            if verification_hints:
              
                # Si plusieurs indices, permettre le choix
                if len(verification_hints) > 1:
                    print("📱 Plusieurs méthodes possibles détectées:")
                    for i, hint in enumerate(verification_hints):
                        emoji = "📧" if hint == "email" else "📱" if hint == "sms" else "💬"
                        print(f"{i+1}. {emoji} {hint.title()}")
                    
                    try:
                        choice_input = input(f"\n🎯 Choisissez une méthode (1-{len(verification_hints)}) ou Entrée pour auto: ").strip()
                        if choice_input:
                            choice_index = int(choice_input) - 1
                            if 0 <= choice_index < len(verification_hints):
                                selected_hint = verification_hints[choice_index]
                                print(f"✅ Tentative avec {selected_hint}")
                    except:
                        pass
                
                # Utiliser le premier indice par défaut
                primary_hint = verification_hints[0]
                if primary_hint == "email":
                    print("📧 Challenge email probable")
                elif primary_hint == "sms":
                    print("📱 Challenge SMS probable")
                else:
                    print(f"📲 Challenge {primary_hint} probable")
            else:
                print("🔍 Type de challenge non identifié - tentative générique")
            
            print("📲 Un code de vérification devrait être envoyé automatiquement")
            print("Vérifiez vos SMS, emails ou notifications Instagram")
            
            # Demander le code directement
            return self._request_verification_code_modern()
                
        except Exception as e:
            return {"success": False, "error": f"Erreur challenge générique: {str(e)}"}
    
    def _request_verification_code_modern(self, retry_count: int = 0) -> dict:
        """Demander le code avec validation du nombre de chiffres"""
        try:
            max_retries = 3
            
            if retry_count >= max_retries:
                print("❌ Trop de tentatives de code incorrect")
                print("🔄 Options:")
                print("1. Changer de méthode de vérification")
                print("2. Quitter et changer de compte")
                
                while True:
                    try:
                        choice = input("Votre choix (1-2): ").strip()
                        if choice == "1":
                            return self._rewind_to_method_selection()
                        elif choice == "2":
                            return {"success": False, "error": "restart_login"}
                        else:
                            print("❌ Choix invalide (1-2)")
                    except KeyboardInterrupt:
                        return {"success": False, "error": "restart_login"}
            
            if retry_count > 0:
                print(f"❌ Code incorrect. Tentative {retry_count + 1}/{max_retries + 1}")
            
            print("\n🔢 Entrez le code de vérification reçu:")
            print("(Le code peut arriver par SMS, email, ou notification Instagram)")
            print("ℹ️  Option: tapez 'changer' pour changer de méthode")
            print("ℹ️  Option: tapez 'quitter' pour changer de compte")
            
            try:
                code = input("Code (6 chiffres): ").strip()
                
                if not code:
                    print("❌ Code requis")
                    return self._request_verification_code_modern(retry_count)
                
                # Gérer les options spéciales
                if code.lower() == "changer":
                    return self._rewind_to_method_selection()
                elif code.lower() == "quitter":
                    return {"success": False, "error": "restart_login"}
                
                # Validation stricte du nombre de chiffres
                if not code.isdigit():
                    print("❌ Le code doit contenir uniquement des chiffres")
                    return self._request_verification_code_modern(retry_count)
                
                if len(code) != 6:
                    print(f"❌ Le code doit contenir exactement 6 chiffres (vous avez entré {len(code)})")
                    return self._request_verification_code_modern(retry_count)
                
                return self._submit_verification_code_modern(code, retry_count)
                
            except KeyboardInterrupt:
                print("\n🔄 Options:")
                print("1. Changer de méthode de vérification") 
                print("2. Quitter et changer de compte")
                
                try:
                    choice = input("Votre choix (1-2): ").strip()
                    if choice == "1":
                        return self._rewind_to_method_selection()
                    else:
                        return {"success": False, "error": "restart_login"}
                except:
                    return {"success": False, "error": "restart_login"}
                    
        except Exception as e:
            return {"success": False, "error": f"Erreur demande code: {str(e)}"}
    
    def _submit_verification_code_modern(self, code: str, retry_count: int = 0) -> dict:
        """ÉTAPE 3: Soumettre le code avec format moderne"""
        try:
            print(f"\n🚀 Verification en Cours... ♻")
            
            current_context = self.challenge_data.get("challenge_context", "")            
            
            # Format direct comme dans le script original
            payload = f"security_code={code}&perf_logging_id={int(time.time() * 1000)}&has_follow_up_screens=0&bk_client_context=%7B%22bloks_version%22%3A%22ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1%22%2C%22styles_id%22%3A%22instagram%22%7D&challenge_context={urllib.parse.quote(current_context)}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"
            
            current_timestamp = time.time()
            
            headers = {
                "accept-language": "fr-FR, en-US",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": "0",
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "INDIGO_PRIMARY_BORDERED_SECONDARY",
                "x-bloks-prism-colors-enabled": "true",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-gray-red": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "true",
                "x-bloks-prism-indigo-link-version": "1",
                "x-bloks-version-id": "ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1",
                "x-fb-client-ip": "True",
                "x-fb-connection-type": "WIFI",
                "x-fb-friendly-name": "IgApi: bloks/apps/com.instagram.challenge.navigation.take_challenge/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "659.000",
                "x-ig-bandwidth-totalbytes-b": "1407377",
                "x-ig-bandwidth-totaltime-ms": "2763",
                "x-ig-client-endpoint": "verify_sms_code",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": f"bloks_unknown_class:verify_sms_code:8:button:{int(current_timestamp * 1000)}::",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-meta-zca": "eyJhbmRyb2lkIjp7ImFrYSI6eyJkYXRhVG9TaWduIjoiIiwiZXJyb3JzIjpbIktFWVNUT1JFX0RJU0FCTEVEX0JZX0NPTkZJRyJdfSwiZ3BpYSI6eyJ0b2tlbiI6IiIsImVycm9ycyI6WyJQTEFZX0lOVEVHUklUWV9ESVNBQkxFRF9CWV9DT05GSUciXX0sInBheWxvYWQiOnsicGx1Z2lucyI6eyJiYXQiOnsic3RhIjoiVW5wbHVnZ2VkIiwibHZsIjo4Mn0sInNjdCI6e319fX19",
                "x-pigeon-rawclienttime": f"{current_timestamp:.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }
            
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/",
                headers=headers,
                data=payload,
                timeout=120
            )
            
            response_text = InstagramEncryption.safe_decode_response(response)
            
            if response.status_code == 200:
                try:
                    result = json.loads(response_text)
                    
                    if result.get("status") == "ok":
                        # Vérifier si c'est vraiment un succès ou un code incorrect
                        if self._is_incorrect_code_response(result, response_text):
                            return self._request_verification_code_modern(retry_count + 1)
                        
                        # Utiliser la fonction de vérification avec le décodage existant
                        parsed_data = InstagramEncryption.safe_parse_json(response)
                        verification_result = self._verify_2fa_login_success(response_text, parsed_data)
                        
                        if verification_result["success"]:
                            print("✅ CODE VÉRIFIÉ AVEC SUCCÈS!")
                            return {
                                "success": True,
                                "message": verification_result["message"],
                                "data": {
                                    "user_data": verification_result["user_data"],
                                    "session_data": verification_result["session_data"]
                                },
                                "status": verification_result.get("status", "active")
                            }
                        else:
                            return {"success": False, "error": "Code incorrect"}
                    else:
                        error_msg = result.get("message", "")
                        if "incorrect" in error_msg.lower():
                            return self._request_verification_code_modern(retry_count + 1)
                        else:
                            return {"success": False, "error": f"Erreur: {result}"}
                            
                except json.JSONDecodeError:
                    if self._is_incorrect_code_text(response_text):
                        print("❌ Code incorrect détecté dans le texte")
                        return self._request_verification_code_modern(retry_count + 1)
                    
                    if response.status_code == 200:
                        print("✅ Succès probable malgré réponse non-JSON")
                        return {
                            "success": True,
                            "message": "2FA vérifié (réponse non-JSON)",
                            "data": {"response_text": response_text}
                        }
                    else:
                        return {"success": False, "error": "Code probablement incorrect"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return {"success": False, "error": f"Erreur: {str(e)}"}
    
    def _is_incorrect_code_response(self, response_data: dict, response_text: str) -> bool:
        """Détecter si la réponse indique un code incorrect"""
        try:
            # Messages spécifiques d'Instagram pour code incorrect
            incorrect_phrases = [
                "Un peu de patience",
                "Vérifiez le code que nous vous avons envoyé et réessayez",
                "V\\u00e9rifiez le code que nous vous avons envoy\\u00e9 et r\\u00e9essayez",
                "code incorrect",
                "invalid code",
                "wrong code"
            ]
            
            response_str = str(response_data) + response_text
            
            return any(phrase in response_str for phrase in incorrect_phrases)
            
        except Exception:
            return False
    
    def _is_incorrect_code_text(self, response_text: str) -> bool:
        """Détecter code incorrect dans texte brut"""
        try:
            incorrect_phrases = [
                "Un peu de patience",
                "Vérifiez le code",
                "V\\u00e9rifiez le code",
                "code incorrect",
                "invalid code",
                "wrong code",
                "réessayez"
            ]
            
            return any(phrase in response_text for phrase in incorrect_phrases)
            
        except Exception:
            return False
    
    def _rewind_to_method_selection(self) -> dict:
        """Revenir à la sélection de méthodes de vérification"""
        try:
            print("🔄 Retour à la sélection de méthodes...")
            
            challenge_data = self.challenge_data
            challenge_context = challenge_data.get("challenge_context", "")
            
            api_url = "https://b.i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.rewind_challenge/"
            
            current_timestamp = time.time()
            
            post_data = {
                "bk_client_context": urllib.parse.quote(json.dumps({
                    "bloks_version": "ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1",
                    "styles_id": "instagram"
                })),
                "challenge_context": challenge_context,
                "bloks_versioning_id": "ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"
            }
            
            headers = {
                "accept-language": "fr-FR, en-US",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": "0",
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "CONTROL",
                "x-bloks-prism-colors-enabled": "false",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-gray-red": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "false",
                "x-bloks-prism-indigo-link-version": "0",
                "x-bloks-version-id": "ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1",
                "x-fb-client-ip": "True",
                "x-fb-connection-type": "WIFI",
                "x-fb-friendly-name": "IgApi: bloks/apps/com.instagram.challenge.navigation.rewind_challenge/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "verify_email_code",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": f"bloks_unknown_class:verify_email_code:1:button:{int(current_timestamp * 1000)}::",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{current_timestamp:.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "x-zero-balance": "",
                "x-zero-eh": f"IG0e{random.choice(['a', 'b', 'c', 'd'])}{random.randint(10000000000000000000000000000, 99999999999999999999999999999)}",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }
            
            payload_str = urllib.parse.urlencode(post_data)
            
            response = self.auth.session.post(api_url, headers=headers, data=payload_str, timeout=15)
            
            if response.status_code == 200:
                response_text = InstagramEncryption.safe_decode_response(response)
                
                try:
                    result = json.loads(response_text)
                    print("✅ Retour à la sélection de méthodes réussi")
                    
                    # Extraire les nouvelles méthodes disponibles
                    methods = self._extract_verification_methods(result)
                    
                    if methods:
                        return self._handle_verify_method_selection({"methods": methods})
                    else:
                        print("❌ Aucune méthode trouvée après rewind")
                        return {"success": False, "error": "Aucune méthode disponible"}
                        
                except json.JSONDecodeError:
                    print("✅ Rewind réussi (réponse non-JSON)")
                    return self._request_verification_code_modern()
            else:
                print(f"❌ Erreur rewind: HTTP {response.status_code}")
                return {"success": False, "error": f"Erreur rewind: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Erreur rewind: {e}")
            return {"success": False, "error": f"Erreur rewind: {str(e)}"}
    
    def _extract_verification_methods(self, bloks_response: dict) -> list:
        """Extraire les méthodes de vérification depuis la réponse Bloks"""
        try:
            methods = []
            response_str = json.dumps(bloks_response)
            
            # Sets pour éviter les doublons
            phone_numbers = set()
            emails = set()
            
            # Rechercher les numéros de téléphone masqués
            phone_patterns = [
                r'\+\d{1,3}\s+\*+\s+\*+\s+\*+\s+\d{2}',
                r'\d{1,3}\s+\*+\s+\*+\s+\*+\s+\d{2}',
                r'\+\d{1,3}\s\*{2}\s\*{2}\s\*{3}\s\d{2}'
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, response_str)
                for match in matches:
                    clean_match = match.strip()
                    if clean_match not in phone_numbers:
                        phone_numbers.add(clean_match)
                        methods.append({
                            "id": "0",
                            "type": "sms",
                            "label": f"SMS au {clean_match}",
                            "description": "Code envoyé par SMS",
                            "value": clean_match
                        })
            
            # Rechercher les emails masqués
            email_patterns = [
                r'[a-zA-Z0-9]\*+[a-zA-Z0-9]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                r'[a-zA-Z]\*+\d+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ]
            
            for pattern in email_patterns:
                matches = re.findall(pattern, response_str)
                for match in matches:
                    clean_match = match.strip()
                    if clean_match not in emails:
                        emails.add(clean_match)
                        methods.append({
                            "id": "1",
                            "type": "email",
                            "label": f"Email à {clean_match}",
                            "description": "Code envoyé par email",
                            "value": clean_match
                        })
            
            # Rechercher WhatsApp si indiqué
            whatsapp_indicators = [
                r'"whatsapp[^"]*":\s*"true"',
                r'"wa[^"]*":\s*"true"', 
                r'"google_oauth_token":\s*"true"'
            ]
            
            whatsapp_found = False
            for indicator in whatsapp_indicators:
                if re.search(indicator, response_str, re.IGNORECASE):
                    if 'whatsapp' in response_str.lower() or 'google_oauth_token":"true"' in response_str:
                        whatsapp_found = True
                        break
            
            if whatsapp_found and phone_numbers:
                first_phone = list(phone_numbers)[0]
                methods.append({
                    "id": "2",
                    "type": "whatsapp",
                    "label": f"WhatsApp au {first_phone}",
                    "description": "Code envoyé via WhatsApp",
                    "value": first_phone
                })
            
            return methods
            
        except Exception as e:
            print(f"❌ Erreur extraction méthodes: {e}")
            return []
    
    def _format_phone_number(self, phone: str) -> str:
        """Formater un numéro de téléphone pour l'affichage"""
        try:
            clean_phone = re.sub(r'[^\d+]', '', str(phone))
            
            if len(clean_phone) >= 6:
                if clean_phone.startswith('+'):
                    country_code = clean_phone[:3]
                    last_digits = clean_phone[-4:]
                    stars = '*' * (len(clean_phone) - 7)
                    return f"{country_code}{stars}{last_digits}"
                else:
                    first_digits = clean_phone[:2]
                    last_digits = clean_phone[-4:]
                    stars = '*' * (len(clean_phone) - 6)
                    return f"{first_digits}{stars}{last_digits}"
            else:
                return phone[:2] + '*' * (len(phone) - 2)
                
        except:
            return str(phone)
    
    def _format_email(self, email: str) -> str:
        """Formater un email pour l'affichage"""
        try:
            email_str = str(email)
            
            if "@" in email_str:
                local, domain = email_str.split("@", 1)
                
                if len(local) <= 2:
                    masked_local = local[0] + "*"
                elif len(local) <= 4:
                    masked_local = local[:2] + "*" * (len(local) - 2)
                else:
                    masked_local = local[:2] + "*" * (len(local) - 4) + local[-2:]
                
                return f"{masked_local}@{domain}"
            else:
                return email_str
                
        except:
            return str(email)
    
    def _verify_2fa_login_success(self, response_text: str, parsed_data: dict = None) -> dict:
        """Vérifier le succès de connexion après 2FA - IDENTIQUE À LA CONNEXION NORMALE"""
        try:
            if parsed_data is None:
                try:
                    parsed_data = json.loads(response_text)
                except json.JSONDecodeError:
                    parsed_data = {"raw_text": response_text}
                except Exception:
                    parsed_data = {}
            
            # Vérifier si la connexion a réussi
            if not self.auth._check_login_success(parsed_data):
                return {"success": False, "error": "Connexion 2FA échouée"}
            
            # Extraire les données utilisateur
            user_data = self.auth._extract_user_data_fixed(response_text)
            
            # Créer un objet response simulé
            class MockResponse:
                def __init__(self, text, cookies_dict=None):
                    self.text = text
                    self.cookies = MockCookies(cookies_dict or {})
                    self.headers = {}
                    self.status_code = 200
                    
            class MockCookies:
                def __init__(self, cookies_dict):
                    self._cookies = cookies_dict
                    
                def __iter__(self):
                    for name, value in self._cookies.items():
                        yield MockCookie(name, value)
                        
            class MockCookie:
                def __init__(self, name, value):
                    self.name = name
                    self.value = value
            
            mock_response = MockResponse(response_text, self.auth.session.cookies.get_dict())
            
            # Extraire les données de session
            session_data = self.auth._extract_session_data_fixed(mock_response, user_data)
            
            # Vérifier le statut du compte
            username = user_data.get("username", "user_from_2fa")
            password_placeholder = "password_from_2fa"
            
            temp_result = {
                "success": True,
                "message": "2FA vérifié avec succès",
                "user_data": user_data,
                "session_data": session_data
            }
            
            final_result = self.auth.check_account_status_after_login(username, password_placeholder, temp_result)
            
            # Sauvegarder la session
            if final_result.get("status") != "disabled":
                self.auth._save_session_fixed(username, session_data, user_data)
            
            # Initialiser l'API
            auth_token = session_data.get("authorization", "")
            user_id = user_data.get("user_id", "")
            if user_id and auth_token:
                # L'API sera initialisée par le client principal
                pass
            
            return final_result
            
        except Exception as e:
            print(f"❌ Erreur vérification 2FA: {str(e)}")
            return {"success": False, "error": f"Erreur vérification 2FA: {str(e)}"}
    
    def solve_general_challenge(self, challenge_data: dict) -> bool:
        """Tenter de résoudre un challenge général automatiquement"""
        try:
            # Extraire les données du challenge
            challenge = challenge_data.get("challenge", {})
            challenge_url = challenge.get("url", "")
            
            # Extraire le challenge_context depuis l'URL
            challenge_context = ""
            if "challenge_context=" in challenge_url:
                import urllib.parse
                parsed_url = urllib.parse.urlparse(challenge_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                challenge_context = query_params.get("challenge_context", [""])[0]
            
            user_id = self._get_user_id_from_session()
            
            # Préparer les données pour take_challenge
            challenge_payload = {
                "_uuid": self.auth.device_manager.device_info['device_uuid'],
                "has_follow_up_screens": "0",
                "bk_client_context": json.dumps({
                    "bloks_version": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
                    "styles_id": "instagram"
                }),
                "challenge_context": challenge_context,
                "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd"
            }
            
            # Headers pour le challenge
            challenge_headers = {
                "accept-language": "fr-FR, en-US",
                "authorization": self._get_auth_token(),
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "ig-intended-user-id": user_id,
                "ig-u-ds-user-id": user_id,
                "ig-u-rur": f"CLN,{user_id},{int(time.time())}:01fe4b7e5da2cfafef2cfd62c178e124519ac81440f1b530c66b711f462db6975182767f",
                "priority": "u=3",
                "x-bloks-is-layout-rtl": "false",
                "x-bloks-prism-button-version": "CONTROL",
                "x-bloks-prism-colors-enabled": "false",
                "x-bloks-prism-elevated-background-fix": "false",
                "x-bloks-prism-extended-palette-indigo": "false",
                "x-bloks-prism-font-enabled": "false",
                "x-bloks-prism-indigo-link-version": "0",
                "x-bloks-version-id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
                "x-fb-client-ip": "True",
                "x-fb-connection-type": "WIFI",
                "x-fb-friendly-name": "IgApi: bloks/apps/com.instagram.challenge.navigation.take_challenge/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "1215.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "warning",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-languages": '{"system_languages":"fr-FR"}',
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": f"com.bloks.www.caa.login.login_homepage:com.bloks.www.caa.login.login_homepage:1:button:{int(time.time() * 1000)}::,IgCdsScreenNavigationLoggerModule:com.bloks.www.caa.login.login_homepage:3:button:{int(time.time() * 1000)}::,com.bloks.www.caa.login.save-credentials:com.bloks.www.caa.login.save-credentials:4:button:{int(time.time() * 1000)}::,bloks_unknown_class:warning:5:button:{int(time.time() * 1000)}::",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": self._generate_www_claim(),
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-meta-zca": "eyJhbmRyb2lkIjp7ImFrYSI6e30sImdwaWEiOnsidG9rZW4iOiIiLCJlcnJvcnMiOlsiUExBWV9JTlRFR1JJVFlfRElTQUJMRURfQllfQ09ORklHIl19LCJwYXlsb2FkIjp7InBsdWdpbnMiOnsiYmF0Ijp7InN0YSI6IlVucGx1Z2dlZCIsImx2bCI6OTF9LCJzY3QiOnt9fX19fQ",
                "x-pigeon-rawclienttime": f"{time.time():.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP",
                "x-fb-rmd": "state=URL_ELIGIBLE"
            }
            
            # Encoder les données du payload
            payload_str = urllib.parse.urlencode(challenge_payload)
            
            # Envoyer la requête de challenge
            response = self.auth.session.post(
                "https://b.i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/",
                headers=challenge_headers,
                data=payload_str,
                timeout=15
            )
            
            return response.status_code == 200
                
        except Exception as e:
            return False
    
    def _get_user_id_from_session(self) -> str:
        """Récupérer user ID depuis la session"""
        # Méthode 1: Depuis user_data
        user_data = self.auth.session_data.get("user_data", {}) or self.auth.session_data.get("logged_in_user", {})
        user_id = user_data.get("user_id")
        
        if user_id:
            return str(user_id)
        
        # Méthode 2: Depuis authorization_data
        auth_data = self.auth.session_data.get("authorization_data", {})
        user_id = auth_data.get("ds_user_id")
        
        if user_id:
            return str(user_id)
        
        # Méthode 3: Depuis cookies
        cookies = self.auth.session_data.get("cookies", {})
        for name, value in cookies.items():
            if "ds_user_id" in name:
                return str(value)
        
        # Méthode 4: Depuis account_id
        account_id = self.auth.session_data.get("account_id")
        if account_id:
            return str(account_id)
        
        # Fallback
        return "58768170545"
    
    def _get_auth_token(self) -> str:
        """Récupérer token d'autorisation"""
        # Méthode 1: Depuis authorization_data
        auth_data = self.auth.session_data.get("authorization_data", {})
        auth_header = auth_data.get("authorization_header")
        
        if auth_header and "Bearer" in auth_header:
            return auth_header
        
        # Méthode 2: Depuis authorization
        auth_token = self.auth.session_data.get("authorization")
        if auth_token and "Bearer" in auth_token:
            return auth_token
        
        # Méthode 3: Construire depuis sessionid
        sessionid = None
        
        if "sessionid" in self.auth.session_data:
            sessionid = self.auth.session_data["sessionid"]
        else:
            cookies = self.auth.session_data.get("cookies", {})
            for key, value in cookies.items():
                if "sessionid" in key.lower():
                    sessionid = value
                    break
        
        if sessionid:
            user_id = self._get_user_id_from_session()
            
            if '%3A' not in sessionid:
                sessionid = urllib.parse.quote(sessionid)
            
            token_data = {
                "ds_user_id": user_id,
                "sessionid": sessionid
            }
            
            encoded = base64.b64encode(json.dumps(token_data, separators=(',', ':')).encode()).decode()
            constructed_token = f"Bearer IGT:2:{encoded}"
            
            self.auth.session_data["authorization"] = constructed_token
            
            return constructed_token
        
        # Fallback avec format basique
        user_id = self._get_user_id_from_session()
        basic_sessionid = f"{user_id}%3Alvz6FpqwtSbbxg%3A14%3AAYenc6E_SD_9y1i7bD0kqflRuRfy9XhDt8y3jiUnxQ"
        token_data = {
            "ds_user_id": user_id,
            "sessionid": basic_sessionid
        }
        encoded = base64.b64encode(json.dumps(token_data, separators=(',', ':')).encode()).decode()
        return f"Bearer IGT:2:{encoded}"
    
    def _generate_www_claim(self) -> str:
        """Générer claim WWW depuis les headers de session"""
        # Récupérer le claim depuis les headers IG de la session
        ig_headers = self.auth.session_data.get("ig_headers", {})
        
        if ig_headers.get("x-ig-www-claim"):
            return ig_headers["x-ig-www-claim"]
        
        # Format basé sur les captures
        user_id = self._get_user_id_from_session()
        timestamp = int(time.time())
        
        return f"hmac.AR1s8TY7BU_rk1J-R5WfLOO6qHRI7pyziid_l-jeoFNFJ{random.choice(['tpL', 'gnN', 'k3p', 'euZ'])}"
