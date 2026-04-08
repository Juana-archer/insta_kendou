# -*- coding: utf-8 -*-
"""
Gestionnaire 2FA Bloks pour Instagram
Gestion complète du flux Bloks avec toutes les méthodes de vérification
"""

import time
import json
import uuid
import random
import urllib.parse
import re
from ..utils.encryption import InstagramEncryption
from ..utils.device import get_optimal_encoding_for_environment

class BloksManager:
    """Gestionnaire du flux Bloks 2FA complet"""

    def __init__(self, auth_instance):
        self.auth = auth_instance
        self.stored_methods_data = {}
        self.challenge_data = {}

    def handle_2fa_flow(self, response_text: str) -> dict:
        """Gérer le flux Bloks 2FA complet"""
        try:
            print("\n🔐 AUTHENTIFICATION 2FA REQUISE")
            print("=" * 50)

            # Étape 1: Requête initiale pour récupérer le context_data
            context_data = self._fetch_bloks_context_data(response_text)

            if not context_data:
                return {"success": False, "error": "Impossible de récupérer le context_data"}

            # Étape 2: Récupérer les méthodes de vérification disponibles
            methods_data = self._get_bloks_verification_methods(context_data)

            if "error" in methods_data:
                return {"success": False, "error": methods_data["error"]}

            # Étape 3: Afficher les méthodes et demander le choix
            selected_method = self._show_bloks_method_selection(methods_data["methods"])

            if not selected_method:
                return {"success": False, "error": "Aucune méthode sélectionnée"}

            # Étape 4: Envoyer la sélection et récupérer le nouveau context
            code_context = self._submit_bloks_method_choice(selected_method, context_data)

            if "error" in code_context:
                return {"success": False, "error": code_context["error"]}

            # Étape 5: Demander et vérifier le code
            return self._handle_bloks_code_verification(code_context)

        except Exception as e:
            return {"success": False, "error": f"Erreur flux Bloks: {str(e)}"}

    def _fetch_bloks_context_data(self, login_response_text: str = "") -> str:
        """Récupérer le context_data via com.bloks.www.caa.ar.uhl.nav.async avec données extraites"""
        try:
            current_timestamp = time.time()

            # Extraire les vraies données depuis la réponse login
            extracted_data = self.auth._extract_login_response_data(login_response_text)

            # Paramètres pour la requête initiale Bloks avec vraies données
            bloks_params = {
                "client_input_params": {
                    "ig_device_id": self.auth.device_manager.device_info['android_id'],
                    "lois_settings": {"lois_token": ""},
                    "vetted_device_nonces": None,
                    "machine_id": self.auth.device_manager.get_x_mid()
                },
                "server_params": {
                    "event_request_id": extracted_data["event_request_id"],
                    "is_from_logged_out": 0,
                    "layered_homepage_experiment_group": "ig4a_ld_aymh_resize",
                    "device_id": extracted_data["device_id"],
                    "waterfall_id": extracted_data["waterfall_id"],
                    "INTERNAL__latency_qpl_instance_id": float(f"6.814{random.randint(1000000000, 9999999999)}E13"),
                    "is_redirect_co": 0,
                    "source": "checkpoint_redirection_login_attempt",
                    "nonce": extracted_data["nonce"],
                    "is_platform_login": 0,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "family_device_id": self.auth.device_manager.device_info['family_device_id'],
                    "offline_experiment_group": "caa_iteration_v3_perf_ig_4",
                    "access_flow_version": "pre_mt_behavior",
                    "ig_user_id": extracted_data["ig_user_id"],
                    "is_from_logged_in_switcher": 0,
                    "qe_device_id": extracted_data["device_id"]
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
                "x-fb-friendly-name": "IgApi: bloks/async_action/com.bloks.www.caa.ar.uhl.nav.async/",
                "x-fb-request-analytics-tags": '{"network_tags":{"product":"567067343352427","purpose":"fetch","surface":"undefined","request_category":"api","retry_attempt":"0"}}',
                "x-fb-server-cluster": "True",
                "x-ig-android-id": self.auth.device_manager.device_info['android_id'],
                "x-ig-app-id": "567067343352427",
                "x-ig-app-locale": "fr_FR",
                "x-ig-bandwidth-speed-kbps": "-1.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "unknown",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
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

            payload = f"params={urllib.parse.quote(json.dumps(bloks_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://b.i.instagram.com/api/v1/bloks/async_action/com.bloks.www.caa.ar.uhl.nav.async/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                context_data = self._extract_bloks_context_data(response_text)
                return context_data
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Erreur récupération context_data: {e}")
            return None

    def _extract_bloks_context_data(self, response_text: str) -> str:
        """Extraire le context_data de la réponse Bloks AVEC PATTERNS AMÉLIORÉS"""
        try:

            # Pattern 1: Chercher directement dans la structure array.Make
            full_context_pattern = r'([A-Za-z0-9+/=_-]{500,}\|[a-zA-Z]+)'
            full_matches = re.findall(full_context_pattern, response_text)

            if full_matches:
                longest_match = max(full_matches, key=len)
                return longest_match

            # Pattern 2: Chercher spécifiquement dans les structures Bloks
            bloks_context_patterns = [
                r'"context_data"[^"]*"([A-Za-z0-9+/=_-]{500,}(?:\|[a-zA-Z]+)?)"',
                r'context_data[^"]*"([A-Za-z0-9+/=_-]{500,}(?:\|[a-zA-Z]+)?)"',
                r'"([A-Za-z0-9+/=_-]{500,}\|[a-zA-Z]+)"[^"]*"[^"]*"method_picker'
            ]

            for pattern in bloks_context_patterns:
                matches = re.findall(pattern, response_text)
                if matches:
                    context_candidate = matches[0]
                    cleaned = context_candidate.replace('\\/', '/').replace('\\"', '"')
                    if len(cleaned) > 500:
                        return cleaned

            # Pattern 3: Recherche dans les array.Make complexes
            array_make_pattern = r'array\.Make[^"]*"([A-Za-z0-9+/=_-]{500,}(?:\|[a-zA-Z]+)?)"'
            array_matches = re.findall(array_make_pattern, response_text)

            if array_matches:
                longest_array = max(array_matches, key=len)
                if len(longest_array) > 500:
                    return longest_array

            # Pattern 4: Fallback avec tous les patterns possibles
            all_long_strings = re.findall(r'([A-Za-z0-9+/=_-]{500,})', response_text)

            if all_long_strings:
                for candidate in sorted(all_long_strings, key=len, reverse=True):
                    if len(candidate) > 1000 and candidate.count('+') > 5 and candidate.count('/') > 5:
                        if not '|' in candidate:
                            candidate += '|aplrr'
                        return candidate

            # Fallback ultime
            fallback = "Q-PTBAK49eHoIb0CC4ADtQiudond3EHyEU_fGaEsQpR2hwLz7ppyuG|aplrr"
            print(f"❌ Fallback context_data: {fallback}")
            return fallback

        except Exception as e:
            print(f"❌ Erreur extraction context_data: {e}")
            return "Q-PTBAK49eHoIb0CC4ADtQiudond3EHyEU_fGaEsQpR2hwLz7ppyuG|aplrr"

    def _get_bloks_verification_methods(self, context_data: str) -> dict:
        """Récupérer les méthodes de vérification disponibles ET stocker les données"""
        try:
            print("🔄 Récupération des méthodes de vérification...")

            server_params = {
                "context_data": context_data,
                "device_id": self.auth.device_manager.device_info['device_uuid'],
                "INTERNAL_INFRA_screen_id": "method_picker"
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
                "x-ig-client-endpoint": "unknown",
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
                "x-zero-balance": "",
                "x-zero-eh": f"IG0e{random.choice(['a', 'b', 'c', 'd'])}{random.randint(10000000000000000000000000000, 99999999999999999999999999999)}",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps({'server_params': server_params}, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            url = "https://b.i.instagram.com/api/v1/bloks/apps/com.bloks.www.ap.two_step_verification.challenge_picker/"

            # STOCKER LES DONNÉES COMPLÈTES POUR LE "CHANGER"
            self.stored_methods_data = {
                "context_data": context_data,
                "headers": headers,
                "payload": payload,
                "url": url,
                "timestamp": time.time()
            }

            response = self.auth.session.post(url, headers=headers, data=payload, timeout=30)
            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                methods = self._extract_bloks_verification_methods(response_text)
                return {"methods": methods, "context_data": context_data}
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"error": f"Erreur récupération méthodes: {str(e)}"}

    def _extract_bloks_verification_methods(self, response_text: str) -> list:
        """Extraire les méthodes de vérification depuis la réponse Bloks AVEC EXTRACTION DU NOUVEAU CONTEXT_DATA"""
        try:
            methods = []

            # ÉTAPE 1: Extraire le nouveau context_data AVANT d'extraire les méthodes
            new_context_data = self._extract_bloks_context_data(response_text)
            if new_context_data and len(new_context_data) > 100:
                self.challenge_data["challenge_context"] = new_context_data
            else:
                print("⚠️ Impossible d'extraire nouveau context_data, utilisation de l'ancien")

            # ÉTAPE 2: CORRECTION 1: Recherche intelligente des numéros uniques
            phone_numbers = set()

            # Pattern plus précis pour capturer les vrais numéros
            phone_patterns = [
                r'\+261\s+\*+\s+\*+\s+\*+\s+(\d{2})',  # Capture terminaison
                r'261\s+\*+\s+\*+\s+\*+\s+(\d{2})'     # Sans +
            ]

            # Extraire seulement les terminaisons uniques
            endings_found = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, response_text)
                for ending in matches:
                    if ending not in endings_found:
                        endings_found.add(ending)
                        # Reconstruire le numéro complet
                        formatted_number = f"+261 ** ** *** {ending}"
                        phone_numbers.add(formatted_number)

            # Ajouter SMS pour chaque numéro unique
            for phone in sorted(phone_numbers):
                methods.append({
                    "id": "SMS",
                    "type": "sms",
                    "label": f"SMS au {phone}",
                    "value": phone
                })

            # CORRECTION 2: WhatsApp intelligent (seulement si différent)
            whatsapp_indicators = [
                r'"SOWA"',
                r'"google_oauth_token":\s*"true"',
                r'WhatsApp'
            ]

            whatsapp_found = any(re.search(indicator, response_text, re.IGNORECASE)
                               for indicator in whatsapp_indicators)

            if whatsapp_found and phone_numbers:
                # Utiliser tous les numéros trouvés pour WhatsApp
                for phone in sorted(phone_numbers):
                    methods.append({
                        "id": "SOWA",
                        "type": "whatsapp",
                        "label": f"WhatsApp au {phone}",
                        "value": phone
                    })

            # CORRECTION 3: Email
            email_patterns = [
                r'[a-zA-Z0-9]\*+[a-zA-Z0-9]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ]

            for pattern in email_patterns:
                matches = re.findall(pattern, response_text)
                for match in matches:
                    methods.append({
                        "id": "EMAIL",
                        "type": "email",
                        "label": f"Email à {match}",
                        "value": match
                    })

            return methods

        except Exception as e:
            print(f"❌ Erreur extraction méthodes: {e}")
            return []

    def _show_bloks_method_selection(self, methods: list) -> dict:
        """Afficher les méthodes Bloks et demander la sélection"""
        try:
            if not methods:
                print("❌ Aucune méthode de vérification disponible")
                return None

            print("\n📱 MÉTHODES DE VÉRIFICATION DISPONIBLES:")
            print("=" * 60)

            for i, method in enumerate(methods):
                emoji = "📱" if method["type"] == "sms" else "💬" if method["type"] == "whatsapp" else "📧"
                print(f"{i+1}. {emoji} {method['label']}")

            print(f"{len(methods)+1}. 🚪 Quitter et changer de compte")

            while True:
                try:
                    max_choice = len(methods) + 1
                    choice_input = input(f"\n🎯 Choisissez une méthode (1-{max_choice}): ").strip()
                    choice_index = int(choice_input) - 1

                    if choice_index == len(methods):
                        return None  # Quitter
                    elif 0 <= choice_index < len(methods):
                        selected_method = methods[choice_index]
                        print(f"✅ Méthode sélectionnée: {selected_method['label']}")
                        return selected_method
                    else:
                        print("❌ Choix invalide, réessayez")

                except ValueError:
                    print("❌ Veuillez entrer un numéro valide")
                except KeyboardInterrupt:
                    return None

        except Exception as e:
            print(f"❌ Erreur sélection méthode: {e}")
            return None

    def _submit_bloks_method_choice(self, selected_method: dict, context_data: str) -> dict:
        """ÉTAPE 1: Soumettre le choix de méthode Bloks"""
        try:
            current_context = self.challenge_data.get("challenge_context", context_data)

            choice_params = {
                "client_input_params": {
                    "selected_challenge": selected_method["id"]
                },
                "server_params": {
                    "context_data": current_context,
                    "INTERNAL__latency_qpl_marker_id": 36707139,
                    "INTERNAL__latency_qpl_instance_id": float(f"6.816{random.randint(1000000000, 9999999999)}E13"),
                    "device_id": self.auth.device_manager.device_info['device_uuid']
                }
            }

            current_timestamp = time.time()

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
                "x-ig-nav-chain": f"com.bloks.www.ap.two_step_verification.challenge_picker:8:button:{int(current_timestamp * 1000)}::",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{current_timestamp:.3f}",
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
                try:
                    result = json.loads(response_text)

                    if result.get("status") == "ok":
                        new_context = self._extract_bloks_context_data(response_text)

                        if new_context and len(new_context) > 100:
                            self.challenge_data["challenge_context"] = new_context

                        code_screen_result = self._fetch_code_entry_screen_with_debug(self.challenge_data["challenge_context"])
                        if code_screen_result["success"]:
                            return {"success": True, "selected_method": selected_method}
                        else:
                            return {"error": f"Échec étape 2: {code_screen_result['error']}"}
                    else:
                        return {"error": f"Erreur sélection: {result}"}

                except json.JSONDecodeError:
                    print("⚠️ ÉTAPE 1: Réponse non-JSON mais status 200")
                    code_screen_result = self._fetch_code_entry_screen_with_debug(current_context)
                    if code_screen_result["success"]:
                        return {"success": True, "selected_method": selected_method}
                    else:
                        return {"error": "Flux partiel complété"}
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"❌ Erreur étape 1: {e}")
            return {"error": f"Erreur: {str(e)}"}

    def _fetch_code_entry_screen_with_debug(self, context_data: str) -> dict:
        """ÉTAPE 2: Charger l'écran de saisie du code"""
        try:
            code_entry_params = {
                "server_params": {
                    "context_data": context_data,
                    "device_id": self.auth.device_manager.device_info['device_uuid'],
                    "INTERNAL_INFRA_screen_id": "generic_code_entry"
                }
            }

            current_timestamp = time.time()

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
                "x-ig-client-endpoint": "unknown",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-pigeon-rawclienttime": f"{current_timestamp:.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            payload = f"params={urllib.parse.quote(json.dumps(code_entry_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"

            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.ap.two_step_verification.code_entry/",
                headers=headers,
                data=payload,
                timeout=120
            )

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                try:
                    result = json.loads(response_text)

                    # Extraire le nouveau context_data depuis la réponse
                    final_context = self._extract_bloks_context_data(response_text)

                    if final_context and len(final_context) > 100:
                        self.challenge_data["challenge_context"] = final_context
                    else:
                        print("⚠️ Context_data final non trouvé, utilisation du précédent")

                    return {"success": True, "context_data": self.challenge_data["challenge_context"]}

                except json.JSONDecodeError:
                    print("⚠️ ÉTAPE 2: Réponse non-JSON mais status 200")
                    return {"success": True, "context_data": context_data}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"❌ Erreur chargement écran code: {e}")
            return {"success": False, "error": f"Erreur: {str(e)}"}

    def _handle_bloks_code_verification(self, code_context: dict) -> dict:
        """Gérer la vérification du code Bloks AVEC GESTION COMPLÈTE DU FLUX"""
        try:
            selected_method = code_context["selected_method"]

            max_retries = 3

            for retry_count in range(max_retries):
                if retry_count > 0:
                    print(f"❌ Code de verification incorrect veiller verifier le code est reessayee. Tentative {retry_count + 1}/{max_retries}")

                print(f"\n🔢 Entrez le code reçu via {selected_method['label']}:")
                print("(Le code doit contenir 6 chiffres)")
                print("ℹ️  Tapez 'changer' pour changer de méthode")

                try:
                    code = input("Code: ").strip()

                    if not code:
                        print("❌ Code requis")
                        continue

                    # OPTION: Changer de méthode
                    if code.lower() == "changer":
                        return self._handle_method_change_from_code_entry()

                    if not code.isdigit():
                        print("❌ Le code doit contenir uniquement des chiffres")
                        continue

                    if len(code) < 6:
                        print(f"❌ Le code doit contenir au moins 6 chiffres (vous avez entré {len(code)})")
                        continue

                    # Vérifier le code
                    result = self._submit_bloks_verification_code_style_bien(code)

                    if result["success"]:
                        return result
                    elif "incorrect" in result.get("error", "").lower():
                        continue  # Code incorrect, réessayer
                    else:
                        return result  # Autre erreur

                except KeyboardInterrupt:
                    return {"success": False, "error": "Annulé par l'utilisateur"}

            return {"success": False, "error": "Trop de tentatives de code incorrect"}

        except Exception as e:
            return {"success": False, "error": f"Erreur vérification code: {str(e)}"}

    def _submit_bloks_verification_code_style_bien(self, code: str) -> dict:
        """Soumettre le code de vérification Bloks EXACTEMENT comme l'exemple fourni"""
        try:
            # Utiliser le context_data depuis challenge_data
            current_context = self.challenge_data.get("challenge_context", "")

            # PARAMÈTRES EXACTS comme votre exemple
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
                    "INTERNAL__latency_qpl_instance_id": float(f"7.{random.randint(1000000000000, 9999999999999)}E13"),
                    "device_id": self.auth.device_manager.device_info['device_uuid']
                }
            }

            # HEADERS EXACTS comme votre exemple
            current_timestamp = time.time()
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
                "x-ig-bandwidth-speed-kbps": f"{random.randint(200, 400)}.000",
                "x-ig-bandwidth-totalbytes-b": "0",
                "x-ig-bandwidth-totaltime-ms": "0",
                "x-ig-client-endpoint": "com.bloks.www.ap.two_step_verification.code_entry",
                "x-ig-capabilities": "3brTv10=",
                "x-ig-connection-type": "WIFI",
                "x-ig-device-id": self.auth.device_manager.device_info['device_uuid'],
                "x-ig-device-locale": "fr_FR",
                "x-ig-family-device-id": self.auth.device_manager.device_info['family_device_id'],
                "x-ig-mapped-locale": "fr_FR",
                "x-ig-nav-chain": f"com.bloks.www.caa.login.landing_screen:com.bloks.www.caa.login.landing_screen:1:button:{int(current_timestamp * 1000)}::,IgCdsScreenNavigationLoggerModule:com.bloks.www.caa.login.login_homepage:2:button:{int(current_timestamp * 1000)}::,IgCdsScreenNavigationLoggerModule:com.bloks.www.ap.two_step_verification.challenge_picker:3:button:{int(current_timestamp * 1000)}::,IgCdsScreenNavigationLoggerModule:com.bloks.www.ap.two_step_verification.code_entry:4:button:{int(current_timestamp * 1000)}::",
                "x-ig-timezone-offset": "10800",
                "x-ig-www-claim": "0",
                "x-mid": self.auth.device_manager.get_x_mid(),
                "x-meta-zca": "eyJhbmRyb2lkIjp7ImFrYSI6eyJkYXRhVG9TaWduIjoiIiwiZXJyb3JzIjpbIktFWVNUT1JFX0RJU0FCTEVEX0JZX0NPTkZJRyJdfSwiZ3BpYSI6eyJ0b2tlbiI6IiIsImVycm9ycyI6WyJQTEFZX0lOVEVHUklUWV9ESVNBQkxFRF9CWV9DT05GSUciXX0sInBheWxvYWQiOnsicGx1Z2lucyI6eyJiYXQiOnsic3RhIjoiVW5wbHVnZ2VkIiwibHZsIjo4NH0sInNjdCI6e319fX19",
                "x-pigeon-rawclienttime": f"{current_timestamp:.3f}",
                "x-pigeon-session-id": f"UFS-{uuid.uuid4()}-0",
                "x-tigon-is-retry": "False",
                "user-agent": self.auth.device_manager.device_info['user_agent'],
                "x-fb-conn-uuid-client": str(uuid.uuid4()).replace('-', ''),
                "x-fb-http-engine": "Tigon/MNS/TCP"
            }

            # PAYLOAD EXACT comme votre exemple
            payload = f"params={urllib.parse.quote(json.dumps(code_params, separators=(',', ':')))}&bk_client_context={urllib.parse.quote(json.dumps({'bloks_version': 'ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1', 'styles_id': 'instagram'}))}&bloks_versioning_id=ef88cb8e7a6a225af847577c11f18eeccda0582b87e294181c4c7425d28047b1"
            print("🚀 Verification en Cours... ♻")

            # REQUÊTE EXACTE comme votre exemple
            response = self.auth.session.post(
                "https://i.instagram.com/api/v1/bloks/async_action/com.bloks.www.ap.two_step_verification.code_entry_async/",
                headers=headers,
                data=payload,
                timeout=120
            )

            # DÉCODAGE UNIFIÉ
            response_text = InstagramEncryption.safe_decode_response(response)
            if response.status_code == 200:
                # Vérifier si code incorrect
                if "Error during code validation" in response_text or "incorrect" in response_text.lower():
                    return {"success": False, "error": "Code incorrect"}

                # NOUVELLE DÉTECTION: Vérifier si Instagram demande un changement de mot de passe
                if "reset_password" in response_text and "com.bloks.www.ap.last_resort_recovery.reset_password" in response_text:
                    print("⚠️ CHANGEMENT DE MOT DE PASSE REQUIS")
                    print("Instagram demande de changer le mot de passe pour ce compte.")
                    return {
                        "success": False, 
                        "error": "Instagram demande un changement de mot de passe. Veuillez vous connecter à l'application Instagram officielle et changer votre mot de passe, puis réessayer."
                    }

                # Utiliser la fonction de vérification 2FA
                parsed_data = InstagramEncryption.safe_parse_json(response)
                verification_result = self._verify_2fa_login_success(response_text, parsed_data)

                if verification_result["success"]:
                    print("🎉 CODE VÉRIFIÉ AVEC SUCCÈS!")
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
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Erreur code: {str(e)}"}

    def _handle_method_change_from_code_entry(self) -> dict:
        """NOUVELLE FONCTION: Gérer le changement de méthode depuis l'écran de code"""
        try:
            print("🔄 CHANGEMENT DE MÉTHODE DE VÉRIFICATION")
            print("=" * 60)

            # Vérifier si on a les données de méthodes sauvegardées
            if not hasattr(self, 'stored_methods_data') or not self.stored_methods_data:
                print("❌ Impossible de récupérer les méthodes alternatives")
                print("💡 Retour à la demande de code actuelle")
                return self._handle_bloks_code_input()

            # Récupérer les données stockées de la requête précédente
            stored_data = self.stored_methods_data

            print("🔄 Récupération des méthodes alternatives...")

            # Réutiliser la même requête avec les mêmes paramètres
            context_data = stored_data["context_data"]
            headers = stored_data["headers"]
            payload = stored_data["payload"]
            url = stored_data["url"]

            # Refaire la même requête pour obtenir les méthodes
            response = self.auth.session.post(url, headers=headers, data=payload, timeout=30)

            response_text = InstagramEncryption.safe_decode_response(response)

            if response.status_code == 200:
                try:
                    result = json.loads(response_text)

                    # Extraire les méthodes depuis la réponse
                    methods = self._extract_bloks_verification_methods(response_text)

                    if methods:
                        # Mettre à jour le context_data si nécessaire
                        new_context_data = self._extract_bloks_context_data(response_text)
                        if new_context_data and len(new_context_data) > 100:
                            self.challenge_data["challenge_context"] = new_context_data

                        print("\n📱 MÉTHODES DE VÉRIFICATION ALTERNATIVES:")
                        print("=" * 60)

                        for i, method in enumerate(methods):
                            emoji = "📱" if method["type"] == "sms" else "💬" if method["type"] == "whatsapp" else "📧"
                            print(f"{i+1}. {emoji} {method['label']}")

                        print(f"{len(methods)+1}. 🔙 Revenir à l'écran de code précédent")
                        print(f"{len(methods)+2}. 🚪 Quitter et changer de compte")

                        while True:
                            try:
                                max_choice = len(methods) + 2
                                choice_input = input(f"\n🎯 Choisissez une méthode (1-{max_choice}): ").strip()
                                choice_index = int(choice_input) - 1

                                if choice_index == len(methods):  # Revenir à l'écran de code
                                    print("🔙 Retour à l'écran de code")
                                    return self._handle_bloks_code_input()
                                elif choice_index == len(methods) + 1:  # Quitter
                                    return {"success": False, "error": "restart_login"}
                                elif 0 <= choice_index < len(methods):
                                    selected_method = methods[choice_index]
                                    print(f"✅ Méthode sélectionnée: {selected_method['label']}")

                                    # Soumettre le nouveau choix
                                    result = self._submit_bloks_method_choice(selected_method, context_data)

                                    if result["success"]:
                                        # Charger l'écran de code pour la nouvelle méthode
                                        code_screen_result = self._fetch_code_entry_screen_with_debug(self.challenge_data["challenge_context"])
                                        if code_screen_result["success"]:
                                            return self._handle_bloks_code_input()
                                        else:
                                            return {"success": False, "error": f"Échec écran code: {code_screen_result['error']}"}
                                    else:
                                        return result
                                else:
                                    print("❌ Choix invalide, réessayez")

                            except ValueError:
                                print("❌ Veuillez entrer un numéro valide")
                            except KeyboardInterrupt:
                                return {"success": False, "error": "restart_login"}
                    else:
                        print("❌ Aucune méthode alternative trouvée")
                        return {"success": False, "error": "Aucune méthode alternative"}

                except json.JSONDecodeError:
                    print("❌ Erreur parsing des méthodes alternatives")
                    return {"success": False, "error": "Erreur parsing méthodes"}
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"❌ Erreur changement méthode: {e}")
            return {"success": False, "error": f"Erreur changement: {str(e)}"}

    def _handle_bloks_code_input(self) -> dict:
        """Gérer la saisie et vérification du code Bloks"""
        try:
            max_retries = 3

            for retry_count in range(max_retries):
                if retry_count > 0:
                    print(f"❌ Code incorrect. Tentative {retry_count + 1}/{max_retries}")

                print(f"\n🔢 Entrez le code de vérification reçu:")
                print("(Le code doit contenir 6 chiffres)")
                print("ℹ️  Tapez 'changer' pour essayer une autre méthode")

                try:
                    code = input("Code: ").strip()

                    if not code:
                        print("❌ Code requis")
                        continue

                    # OPTION: Changer de méthode
                    if code.lower() == "changer":
                        return self._handle_method_change_from_code_entry()

                    if not code.isdigit() or len(code) != 6:
                        print("❌ Le code doit contenir exactement 6 chiffres")
                        continue

                    # UTILISER LA NOUVELLE FONCTION
                    result = self._submit_bloks_verification_code_style_bien(code)

                    if result["success"]:
                        return result
                    elif "incorrect" in result.get("error", "").lower():
                        continue  # Code incorrect, réessayer
                    else:
                        return result  # Autre erreur

                except KeyboardInterrupt:
                    return {"success": False, "error": "Annulé par l'utilisateur"}

            return {"success": False, "error": "Trop de tentatives de code incorrect"}

        except Exception as e:
            return {"success": False, "error": f"Erreur vérification: {str(e)}"}

    def _verify_2fa_login_success(self, response_text: str, parsed_data: dict = None) -> dict:
        """Vérifier le succès de connexion après 2FA Bloks"""
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
