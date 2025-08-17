import re
import time
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

class LiteAPKsHandler:
    @staticmethod
    def is_liteapks_link(url):
        domain = urlparse(url).netloc.lower()
        return 'liteapks.com' in domain

    @staticmethod
    def get_scraper():
        return cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'desktop': True,
        }, delay=1)

    @staticmethod
    def get_direct_link(url, retries=3):
        scraper = LiteAPKsHandler.get_scraper()
        
        for attempt in range(retries):
            try:
                print(f"Intento {attempt + 1}: Procesando LiteAPKs...")
                
                # PASO 1: Acceder a la página inicial
                print(f"Paso 1: Accediendo a {url}")
                response = scraper.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar el botón de descarga con el span que contiene "Download ("
                download_button = None
                
                # Buscar span que contenga "Download (" y obtener su elemento padre (el enlace)
                download_spans = soup.find_all('span', class_='align-middle')
                for span in download_spans:
                    if span.get_text() and 'Download (' in span.get_text():
                        # Buscar el elemento padre que sea un enlace
                        parent = span.parent
                        while parent and parent.name != 'a':
                            parent = parent.parent
                        if parent and parent.name == 'a' and parent.get('href'):
                            download_button = parent
                            break
                
                if not download_button:
                    raise Exception("No se encontró el botón de descarga en la página inicial")
                
                # PASO 2: Ir a la segunda página
                second_page_url = urljoin(url, download_button['href'])
                print(f"Paso 2: Accediendo a segunda página {second_page_url}")
                
                response = scraper.get(second_page_url)
                response.raise_for_status()
                
                # PASO 3: Construir URL de tercera página agregando "/1"
                if not second_page_url.endswith('/'):
                    third_page_url = second_page_url + '/1'
                else:
                    third_page_url = second_page_url + '1'
                
                print(f"Paso 3: Accediendo a tercera página {third_page_url}")
                response = scraper.get(third_page_url)
                response.raise_for_status()
                
                # PASO 4: Esperar 5 segundos
                print("Esperando 5 segundos...")
                time.sleep(5)
                
                # PASO 5: Parsear la tercera página y buscar el enlace directo
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Método 1: Buscar span con "Download (" y obtener el enlace padre
                download_spans = soup.find_all('span', class_='align-middle')
                for span in download_spans:
                    if span.get_text() and 'Download (' in span.get_text():
                        # Buscar el elemento padre que sea un enlace
                        parent = span.parent
                        while parent and parent.name != 'a':
                            parent = parent.parent
                        if parent and parent.name == 'a' and parent.get('href'):
                            direct_url = parent['href']
                            if direct_url.startswith('http'):
                                print(f"Enlace encontrado (Método 1): {direct_url}")
                                return direct_url

                # Método 2: Buscar enlaces que apunten a archivos APK o dominios de descarga
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Buscar enlaces que contengan extensiones de archivos o dominios de descarga comunes
                    if any(x in href.lower() for x in ['.apk', 'download', 'file']):
                        if href.startswith('http'):
                            print(f"Enlace encontrado (Método 2): {href}")
                            return href

                # Método 3: Buscar en JavaScript patrones de descarga
                for script in soup.find_all('script'):
                    if script.string:
                        # Buscar patrones de URL de descarga en JavaScript
                        matches = re.findall(r'(https?://[^\s"\']+\.apk[^\s"\']*)', script.string)
                        if matches:
                            print(f"Enlace encontrado (Método 3): {matches[0]}")
                            return matches[0]
                        
                        # Buscar otros patrones de descarga
                        matches = re.findall(r'(https?://[^\s"\']*(?:download|file)[^\s"\']*)', script.string)
                        if matches:
                            for match in matches:
                                if not any(x in match.lower() for x in ['google', 'facebook', 'twitter']):
                                    print(f"Enlace encontrado (Método 3b): {match}")
                                    return match

                # Método 4: Buscar cualquier enlace externo que no sea de redes sociales
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http') and 'liteapks.com' not in href:
                        # Evitar enlaces de redes sociales
                        if not any(x in href.lower() for x in ['facebook', 'twitter', 'instagram', 'youtube', 'telegram']):
                            print(f"Enlace encontrado (Método 4): {href}")
                            return href

            except Exception as e:
                print(f"Error en intento {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    raise Exception(f"Error LiteAPKs después de {retries} intentos: {str(e)}")
                time.sleep(3)

        raise Exception("No se encontró enlace directo después de varios intentos")

    @staticmethod
    def extract_app_info(url):
        """Extrae información de la app desde la URL"""
        scraper = LiteAPKsHandler.get_scraper()
        
        try:
            response = scraper.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer título
            title = "APK"
            
            # Buscar en diferentes elementos posibles
            title_selectors = ['h1', 'h2', '.app-title', '.title', 'title']
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title = title_element.get_text().strip()
                    break
            
            # Limpiar el título de texto extra
            title = re.sub(r'\s*-\s*LiteAPKs.*', '', title, flags=re.IGNORECASE)
            title = title.strip()
            
            # Extraer versión si está disponible
            version = "Unknown"
            
            # Buscar versión en el título o en otros elementos
            version_patterns = [
                r'v(\d+\.\d+[\.\d]*)',
                r'version\s*(\d+\.\d+[\.\d]*)',
                r'(\d+\.\d+[\.\d]*)'
            ]
            
            for pattern in version_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    version = match.group(1)
                    break
            
            # Si no se encontró en el título, buscar en elementos específicos
            if version == "Unknown":
                version_selectors = ['.version', '.app-version', '[class*="version"]']
                for selector in version_selectors:
                    version_element = soup.select_one(selector)
                    if version_element:
                        version_text = version_element.get_text()
                        match = re.search(r'(\d+\.\d+[\.\d]*)', version_text)
                        if match:
                            version = match.group(1)
                            break
            
            return {
                'title': title,
                'version': version,
                'source': 'LiteAPKs'
            }
            
        except Exception as e:
            return {
                'title': 'APK Download',
                'version': 'Unknown',
                'source': 'LiteAPKs',
                'error': str(e)
            }

    @staticmethod
    def get_download_info(url):
        """Obtiene tanto el enlace directo como la información de la app"""
        try:
            direct_link = LiteAPKsHandler.get_direct_link(url)
            app_info = LiteAPKsHandler.extract_app_info(url)
            
            return {
                'direct_link': direct_link,
                'app_info': app_info,
                'success': True
            }
            
        except Exception as e:
            return {
                'direct_link': None,
                'app_info': None,
                'success': False,
                'error': str(e)
            }

# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo con la URL de Spotify que proporcionaste
    test_url = "https://liteapks.com/spotify-2.html"
    
    print("Probando LiteAPKs Handler...")
    print(f"URL: {test_url}")
    
    # Verificar si es un enlace de LiteAPKs
    if LiteAPKsHandler.is_liteapks_link(test_url):
        print("✅ Es un enlace de LiteAPKs")
        
        # Obtener información y enlace de descarga
        result = LiteAPKsHandler.get_download_info(test_url)
        
        if result['success']:
            print("✅ Descarga exitosa!")
            print(f"📱 App: {result['app_info']['title']}")
            print(f"📋 Versión: {result['app_info']['version']}")
            print(f"🔗 Enlace directo: {result['direct_link']}")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("❌ No es un enlace de LiteAPKs")