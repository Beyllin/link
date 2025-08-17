import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class MegaUpHandler:
    @staticmethod
    def is_megaup_link(url):
        """Verifica si la URL es de MegaUp"""
        domain = urlparse(url).netloc.lower()
        return 'megaup.net' in domain or 'download.megaup.net' in domain

    @staticmethod
    def _setup_driver(headless=False):
        """Configura el driver de Chrome"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Configuración recomendada
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Usar webdriver-manager para manejar ChromeDriver automáticamente
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(30)
        return driver

    @staticmethod
    def _solve_cloudflare_captcha(driver, max_wait=30):
        """Resuelve el captcha de Cloudflare haciendo clic en el checkbox"""
        try:
            logger.info("Verificando si hay captcha de Cloudflare...")
            
            # Esperar a que la página cargue completamente
            time.sleep(4)  # Tiempo que mencionaste que tarda en aparecer
            
            # Buscar diferentes selectores posibles para el checkbox de Cloudflare
            selectors = [
                'input[type="checkbox"]',
                '#cf-chl-widget-container input[type="checkbox"]',
                '.cf-turnstile input[type="checkbox"]',
                'input.cf-turnstile-response',
                '[data-sitekey] input[type="checkbox"]'
            ]
            
            checkbox = None
            for selector in selectors:
                try:
                    checkboxes = driver.find_elements(By.CSS_SELECTOR, selector)
                    if checkboxes:
                        # Filtrar checkboxes visibles
                        visible_checkboxes = [cb for cb in checkboxes if cb.is_displayed()]
                        if visible_checkboxes:
                            checkbox = visible_checkboxes[0]
                            logger.info(f"Checkbox encontrado con selector: {selector}")
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} no funcionó: {str(e)}")
                    continue
            
            # Si no encontramos checkbox, buscar por iframe (algunos captchas están en iframe)
            if not checkbox:
                try:
                    logger.info("Buscando checkbox en iframe...")
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            driver.switch_to.frame(iframe)
                            checkbox = driver.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
                            if checkbox.is_displayed():
                                logger.info("Checkbox encontrado en iframe")
                                break
                            driver.switch_to.default_content()
                        except:
                            driver.switch_to.default_content()
                            continue
                except Exception as e:
                    logger.debug(f"Error buscando en iframes: {str(e)}")
                    driver.switch_to.default_content()
            
            if checkbox:
                logger.info("Haciendo clic en el checkbox del captcha...")
                
                # Intentar diferentes métodos de clic
                try:
                    # Método 1: Clic directo
                    checkbox.click()
                    logger.info("✔ Clic directo exitoso")
                except:
                    try:
                        # Método 2: Clic con JavaScript
                        driver.execute_script("arguments[0].click();", checkbox)
                        logger.info("✔ Clic con JavaScript exitoso")
                    except:
                        try:
                            # Método 3: Marcar como checked
                            driver.execute_script("arguments[0].checked = true;", checkbox)
                            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", checkbox)
                            logger.info("✔ Checkbox marcado programáticamente")
                        except Exception as e:
                            logger.error(f"No se pudo hacer clic en el checkbox: {str(e)}")
                            return False
                
                # Esperar a que el captcha se resuelva
                logger.info("Esperando resolución del captcha...")
                time.sleep(5)
                
                # Verificar si la página cambió o si ya no hay captcha
                try:
                    driver.switch_to.default_content()
                    # Verificar si ya no hay elementos de captcha
                    captcha_elements = driver.find_elements(By.CSS_SELECTOR, 
                                                          'input[type="checkbox"], .cf-turnstile, #cf-chl-widget-container')
                    if not captcha_elements or not any(elem.is_displayed() for elem in captcha_elements):
                        logger.info("✔ Captcha resuelto exitosamente")
                        return True
                except:
                    pass
                
                # Esperar adicional por si el captcha toma más tiempo
                time.sleep(3)
                return True
            else:
                logger.info("No se encontró checkbox de captcha, continuando...")
                return True
                
        except Exception as e:
            logger.error(f"Error resolviendo captcha: {str(e)}")
            return False

    @staticmethod
    def _click_download_button(driver):
        """Localiza y hace clic en el botón 'DOWNLOAD / VIEW NOW'"""
        try:
            # Esperar a que el botón esté disponible
            download_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(., 'DOWNLOAD / VIEW NOW')]"))
            )
            logger.info("Botón 'DOWNLOAD / VIEW NOW' encontrado")
            
            # Hacer clic con JavaScript para mayor confiabilidad
            driver.execute_script("arguments[0].click();", download_btn)
            logger.info("Click en botón realizado")
            
            return True
        except Exception as e:
            logger.error(f"Error al hacer clic en botón: {str(e)}")
            return False

    @staticmethod
    def _get_final_download_link(driver):
        """Obtiene el enlace de descarga final"""
        try:
            # Esperar a que aparezca el botón final
            final_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "btndownload"))
            )
            logger.info("Botón final encontrado")
            
            # Obtener el enlace del atributo href o de la redirección
            download_link = final_btn.get_attribute('href')
            
            if not download_link:
                logger.info("No se encontró href, intentando con redirección...")
                current_url = driver.current_url
                final_btn.click()
                time.sleep(3)
                download_link = driver.current_url
                driver.get(current_url)  # Volver atrás
                
            if not download_link.startswith('http'):
                raise Exception("Enlace de descarga no válido")
                
            return download_link
        except Exception as e:
            logger.error(f"Error obteniendo enlace final: {str(e)}")
            return None

    @staticmethod
    def get_direct_link(url, retries=2):
        """Obtiene el enlace directo de descarga de MegaUp"""
        driver = None
        try:
            logger.info(f"Procesando enlace MegaUp: {url}")
            driver = MegaUpHandler._setup_driver(headless=True)
            
            # Paso 1: Navegar a la URL
            driver.get(url)
            time.sleep(2)  # Espera inicial
            
            # Paso 2: Hacer clic en el botón principal
            if not MegaUpHandler._click_download_button(driver):
                raise Exception("No se pudo hacer clic en el botón de descarga")
            
            # Paso 3: Resolver captcha de Cloudflare si aparece
            logger.info("Esperando redirección y verificando captcha...")
            time.sleep(3)
            
            if not MegaUpHandler._solve_cloudflare_captcha(driver):
                logger.warning("Problema resolviendo captcha, pero continuando...")
            
            # Paso 4: Espera adicional después del captcha
            time.sleep(3)
            
            # Paso 5: Obtener enlace final
            download_link = MegaUpHandler._get_final_download_link(driver)
            
            if not download_link:
                raise Exception("No se pudo obtener el enlace de descarga final")
            
            logger.info(f"Enlace de descarga obtenido: {download_link}")
            return download_link
            
        except Exception as e:
            logger.error(f"Error en MegaUpHandler: {str(e)}")
            if retries > 0:
                logger.info(f"Reintentando... ({retries} intentos restantes)")
                time.sleep(3)
                return MegaUpHandler.get_direct_link(url, retries-1)
            raise Exception(f"No se pudo obtener el enlace después de {retries+1} intentos")
            
        finally:
            if driver:
                driver.quit()

    @staticmethod
    def test_handler():
        """Método de prueba para verificar el funcionamiento"""
        test_url = "https://megaup.net/c6aed7a14eaaf0343cbef7bc4bcbdcb3/aewrhewarhasdgdsrgrsg.rar"
        driver = None
        try:
            print("=== Iniciando prueba de MegaUpHandler ===")
            
            # Prueba en modo visible para depuración
            driver = MegaUpHandler._setup_driver(headless=False)
            driver.get(test_url)
            
            print("Página cargada. Buscando botón 'DOWNLOAD / VIEW NOW'...")
            time.sleep(2)
            
            if MegaUpHandler._click_download_button(driver):
                print("✔ Botón clickeado exitosamente")
                time.sleep(3)
                
                print("Verificando y resolviendo captcha...")
                if MegaUpHandler._solve_cloudflare_captcha(driver):
                    print("✔ Captcha procesado")
                else:
                    print("⚠ Problema con captcha, continuando...")
                
                time.sleep(3)
                print("Buscando botón final de descarga...")
                download_link = MegaUpHandler._get_final_download_link(driver)
                
                if download_link:
                    print(f"✔ Enlace obtenido: {download_link}")
                    return download_link
                else:
                    print("✖ No se pudo obtener enlace final")
                    return None
            else:
                print("✖ No se pudo hacer clic en el botón")
                return None
                
        except Exception as e:
            print(f"✖ Error en prueba: {str(e)}")
            return None
        finally:
            if driver:
                print("Cerrando navegador en 5 segundos...")
                time.sleep(5)
                driver.quit()

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar prueba
    result = MegaUpHandler.test_handler()
    if result:
        print(f"\n🎉 ¡Éxito! Enlace final: {result}")
    else:
        print("\n❌ La prueba falló")