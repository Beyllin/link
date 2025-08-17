import re
import time
import json
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from base64 import b64decode

class MediaFireHandler:
    @staticmethod
    def is_mediafire_link(url):
        domain = urlparse(url).netloc.lower()
        return 'mediafire.com' in domain

    @staticmethod
    def get_scraper():
        return cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False,
            'desktop': True,
        })

    @staticmethod
    def extract_file_id(url):
        patterns = [
            r'/file/([a-z0-9]+)/',
            r'\?([a-z0-9]+)$',
            r'file/([a-z0-9]+)$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def get_direct_link(url, retries=3):
        scraper = MediaFireHandler.get_scraper()
        
        for attempt in range(retries):
            try:
                # Método 1: Extraer de la API
                file_id = MediaFireHandler.extract_file_id(url)
                if file_id:
                    api_url = f"https://www.mediafire.com/api/1.5/file/get_links.php?quickkey={file_id}&link_type=direct_download"
                    response = scraper.get(api_url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('response', {}).get('links', [{}])[0].get('direct_download'):
                            return data['response']['links'][0]['direct_download']

                # Método 2: Scraping mejorado con delays
                time.sleep(1)
                response = scraper.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar en el botón de descarga
                download_btn = soup.find('a', {'id': 'downloadButton'})
                if download_btn:
                    if download_btn.get('href', '').startswith('http'):
                        return download_btn['href']
                    if download_btn.get('data-scrambled-url'):
                        try:
                            return b64decode(download_btn['data-scrambled-url']).decode('utf-8')
                        except:
                            pass

                # Método 3: Buscar en scripts JavaScript
                for script in soup.find_all('script'):
                    if script.string and 'downloadUrl' in script.string:
                        match = re.search(r'downloadUrl\s*:\s*["\'](https?://[^"\']+)', script.string)
                        if match:
                            return match.group(1)

                # Método 4: Patrón de descarga directa
                matches = re.findall(r'(https?://download\d*\.mediafire\.com/\S+)', response.text)
                if matches:
                    return matches[0]

            except Exception as e:
                if attempt == retries - 1:
                    raise Exception(f"Error MediaFire: {str(e)}")
                time.sleep(2)

        raise Exception("No se encontró enlace directo después de varios intentos")

    @staticmethod
    def process_folder(url, max_files=15):
        scraper = MediaFireHandler.get_scraper()
        try:
            # Extraer folder_key
            folder_key = url.split('/folder/')[1].split('/')[0]
            
            # Intentar con la API primero
            api_url = f"https://www.mediafire.com/api/1.5/folder/get_content.php?folder_key={folder_key}&content_type=files&response_format=json"
            response = scraper.get(api_url)
            
            file_urls = []
            if response.status_code == 200:
                data = response.json()
                files = data.get('response', {}).get('folder_content', {}).get('files', [])
                if files:
                    file_urls = [f"https://www.mediafire.com/file/{file['quickkey']}" for file in files]

            # Si la API falla o no devuelve resultados, hacer scraping HTML
            if not file_urls:
                response = scraper.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar enlaces en la tabla
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/file/' in href:
                        if href.startswith('/'):
                            href = f"https://www.mediafire.com{href}"
                        file_urls.append(href)
            
            # Eliminar duplicados manteniendo el orden
            seen = set()
            unique_files = [x for x in file_urls if not (x in seen or seen.add(x))]
            
            return unique_files[:max_files]

        except Exception as e:
            raise Exception(f"Error al procesar carpeta: {str(e)}")