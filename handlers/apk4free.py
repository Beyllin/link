import re
import time
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

class APK4FreeHandler:
    @staticmethod
    def is_apk4free_link(url):
        domain = urlparse(url).netloc.lower()
        return 'apk4free.net' in domain

    @staticmethod
    def get_scraper():
        return cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'desktop': True,
        }, delay=1)

    @staticmethod
    def normalize_url(url):
        """Normaliza la URL eliminando caracteres extra y asegurando formato correcto"""
        # Limpiar caracteres extra como %22
        url = re.sub(r'%22|"', '', url)
        
        # Asegurar que termine con /
        if not url.endswith('/'):
            url += '/'
            
        # Si no tiene /download/, agregarlo
        if '/download/' not in url:
            # Quitar la / final temporalmente
            if url.endswith('/'):
                url = url[:-1]
            url += '/download/'
            
        return url

    @staticmethod
    def get_direct_link(url, retries=3):
        scraper = APK4FreeHandler.get_scraper()
        
        # Normalizar URL primero
        download_url = APK4FreeHandler.normalize_url(url)
        
        for attempt in range(retries):
            try:
                print(f"Intento {attempt + 1}: Accediendo a {download_url}")
                
                # Hacer request a la página de descarga
                response = scraper.get(download_url)
                response.raise_for_status()
                
                # Esperar 6 segundos como mencionas
                print("Esperando 6 segundos...")
                time.sleep(6)
                
                # Parsear HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Método 1: Buscar el primer botón después de "Download links"
                download_links_text = soup.find(text=re.compile(r'Download links', re.IGNORECASE))
                if download_links_text:
                    # Buscar el elemento padre que contiene "Download links"
                    parent = download_links_text.parent
                    if parent:
                        # Buscar el primer enlace con clase buttond downloadAPK dapk_b después del texto
                        next_link = parent.find_next('a', class_='buttond downloadAPK dapk_b')
                        if next_link and next_link.get('href'):
                            direct_url = next_link['href']
                            if direct_url.startswith('http'):
                                print(f"Enlace encontrado (Método 1): {direct_url}")
                                return direct_url

                # Método 2: Buscar cualquier enlace con la clase específica
                download_button = soup.find('a', class_='buttond downloadAPK dapk_b')
                if download_button and download_button.get('href'):
                    direct_url = download_button['href']
                    if direct_url.startswith('http'):
                        print(f"Enlace encontrado (Método 2): {direct_url}")
                        return direct_url

                # Método 3: Buscar enlaces que apunten a files.apk4free.net
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'files.apk4free.net' in href:
                        print(f"Enlace encontrado (Método 3): {href}")
                        return href

                # Método 4: Buscar en JavaScript si hay algún enlace de descarga
                for script in soup.find_all('script'):
                    if script.string:
                        # Buscar patrones de URL en el JavaScript
                        matches = re.findall(r'(https?://files\.apk4free\.net/[^\s"\']+)', script.string)
                        if matches:
                            print(f"Enlace encontrado (Método 4): {matches[0]}")
                            return matches[0]

                # Si no se encontró nada, intentar hacer un segundo request después de más tiempo
                if attempt == 0:
                    print("No se encontró enlace, esperando más tiempo...")
                    time.sleep(5)
                    continue

            except Exception as e:
                print(f"Error en intento {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    raise Exception(f"Error APK4Free después de {retries} intentos: {str(e)}")
                time.sleep(3)

        raise Exception("No se encontró enlace directo después de varios intentos")

    @staticmethod
    def extract_app_info(url):
        """Extrae información de la app desde la URL"""
        scraper = APK4FreeHandler.get_scraper()
        
        try:
            # Si es URL de descarga, obtener la URL original
            original_url = url.replace('/download/', '/') if '/download/' in url else url
            
            response = scraper.get(original_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer título
            title = "APK"
            title_element = soup.find('h1') or soup.find('title')
            if title_element:
                title = title_element.get_text().strip()
            
            # Extraer versión si está disponible
            version_pattern = r'v?(\d+\.\d+[\.\d]*)'
            version_match = re.search(version_pattern, title)
            version = version_match.group(1) if version_match else "Unknown"
            
            return {
                'title': title,
                'version': version,
                'source': 'APK4Free'
            }
            
        except Exception as e:
            return {
                'title': 'APK Download',
                'version': 'Unknown',
                'source': 'APK4Free',
                'error': str(e)
            }

    @staticmethod
    def get_download_info(url):
        """Obtiene tanto el enlace directo como la información de la app"""
        try:
            direct_link = APK4FreeHandler.get_direct_link(url)
            app_info = APK4FreeHandler.extract_app_info(url)
            
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
    test_url = "https://apk4free.net/spotify-music-premium/"
    
    print("Probando APK4Free Handler...")
    print(f"URL: {test_url}")
    
    # Verificar si es un enlace de APK4Free
    if APK4FreeHandler.is_apk4free_link(test_url):
        print("✅ Es un enlace de APK4Free")
        
        # Obtener información y enlace de descarga
        result = APK4FreeHandler.get_download_info(test_url)
        
        if result['success']:
            print("✅ Descarga exitosa!")
            print(f"📱 App: {result['app_info']['title']}")
            print(f"📋 Versión: {result['app_info']['version']}")
            print(f"🔗 Enlace directo: {result['direct_link']}")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("❌ No es un enlace de APK4Free")