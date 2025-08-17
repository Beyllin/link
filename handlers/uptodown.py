import re
import time
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

class UptodownHandler:
    @staticmethod
    def is_uptodown_link(url):
        domain = urlparse(url).netloc.lower()
        return 'uptodown.com' in domain

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
        """Normaliza la URL agregando automáticamente /download al final"""
        # Limpiar caracteres extra como %22
        url = re.sub(r'%22|"', '', url)
        
        # Quitar la / final si existe
        if url.endswith('/'):
            url = url[:-1]
            
        # Si no tiene /download, agregarlo
        if not url.endswith('/download'):
            url += '/download'
            
        return url

    @staticmethod
    def get_direct_link(url, retries=3):
        scraper = UptodownHandler.get_scraper()
        
        # Normalizar URL primero (agregar /download automáticamente)
        download_url = UptodownHandler.normalize_url(url)
        
        for attempt in range(retries):
            try:
                print(f"Intento {attempt + 1}: Accediendo a {download_url}")
                
                # Hacer request a la página de descarga
                response = scraper.get(download_url, allow_redirects=True)
                response.raise_for_status()
                
                # Verificar si hubo redirección (ej: a .en.uptodown.com)
                final_url = response.url
                if final_url != download_url:
                    print(f"Redirección detectada: {final_url}")
                    download_url = final_url
                
                # Esperar 5 segundos para que cargue el botón
                print("Esperando 5 segundos para que cargue el botón...")
                time.sleep(5)
                
                # Parsear HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Método 1: Buscar el botón específico de descarga de Uptodown (PRIORIDAD MÁXIMA)
                # Buscar por ID específico
                download_button = soup.find('button', id='detail-download-button')
                if download_button and download_button.get('data-url'):
                    data_url = download_button['data-url']
                    # Construir la URL completa
                    if data_url.startswith('/'):
                        data_url = data_url[1:]  # Quitar / inicial si existe
                    
                    direct_url = f"https://dw.uptodown.net/dwn/{data_url}"
                    print(f"Enlace encontrado (Método 1 - ID button): {direct_url}")
                    return direct_url

                # Método 2: Buscar por clases específicas del botón
                download_button = soup.find('button', class_=re.compile(r'button.*download', re.IGNORECASE))
                if download_button and download_button.get('data-url'):
                    data_url = download_button['data-url']
                    if data_url.startswith('/'):
                        data_url = data_url[1:]
                    
                    direct_url = f"https://dw.uptodown.net/dwn/{data_url}"
                    print(f"Enlace encontrado (Método 2 - Clase button): {direct_url}")
                    return direct_url

                # Método 3: Buscar cualquier elemento con data-url que contenga "Download"
                elements_with_data_url = soup.find_all(attrs={'data-url': True})
                for element in elements_with_data_url:
                    element_text = element.get_text()
                    if re.search(r'Download|Descargar', element_text, re.IGNORECASE):
                        data_url = element['data-url']
                        if data_url.startswith('/'):
                            data_url = data_url[1:]
                        
                        direct_url = f"https://dw.uptodown.net/dwn/{data_url}"
                        print(f"Enlace encontrado (Método 3 - Data-URL): {direct_url}")
                        return direct_url

                # Método 4: Buscar enlaces directos ya completos de dw.uptodown.net (fallback)
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Buscar específicamente enlaces completos a dw.uptodown.net que terminen en .apk
                    if ('dw.uptodown.net' in href and href.endswith('.apk')):
                        print(f"Enlace encontrado (Método 4 - dw.uptodown.net completo): {href}")
                        return href

                # Método 3: Buscar botón verde por clases CSS típicas de Uptodown
                green_button_classes = [
                    'download-button', 'btn-download', 'download-link', 'main-download', 
                    'button-download', 'green-button', 'primary-button', 'download-btn'
                ]
                
                for class_name in green_button_classes:
                    elements = soup.find_all(['a', 'button', 'div'], class_=re.compile(class_name, re.IGNORECASE))
                    for element in elements:
                        # Verificar si contiene texto relacionado con descarga
                        element_text = element.get_text()
                        if re.search(r'Download|Descargar', element_text, re.IGNORECASE):
                            if element.name == 'a' and element.get('href'):
                                href = element['href']
                                if 'dw.uptodown.net' in href:
                                    print(f"Enlace encontrado (Método 3 - Clase verde): {href}")
                                    return href
                            
                            # Buscar enlace padre
                            parent_link = element.find_parent('a')
                            if parent_link and parent_link.get('href'):
                                href = parent_link['href']
                                if 'dw.uptodown.net' in href:
                                    print(f"Enlace encontrado (Método 3 - Parent clase): {href}")
                                    return href

                # Método 4: Buscar enlaces directos con "Download" 
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    link_text = link.get_text().strip()
                    
                    # Debe contener "Download" y ser enlace de dw.uptodown.net
                    if (re.search(r'\bDownload\b', link_text, re.IGNORECASE) and 
                        'dw.uptodown.net' in href):
                        print(f"Enlace encontrado (Método 4 - Download directo): {href}")
                        return href

                # Método 5: Buscar en JavaScript y atributos especiales
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # Buscar URLs de dw.uptodown.net en JavaScript
                        matches = re.findall(r'(https?://dw\.uptodown\.net/[^\s"\']+\.apk)', script.string)
                        if matches:
                            print(f"Enlace encontrado (Método 5 - JavaScript): {matches[0]}")
                            return matches[0]

                # Método 6: Buscar en atributos de datos y onclick
                for element in soup.find_all(attrs={'data-url': True}):
                    data_url = element['data-url']
                    if 'dw.uptodown.net' in data_url and data_url.endswith('.apk'):
                        print(f"Enlace encontrado (Método 6 - Data URL): {data_url}")
                        return data_url

                for element in soup.find_all(attrs={'onclick': True}):
                    onclick = element['onclick']
                    # Buscar URLs de dw.uptodown.net en eventos onclick
                    url_matches = re.findall(r'(https?://dw\.uptodown\.net/[^\s"\')]+\.apk)', onclick)
                    for match in url_matches:
                        print(f"Enlace encontrado (Método 6 - OnClick): {match}")
                        return match

                # Método 7: Búsqueda amplia de cualquier enlace .apk externo (fallback)
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if (href.startswith('http') and 
                        href.endswith('.apk') and 
                        'uptodown.com' not in href):
                        print(f"Enlace encontrado (Método 7 - APK externo): {href}")
                        return href

                # Si no se encontró nada en el primer intento, esperar más tiempo
                if attempt == 0:
                    print("No se encontró enlace, esperando más tiempo...")
                    time.sleep(3)
                    continue

            except Exception as e:
                print(f"Error en intento {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    raise Exception(f"Error Uptodown después de {retries} intentos: {str(e)}")
                time.sleep(3)

        raise Exception("No se encontró enlace directo después de varios intentos")

    @staticmethod
    def extract_app_info(url):
        """Extrae información de la app desde la URL"""
        scraper = UptodownHandler.get_scraper()
        
        try:
            # Si es URL de descarga, obtener la URL original
            original_url = url.replace('/download', '') if '/download' in url else url
            
            response = scraper.get(original_url, allow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer título
            title = "APK"
            # Buscar en diferentes elementos típicos de Uptodown
            title_selectors = [
                'h1',
                '.app-name',
                '.detail-app-name',
                'title'
            ]
            
            for selector in title_selectors:
                if '.' in selector:
                    title_element = soup.find(class_=selector.replace('.', ''))
                else:
                    title_element = soup.find(selector)
                
                if title_element:
                    title = title_element.get_text().strip()
                    break
            
            # Limpiar el título (remover "para Android" y similar)
            title = re.sub(r'\s+(para|for)\s+Android.*$', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s+- Uptodown.*$', '', title, flags=re.IGNORECASE)
            
            # Extraer versión
            version = "Unknown"
            version_selectors = [
                '.version',
                '.app-version',
                '.detail-app-version'
            ]
            
            for selector in version_selectors:
                version_element = soup.find(class_=selector.replace('.', ''))
                if version_element:
                    version_text = version_element.get_text().strip()
                    version_match = re.search(r'v?(\d+\.\d+[\.\d]*)', version_text)
                    if version_match:
                        version = version_match.group(1)
                        break
            
            # Si no se encontró versión, buscar en el título
            if version == "Unknown":
                version_match = re.search(r'v?(\d+\.\d+[\.\d]*)', title)
                if version_match:
                    version = version_match.group(1)
            
            return {
                'title': title,
                'version': version,
                'source': 'Uptodown'
            }
            
        except Exception as e:
            return {
                'title': 'APK Download',
                'version': 'Unknown',
                'source': 'Uptodown',
                'error': str(e)
            }

    @staticmethod
    def get_download_info(url):
        """Obtiene tanto el enlace directo como la información de la app"""
        try:
            direct_link = UptodownHandler.get_direct_link(url)
            app_info = UptodownHandler.extract_app_info(url)
            
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
    # Ejemplo con la URL de Google Drive que proporcionaste
    test_url = "https://google-drive.uptodown.com/android"
    
    print("Probando Uptodown Handler...")
    print(f"URL original: {test_url}")
    print(f"URL normalizada: {UptodownHandler.normalize_url(test_url)}")
    
    # Verificar si es un enlace de Uptodown
    if UptodownHandler.is_uptodown_link(test_url):
        print("✅ Es un enlace de Uptodown")
        
        # Obtener información y enlace de descarga
        result = UptodownHandler.get_download_info(test_url)
        
        if result['success']:
            print("✅ Descarga exitosa!")
            print(f"📱 App: {result['app_info']['title']}")
            print(f"📋 Versión: {result['app_info']['version']}")
            print(f"🔗 Enlace directo: {result['direct_link']}")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("❌ No es un enlace de Uptodown")