#!/bin/bash

# Variables de configuración
VENV_DIR="venv"
REQUIREMENTS="requirements.txt"
BOT_SCRIPT="main.py"
LOG_FILE="logs/bot.log"  # Cambiado para coincidir con tu logging_handler.py
PID_FILE="bot.pid"
PROJECT_DIR=$(pwd)

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Función para verificar si el bot está corriendo
is_running() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        else
            rm -f $PID_FILE
            return 1
        fi
    else
        return 1
    fi
}

# Función para limpiar procesos huérfanos
cleanup_orphans() {
    info "Limpiando procesos huérfanos..."
    
    # Matar procesos Python relacionados con el bot
    pkill -f "python.*main.py" 2>/dev/null || true
    pkill -f "chromedriver" 2>/dev/null || true
    pkill -f "chrome.*headless" 2>/dev/null || true
    
    # Limpiar archivos temporales
    rm -f $PID_FILE
    
    log "Limpieza completada"
}

# Función para configurar entorno
setup_environment() {
    log "Configurando entorno virtual..."
    
    # Crear venv si no existe
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv $VENV_DIR
        log "Entorno virtual creado"
    fi
    
    # Activar venv
    source $VENV_DIR/bin/activate
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar dependencias
    if [ -f "$REQUIREMENTS" ]; then
        pip install -r $REQUIREMENTS
        log "Dependencias instaladas"
    else
        error "Archivo requirements.txt no encontrado"
        exit 1
    fi
    
    # Verificar Chrome
    if ! command -v google-chrome &> /dev/null; then
        warning "Google Chrome no encontrado. Instalando..."
        sudo apt update
        sudo apt install -y google-chrome-stable
    fi
    
    log "Entorno configurado correctamente"
}

# Función para verificar configuración
check_config() {
    info "Verificando configuración..."
    
    # Verificar archivo .env
    if [ ! -f ".env" ]; then
        error "Archivo .env no encontrado"
        info "Crea un archivo .env con BOT_TOKEN=tu_token_aqui"
        exit 1
    fi
    
    # Verificar TOKEN
    if ! grep -q "BOT_TOKEN=" .env; then
        error "BOT_TOKEN no encontrado en .env"
        exit 1
    fi
    
    # Verificar DISPLAY para modo gráfico
    if [ -z "$DISPLAY" ]; then
        warning "DISPLAY no configurado. Configurando para modo gráfico..."
        export DISPLAY=:0
    fi
    
    log "Configuración verificada"
}

case "$1" in
    start)
        log "🚀 Iniciando bot de Telegram..."
        
        if is_running; then
            warning "El bot ya está corriendo (PID: $(cat $PID_FILE))"
            exit 1
        fi
        
        # Verificar configuración
        check_config
        
        # Activar entorno virtual
        if [ ! -d "$VENV_DIR" ]; then
            setup_environment
        else
            source $VENV_DIR/bin/activate
        fi
        
        # Configurar variables de entorno
        export DISPLAY=:0
        
        # Crear directorio de logs
        mkdir -p logs
        
        # Iniciar bot en background
        nohup python $BOT_SCRIPT > $LOG_FILE 2>&1 &
        BOT_PID=$!
        echo $BOT_PID > $PID_FILE
        
        # Esperar un momento para verificar que inició correctamente
        sleep 3
        
        if is_running; then
            log "✅ Bot iniciado exitosamente (PID: $BOT_PID)"
            info "Ver logs: ./manage_bot.sh logs"
        else
            error "❌ El bot falló al iniciar. Ver logs para más detalles."
            cat $LOG_FILE
            exit 1
        fi
        ;;
        
    stop)
        log "🛑 Deteniendo bot..."
        
        if is_running; then
            PID=$(cat $PID_FILE)
            kill -TERM $PID 2>/dev/null
            
            # Esperar hasta 10 segundos para shutdown graceful
            for i in {1..10}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    break
                fi
                sleep 1
            done
            
            # Si aún está corriendo, forzar cierre
            if ps -p $PID > /dev/null 2>&1; then
                warning "Forzando cierre del bot..."
                kill -9 $PID 2>/dev/null
            fi
            
            rm -f $PID_FILE
            log "✅ Bot detenido"
        else
            warning "El bot no está corriendo"
        fi
        
        # Limpieza adicional
        cleanup_orphans
        ;;
        
    restart)
        log "🔄 Reiniciando bot..."
        $0 stop
        sleep 3
        $0 start
        ;;
        
    rebuild)
        log "🔧 Reconstruyendo entorno completo..."
        
        # Detener bot si está corriendo
        $0 stop
        
        # Limpiar entorno virtual existente
        if [ -d "$VENV_DIR" ]; then
            rm -rf $VENV_DIR
            log "Entorno virtual anterior eliminado"
        fi
        
        # Configurar nuevo entorno
        setup_environment
        
        log "✅ Entorno reconstruido. Usar './manage_bot.sh start' para iniciar"
        ;;
        
    status)
        info "📊 Estado del bot:"
        
        if is_running; then
            PID=$(cat $PID_FILE)
            UPTIME=$(ps -o etime= -p $PID 2>/dev/null | tr -d ' ')
            MEMORY=$(ps -o rss= -p $PID 2>/dev/null | tr -d ' ')
            
            log "✅ Bot CORRIENDO"
            echo "   📍 PID: $PID"
            echo "   ⏱️  Tiempo activo: $UPTIME"
            echo "   💾 Memoria: ${MEMORY}KB"
            echo "   📁 Directorio: $PROJECT_DIR"
            echo "   🖥️  Display: ${DISPLAY:-'No configurado'}"
        else
            error "❌ Bot NO ESTÁ CORRIENDO"
        fi
        
        # Verificar procesos relacionados
        CHROME_PROCESSES=$(pgrep -f chrome | wc -l)
        DRIVER_PROCESSES=$(pgrep -f chromedriver | wc -l)
        
        echo "   🌐 Procesos Chrome: $CHROME_PROCESSES"
        echo "   🚗 Procesos ChromeDriver: $DRIVER_PROCESSES"
        ;;
        
    logs)
        if [ ! -f "$LOG_FILE" ]; then
            error "Archivo de log no encontrado"
            exit 1
        fi
        
        info "📄 Mostrando logs del bot (Ctrl+C para salir):"
        tail -f $LOG_FILE
        ;;
        
    test)
        log "🧪 Ejecutando prueba del sistema..."
        
        # Verificar dependencias
        check_config
        
        # Activar entorno
        if [ -d "$VENV_DIR" ]; then
            source $VENV_DIR/bin/activate
        else
            error "Entorno virtual no encontrado. Ejecutar: ./manage_bot.sh rebuild"
            exit 1
        fi
        
        # Prueba rápida
        export DISPLAY=:0
        python -c "
import sys
print('✅ Python:', sys.version.split()[0])

try:
    from selenium import webdriver
    print('✅ Selenium importado correctamente')
except Exception as e:
    print('❌ Error Selenium:', e)

try:
    from telegram.ext import ApplicationBuilder
    print('✅ python-telegram-bot importado correctamente')
except Exception as e:
    print('❌ Error Telegram:', e)

try:
    import os
    if os.environ.get('DISPLAY'):
        print('✅ DISPLAY configurado:', os.environ.get('DISPLAY'))
    else:
        print('⚠️ DISPLAY no configurado')
except Exception as e:
    print('❌ Error DISPLAY:', e)

# Prueba de Chrome
try:
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('https://www.google.com')
    title = driver.title
    driver.quit()
    print('✅ Chrome funciona correctamente - Título:', title[:30])
except Exception as e:
    print('❌ Error Chrome:', str(e)[:100])
"
        log "Prueba completada"
        ;;
        
    chrome-test)
        log "🧪 Prueba específica de Chrome..."
        
        # Activar entorno
        if [ -d "$VENV_DIR" ]; then
            source $VENV_DIR/bin/activate
        else
            error "Entorno virtual no encontrado"
            exit 1
        fi
        
        export DISPLAY=:0
        
        info "Verificando instalación de Chrome..."
        google-chrome --version || error "Chrome no instalado"
        
        info "Verificando ChromeDriver..."
        python -c "
from webdriver_manager.chrome import ChromeDriverManager
driver_path = ChromeDriverManager().install()
print('ChromeDriver instalado en:', driver_path)
"
        
        info "Prueba básica de Chrome headless..."
        python -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://httpbin.org/user-agent')
    print('✅ Chrome headless funciona')
    driver.quit()
except Exception as e:
    print('❌ Error:', e)
"
        
        if [ -n "$DISPLAY" ]; then
            info "Prueba de Chrome gráfico..."
            python -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.google.com')
    print('✅ Chrome gráfico funciona - Título:', driver.title)
    time.sleep(2)  # Para que puedas verlo
    driver.quit()
except Exception as e:
    print('❌ Error modo gráfico:', e)
"
        fi
        
        log "Prueba de Chrome completada"
        ;;
        
    fix-chrome)
        log "🔧 Arreglando instalación de Chrome..."
        
        # Actualizar sistema
        sudo apt update
        
        # Instalar dependencias de Chrome
        sudo apt install -y \
            google-chrome-stable \
            fonts-liberation \
            libasound2 \
            libatk-bridge2.0-0 \
            libdrm2 \
            libxcomposite1 \
            libxdamage1 \
            libxrandr2 \
            libgbm1 \
            libxss1 \
            libnss3
        
        # Verificar instalación
        google-chrome --version
        
        # Limpiar cache de ChromeDriver
        rm -rf ~/.wdm
        
        log "✅ Chrome reinstalado y configurado"
        ;;
        
    test)
        log "🧪 Ejecutando prueba del sistema..."
        
        # Verificar dependencias
        check_config
        
        # Activar entorno
        if [ -d "$VENV_DIR" ]; then
            source $VENV_DIR/bin/activate
        else
            error "Entorno virtual no encontrado. Ejecutar: ./manage_bot.sh rebuild"
            exit 1
        fi
        
        # Prueba rápida
        export DISPLAY=:0
        python -c "
import sys
print('✅ Python:', sys.version.split()[0])

try:
    from selenium import webdriver
    print('✅ Selenium importado correctamente')
except Exception as e:
    print('❌ Error Selenium:', e)

try:
    from telegram.ext import ApplicationBuilder
    print('✅ python-telegram-bot importado correctamente')
except Exception as e:
    print('❌ Error Telegram:', e)

try:
    import os
    if os.environ.get('DISPLAY'):
        print('✅ DISPLAY configurado:', os.environ.get('DISPLAY'))
    else:
        print('⚠️ DISPLAY no configurado')
except Exception as e:
    print('❌ Error DISPLAY:', e)
"
        log "Prueba completada"
        ;;
        
    clean)
        log "🧹 Limpieza completa del sistema..."
        
        # Detener bot
        $0 stop
        
        # Limpiar procesos
        cleanup_orphans
        
        # Limpiar archivos temporales
        rm -f logs/bot.log*  # Limpiar logs también
        rm -f $PID_FILE
        
        # Limpiar cache de ChromeDriver
        rm -rf ~/.wdm
        
        log "✅ Limpieza completada"
        ;;
        
    install)
        log "📦 Instalación completa del bot..."
        
        # Verificar que estamos en el directorio correcto
        if [ ! -f "main.py" ]; then
            error "main.py no encontrado. ¿Estás en el directorio correcto?"
            exit 1
        fi
        
        # Configurar entorno
        setup_environment
        
        # Crear archivo .env si no existe
        if [ ! -f ".env" ]; then
            info "Creando archivo .env de ejemplo..."
            cat > .env << EOF
BOT_TOKEN=TU_TOKEN_AQUI
TZ=America/New_York
EOF
            warning "⚠️ EDITA EL ARCHIVO .env CON TU TOKEN DE BOT REAL"
        fi
        
        log "✅ Instalación completada"
        info "Pasos siguientes:"
        info "1. Editar .env con tu token real"
        info "2. Ejecutar: ./manage_bot.sh start"
        ;;
        
    *)
        echo -e "${BLUE}🤖 Gestor del Bot de Telegram${NC}"
        echo ""
        echo "Uso: $0 {comando}"
        echo ""
        echo "Comandos principales:"
        echo "  start      - Iniciar bot (equivalente a docker-compose up -d)"
        echo "  stop       - Detener bot (equivalente a docker-compose down)"
        echo "  restart    - Reiniciar bot (equivalente a down + up)"
        echo "  rebuild    - Reconstruir entorno (equivalente a build --no-cache)"
        echo ""
        echo "Comandos de mantenimiento:"
        echo "  status     - Ver estado del bot"
        echo "  logs       - Ver logs en tiempo real"
        echo "  test       - Probar configuración del sistema"
        echo "  clean      - Limpieza completa"
        echo "  install    - Instalación inicial completa"
        echo ""
        echo "Comandos de Chrome:"
        echo "  chrome-test - Prueba específica de Chrome"
        echo "  fix-chrome  - Arreglar instalación de Chrome"
        echo ""
        echo "Ejemplos:"
        echo "  ./manage_bot.sh install      # Primera instalación"
        echo "  ./manage_bot.sh fix-chrome   # Arreglar Chrome"
        echo "  ./manage_bot.sh chrome-test  # Probar Chrome"
        echo "  ./manage_bot.sh start        # Iniciar bot"
        echo "  ./manage_bot.sh logs         # Ver qué está pasando"
        echo ""
        exit 1
        ;;
esac

exit 0