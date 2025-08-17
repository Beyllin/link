import re
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

class FilmAffinityHandler:
    @staticmethod
    def is_filmaffinity_link(url):
        """Detecta si la URL es de FilmAffinity (móvil o escritorio)"""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            path = parsed.path
            
            # Verificar dominios de FilmAffinity
            valid_domains = ['filmaffinity.com', 'm.filmaffinity.com', 'www.filmaffinity.com']
            domain_match = any(valid_domain in domain for valid_domain in valid_domains)
            
            # Verificar que contenga /film en el path
            path_match = '/film' in path
            
            return domain_match and path_match
        except Exception:
            return False

    @staticmethod
    def get_driver():
        """Configura y retorna un driver de Chrome optimizado"""
        options = Options()
        options.add_argument('--headless')  # Ejecutar en segundo plano
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1')
        options.add_argument('--accept-language=es-ES,es;q=0.9,en;q=0.8')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            raise Exception(f"Error al inicializar ChromeDriver: {str(e)}. Asegúrate de tener ChromeDriver instalado.")

    @staticmethod
    def clean_name(name):
        """Limpia nombres eliminando guiones y puntos para hashtags"""
        if not name:
            return ""
        # Eliminar guiones, puntos, apóstrofes y caracteres especiales
        cleaned = re.sub(r'[-.\(\)\[\],\']', '', name.strip())
        # Eliminar espacios extra y capitalizar cada palabra
        words = cleaned.split()
        return ''.join(word.capitalize() for word in words if word)

    @staticmethod
    def clean_genre(genre):
        """Limpia y normaliza géneros según las reglas especificadas"""
        if not genre:
            return None
            
        genre = genre.strip()
        
        # Aplicar reglas de cambio de géneros
        genre_mappings = {
            'Fantástico': 'Fantasía',
            'Aventuras': 'Aventura', 
            'Suspense': 'Suspenso',
            'Autismo / Asperger': 'Autismo',
            'Zonas frías/polares': 'ZonasFrías',
            'Trabajo/empleo': 'Trabajo'
        }
        
        # Cambiar el género si está en el mapeo
        for old_genre, new_genre in genre_mappings.items():
            if genre == old_genre:
                genre = new_genre
                break
        
        # Caso especial: géneros que se dividen en dos
        if 'perros' in genre.lower() and 'lobos' in genre.lower():
            return ['Perros', 'Lobos']
        elif 'colegios' in genre.lower() and 'universidad' in genre.lower():
            return ['Colegios', 'Universidad']  
        elif 'posesiones' in genre.lower() and 'exorcismos' in genre.lower():
            return ['Posesiones', 'Exorcismos']
        elif 'secuestros' in genre.lower() and 'desapariciones' in genre.lower():
            return ['Secuestros', 'Desapariciones']
        elif 'trenes' in genre.lower() and 'metros' in genre.lower():
            return ['Trenes', 'Metros']
        elif 'robos' in genre.lower() and 'atracos' in genre.lower():
            return ['Robos', 'Atracos']
        elif 'drama judicial' in genre.lower() and ('abogados' in genre.lower() or 'abogados/as' in genre.lower()):
            return ['DramaJudicial']
        
        # Eliminar el género "3-D" completamente
        if genre == '3-D':
            return None
            
        # Limpiar espacios y capitalizar cada palabra
        words = genre.split()
        return ''.join(word.capitalize() for word in words if word)

    @staticmethod
    def extract_movie_info(url, retries=2):
        driver = None
        
        for attempt in range(retries):
            try:
                driver = FilmAffinityHandler.get_driver()
                
                print(f"DEBUG - Intento {attempt + 1}: Accediendo a {url}")
                driver.get(url)
                
                # Esperar a que la página cargue completamente
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Esperar un poco más para asegurar que todo el contenido dinámico cargue
                time.sleep(3)
                
                # Obtener el HTML de la página
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                print(f"DEBUG - Título de la página: {soup.title.string if soup.title else 'No title'}")
                
                # Extraer géneros usando múltiples estrategias
                genres = []
                
                # Estrategia 1: Buscar por dt con texto "Género"
                genre_dts = soup.find_all('dt', string=lambda text: text and 'género' in text.lower())
                for genre_dt in genre_dts:
                    genre_dd = genre_dt.find_next_sibling('dd')
                    if genre_dd:
                        # Buscar enlaces en el dd
                        genre_links = genre_dd.find_all('a')
                        for link in genre_links:
                            genre_text = link.get_text().strip()
                            if genre_text:
                                cleaned_genres = FilmAffinityHandler.clean_genre(genre_text)
                                if cleaned_genres:
                                    # Si es una lista (caso Perros/Lobos), agregar cada elemento
                                    if isinstance(cleaned_genres, list):
                                        for single_genre in cleaned_genres:
                                            if single_genre not in genres:
                                                genres.append(single_genre)
                                    # Si es un string normal, agregar directamente
                                    else:
                                        if cleaned_genres not in genres:
                                            genres.append(cleaned_genres)
                        
                        # Si no hay enlaces, buscar texto directo
                        if not genre_links:
                            genre_text = genre_dd.get_text().strip()
                            # Dividir por comas o espacios múltiples
                            genre_parts = re.split(r'[,\s]{2,}', genre_text)
                            for part in genre_parts:
                                part = part.strip()
                                if part:
                                    cleaned_genres = FilmAffinityHandler.clean_genre(part)
                                    if cleaned_genres:
                                        if isinstance(cleaned_genres, list):
                                            for single_genre in cleaned_genres:
                                                if single_genre not in genres:
                                                    genres.append(single_genre)
                                        else:
                                            if cleaned_genres not in genres:
                                                genres.append(cleaned_genres)
                
                # Estrategia 2: Buscar enlaces que contengan "/genre/"
                if not genres:
                    genre_links = soup.find_all('a', href=re.compile(r'/genre/'))
                    for link in genre_links[:8]:  # Limitar para evitar spam
                        genre_text = link.get_text().strip()
                        if genre_text and genre_text.lower() not in ['ver más', 'more', 'género', '']:
                            cleaned_genres = FilmAffinityHandler.clean_genre(genre_text)
                            if cleaned_genres:
                                if isinstance(cleaned_genres, list):
                                    for single_genre in cleaned_genres:
                                        if single_genre not in genres:
                                            genres.append(single_genre)
                                else:
                                    if cleaned_genres not in genres:
                                        genres.append(cleaned_genres)
                
                # Estrategia 3: Buscar en meta tags
                if not genres:
                    meta_desc = soup.find('meta', {'name': 'description'})
                    if meta_desc:
                        content = meta_desc.get('content', '')
                        if 'Género:' in content:
                            genre_part = content.split('Género:')[1].split('|')[0].strip()
                            genre_words = re.findall(r'\b[A-ZÁÉÍÓÚ][a-záéíóú]+\b', genre_part)
                            for word in genre_words[:5]:  # Máximo 5 géneros
                                cleaned_genres = FilmAffinityHandler.clean_genre(word)
                                if cleaned_genres:
                                    if isinstance(cleaned_genres, list):
                                        for single_genre in cleaned_genres:
                                            if single_genre not in genres:
                                                genres.append(single_genre)
                                    else:
                                        if cleaned_genres not in genres:
                                            genres.append(cleaned_genres)
                
                print(f"DEBUG - Géneros encontrados: {genres}")
                
                # Extraer reparto (primeros 6 actores)
                actors = []
                is_animation = False
                
                # Verificar si es película de animación (volviendo a la lógica original)
                if 'Animación' in genres or 'Animacion' in genres:
                    is_animation = True
                    print("DEBUG - Película de animación detectada, omitiendo extracción de actores")
                
                if not is_animation:
                    # Estrategia 1: Buscar por dt con texto "Reparto"
                    cast_dts = soup.find_all('dt', string=lambda text: text and 'reparto' in text.lower())
                    for cast_dt in cast_dts:
                        cast_dd = cast_dt.find_next_sibling('dd')
                        if cast_dd:
                            # Verificar si el contenido del reparto contiene "Animación"
                            cast_content = cast_dd.get_text().lower()
                            if 'animación' in cast_content or 'animacion' in cast_content:
                                is_animation = True
                                print("DEBUG - 'Animación' encontrada en reparto, omitiendo actores")
                                break
                            
                            actor_links = cast_dd.find_all('a')
                            for link in actor_links[:6]:  # Solo los primeros 6
                                actor_name = link.get_text().strip()
                                if actor_name and len(actor_name) > 2:
                                    cleaned_actor = FilmAffinityHandler.clean_name(actor_name)
                                    if cleaned_actor and cleaned_actor not in actors:
                                        actors.append(cleaned_actor)
                            
                            # Si no hay suficientes actores con enlaces, buscar en texto
                            if len(actors) < 3:
                                cast_text = cast_dd.get_text()
                                # Buscar nombres que parezcan actores (formato "Nombre Apellido")
                                potential_actors = re.findall(r'\b[A-ZÁÉÍÓÚ][a-záéíóú]+\s+[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)?\b', cast_text)
                                for actor_name in potential_actors[:6]:
                                    if len(actors) >= 6:
                                        break
                                    cleaned_actor = FilmAffinityHandler.clean_name(actor_name)
                                    if cleaned_actor and cleaned_actor not in actors:
                                        actors.append(cleaned_actor)
                
                # Estrategia 2: Buscar enlaces que contengan "/person.php" o "/person/" (solo si no es animación)
                if not is_animation and len(actors) < 6:
                    person_patterns = [r'/person\.php', r'/person/']
                    for pattern in person_patterns:
                        person_links = soup.find_all('a', href=re.compile(pattern))
                        for link in person_links:
                            if len(actors) >= 6:
                                break
                            actor_name = link.get_text().strip()
                            if actor_name and len(actor_name) > 2 and len(actor_name) < 50:
                                cleaned_actor = FilmAffinityHandler.clean_name(actor_name)
                                if cleaned_actor and cleaned_actor not in actors:
                                    actors.append(cleaned_actor)
                
                # Estrategia 3: Buscar en meta description (solo si no es animación)
                if not is_animation and len(actors) < 3:
                    meta_desc = soup.find('meta', {'name': 'description'})
                    if meta_desc:
                        content = meta_desc.get('content', '')
                        # Buscar patrones como "con Nombre Apellido, Nombre2 Apellido2"
                        potential_actors = re.findall(r'\b[A-ZÁÉÍÓÚ][a-záéíóú]+\s+[A-ZÁÉÍÓÚ][a-záéíóú]+\b', content)
                        for actor_name in potential_actors[:6]:
                            if len(actors) >= 6:
                                break
                            # Filtrar nombres que no sean lugares o cosas comunes
                            if not any(word in actor_name.lower() for word in ['nueva', 'york', 'estados', 'unidos', 'america', 'films']):
                                cleaned_actor = FilmAffinityHandler.clean_name(actor_name)
                                if cleaned_actor and len(cleaned_actor) > 3 and cleaned_actor not in actors:
                                    actors.append(cleaned_actor)
                
                if is_animation:
                    print("DEBUG - Película de animación: no se agregaron actores")
                else:
                    print(f"DEBUG - Actores encontrados: {actors}")
                
                # Formatear resultado
                if actors or genres:
                    result_parts = ['#Películas', '#MP4']
                    
                    # Agregar actores
                    for actor in actors[:6]:  # Máximo 6 actores
                        result_parts.append(f'#{actor}')
                    
                    # Agregar géneros en el orden que aparecen
                    for genre in genres:
                        result_parts.append(f'#{genre}')
                    
                    result = ' '.join(result_parts)
                    print(f"DEBUG - Resultado final: {result}")
                    return result
                else:
                    print("DEBUG - No se encontraron géneros ni actores")
                    raise Exception("No se encontraron géneros ni actores en la página")
                    
            except Exception as e:
                print(f"DEBUG - Error en intento {attempt + 1}: {str(e)}")
                if attempt == retries - 1:
                    raise Exception(f"Error FilmAffinity: {str(e)}")
                time.sleep(3)
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
        
        raise Exception("No se pudo extraer información después de varios intentos")

    @staticmethod
    def process_url(url):
        """Método principal para procesar una URL de FilmAffinity"""
        try:
            if not FilmAffinityHandler.is_filmaffinity_link(url):
                raise Exception("La URL no es de FilmAffinity")
            
            return FilmAffinityHandler.extract_movie_info(url)
            
        except Exception as e:
            raise Exception(f"Error al procesar URL de FilmAffinity: {str(e)}")