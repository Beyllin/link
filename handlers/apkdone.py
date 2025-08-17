import re
import time
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

class APKDoneHandler:
    @staticmethod
    def is_apkdone_link(url):
        domain = urlparse(url).netloc.lower()
        return 'apkdone.com' in domain

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
    def is_valid_download_button(element):
        """
        Verifica si un botón es el correcto para descargar
        Evita el botón "Fast Download with APKDone" y busca "Download APK" con tamaño
        """
        if not element:
            return False
            
        # Obtener todo el texto del elemento
        text = element.get_text().strip()
        
        # RECHAZAR explícitamente el botón "Fast Download with APKDone"
        rejected_patterns = [
            r'Fast\s*Download\s*with\s*APKDone',
            r'Fast\s*Download\s*APKDone',
            r'APKDone\s*Fast',
        ]
        
        for pattern in rejected_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"❌ Botón rechazado (Fast Download): {text}")
                return False
        
        # ACEPTAR botones que contengan "Download APK" 
        # Preferiblemente con tamaño (ej: "Download APK (53 MB)")
        valid_patterns = [
            r'Download\s*APK.*\(\d+(?:\.\d+)?\s*[KMGT]?B\)',  # Con tamaño específico
            r'Download\s*APK(?!\s*Done)(?!\s*with)',  # Sin "APKDone" o "with" después
        ]
        
        for pattern in valid_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"✅ Botón válido encontrado: {text}")
                return True
        
        return False

    @staticmethod
    def fix_download_url(url):
        """
        Corrige URLs de descarga cambiando hole.apkdone.io por file.apkdone.io
        """
        if url and 'hole.apkdone.io' in url:
            corrected_url = url.replace('hole.apkdone.io', 'file.apkdone.io')
            print(f"🔧 URL corregida: {url} -> {corrected_url}")
            return corrected_url
        return url

    @staticmethod
    def get_direct_link(url, retries=3):
        scraper = APKDoneHandler.get_scraper()
        
        # Normalizar URL primero
        download_url = APKDoneHandler.normalize_url(url)
        
        for attempt in range(retries):
            try:
                print(f"Intento {attempt + 1}: Accediendo a {download_url}")
                
                # Hacer request a la página de descarga
                response = scraper.get(download_url)
                response.raise_for_status()
                
                # Esperar unos segundos para que cargue el contenido
                print("Esperando 3 segundos...")
                time.sleep(3)
                
                # Parsear HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Método 1: Buscar específicamente "Download APK" con validación
                print("🔍 Buscando botones 'Download APK'...")
                download_buttons = soup.find_all('a', href=True)
                
                valid_buttons = []
                for button in download_buttons:
                    if APKDoneHandler.is_valid_download_button(button):
                        valid_buttons.append(button)
                
                # Priorizar botones con tamaño en el texto
                for button in valid_buttons:
                    text = button.get_text().strip()
                    # Buscar patrón con tamaño (ej: "Download APK (53 MB)")
                    if re.search(r'\(\d+(?:\.\d+)?\s*[KMGT]?B\)', text, re.IGNORECASE):
                        direct_url = button['href']
                        if not direct_url.startswith('http'):
                            direct_url = urljoin(download_url, direct_url)
                        # Corregir URL si es necesario
                        direct_url = APKDoneHandler.fix_download_url(direct_url)
                        print(f"✅ Enlace prioritario encontrado (con tamaño): {direct_url}")
                        return direct_url
                
                # Si no hay con tamaño, usar el primer botón válido
                if valid_buttons:
                    button = valid_buttons[0]
                    direct_url = button['href']
                    if not direct_url.startswith('http'):
                        direct_url = urljoin(download_url, direct_url)
                    # Corregir URL si es necesario
                    direct_url = APKDoneHandler.fix_download_url(direct_url)
                    print(f"✅ Enlace válido encontrado: {direct_url}")
                    return direct_url

                # Método 2: Buscar por patrones específicos en el texto
                print("🔍 Buscando por patrones específicos...")
                for link in soup.find_all('a', href=True):
                    link_text = link.get_text().strip()
                    
                    # Solo aceptar si contiene "Download APK" y NO contiene "Fast Download"
                    if (re.search(r'Download\s*APK', link_text, re.IGNORECASE) and 
                        not re.search(r'Fast\s*Download', link_text, re.IGNORECASE) and
                        not re.search(r'APKDone', link_text, re.IGNORECASE)):
                        
                        direct_url = link['href']
                        if not direct_url.startswith('http'):
                            direct_url = urljoin(download_url, direct_url)
                        # Corregir URL si es necesario
                        direct_url = APKDoneHandler.fix_download_url(direct_url)
                        print(f"✅ Enlace encontrado (Método 2): {direct_url}")
                        return direct_url

                # Método 3: Buscar enlaces que apunten directamente a archivos APK
                print("🔍 Buscando enlaces directos a APK...")
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.lower().endswith('.apk'):
                        if not href.startswith('http'):
                            href = urljoin(download_url, href)
                        # Verificar que no sea la misma página de descarga
                        if href != download_url:
                            print(f"✅ Enlace directo APK encontrado: {href}")
                            return href

                # Método 4: Buscar por clases específicas, pero con validación de texto
                print("🔍 Buscando por clases CSS...")
                download_classes = [
                    'download-btn', 'download-button', 'btn-download', 
                    'download-link', 'apk-download', 'download'
                ]
                
                for class_name in download_classes:
                    buttons = soup.find_all('a', class_=re.compile(class_name, re.IGNORECASE), href=True)
                    for button in buttons:
                        if APKDoneHandler.is_valid_download_button(button):
                            direct_url = button['href']
                            if not direct_url.startswith('http'):
                                direct_url = urljoin(download_url, direct_url)
                            print(f"✅ Enlace encontrado por clase ({class_name}): {direct_url}")
                            return direct_url

                # Si no se encontró nada en el primer intento, esperar más tiempo
                if attempt == 0:
                    print("⏳ No se encontró enlace, esperando más tiempo...")
                    time.sleep(5)
                    continue

            except Exception as e:
                print(f"❌ Error en intento {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    raise Exception(f"Error APKDone después de {retries} intentos: {str(e)}")
                time.sleep(3)

        raise Exception("No se encontró enlace directo después de varios intentos")

    @staticmethod
    def extract_app_info(url):
        """Extrae información de la app desde la URL"""
        scraper = APKDoneHandler.get_scraper()
        
        try:
            # Si es URL de descarga, obtener la URL original
            original_url = url.replace('/download/', '/') if '/download/' in url else url
            
            response = scraper.get(original_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer título
            title = "APK"
            # Buscar en diferentes elementos posibles
            title_elements = [
                soup.find('h1'),
                soup.find('h2'), 
                soup.find('title'),
                soup.find('meta', attrs={'property': 'og:title'}),
                soup.find('meta', attrs={'name': 'title'})
            ]
            
            for element in title_elements:
                if element:
                    if element.name == 'meta':
                        title = element.get('content', '').strip()
                    else:
                        title = element.get_text().strip()
                    if title and title != "APK":
                        break
            
            # Extraer versión si está disponible
            version_patterns = [
                r'v?(\d+\.\d+[\.\d]*)',
                r'Version:?\s*(\d+\.\d+[\.\d]*)',
                r'Ver:?\s*(\d+\.\d+[\.\d]*)'
            ]
            
            version = "Unknown"
            text_content = soup.get_text()
            
            for pattern in version_patterns:
                version_match = re.search(pattern, title + " " + text_content, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)
                    break
            
            # Extraer tamaño - también intentar desde los botones de descarga
            size = "Unknown"
            
            # Primero buscar en botones de descarga válidos
            download_buttons = soup.find_all('a', href=True)
            for button in download_buttons:
                if APKDoneHandler.is_valid_download_button(button):
                    button_text = button.get_text()
                    size_match = re.search(r'\((\d+(?:\.\d+)?\s*[KMGT]?B)\)', button_text, re.IGNORECASE)
                    if size_match:
                        size = size_match.group(1)
                        break
            
            # Si no se encontró en botones, buscar en el texto general
            if size == "Unknown":
                size_patterns = [
                    r'(\d+(?:\.\d+)?\s*(?:MB|GB|KB))',
                    r'Size:?\s*(\d+(?:\.\d+)?\s*(?:MB|GB|KB))'
                ]
                
                for pattern in size_patterns:
                    size_match = re.search(pattern, text_content, re.IGNORECASE)
                    if size_match:
                        size = size_match.group(1)
                        break
            
            return {
                'title': title,
                'version': version,
                'size': size,
                'source': 'APKDone'
            }
            
        except Exception as e:
            return {
                'title': 'APK Download',
                'version': 'Unknown',
                'size': 'Unknown',
                'source': 'APKDone',
                'error': str(e)
            }

    @staticmethod
    def get_download_info(url):
        """Obtiene tanto el enlace directo como la información de la app"""
        try:
            direct_link = APKDoneHandler.get_direct_link(url)
            app_info = APKDoneHandler.extract_app_info(url)
            
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
    # Ejemplo con la URL que proporcionaste
    test_url = "https://apkdone.com/root-booster/"
    
    print("🚀 Probando APKDone Handler (versión filtrada)...")
    print(f"🔗 URL: {test_url}")
    print("=" * 50)
    
    # Verificar si es un enlace de APKDone
    if APKDoneHandler.is_apkdone_link(test_url):
        print("✅ Es un enlace de APKDone")
        
        # Obtener información y enlace de descarga
        result = APKDoneHandler.get_download_info(test_url)
        
        if result['success']:
            print("\n🎉 ¡Descarga exitosa!")
            print("-" * 30)
            print(f"📱 App: {result['app_info']['title']}")
            print(f"📋 Versión: {result['app_info']['version']}")
            print(f"💾 Tamaño: {result['app_info']['size']}")
            print(f"🔗 Enlace directo: {result['direct_link']}")
        else:
            print(f"\n❌ Error: {result['error']}")
    else:
        print("❌ No es un enlace de APKDone")