# -*- coding: utf-8 -*-
"""
Gestionnaire 2FA Alternatif pour Instagram
Gestion complète du flux alternatif avec entrypoint et code_entry
"""

import time
import json
import uuid
import random
import urllib.parse
import re
from ..utils.encryption import InstagramEncryption
from ..utils.device import get_optimal_encoding_for_environment

class AlternativeManager:
    """Gestionnaire du flux 2FA alternatif complet"""

    def __init__(self, auth_instance):
        self.auth = auth_instance
        self.challenge_data = {}

    def handle_2fa_flow(self, response_text: str) -> dict:
        """Gérer le nouveau flux 2FA alternatif AVEC L'ORDRE CORRECT ET MENUS NUMERIQUES"""
        try:
            print("\n🔐 2FA DETECTEE")
            print("=" * 50)

            # ÉTAPE 1: Extraire le context_data initial de la réponse de login
            initial_context = self._extract_context_from_alternative_response(response_text)

            if not initial_context:
                print("❌ Impossible d'extraire le context_data initial")
                return {"success": False, "error": "Context_data initial non trouvé"}

            self.challenge_data = {"challenge_context": initial_context}

            # ÉTAPE 2: Requête entrypoint_async IMMÉDIATE
            entrypoint_result = self._call_alternative_entrypoint(initial_context)

            if not entrypoint_result["success"]:
                return {"success": False, "error": f"Échec entrypoint: {entrypoint_result['error']}"}

            # ÉTAPE 3: Vérifier si Instagram force le passage par challenge_picker
            if "challenge_picker" in entrypoint_result["response"] and "method_picker" in entrypoint_result["response"]:
                # Récupérer les méthodes disponibles via challenge_picker
                methods_result = self._get_alternative_verification_methods(self.challenge_data["challenge_context"])
                
                if methods_result["success"] and methods_result["methods"]:
                    # Demander à l'utilisateur de choisir une méthode (choix numérique)
                    print("📱 Plusieurs méthodes de vérification disponibles")
                    selected_method = self._show_alternative_method_selection(methods_result["methods"])
                    
                    if selected_method and not selected_method.get("restart_requested"):
                        # Soumettre le choix de la méthode sélectionnée
                        choice_result = self._submit_alternative_method_choice(selected_method)
                        
                        if choice_result["success"]:
                            # Charger l'écran de saisie de code
                            code_screen_result = self._load_alternative_code_entry_screen()
                            
                            if code_screen_result["success"]:
                                print("📱 Un code de vérification a été envoyé")
                                return self._handle_alternative_code_verification()
                            else:
                                return {"success": False, "error": f"Échec écran code: {code_screen_result['error']}"}
                        else:
                            return {"success": False, "error": f"Échec soumission choix: {choice_result['error']}"}
                    elif selected_method and selected_method.get("restart_requested"):
                        return {"success": False, "error": "restart_login", "restart_requested": True}
                    else:
                        return {"success": False, "error": "Aucune méthode sélectionnée"}
                else:
                    return {"success": False, "error": "Aucune méthode de vérification disponible"}
            else:
                # Flux normal : accès direct au code_entry (comme avant)
                print("📱 Accès direct à la saisie de code...")
                code_entry_result = self._load_direct_code_entry_screen()
                
                if not code_entry_result["success"]:
                    return {"success": False, "error": f"Échec code_entry: {code_entry_result['error']}"}
                
                print("📱 Un code de vérification a été envoyé")
                return self._handle_alternative_code_verification()

        except Exception as e:
            return {"success": False, "error": f"Erreur flux alternatif: {str(e)}"}

    def _extract_context_from_alternative_response(self, response_text: str) -> str:
        """Extraire context_data du nouveau flux"""
        try:
            # Patterns pour le nouveau flux
            context_patterns = [
                r'"context_data"[^"]*"([A-Za-z0-9+/=_-]{500,}(?:\|[a-zA-Z]+)?)"',
                r'context_data["\\\s:]*([A-Za-z0-9+/=_-]{500,}(?:\|[a-zA-Z]+)?)',
                r'([A-Za-z0-9+/=_-]{500,}\|[a-zA-Z]{4,})'
            ]

            for pattern in context_patterns:
                matches = re.findall(pattern, response_text)
                if matches:
                    context = matches[0]
                    # Nettoyer les échappements
                    context = context.replace('\\/', '/').replace('\\"', '"')
                    if len(context) > 500:
                        return context

            # Fallback avec suffixe standard
            fallback = "Adng8k4lYCNZHf6znKemw4Lr5VxOZizmQIzhG0JnvsG4vKXuM78CT2DxDuJ09R8x|aplc"
            print(f"⚠️ Fallback context_data: {fallback}")
            return fallback

        except Exception as e:
            print(f"❌ Erreur extraction context alternatif: {e}")
            return "fallback_context_data|aplc"

    def _call_alternative_entrypoint(self, context_data: str) -> dict:
        """Appel au entrypoint_async alternatif"""
        try:

            current_timestamp = time.time()

            entrypoint_params = {
                "client_input_params": {
                    "auth_secure_device_id": "",
                    "accounts_list": [],
                    "has_whatsapp_installed": 0,
                    "family_device_id": self.auth.device_manager.device_info['family_device_id'],
                    "machine_id": self.auth.device_manager.get_x_mid()
                },
                "server_params": {
                    "context_data": context_data,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": float(f"1.0{random.randint(1000000000000, 9999999999999)}E14"),
                    "device_id": self.auth.device_manager.device_info['device_uuid']
                }
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
                "x-fb-friendly-name": "IgApi: bloks/async_action/com.bloks.www.ap.two_step_verification.entrypoint_async/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.caa.login.login_homepage",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
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

            payload = f"params={urllib.parse.quote(json.dumps(entrypoint_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.ap.two_step_verification.entrypoint_async/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                # Mettre à jour le context_data
                new_context = self._extract_context_from_alternative_response(response_text)
                if new_context and len(new_context) > 100:
                    self.challenge_data["challenge_context"] = new_context
                return {"success": True, "response": response_text}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur entrypoint: {str(e)}"}

    def _load_direct_code_entry_screen(self) -> dict:
        """Charger directement l'écran de saisie du code après entrypoint"""
        try:
            current_context = self.challenge_data.get("challenge_context", "")

            entry_params = {
                "server_params": {
                    "context_data": current_context,
                    "device_id": self.auth.device_manager.device_info['device_uuid'],
                    "INTERNAL_INFRA_screen_id": "generic_code_entry"
                }
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
                "x-fb-friendly-name": "IgApi: bloks/apps/com.bloks.www.ap.two_step_verification.code_entry/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.caa.login.login_homepage",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{time.time():.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps(entry_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.ap.two_step_verification.code_entry/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                # Mettre à jour context_data final
                final_context = self._extract_context_from_alternative_response(response_text)
                if final_context and len(final_context) > 100:
                    self.challenge_data["challenge_context"] = final_context
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur écran code: {str(e)}"}

    def _handle_alternative_code_verification(self) -> dict:
        """Gérer vérification code alternatif AVEC OPTIONS NUMERIQUES UNIQUEMENT"""
        try:
            max_retries = 3

            for retry_count in range(max_retries):
                if retry_count > 0:
                    print(f"❌ Code incorrect. Tentative {retry_count + 1}/{max_retries}")

                print(f"\n🔢 VERIFICATION REQUISE")
                print("=" * 50)
                print("1. Entrer le code de vérification")
                print("2. Essayer une autre méthode de vérification")
                print("3. Quitter")
                print("-" * 50)

                try:
                    choice = input("Votre choix (1-3): ").strip()

                    if choice == "1":
                        code = input("\n📱 Entrez le code de vérification (6 chiffres): ").strip()

                        if not code:
                            print("❌ Code requis")
                            continue

                        if not code.isdigit() or len(code) != 6:
                            print("❌ Le code doit contenir exactement 6 chiffres")
                            continue

                        # Vérifier le code
                        result = self._submit_alternative_verification_code(code)

                        if result["success"]:
                            return result
                        elif "incorrect" in result.get("error", "").lower():
                            continue  # Code incorrect, réessayer
                        else:
                            return result  # Autre erreur

                    elif choice == "2":
                        return self._change_alternative_verification_method()

                    elif choice == "3":
                        return {"success": False, "error": "Connexion annulée par l'utilisateur"}

                    else:
                        print("❌ Choix invalide. Veuillez choisir 1, 2 ou 3")

                except KeyboardInterrupt:
                    return {"success": False, "error": "Annulé par l'utilisateur"}

            return {"success": False, "error": "Trop de tentatives de code incorrect"}

        except Exception as e:
            return {"success": False, "error": f"Erreur vérification: {str(e)}"}
    def _change_alternative_verification_method(self) -> dict:
        """Changer de méthode dans le flux alternatif AVEC MENU NUMERIQUE"""
        try:
            print("\n🔄 CHANGEMENT DE MÉTHODE DE VÉRIFICATION")
            print("=" * 50)
            print("1. Continuer avec le changement de méthode")
            print("2. Retourner à la saisie du code")
            print("3. Quitter")
            print("-" * 50)
            
            choice = input("Votre choix (1-3): ").strip()
            
            if choice == "1":
                # Continuer avec le changement de méthode
                pass
            elif choice == "2":
                # Retourner à la saisie du code
                return self._handle_alternative_code_verification()
            elif choice == "3":
                return {"success": False, "error": "Connexion annulée par l'utilisateur"}
            else:
                print("❌ Choix invalide")
                return self._change_alternative_verification_method()

            current_context = self.challenge_data.get("challenge_context", "")

            # REQUÊTE "is_try_another_way" comme dans l'exemple
            another_way_params = {
                "client_input_params": {},
                "server_params": {
                    "context_data": current_context,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": float(f"1.0{random.randint(1000000000000, 9999999999999)}E14"),
                    "device_id": self.auth.device_manager.device_info['device_uuid'],
                    "is_try_another_way": 1  # CLEF IMPORTANTE
                }
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
                "x-fb-friendly-name": "IgApi: bloks/async_action/com.bloks.www.ap.two_step_verification.code_entry_async/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.ap.two_step_verification.code_entry",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{time.time():.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps(another_way_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.ap.two_step_verification.code_entry_async/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                # Mettre à jour context et récupérer les méthodes
                new_context = self._extract_context_from_alternative_response(response_text)
                if new_context:
                    self.challenge_data["challenge_context"] = new_context

                # Maintenant récupérer les méthodes disponibles
                methods_result = self._get_alternative_verification_methods(self.challenge_data["challenge_context"])

                if methods_result["success"]:
                    # Afficher les méthodes à l'utilisateur et lui demander de choisir
                    selected_method = self._show_alternative_method_selection(methods_result["methods"])

                    if selected_method:
                        # Soumettre le choix
                        choice_result = self._submit_alternative_method_choice(selected_method)

                        if choice_result["success"]:
                            # Charger l'écran de code et demander le code
                            code_screen_result = self._load_alternative_code_entry_screen()

                            if code_screen_result["success"]:
                                # Maintenant demander le code avec la nouvelle méthode
                                return self._handle_alternative_code_verification()
                            else:
                                return {"success": False, "error": f"Échec écran code: {code_screen_result['error']}"}
                        else:
                            return {"success": False, "error": f"Échec choix: {choice_result['error']}"}
                    else:
                        return {"success": False, "error": "Aucune méthode sélectionnée"}
                else:
                    return {"success": False, "error": f"Échec récupération méthodes: {methods_result['error']}"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur changement méthode: {str(e)}"}
    def _get_alternative_verification_methods(self, context_data: str) -> dict:
        """Récupérer les méthodes via challenge_picker alternatif"""
        try:

            picker_params = {
                "server_params": {
                    "context_data": context_data,
                    "device_id": self.auth.device_manager.device_info['device_uuid'],
                    "INTERNAL_INFRA_screen_id": "method_picker"
                }
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
                "x-fb-friendly-name": "IgApi: bloks/apps/com.bloks.www.ap.two_step_verification.challenge_picker/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.ap.two_step_verification.code_entry",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{time.time():.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps(picker_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.ap.two_step_verification.challenge_picker/",
                headers=headers,
                data=payload,
                timeout=30
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                # Mettre à jour context_data et extraire méthodes
                new_context = self._extract_context_from_alternative_response(response_text)
                if new_context and len(new_context) > 100:
                    self.challenge_data["challenge_context"] = new_context

                methods = self._extract_alternative_verification_methods(response_text)
                return {"success": True, "methods": methods}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur méthodes: {str(e)}"}

    def _extract_alternative_verification_methods(self, response_text: str) -> list:
        """Extraire les méthodes du challenge_picker alternatif"""
        try:
            methods = []

            # Rechercher SMS
            sms_patterns = [
                r'Texto.*?(\+\d{1,3}\s+\*+\s+\*+\s+\*+\s+\d{2})',
                r'SMS.*?(\+\d{1,3}\s+\*+\s+\*+\s+\*+\s+\d{2})',
                r'(\+\d{1,3}\s+\*+\s+\*+\s+\*+\s+\d{2})'
            ]

            for pattern in sms_patterns:
                matches = re.findall(pattern, response_text)
                for match in matches:
                    if match not in [m.get("value") for m in methods]:
                        methods.append({
                            "id": "SMS",
                            "type": "sms",
                            "label": f"SMS au {match}",
                            "value": match
                        })
                        print(f"📱 SMS trouvé: {match}")
                        break

            # Rechercher Email
            email_patterns = [
                r'Email.*?([a-zA-Z0-9]\*+[a-zA-Z0-9]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'([a-zA-Z0-9]\*+[a-zA-Z0-9]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]

            for pattern in email_patterns:
                matches = re.findall(pattern, response_text)
                for match in matches:
                    if match not in [m.get("value") for m in methods]:
                        methods.append({
                            "id": "EMAIL",
                            "type": "email",
                            "label": f"Email à {match}",
                            "value": match
                        })
                        print(f"📧 Email trouvé: {match}")
                        break

            # Rechercher WhatsApp (si mentionné avec google_oauth_token)
            if "google_oauth_token" in response_text and any(m["type"] == "sms" for m in methods):
                sms_number = next(m["value"] for m in methods if m["type"] == "sms")
                methods.append({
                    "id": "WHATSAPP",
                    "type": "whatsapp",
                    "label": f"WhatsApp au {sms_number}",
                    "value": sms_number
                })
                print(f"💬 WhatsApp trouvé: {sms_number}")

            return methods

        except Exception as e:
            print(f"❌ Erreur extraction méthodes alternatives: {e}")
            return []

    def _show_alternative_method_selection(self, methods: list) -> dict:
        """Afficher sélection méthodes alternatives AVEC CHOIX NUMERIQUES UNIQUEMENT"""
        try:
            if not methods:
                print("❌ Aucune méthode alternative disponible")
                return None

            while True:
                print("\n📱 MÉTHODES DE VÉRIFICATION DISPONIBLES:")
                print("=" * 60)

                for i, method in enumerate(methods):
                    emoji = "📱" if method["type"] == "sms" else "📧" if method["type"] == "email" else "💬"
                    print(f"{i+1}. {emoji} {method['label']}")

                print(f"{len(methods)+1}. 🚪 Quitter et changer de compte")
                print("-" * 60)

                try:
                    max_choice = len(methods) + 1
                    choice_input = input(f"Votre choix (1-{max_choice}): ").strip()
                    
                    if not choice_input.isdigit():
                        print("❌ Veuillez entrer un numéro valide")
                        continue
                        
                    choice_index = int(choice_input) - 1

                    if choice_index == len(methods):
                        return {"success": False, "error": "restart_login", "restart_requested": True}
                    elif 0 <= choice_index < len(methods):
                        selected_method = methods[choice_index]
                        print(f"✅ Méthode sélectionnée: {selected_method['label']}")
                        return selected_method
                    else:
                        print(f"❌ Choix invalide. Veuillez choisir entre 1 et {max_choice}")

                except ValueError:
                    print("❌ Veuillez entrer un numéro valide")
                except KeyboardInterrupt:
                    return None

        except Exception as e:
            print(f"❌ Erreur sélection alternative: {e}")
            return None


    def _submit_alternative_method_choice(self, selected_method: dict) -> dict:
        """Soumettre choix méthode alternative"""
        try:

            current_context = self.challenge_data.get("challenge_context", "")

            choice_params = {
                "client_input_params": {
                    "selected_challenge": selected_method["id"]
                },
                "server_params": {
                    "context_data": current_context,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": float(f"1.0{random.randint(1000000000000, 9999999999999)}E14"),
                    "device_id": self.auth.device_manager.device_info['device_uuid']
                }
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
                "x-fb-friendly-name": "IgApi: bloks/async_action/com.bloks.www.bloks.ap.two_step_verification.challenge_picker.async/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.ap.two_step_verification.challenge_picker",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{time.time():.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps(choice_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.bloks.ap.two_step_verification.challenge_picker.async/",
                headers=headers,
                data=payload,
                timeout=30
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                # Mettre à jour context_data et lancer écran code
                new_context = self._extract_context_from_alternative_response(response_text)
                if new_context and len(new_context) > 100:
                    self.challenge_data["challenge_context"] = new_context

                # Appeler écran de saisie code
                code_screen_result = self._load_alternative_code_entry_screen()
                return code_screen_result
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur choix alternatif: {str(e)}"}

    def _load_alternative_code_entry_screen(self) -> dict:
        """Charger écran saisie code alternatif"""
        try:
            current_context = self.challenge_data.get("challenge_context", "")

            entry_params = {
                "server_params": {
                    "context_data": current_context,
                    "device_id": self.auth.device_manager.device_info['device_uuid'],
                    "INTERNAL_INFRA_screen_id": "generic_code_entry"
                }
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
                "x-fb-friendly-name": "IgApi: bloks/apps/com.bloks.www.ap.two_step_verification.code_entry/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.ap.two_step_verification.challenge_picker",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{time.time():.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps(entry_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.ap.two_step_verification.code_entry/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                # Mettre à jour context_data final
                final_context = self._extract_context_from_alternative_response(response_text)
                if final_context and len(final_context) > 100:
                    self.challenge_data["challenge_context"] = final_context
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur écran code: {str(e)}"}

    
    def _submit_alternative_verification_code(self, code: str) -> dict:
        """Soumettre code vérification alternatif avec EXACTEMENT la même logique que login() normal"""
        try:

            current_context = self.challenge_data.get("challenge_context", "")

            code_params = {
                "client_input_params": {
                    "auth_secure_device_id": "",
                    "code": code,
                    "family_device_id": self.auth.device_manager.device_info['family_device_id'],
                    "device_id": self.auth.device_manager.device_info['android_id'],
                    "machine_id": self.auth.device_manager.get_x_mid()
                },
                "server_params": {
                    "context_data": current_context,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": float(f"1.0{random.randint(1000000000000, 9999999999999)}E14"),
                    "device_id": self.auth.device_manager.device_info['device_uuid']
                }
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
                "x-fb-friendly-name": "IgApi: bloks/async_action/com.bloks.www.ap.two_step_verification.code_entry_async/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.ap.two_step_verification.code_entry",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{time.time():.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps(code_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            print("🚀 Verification en Cours... ♻")

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.ap.two_step_verification.code_entry_async/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            # UTILISER EXACTEMENT LA MÊME LOGIQUE QUE login() NORMAL
            if response.status_code == 200:
                try:
                    # Parser la réponse JSON exactement comme login()
                    response_data = json.loads(response_text)
                    
                    # Vérifier les cas spécifiques EXACTEMENT comme login()
                    if self.auth._is_invalid_credentials(response_data):
                        return {"success": False, "error": "invalid_credentials"}
                    
                    # Vérifier 2FA Bloks EXACTEMENT comme login()
                    elif self.auth._is_bloks_2fa_response(response_text):
                        challenge_result = self.auth.bloks_manager.handle_2fa_flow(response_text)
                        if challenge_result["success"]:
                            return {
                                "success": True,
                                "message": "Connexion réussie après Bloks 2FA",
                                "data": {
                                    "user_data": challenge_result.get("data", {}).get("user_data", {}),
                                    "session_data": challenge_result.get("data", {}).get("session_data", {})
                                }
                            }
                        else:
                            return {"success": False, "error": f"Échec Bloks 2FA: {challenge_result['error']}"}
                    
                    # Vérifier 2FA alternatif EXACTEMENT comme login()
                    elif self.auth._is_alternative_2fa_response(response_text):
                        challenge_result = self.auth.alternative_manager.handle_2fa_flow(response_text)
                        if challenge_result["success"]:
                            return {
                                "success": True,
                                "message": "Connexion réussie après 2FA alternatif",
                                "data": {
                                    "user_data": challenge_result.get("data", {}).get("user_data", {}),
                                    "session_data": challenge_result.get("data", {}).get("session_data", {})
                                }
                            }
                        else:
                            return {"success": False, "error": f"Échec 2FA alternatif: {challenge_result['error']}"}
                    
                    # Challenge classique EXACTEMENT comme login()
                    elif "PresentCheckpointsFlow" in response_text or "challenge_required" in response_text.lower():
                        challenge_result = self.auth.classic_manager.handle_2fa_flow(response_text)
                        if challenge_result["success"]:
                            return {
                                "success": True,
                                "message": "Connexion réussie après 2FA",
                                "data": {
                                    "user_data": challenge_result.get("data", {}).get("user_data", {}),
                                    "session_data": challenge_result.get("data", {}).get("session_data", {})
                                }
                            }
                        else:
                            return {"success": False, "error": f"Échec 2FA: {challenge_result['error']}"}
                    
                    # Connexion réussie EXACTEMENT comme login()
                    elif self.auth._check_login_success(response_data):
                        print("🎉 CODE VÉRIFIÉ AVEC SUCCÈS!")
                        
                        # EXACTEMENT la même logique que login() pour connexion réussie
                        result = {
                            "success": True,
                            "message": "Connexion réussie!"
                        }
                        
                        # EXACTEMENT la même extraction user_data que login()
                        user_data = self.auth._extract_user_data_fixed(response_data)
                        result["user_data"] = user_data
                        
                        # EXACTEMENT la même extraction session_data que login()
                        session_data = self.auth._extract_session_data_fixed(response, user_data)
                        result["session_data"] = session_data
                        self.auth.session_data = session_data
                        
                        # EXACTEMENT la même vérification de statut que login()
                        if hasattr(self.auth, '_current_login_credentials') and self.auth._current_login_credentials:
                            username, password = self.auth._current_login_credentials
                            final_result = self.auth.check_account_status_after_login(username, password, result)
                        else:
                            final_result = result
                        
                        # EXACTEMENT la même sauvegarde que login()
                        if final_result.get("status") != "disabled":
                            if hasattr(self.auth, '_current_login_credentials') and self.auth._current_login_credentials:
                                username, _ = self.auth._current_login_credentials
                                self.auth._save_session_with_device(username, session_data, user_data, self.auth.current_device_info)
                        
                        # Retourner dans le même format que le 2FA réussi
                        return {
                            "success": True,
                            "message": "2FA vérifié avec succès",
                            "data": {
                                "user_data": final_result.get("user_data", user_data),
                                "session_data": final_result.get("session_data", session_data)
                            }
                        }
                    
                    else:
                        # EXACTEMENT la même gestion d'erreur que login()
                        error_type = self.auth._extract_error_message(response_data)
                        if error_type == "user_not_found":
                            return {"success": False, "error": "user_not_found"}
                        elif error_type == "password_incorrect":
                            return {"success": False, "error": "password_incorrect"}
                        elif error_type == "invalid_credentials":
                            return {"success": False, "error": "invalid_credentials"}
                        elif error_type == "rate_limit":
                            return {"success": False, "error": "rate_limit"}
                        else:
                            return {"success": False, "error": "Code incorrect"}
                
                except json.JSONDecodeError:
                    return {"success": False, "error": "Code incorrect"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur code alternatif: {str(e)}"}

    def _verify_2fa_login_success(self, response, response_text: str = None) -> dict:
        """SUPPRIMÉE - Utilise maintenant directement la logique de login() dans _submit_alternative_verification_code"""
        # Cette fonction n'est plus utilisée car on utilise maintenant
        # exactement la même logique que login() dans _submit_alternative_verification_code
        pass
