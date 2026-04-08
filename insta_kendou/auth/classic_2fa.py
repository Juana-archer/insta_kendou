# -*- coding: utf-8 -*-
"""
Gestionnaire 2FA Classique pour Instagram
Gestion complète du flux de challenge/checkpoint classique
"""

import time
import json
import uuid
import random
import urllib.parse
import re
from ..utils.encryption import InstagramEncryption
from ..utils.device import get_optimal_encoding_for_environment

class ClassicManager:
    """Gestionnaire du flux 2FA classique complet"""

    def __init__(self, auth_instance):
        self.auth = auth_instance
        self.challenge_data = {}

    def handle_2fa_flow(self, response_text: str) -> dict:
        """Gérer le 2FA avec gestion améliorée des cas edge"""
        try:
            print("\n🔐 AUTHENTIFICATION À DEUX FACTEURS REQUISE")
            print("=" * 50)

            # Extraire l'URL de challenge depuis la réponse Bloks
            challenge_url, challenge_context, api_path, method = self.extract_challenge_url_from_bloks(response_text)

            if not challenge_url:
                print("❌ Impossible d'extraire l'URL de challenge")
                return {"success": False, "error": "URL de challenge non trouvée"}

            # Sauvegarder les données de base
            self.challenge_data = {
                "challenge_url": challenge_url,
                "challenge_context": challenge_context,
                "api_path": api_path
            }

            # Essayer de récupérer les détails du challenge
            challenge_data = self.get_challenge_data(challenge_url)

            if "error" in challenge_data:
                print(f"⚠️ Impossible de récupérer les méthodes: {challenge_data['error']}")
                print("📲 Passage en mode challenge générique")
                return self.handle_generic_challenge_fallback()

            # Analyser le type de challenge
            step_name = challenge_data.get("step_name", "unknown")
            step_data = challenge_data.get("step_data", {})

            print(f"🔍 Type de challenge: {step_name}")

            # Mettre à jour les données sauvegardées
            self.challenge_data.update({
                "step_name": step_name,
                "step_data": step_data,
                "full_data": challenge_data
            })

            # Gérer selon le type de challenge
            if step_name == "select_verify_method":
                return self.handle_verify_method_selection_modern(step_data)
            elif step_name in ["verify_code", "verify_sms_code", "verify_email_code"]:
                return self.handle_code_verification_modern(step_data)
            else:
                return self.handle_generic_challenge_fallback()

        except Exception as e:
            print(f"❌ Erreur gestion 2FA: {str(e)}")
            return {"success": False, "error": str(e)}

    def extract_challenge_url_from_bloks(self, response_text: str) -> tuple:
        """Extraire URL de challenge avec NETTOYAGE COMPLET des échappements"""
        try:
            challenge_url = ""
            challenge_context = ""
            api_path = ""

            # 1. Extraire URL complète avec tous les tokens
            url_patterns = [
                r'url\\*"\\*:\\*"\\*(https:\\*/\\*/i\.instagram\.com\\*/challenge\\*/[^"\\]*[A-Za-z0-9_-]+\\*/[A-Za-z0-9_-]+[^"\\]*)',
                r'"url"[^"]*"(https://i\.instagram\.com/challenge/[^"]*)"',
            ]

            for pattern in url_patterns:
                matches = re.findall(pattern, response_text)
                if matches:
                    challenge_url = matches[0]

                    # NETTOYAGE COMPLET des échappements
                    challenge_url = challenge_url.replace('\\\\\\\\\\\\\\/', '/')
                    challenge_url = challenge_url.replace('\\\\\\\\\\/', '/')
                    challenge_url = challenge_url.replace('\\\\\\/', '/')
                    challenge_url = challenge_url.replace('\\/', '/')
                    challenge_url = challenge_url.replace('\\"', '"')
                    break

            # 2. Extraire challenge_context COMPLET
            context_patterns = [
                r'challenge_context\\*"\\*:\\*"\\*([A-Za-z0-9+/=_-]+)',
                r'"challenge_context"[^"]*"([A-Za-z0-9+/=_-]+)"',
            ]

            for pattern in context_patterns:
                matches = re.findall(pattern, response_text)
                if matches:
                    challenge_context = matches[0]
                    challenge_context = challenge_context.replace('\\/', '/')
                    challenge_context = challenge_context.replace('\\"', '"')
                    break

            # 3. Extraire api_path COMPLET
            path_patterns = [
                r'api_path\\*"\\*:\\*"\\*([^"\\]*[A-Za-z0-9_-]+\\*\/[A-Za-z0-9_-]+[^"\\]*)',
                r'"api_path"[^"]*"([^"]*)"',
            ]

            for pattern in path_patterns:
                matches = re.findall(pattern, response_text)
                if matches:
                    api_path = matches[0]

                    # NETTOYAGE COMPLET
                    api_path = api_path.replace('\\\\\\\\\\\\\\/', '/')
                    api_path = api_path.replace('\\\\\\\\\\/', '/')
                    api_path = api_path.replace('\\\\\\/', '/')
                    api_path = api_path.replace('\\/', '/')
                    api_path = api_path.replace('\\"', '"')
                    break

            # Validation finale
            if challenge_url and challenge_context:
                return challenge_url, challenge_context, api_path, "regex_cleaned"

            print("\n❌ ÉCHEC D'EXTRACTION")
            return None, None, None, None

        except Exception as e:
            print(f"❌ Erreur extraction: {e}")
            return None, None, None, None

    def get_challenge_data(self, challenge_url: str) -> dict:
        """Récupérer données de challenge avec DÉCODAGE UNIFIÉ pour tous les environnements"""
        try:
            challenge_context = self.challenge_data.get("challenge_context", "")

            # Vérifier que l'URL est correctement nettoyée
            if not challenge_url.startswith('https://'):
                print(f"❌ URL mal formatée: {challenge_url}")
                return {"error": "URL de challenge mal formatée"}

            # Construire l'URL API directe EXACTEMENT comme votre exemple
            if "/challenge/" in challenge_url:
                path_match = re.search(r'/challenge/(.+)/?$', challenge_url)
                if path_match:
                    challenge_path = path_match.group(1).rstrip('/')
                    api_url = f"https://i.instagram.com/api/v1/challenge/{challenge_path}/"
                else:
                    print("❌ Impossible d'extraire le path de challenge")
                    return {"error": "Path de challenge introuvable"}
            else:
                print("❌ URL de challenge invalide")
                return {"error": "URL de challenge invalide"}

            # PARAMÈTRES EXACTS
            params = {
                "guid": self.auth.device_manager.device_info['device_uuid'],
                "device_id": self.auth.device_manager.device_info['android_id'],
                "challenge_context": challenge_context
            }

            # TIMESTAMP PRÉCIS
            current_timestamp = time.time()
            pigeon_rawclienttime = f"{current_timestamp:.3f}"
            nav_chain_timestamp = f"{int(current_timestamp * 1000):.0f}"

            # HEADERS EXACTS basés sur votre exemple qui fonctionne
            headers = {
                "accept-language": "fr-FR, en-US",
                "ig-intended-user-id": "0",
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
                "x-fb-friendly-name": f"IgApi: challenge/{challenge_path}/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "3204.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.caa.login.login_homepage",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": f"com.bloks.www.caa.login.aymh_single_profile_screen_entry:com.bloks.www.caa.login.aymh_single_profile_screen_entry:1:button:{nav_chain_timestamp}::",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-meta-zca": "eyJhbmRyb2lkIjp7ImFrYSI6e30sImdwaWEiOnsidG9rZW4iOiIiLCJlcnJvcnMiOlsiUExBWV9JTlRFR1JJVFlfRElTQUJMRURfQllfQ09ORklHIl19LCJwYXlsb2FkIjp7InBsdWdpbnMiOnsiYmF0Ijp7InN0YSI6IlVucGx1Z2dlZCIsImx2bCI6ODZ9LCJzY3QiOnt9fX19fQ",
                "x-pigeon-rawclienttime": pigeon_rawclienttime,
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            # ATTENDRE 2-3 SECONDES avant la requête
            time.sleep(2)
            # Envoyer la requête GET avec les paramètres EXACTS
            response = self.auth.session.get(api_url, headers=headers, params=params, timeout=30)

            # UTILISER LE DÉCODAGE UNIFIÉ
            response_text = InstagramEncryption.safe_decode_response(response)

            try:
                # UTILISER LE PARSING JSON UNIFIÉ
                parsed_data = InstagramEncryption.safe_parse_json(response)

                # Vérifier si c'est une erreur de parsing
                if isinstance(parsed_data, dict) and "error" in parsed_data:
                    if parsed_data["error"] == "Non-JSON":
                        print("⚠️ Réponse non-JSON décodée avec succès:")
                        print(parsed_data["raw_text"])
                        return {"error": "Réponse non-JSON", "raw_response": parsed_data["raw_text"]}
                    else:
                        print(f"❌ Erreur parsing: {parsed_data['error']}")
                        return {"error": f"Erreur parsing: {parsed_data['error']}"}

                if response.status_code == 200:
                    # VÉRIFIER SI LA RÉPONSE CONTIENT LES DONNÉES ATTENDUES
                    if parsed_data.get("action") == "close":
                        print("⚠️ PROBLÈME: Instagram ferme le challenge automatiquement")
                        print("🔄 Essai avec méthode alternative...")

                        # ESSAYER AVEC LA MÉTHODE POST au lieu de GET
                        return self._try_challenge_post_method(api_url, params, headers, challenge_path)

                    step_name = parsed_data.get("step_name", "unknown")
                    step_data = parsed_data.get("step_data", {})

                    if step_name != "unknown" and step_data:
                        return {
                            "step_name": step_name,
                            "step_data": step_data,
                            "status": "ok",
                            "raw_response": parsed_data
                        }
                    else:
                        print("❌ Données de challenge vides ou invalides")
                        return {"error": "Données de challenge vides"}
                else:
                    print(f"❌ Erreur HTTP {response.status_code}")
                    return {
                        "error": f"HTTP {response.status_code}",
                        "raw_response": parsed_data
                    }

            except Exception as parsing_error:
                print(f"❌ Erreur critique parsing: {parsing_error}")
                print("📄 CONTENU BRUT POUR DEBUG:")
                print(response_text[:1000] + "..." if len(response_text) > 1000 else response_text)
                return {
                    "error": f"Erreur parsing critique: {parsing_error}",
                    "raw_response": response_text
                }

        except Exception as e:
            print(f"❌ Erreur récupération données challenge: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _try_challenge_post_method(self, api_url: str, params: dict, headers: dict, challenge_path: str) -> dict:
        """Méthode alternative avec POST si GET échoue"""
        try:
            print("\n🔄 TENTATIVE AVEC MÉTHODE POST:")
            print("-" * 40)

            # Modifier headers pour POST
            headers_post = headers.copy()
            headers_post["content-type"] = "application/x-www-form-urlencoded; charset=UTF-8"

            print("📤 ENVOI REQUÊTE POST:")

            # Envoyer en POST au lieu de GET
            response = self.auth.session.post(api_url, headers=headers_post, data=params, timeout=30)

            print(f"📥 RÉPONSE POST: Status {response.status_code}")

            response_text = InstagramEncryption.safe_decode_response(response)
            print(f"📄 CONTENU RÉPONSE POST:")
            print(response_text)

            try:
                response_json = json.loads(response_text)

                if response.status_code == 200:
                    step_name = response_json.get("step_name", "unknown")
                    step_data = response_json.get("step_data", {})

                    if step_name != "unknown" and step_data:
                        print("✅ SUCCÈS AVEC MÉTHODE POST!")
                        return {
                            "step_name": step_name,
                            "step_data": step_data,
                            "status": "ok",
                            "raw_response": response_json
                        }

                return {"error": "Échec méthode POST"}

            except json.JSONDecodeError:
                return {"error": "POST non-JSON", "raw_response": response_text}

        except Exception as e:
            return {"error": f"Erreur POST: {str(e)}"}

    def handle_verify_method_selection_modern(self, step_data: dict) -> dict:
        """Gérer la sélection de méthode avec données extraites réelles"""
        try:
            print("\n📱 MÉTHODES DE VÉRIFICATION DISPONIBLES:")
            print("=" * 60)

            # Extraire directement depuis step_data si pas de méthodes pré-extraites
            methods = step_data.get("methods", [])

            if not methods:
                # Extraire depuis step_data réel
                phone_number = step_data.get("phone_number", "")
                email = step_data.get("email", "")
                google_oauth_token = step_data.get("google_oauth_token", "false")
                show_selfie_captcha = step_data.get("show_selfie_captcha", False)

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

                # Ajouter WhatsApp SEULEMENT si google_oauth_token="true" ET qu'il y a un numéro
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
                return self.request_verification_code_modern()

            # NOUVELLE BOUCLE: Gestion des méthodes temporairement indisponibles
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
                        result = self.submit_verify_method_choice_modern(selected_method["id"])

                        # NOUVEAU: Vérifier si cette méthode est temporairement bloquée
                        if not result["success"] and result.get("retry_method_selection"):
                            blocked_method_id = result.get("blocked_method")
                            if blocked_method_id:
                                blocked_methods.add(blocked_method_id)
                            continue  # Redemander le choix

                        # Si succès ou autre erreur, retourner le résultat
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

    def submit_verify_method_choice_modern(self, choice_value: str) -> dict:
        """Soumettre le choix de méthode avec logs complets et gestion d'erreurs améliorée"""
        try:
            print(f"\n🚀 SOUMISSION DU CHOIX: {choice_value}")

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
            response = self.auth.session.post(api_url, headers=headers, data=params, timeout=30)

            # Décoder et analyser la réponse
            response_text = InstagramEncryption.safe_decode_response(response)
            try:
                result = json.loads(response_text)

                if response.status_code == 200:
                    # Vérifier le status de la réponse
                    if result.get("status") == "ok":
                        print("✅ Code de vérification envoyé avec succès!")

                        # Extraire où le code a été envoyé depuis la réponse RÉELLE
                        step_data = result.get("step_data", {})
                        phone_sent = step_data.get("phone_number", "")
                        email_sent = step_data.get("email", "")

                        if phone_sent:
                            print(f"📱 Code envoyé par SMS au: {phone_sent}")
                        if email_sent:
                            print(f"📧 Code envoyé par email à: {email_sent}")

                        # Passer à la demande de code
                        return self.request_verification_code_modern()
                    else:
                        return {"success": False, "error": f"Erreur réponse: {result}"}
                else:
                    # GESTION AMÉLIORÉE DES ERREURS HTTP 400
                    if response.status_code == 400:
                        error_message = result.get("message", "").lower()
                        
                        # Cas 1: "Veuillez patienter quelques minutes"
                        if "patienter" in error_message or "wait" in error_message:
                            print(f"⏳ {result.get('message', 'Méthode temporairement indisponible')}")
                            print("🔄 Cette méthode sera ignorée temporairement")
                            return {
                                "success": False, 
                                "retry_method_selection": True,
                                "blocked_method": choice_value,
                                "error": "Méthode temporairement bloquée"
                            }
                        
                        # Cas 2: "Select a valid choice. X is not one of the available choices"
                        elif "not one of the available choices" in error_message or "valid choice" in error_message:
                            print(f"❌ {result.get('message', 'Choix invalide')}")
                            print("🔄 Cette méthode n'est plus disponible")
                            return {
                                "success": False, 
                                "retry_method_selection": True,
                                "blocked_method": choice_value,
                                "error": "Méthode non disponible"
                            }
                        
                        # Autres erreurs 400
                        else:
                            return {"success": False, "error": f"Erreur HTTP 400: {result}"}
                    
                    else:
                        return {"success": False, "error": f"Erreur HTTP {response.status_code}: {result}"}

            except json.JSONDecodeError:
                print("❌ Réponse non-JSON:")
                print(response_text)

                # Parfois le code est envoyé même si la réponse n'est pas JSON
                if response.status_code == 200:
                    print("✅ Code probablement envoyé (réponse non-JSON mais status 200)")
                    return self.request_verification_code_modern()
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}: {response_text}"}

        except Exception as e:
            print(f"❌ Erreur soumission choix: {e}")
            return {"success": False, "error": f"Erreur soumission choix: {str(e)}"}

    def handle_code_verification_modern(self, step_data: dict) -> dict:
        """Gérer la vérification de code (format moderne)"""
        try:
            # Analyser les détails du code envoyé
            phone_number = step_data.get("phone_number", "")
            email = step_data.get("email", "")

            if phone_number:
                print(f"📱 Code envoyé par SMS au: {self.format_phone_number(phone_number)}")
            elif email:
                print(f"📧 Code envoyé par email à: {self.format_email(email)}")
            else:
                print("📲 Code de vérification envoyé")

            return self.request_verification_code_modern()

        except Exception as e:
            return {"success": False, "error": f"Erreur vérification code: {str(e)}"}

    def request_verification_code_modern(self, retry_count: int = 0) -> dict:
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
                            return self.rewind_to_method_selection()
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
                    return self.request_verification_code_modern(retry_count)

                # Gérer les options spéciales
                if code.lower() == "changer":
                    return self.rewind_to_method_selection()
                elif code.lower() == "quitter":
                    return {"success": False, "error": "restart_login"}

                # Validation stricte du nombre de chiffres
                if not code.isdigit():
                    print("❌ Le code doit contenir uniquement des chiffres")
                    return self.request_verification_code_modern(retry_count)

                if len(code) != 6:
                    print(f"❌ Le code doit contenir exactement 6 chiffres (vous avez entré {len(code)})")
                    return self.request_verification_code_modern(retry_count)

                return self.submit_verification_code_modern(code, retry_count)

            except KeyboardInterrupt:
                print("\n🔄 Options:")
                print("1. Changer de méthode de vérification")
                print("2. Quitter et changer de compte")

                try:
                    choice = input("Votre choix (1-2): ").strip()
                    if choice == "1":
                        return self.rewind_to_method_selection()
                    else:
                        return {"success": False, "error": "restart_login"}
                except:
                    return {"success": False, "error": "restart_login"}

        except Exception as e:
            return {"success": False, "error": f"Erreur demande code: {str(e)}"}

    def submit_verification_code_modern(self, code: str, retry_count: int = 0) -> dict:
        """ÉTAPE 3: Soumettre le code avec debug complet et nouveau format"""
        try:
            current_context = self.challenge_data.get("challenge_context", "")

            # Utiliser le format direct comme dans le script simple
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

            print(f"\n🚀 Verification en Cours... ♻")

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)
            print(response_text)

            if response.status_code == 200:
                try:
                    result = json.loads(response_text)

                    if result.get("status") == "ok":
                        # Vérifier si c'est vraiment un succès ou un code incorrect
                        if self._is_incorrect_code_response(result, response_text):
                            return self.request_verification_code_modern(retry_count + 1)
                        if "reset_password" in response_text and "com.bloks.www.ap.last_resort_recovery.reset_password" in response_text:
                            print("⚠️ CHANGEMENT DE MOT DE PASSE REQUIS")
                            print("Instagram demande de changer le mot de passe pour ce compte.")
                            return {
                                "success": False, 
                                "error": "Instagram demande un changement de mot de passe. Veuillez vous connecter à l'application Instagram officielle et changer votre mot de passe, puis réessayer."
                            }

                        # Utiliser la nouvelle fonction de vérification
                        parsed_data = InstagramEncryption.safe_parse_json(response)
                        verification_result = self._verify_2fa_login_success(response_text, parsed_data)

                        if verification_result["success"]:
                            print("✅ ÉTAPE 3: Code vérifié avec succès!")
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
                            return self.request_verification_code_modern(retry_count + 1)
                        else:
                            return {"success": False, "error": f"Erreur: {result}"}

                except json.JSONDecodeError:
                    print("⚠️ ÉTAPE 3: Réponse non-JSON")
                    if self._is_incorrect_code_text(response_text):
                        print("❌ Code incorrect détecté dans le texte")
                        return self.request_verification_code_modern(retry_count + 1)

                    if response.status_code == 200:
                        print("✅ ÉTAPE 3: Succès probable malgré réponse non-JSON")
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
            print(f"❌ Erreur étape 3: {e}")
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

    def handle_generic_challenge_fallback(self) -> dict:
        """Fallback pour challenge générique sans sélection de méthodes"""
        try:
            print("🔐 Challenge de sécurité détecté")
            print("📲 Un code de vérification devrait être envoyé automatiquement")
            print("Vérifiez vos SMS, emails ou notifications Instagram")

            # Demander directement le code
            return self.request_verification_code_modern()

        except Exception as e:
            return {"success": False, "error": f"Erreur challenge générique: {str(e)}"}

    def rewind_to_method_selection(self) -> dict:
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

            response = self.auth.session.post(api_url, headers=headers, data=payload_str, timeout=30)

            if response.status_code == 200:
                response_text = InstagramEncryption.safe_decode_response(response)

                try:
                    result = json.loads(response_text)
                    print("✅ Retour à la sélection de méthodes réussi")

                    # Extraire les nouvelles méthodes disponibles
                    methods = self._extract_verification_methods(result)

                    if methods:
                        return self.handle_verify_method_selection_modern({"methods": methods})
                    else:
                        print("❌ Aucune méthode trouvée après rewind")
                        return {"success": False, "error": "Aucune méthode disponible"}

                except json.JSONDecodeError:
                    print("✅ Rewind réussi (réponse non-JSON)")
                    # Essayer de continuer avec la sélection générique
                    return self.request_verification_code_modern()
            else:
                print(f"❌ Erreur rewind: HTTP {response.status_code}")
                return {"success": False, "error": f"Erreur rewind: {response.status_code}"}

        except Exception as e:
            print(f"❌ Erreur rewind: {e}")
            return {"success": False, "error": f"Erreur rewind: {str(e)}"}

    def _extract_verification_methods(self, bloks_response: dict) -> list:
        """Extraire les méthodes de vérification RÉELLES depuis la réponse Bloks sans doublons"""
        try:
            methods = []
            response_str = json.dumps(bloks_response)

            # Sets pour éviter les doublons
            phone_numbers = set()
            emails = set()

            # Rechercher les numéros de téléphone masqués (format +261 ** ** *** 95)
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

            # Rechercher les emails masqués (format e*******3@gmail.com)
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

            # CORRECTION: Rechercher WhatsApp SEULEMENT s'il y a une mention explicite ET un token
            whatsapp_indicators = [
                r'"whatsapp[^"]*":\s*"true"',
                r'"wa[^"]*":\s*"true"',
                r'"google_oauth_token":\s*"true"'
            ]

            whatsapp_found = False
            for indicator in whatsapp_indicators:
                if re.search(indicator, response_str, re.IGNORECASE):
                    # Vérifier aussi qu'il y a une mention explicite de WhatsApp
                    if 'whatsapp' in response_str.lower() or 'google_oauth_token":"true"' in response_str:
                        whatsapp_found = True
                        break

            if whatsapp_found and phone_numbers:
                # Utiliser le premier numéro trouvé pour WhatsApp
                first_phone = list(phone_numbers)[0]
                methods.append({
                    "id": "2",
                    "type": "whatsapp",
                    "label": f"WhatsApp au {first_phone}",
                    "description": "Code envoyé via WhatsApp",
                    "value": first_phone
                })
                print(f"💬 WhatsApp ajouté")

            return methods

        except Exception as e:
            print(f"❌ Erreur extraction méthodes: {e}")
            return []

    def format_phone_number(self, phone: str) -> str:
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

    def format_email(self, email: str) -> str:
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
        """Vérifier le succès de connexion après 2FA classique"""
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

            return final_result

        except Exception as e:
            print(f"❌ Erreur vérification 2FA: {str(e)}")
            return {"success": False, "error": f"Erreur vérification 2FA: {str(e)}"}
