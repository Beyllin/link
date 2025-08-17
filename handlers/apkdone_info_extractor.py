import re
import time
import requests
import json
import multiprocessing as mp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from functools import wraps

class APKDoneInfoExtractor:
    
    # Diccionario de traducción de géneros
    GENRE_TRANSLATIONS = {
        # Géneros de aplicaciones
        "Art & Design": "Arte y Diseño",
        "Auto & Vehicles": "Automóviles y Vehículos", 
        "Beauty": "Belleza",
        "Books & Reference": "Libros y Referencias",
        "Business": "Negocios",
        "Comics": "Cómics",
        "Communication": "Comunicación",
        "Dating": "Citas",
        "Education": "Educación",
        "Entertainment": "Entretenimiento",
        "Events": "Eventos",
        "Finance": "Finanzas",
        "Food & Drink": "Comida y Bebida",
        "Health & Fitness": "Salud y Fitness",
        "House & Home": "Casa y Hogar",
        "Libraries & Demo": "Bibliotecas y Demo",
        "Lifestyle": "Estilo de Vida",
        "Maps & Navigation": "Mapas y Navegación",
        "Medical": "Medicina",
        "Music & Audio": "Música y Audio",
        "News & Magazines": "Noticias y Revistas",
        "Parenting": "Crianza",
        "Personalization": "Personalización",
        "Photography": "Fotografía",
        "Productivity": "Productividad",
        "Shopping": "Compras",
        "Social": "Social",
        "Sports": "Deportes",
        "Tools": "Herramientas",
        "Travel & Local": "Viajes y Local",
        "Video Players & Editors": "Reproductores y Editores de Video",
        "Weather": "Clima",
        # Géneros de juegos
        "Action": "Acción",
        "Adventure": "Aventura",
        "Arcade": "Arcade",
        "Board": "Mesa",
        "Card": "Cartas",
        "Casino": "Casino",
        "Casual": "Casual",
        "Educational": "Educativo",
        "Music": "Música",
        "Puzzle": "Puzzle",
        "Racing": "Carreras",
        "Role Playing": "Juegos de Rol",
        "Simulation": "Simulación",
        "Sports": "Deportes",
        "Strategy": "Estrategia",
        "Trivia": "Trivia",
        "Word": "Palabras"
    }

    @staticmethod
    def get_scraper():
        """Crea una nueva sesión de requests para cada proceso"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        return session

    @staticmethod
    def translate_text(text):
        """Traduce textos comunes al español usando un diccionario básico"""
        translations = {
            # Modificaciones comunes
            "Premium Unlocked": "Premium Desbloqueado",
            "Pro Unlocked": "Pro Desbloqueado", 
            "Paid Unlocked": "Pagado Desbloqueado",
            "Full Unlocked": "Completamente Desbloqueado",
            "Ad-Free": "Sin Anuncios",
            "No Ads": "Sin Publicidad",
            "Unlimited": "Ilimitado",
            "VIP Unlocked": "VIP Desbloqueado",
            "Premium Features": "Características Premium",
            "All Features Unlocked": "Todas las Características Desbloqueadas",
            
            # Palabras comunes en descripciones
            "generate": "genera",
            "create": "crea",
            "edit": "edita",
            "remove": "elimina",
            "convert": "convierte",
            "fix": "corrige",
            "enhance": "mejora",
            "photo": "foto",
            "photos": "fotos",
            "image": "imagen",
            "images": "imágenes",
            "video": "video",
            "videos": "videos",
            "background": "fondo",
            "sketch": "boceto",
            "text": "texto",
            "blurry": "borrosas",
            "from": "a partir de",
            "to": "en",
            "and": "y"
        }
        
        result = text
        for english, spanish in translations.items():
            # Reemplazar palabras completas (case insensitive)
            result = re.sub(r'\b' + re.escape(english) + r'\b', spanish, result, flags=re.IGNORECASE)
        
        return result

    @staticmethod
    def format_genres(genres_text):
        """Formatea los géneros para hashtags"""
        if not genres_text:
            return ""
        
        # Traducir el género
        translated = APKDoneInfoExtractor.GENRE_TRANSLATIONS.get(genres_text, genres_text)
        
        # Dividir por & o and y crear hashtags
        parts = re.split(r'\s*&\s*|\s+and\s+', translated, flags=re.IGNORECASE)
        hashtags = []
        
        for part in parts:
            # Limpiar y crear hashtag
            clean_part = part.strip()
            if clean_part:
                hashtag = "#" + clean_part.replace(" ", "")
                hashtags.append(hashtag)
        
        return " ".join(hashtags)

    @staticmethod
    def _extract_app_info_process(url, result_queue, process_id):
        """Función que se ejecuta en proceso separado para extraer información"""
        try:
            print(f"🔄 Proceso {process_id} (PID: {mp.current_process().pid}): Iniciando extracción...")
            
            # Crear una sesión completamente nueva para este proceso
            scraper = APKDoneInfoExtractor.get_scraper()
            
            # Si es URL de descarga, obtener la URL original
            original_url = url.replace('/download/', '/') if '/download/' in url else url
            print(f"🌐 Proceso {process_id}: Accediendo a {original_url}")
            
            response = scraper.get(original_url, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"✅ Proceso {process_id}: HTML cargado ({len(response.text)} chars)")
            
            # Extraer información usando métodos estáticos
            app_name = APKDoneInfoExtractor._extract_app_name_static(soup)
            version = APKDoneInfoExtractor._extract_version_static(soup, app_name)
            category = APKDoneInfoExtractor._extract_category_static(soup)
            app_type = APKDoneInfoExtractor._extract_app_type_static(soup, original_url)
            mod_info = APKDoneInfoExtractor._extract_mod_info_static(soup)
            description = APKDoneInfoExtractor._extract_description_static(soup)
            playstore_link = APKDoneInfoExtractor._extract_playstore_link_static(soup)
            
            result = {
                'app_name': app_name,
                'version': version,
                'category': category,
                'app_type': app_type,
                'mod_info': mod_info,
                'description': description,
                'playstore_link': playstore_link,
                'success': True,
                'process_id': process_id
            }
            
            print(f"✅ Proceso {process_id}: Extracción completada exitosamente")
            print(f"   - App: {app_name}")
            print(f"   - Versión: {version}")
            print(f"   - Categoría: {category}")
            
            result_queue.put(result)
            
        except Exception as e:
            print(f"❌ Proceso {process_id}: Error - {str(e)}")
            error_result = {
                'success': False,
                'error': str(e),
                'process_id': process_id
            }
            result_queue.put(error_result)

    @staticmethod
    def _extract_app_name_static(soup):
        """Extrae el nombre de la app (método estático)"""
        selectors = ['h1', 'h2', 'h3', '.app-title', '.title', '[class*="title"]']
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 2:
                    clean_name = re.sub(r'\s*(MOD|APK|Download|Free).*$', '', text, flags=re.IGNORECASE).strip()
                    if clean_name:
                        return clean_name
        return "App"

    @staticmethod 
    def _extract_version_static(soup, app_name):
        """Extrae la versión (método estático)"""
        # Método 1: Buscar "Version" literal
        version_text = soup.find(text=re.compile(r'Version', re.IGNORECASE))
        if version_text:
            parent = version_text.parent
            if parent:
                next_elements = parent.find_next_siblings()
                for elem in next_elements[:3]:
                    text = elem.get_text().strip()
                    version_match = re.search(r'(\d+\.\d+[\.\d]*)', text)
                    if version_match:
                        return version_match.group(1)
        
        # Método 2: Buscar en el nombre de la app
        version_match = re.search(r'v?(\d+\.\d+[\.\d]*)', app_name)
        if version_match:
            return version_match.group(1)
        
        # Método 3: Buscar en todo el texto
        all_text = soup.get_text()
        version_patterns = [
            r'Version:?\s*(\d+\.\d+[\.\d]*)',
            r'v(\d+\.\d+[\.\d]*)',
            r'Ver:?\s*(\d+\.\d+[\.\d]*)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"

    @staticmethod
    def _extract_category_static(soup):
        """Extrae la categoría (método estático)"""
        selectors = [
            '.chip-category',
            'a[href*="/app/"]',
            'a[href*="/category/"]',
            '[class*="category"]',
            '[class*="genre"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                if text and ('&' in text or len(text) > 3):
                    return text
        return ""

    @staticmethod
    def _extract_app_type_static(soup, url):
        """Extrae el tipo (método estático)"""
        type_element = soup.find('span', string=re.compile(r'^(Apps|Games)$'))
        if type_element:
            return type_element.get_text().strip()
        
        if '/game/' in url.lower():
            return "Games"
        
        content = soup.get_text().lower()
        if 'game' in content and 'games' in content:
            return "Games"
        
        return "Apps"

    @staticmethod
    def _extract_mod_info_static(soup):
        """Extrae información del MOD (método estático)"""
        mod_element = soup.find('span', class_='chip-text')
        if mod_element:
            return mod_element.get_text().strip()
        
        mod_patterns = [
            r'Premium\s+Unlocked',
            r'Pro\s+Unlocked', 
            r'Ad.?Free',
            r'Unlocked',
            r'Premium',
            r'VIP'
        ]
        
        content = soup.get_text()
        for pattern in mod_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""

    @staticmethod
    def _extract_description_static(soup):
        """Extrae la descripción (método estático)"""
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 20 and not re.match(r'^(Download|Install|Features)', text):
                return text
        return ""

    @staticmethod
    def _extract_playstore_link_static(soup):
        """Extrae el enlace de Play Store (método estático)"""
        playstore_element = soup.find('a', href=re.compile(r'play\.google\.com'))
        if playstore_element:
            return playstore_element['href']
        return ""

    @staticmethod
    def format_message(app_info):
        """Formatea la información en el formato EXACTO solicitado"""
        if not app_info.get('success', False):
            return "Error al obtener información de la aplicación"
        
        try:
            app_name = app_info.get('app_name', 'App')
            version = app_info.get('version', 'Unknown')
            category = app_info.get('category', '')
            app_type = app_info.get('app_type', 'Apps')
            mod_info = app_info.get('mod_info', '')
            description = app_info.get('description', '')
            playstore_link = app_info.get('playstore_link', '')
            
            # LÍNEA 1: Creatify v2.2.2 Mod #Apps 👩‍💻 #Arte #Diseño
            line1_parts = []
            
            # Nombre de la app
            line1_parts.append(app_name)
            
            # Versión
            if version != 'Unknown':
                line1_parts.append(f"v{version}")
            
            # "Mod" siempre se agrega
            line1_parts.append("Mod")
            
            # Tipo de app (#Apps o #Games)
            if app_type.lower() == 'games':
                line1_parts.append("#Games 🎮")
            else:
                line1_parts.append("#Apps 👩‍💻")
            
            # Géneros como hashtags
            genre_hashtags = APKDoneInfoExtractor.format_genres(category)
            if genre_hashtags:
                line1_parts.append(genre_hashtags)
            
            line1 = " ".join(line1_parts)
            
            # LÍNEA 3: Información del Mod: Premium Desbloqueado
            line3 = ""
            if mod_info:
                translated_mod = APKDoneInfoExtractor.translate_text(mod_info)
                line3 = f"Información del Mod: {translated_mod}"
            
            # LÍNEA 5: Descripción con hashtags y enlace
            line5 = ""
            if description:
                translated_desc = APKDoneInfoExtractor.translate_text(description)
                line5_parts = [f"{app_name}: {translated_desc}"]
                
                # Agregar géneros al final
                if genre_hashtags:
                    line5_parts.append(genre_hashtags)
                
                # Agregar enlace de Play Store
                if playstore_link:
                    line5_parts.append(playstore_link)
                
                line5 = " ".join(line5_parts)
            
            # Construir mensaje completo con el formato exacto
            message_parts = [line1]
            
            if line3:  # Solo agregar si hay información del MOD
                message_parts.extend(["", line3])  # Línea vacía + info del MOD
            
            if line5:  # Solo agregar si hay descripción
                message_parts.extend(["", line5])  # Línea vacía + descripción
            
            return "\n".join(message_parts)
            
        except Exception as e:
            return f"Error al formatear mensaje: {str(e)}"

    @staticmethod
    def get_formatted_info(url, timeout=30, max_processes=2):
        """
        Función principal que extrae y formatea información usando multiprocessing
        
        Args:
            url (str): URL de APKDone
            timeout (int): Timeout en segundos
            max_processes (int): Número máximo de procesos paralelos
        
        Returns:
            dict: Resultado con success, message, raw_info
        """
        print(f"🚀 Iniciando extracción multiprocess para: {url}")
        
        # Cola para comunicación entre procesos
        result_queue = mp.Queue()
        processes = []
        
        try:
            # Crear múltiples procesos para mayor robustez
            for i in range(max_processes):
                process = mp.Process(
                    target=APKDoneInfoExtractor._extract_app_info_process,
                    args=(url, result_queue, i+1)
                )
                processes.append(process)
                process.start()
                print(f"🔄 Proceso {i+1} iniciado (PID: {process.pid})")
            
            # Esperar resultado del primer proceso que termine exitosamente
            successful_result = None
            start_time = time.time()
            
            while (time.time() - start_time) < timeout and successful_result is None:
                try:
                    if not result_queue.empty():
                        result = result_queue.get(timeout=1)
                        
                        if result.get('success', False):
                            successful_result = result
                            print(f"✅ Proceso {result.get('process_id', 'X')} completado exitosamente")
                            break
                        else:
                            print(f"❌ Proceso {result.get('process_id', 'X')} falló: {result.get('error', 'Unknown')}")
                    else:
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"⚠️  Error recibiendo resultado: {str(e)}")
                    continue
            
            # Si obtuvimos un resultado exitoso, formatearlo
            if successful_result:
                formatted_message = APKDoneInfoExtractor.format_message(successful_result)
                
                return {
                    'success': True,
                    'message': formatted_message,
                    'raw_info': successful_result
                }
            else:
                return {
                    'success': False,
                    'message': '',
                    'error': 'Timeout: No se pudo extraer información en el tiempo límite'
                }
                
        except Exception as e:
            print(f"❌ Error crítico en multiprocessing: {str(e)}")
            return {
                'success': False,
                'message': '',
                'error': str(e)
            }
            
        finally:
            # Limpiar procesos
            print("🧹 Terminando procesos...")
            for i, process in enumerate(processes):
                if process.is_alive():
                    print(f"⏹️  Terminando proceso {i+1}...")
                    process.terminate()
                    process.join(timeout=2)
                    if process.is_alive():
                        print(f"🔪 Matando proceso {i+1} forzadamente...")
                        process.kill()

# Función de prueba independiente
def test_multiprocess_extractor():
    """Función de prueba para el extractor multiprocess"""
    print("🧪 PROBANDO EXTRACTOR MULTIPROCESS")
    print("=" * 60)
    
    test_url = "https://apkdone.com/creatify/"
    
    try:
        result = APKDoneInfoExtractor.get_formatted_info(test_url)
        
        print(f"\n📊 RESULTADO:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success', False):
            print(f"\n📝 MENSAJE FORMATEADO:")
            print("-" * 40)
            print(result['message'])
            print("-" * 40)
            
            print(f"\n🔍 INFO RAW:")
            raw_info = result.get('raw_info', {})
            for key, value in raw_info.items():
                if key not in ['success', 'process_id']:
                    print(f"  {key}: {value}")
        else:
            print(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {str(e)}")
        import traceback
        print(f"📊 Traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_multiprocess_extractor()