# a2zapk.py - Versión mejorada basada en AZ2APK.txt funcional
import time
import re
import logging
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class A2ZAPKHandler:
    @staticmethod
    def is_a2zapk_link(url):
        """Verifica si el enlace es de A2ZAPK"""
        domain = urlparse(url).netloc.lower()
        return 'a2zapk.io' in domain

    @staticmethod
    def _setup_driver():
        """Configuración del driver Chrome - Simplificada como en AZ2APK.txt"""
        chrome_options = Options()
        
        # Configuraciones básicas para Ubuntu/servidor
        chrome_options.add_argument("--headless=new")  # Comentar esta línea para debug
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Configuraciones anti-detección (como en AZ2APK.txt)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-infobars')
        
        # User-Agent móvil (exactamente como en AZ2APK.txt)
        mobile_ua = "Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        chrome_options.add_argument(f'user-agent={mobile_ua}')
        
        # REMOVIDAS las configuraciones que podrían estar causando problemas:
        # --disable-javascript, --disable-images, --disable-plugins
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver

    @staticmethod
    def _extract_link_ultrafast(driver):
        """Extracción ultrarrápida exactamente como en AZ2APK.txt"""
        try:
            logger.info("Iniciando extracción ultrarrápida...")
            
            # Búsqueda múltiple simultánea (exactamente como en AZ2APK.txt)
            potential_selectors = [
                "//span[contains(text(), 'DOWNLOAD')]/ancestor::a",
                "//span[contains(text(), 'Download')]/ancestor::a", 
                "//a[contains(@href, '.apk')]",
                "//a[contains(text(), 'download') and contains(@href, 'http')]",
                "//a[contains(@class, 'download')]",
                "//button[contains(text(), 'download')]/parent::a",
            ]
            
            # Buscar todos los elementos posibles de una vez
            for selector in potential_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        href = elements[0].get_attribute('href')
                        if href and 'http' in href and href != driver.current_url:
                            logger.info(f"Enlace encontrado con selector: {selector}")
                            return href
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
            
            # Fallback: buscar CUALQUIER enlace (como en AZ2APK.txt)
            logger.info("Iniciando búsqueda fallback...")
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links[:10]:  # Solo primeros 10 para velocidad (como en AZ2APK.txt)
                try:
                    href = link.get_attribute('href')
                    text = link.text.lower()
                    
                    if href and href != driver.current_url:
                        if any(pattern in href.lower() for pattern in ['.apk', 'download', 'file']):
                            logger.info(f"Enlace encontrado por patrón URL: {href}")
                            return href
                        if href and any(pattern in text for pattern in ['download', 'get', 'direct']):
                            logger.info(f"Enlace encontrado por patrón texto: {href}")
                            return href
                except Exception as e:
                    logger.debug(f"Error procesando enlace: {e}")
                    continue
                    
            logger.warning("No se encontró enlace con extracción ultrarrápida")
            return None
            
        except Exception as e:
            logger.error(f"Error en extracción ultrarrápida: {e}")
            return None

    @staticmethod
    def _extract_with_regex_emergency(driver):
        """Búsqueda de emergencia como en AZ2APK.txt"""
        try:
            logger.info("Iniciando búsqueda de emergencia...")
            page_source = driver.page_source
            
            # Patrones exactos de AZ2APK.txt
            patterns = [
                r'href=["\']([^"\']*\.apk[^"\']*)["\']',
                r'href=["\']([^"\']*download[^"\']*)["\']',
                r'href=["\']([^"\']*file[^"\']*)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if match and 'http' in match and match != driver.current_url:
                            logger.info(f"Enlace encontrado con regex: {match}")
                            return match
            
            logger.warning("No se encontró enlace con búsqueda de emergencia")
            return None
                        
        except Exception as e:
            logger.error(f"Error en búsqueda de emergencia: {e}")
            return None

    @staticmethod
    def _try_duplicate_tab(driver, original_window):
        """Duplicación de pestaña como en AZ2APK.txt"""
        try:
            logger.info("Intentando duplicar pestaña...")
            duplicated = False
            
            # Método 1: Ctrl+Shift+K (como en AZ2APK.txt)
            try:
                ActionChains(driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys('k').key_up(Keys.SHIFT).key_up(Keys.CONTROL).perform()
                time.sleep(0.5)
                if len(driver.window_handles) > 1:
                    duplicated = True
                    logger.info("✅ Duplicación exitosa con Ctrl+Shift+K")
            except Exception as e:
                logger.debug(f"Fallo método Ctrl+Shift+K: {e}")
            
            # Método 2: JavaScript (como en AZ2APK.txt)
            if not duplicated:
                try:
                    driver.execute_script("window.open(window.location.href, '_blank');")
                    time.sleep(0.5)
                    if len(driver.window_handles) > 1:
                        duplicated = True
                        logger.info("✅ Duplicación exitosa con JavaScript")
                except Exception as e:
                    logger.debug(f"Fallo método JavaScript: {e}")
            
            return duplicated
            
        except Exception as e:
            logger.error(f"Error en duplicación de pestaña: {e}")
            return False

    @staticmethod
    def _distraction_strategy(driver, original_window):
        """Estrategia de distracción exactamente como en AZ2APK.txt"""
        try:
            logger.info("🎭 EJECUTANDO ESTRATEGIA DE DISTRACCIÓN...")
            
            # Duplicar pestaña
            duplicated = A2ZAPKHandler._try_duplicate_tab(driver, original_window)
            
            if not duplicated:
                logger.warning("❌ DUPLICACIÓN AUTOMÁTICA FALLÓ")
                # En modo headless no podemos pedir input manual
                return False
            
            # Ir a la pestaña duplicada por 5 segundos (DISTRACCIÓN)
            logger.info("🎭 FASE DE DISTRACCIÓN: Cambiando a pestaña duplicada...")
            
            new_windows = [window for window in driver.window_handles if window != original_window]
            if new_windows:
                duplicated_window = new_windows[0]
                driver.switch_to.window(duplicated_window)
                logger.info(f"✅ En pestaña duplicada: {duplicated_window}")
                
                # DISTRACCIÓN: Estar 5 segundos en la duplicada
                logger.info("⏳ DISTRAYENDO por 5 segundos en pestaña duplicada...")
                time.sleep(5)
                
                # REGRESAR RÁPIDAMENTE A LA ORIGINAL
                logger.info("🏃‍♂️ ¡REGRESANDO VELOCMENTE A LA ORIGINAL!")
                driver.switch_to.window(original_window)
                
                return True
            else:
                logger.warning("❌ No se encontró pestaña duplicada")
                return False
                
        except Exception as e:
            logger.error(f"Error en estrategia de distracción: {e}")
            # Asegurarse de volver a la ventana original
            try:
                driver.switch_to.window(original_window)
            except:
                pass
            return False

    @staticmethod
    def get_direct_link(url, retries=2):
        """
        Obtiene el enlace directo siguiendo exactamente la estrategia de AZ2APK.txt
        """
        driver = None
        try:
            logger.info(f"Procesando enlace A2ZAPK: {url}")
            
            # Extraer ID y construir URL de descarga si es necesario
            if '/dload/' not in url:
                match = re.search(r'/(\d+)-', url)
                if match:
                    file_id = match.group(1)
                    url = f"https://a2zapk.io/dload/{file_id}/"
                    logger.info(f"URL convertida a formato dload: {url}")

            driver = A2ZAPKHandler._setup_driver()
            wait = WebDriverWait(driver, 10)
            
            # Paso 1: Navegar a la página inicial (como en AZ2APK.txt)
            logger.info("🚀 Accediendo a la página inicial...")
            driver.get(url)
            time.sleep(3)  # Mismo tiempo que AZ2APK.txt
            
            # Paso 2: Localizar el botón de descarga inicial (como en AZ2APK.txt)
            logger.info("🔍 Localizando botón de descarga inicial...")
            
            try:
                download_button = wait.until(
                    EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Direct Download APK"))
                )
            except:
                # Fallback con otros selectores
                download_selectors = [
                    "//a[contains(@onclick, 'go(') and contains(., 'Download')]",
                    "//a[contains(text(), 'DOWNLOAD')]",
                    "//button[contains(text(), 'Download')]/ancestor::a",
                    "//a[contains(@class, 'download')]"
                ]
                
                download_button = None
                for selector in download_selectors:
                    try:
                        download_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        logger.info(f"✅ Botón encontrado con selector: {selector}")
                        break
                    except:
                        continue
                
                if not download_button:
                    raise Exception("No se encontró botón de descarga inicial")
            
            # Guardar ventana original (como en AZ2APK.txt)
            original_window = driver.current_window_handle
            logger.info(f"📝 Ventana original guardada: {original_window}")
            
            # Paso 3: Click y duplicación inmediata (como en AZ2APK.txt)
            logger.info("🎯 Haciendo clic en descarga...")
            download_button.click()
            
            # Esperar 0.5 segundo para que empiece a cargar (como en AZ2APK.txt)
            logger.info("Esperando 0.5 segundo...")
            time.sleep(0.5)
            
            # Ejecutar estrategia de distracción
            distraction_success = A2ZAPKHandler._distraction_strategy(driver, original_window)
            
            # Paso 4: EXTRACCIÓN ULTRARRÁPIDA (como en AZ2APK.txt)
            logger.info("⚡ INICIANDO EXTRACCIÓN ULTRARRÁPIDA (1.5 seg max)...")
            start_time = time.time()
            
            # Asegurarse de estar en ventana original
            try:
                driver.switch_to.window(original_window)
            except:
                pass
            
            # Verificar URL actual
            current_url = driver.current_url
            logger.info(f"🔍 URL original ahora: {current_url}")
            
            # EXTRACCIÓN ULTRARRÁPIDA
            download_link = A2ZAPKHandler._extract_link_ultrafast(driver)
            
            extraction_time = time.time() - start_time
            logger.info(f"⏱️ Tiempo de extracción: {extraction_time:.2f} segundos")
            
            if download_link:
                logger.info(f"🎉 ¡ENLACE EXTRAÍDO!: {download_link}")
                
                # Validar que el enlace sea válido
                if download_link.startswith('http') and download_link != url and download_link != current_url:
                    # Información adicional (como en AZ2APK.txt)
                    if '/file/' in current_url:
                        logger.info("✅ Confirmado: Estábamos en página final (/file/)")
                    else:
                        logger.info("⚠️ Nota: No se detectó /file/ en URL, pero enlace extraído")
                    
                    return download_link
                else:
                    logger.warning(f"Enlace no válido: {download_link}")
                    raise Exception("Enlace extraído no es válido")
            else:
                logger.info("❌ No se pudo extraer enlace en tiempo límite")
                logger.info("🔍 Intentando búsqueda de emergencia...")
                
                # Búsqueda de emergencia (como en AZ2APK.txt)
                emergency_link = A2ZAPKHandler._extract_with_regex_emergency(driver)
                
                if emergency_link:
                    emergency_time = time.time() - start_time
                    logger.info(f"🚨 ENLACE DE EMERGENCIA: {emergency_link}")
                    logger.info(f"⏱️ Tiempo emergencia: {emergency_time:.2f}s")
                    return emergency_link
                else:
                    raise Exception("Ni siquiera la búsqueda de emergencia encontró enlaces")

        except Exception as e:
            logger.error(f"Error en intento: {str(e)}")
            if retries > 0:
                logger.info(f"🔄 Reintentando... ({retries} intentos restantes)")
                time.sleep(3)
                return A2ZAPKHandler.get_direct_link(url, retries-1)
            raise Exception(f"Error al procesar enlace A2ZAPK después de múltiples intentos: {str(e)}")
            
        finally:
            if driver:
                try:
                    # Cerrar pestañas adicionales
                    if len(driver.window_handles) > 1:
                        for handle in driver.window_handles[1:]:
                            try:
                                driver.switch_to.window(handle)
                                driver.close()
                            except:
                                pass
                    driver.quit()
                    logger.info("🚪 Driver cerrado correctamente")
                except Exception as e:
                    logger.warning(f"Error cerrando driver: {e}")

    @staticmethod
    def test_handler():
        """Método de prueba para verificar el funcionamiento del handler"""
        test_url = "https://a2zapk.io/dload/1383009/"  # URL de ejemplo
        
        try:
            logger.info("🧪 Iniciando prueba del A2ZAPKHandler...")
            logger.info("🎭 INICIANDO ESTRATEGIA DE DISTRACCIÓN")
            logger.info("📋 Plan: Click → Duplicar → Distraer 5seg → Regresar → Extraer <1.5seg")
            logger.info("⚡ Extracción optimizada para máxima velocidad")
            logger.info("-" * 60)
            
            result = A2ZAPKHandler.get_direct_link(test_url)
            logger.info(f"✅ Prueba exitosa: {result}")
            
            logger.info("\n" + "="*60)
            logger.info("🎯 PROCESO COMPLETADO - ESTRATEGIA DE DISTRACCIÓN")
            logger.info("🎊 ¡MISIÓN COMPLETADA!")
            logger.info("="*60)
            
            return result
        except Exception as e:
            logger.error(f"❌ Prueba falló: {e}")
            raise