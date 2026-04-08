# -*- coding: utf-8 -*-
"""
Gestionnaire de traitement des médias pour Instagram
Préparation des images, génération des IDs et hash PDQ
"""

import os
import time
import hashlib
import random
from io import BytesIO
from .license import validate_license

class MediaProcessor:
    """Gestionnaire de traitement des médias pour Instagram"""
    
    def __init__(self):
        # Validation licence obligatoire
        if not validate_license():
            raise PermissionError("Ce script n'est pas autorisé à utiliser cette bibliothèque. Veuillez contacter le créateur via: 0389561802 ou https://t.me/Kenny5626")
    
    @staticmethod
    def prepare_image_for_instagram(image_path: str, story_mode: bool = False) -> tuple:
        """Préparer une image pour Instagram"""
        try:
            # Vérifier si le fichier existe
            if not os.path.exists(image_path):
                return None, None, f"Fichier non trouvé: {image_path}"
            
            # Installer Pillow si pas disponible
            try:
                from PIL import Image
            except ImportError:
                print("📦 Installation de Pillow en cours...")
                import subprocess
                subprocess.check_call(['pip', 'install', 'Pillow'])
                from PIL import Image
                print("✅ Pillow installé avec succès")
            
            # Ouvrir l'image avec PIL
            with Image.open(image_path) as img:
                # Convertir en RGB si nécessaire
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                original_width, original_height = img.size
                
                if story_mode:
                    # Format story Instagram (9:16)
                    target_width = 720
                    target_height = 1280
                    
                    # Redimensionner en gardant le ratio
                    ratio = min(target_width / original_width, target_height / original_height)
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Créer une nouvelle image avec fond noir pour le format 9:16
                    story_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                    x = (target_width - new_width) // 2
                    y = (target_height - new_height) // 2
                    story_img.paste(img, (x, y))
                    
                    img = story_img
                else:
                    # Format post Instagram (1:1 ou proche)
                    target_size = 1080
                    
                    # Redimensionner
                    if original_width > original_height:
                        new_width = target_size
                        new_height = int(original_height * target_size / original_width)
                    else:
                        new_height = target_size
                        new_width = int(original_width * target_size / original_height)
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Sauvegarder en format JPEG au lieu de WebP pour compatibilité
                output = BytesIO()
                
                # Essayer JPEG d'abord (plus compatible)
                try:
                    img.save(output, format='JPEG', quality=90, optimize=True)
                    image_data = output.getvalue()
                    return image_data, img.size, None
                except Exception:
                    # Si JPEG échoue, essayer PNG
                    output = BytesIO()
                    img.save(output, format='PNG', optimize=True)
                    image_data = output.getvalue()
                    return image_data, img.size, None
                
        except Exception as e:
            return None, None, f"Erreur traitement image: {str(e)}"
    
    @staticmethod
    def generate_upload_id() -> str:
        """Générer un ID d'upload unique"""
        return str(int(time.time() * 1000))
    
    @staticmethod
    def generate_pdq_hash(image_data: bytes) -> str:
        """Générer un hash PDQ factice pour l'image"""
        # Générer un hash PDQ factice basé sur les données de l'image
        hash_base = hashlib.md5(image_data).hexdigest()
        # Format PDQ hash Instagram
        pdq_hash = ''.join(c if c.isdigit() else '9' if ord(c) % 2 else '6' for c in hash_base[:64])
        return f"{pdq_hash}:59"
