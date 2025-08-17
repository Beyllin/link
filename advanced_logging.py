import logging
import os
import sys
import time
import threading
import traceback
import psutil
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any
import asyncio
from io import BytesIO

class MirrorLeechBotLogger:
    """Sistema de logging inspirado en mirror-leech-telegram-bot"""
    
    def __init__(self):
        self.bot_start_time = datetime.now()
        self.logger = None
        self.lock = threading.Lock()
        self.log_file_path = 'logs/bot.log'
        self.setup_logging()
        
    def setup_logging(self):
        """Configura el sistema de logging como mirror-leech"""
        # Crear directorio de logs
        os.makedirs('logs', exist_ok=True)
        
        # Configurar logger principal
        self.logger = logging.getLogger('bot')
        self.logger.setLevel(logging.INFO)
        
        # Limpiar handlers existentes
        self.logger.handlers.clear()
        
        # Formato exacto como mirror-leech
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo principal (rotativo)
        file_handler = RotatingFileHandler(
            self.log_file_path,
            maxBytes=50*1024*1024,  # 50 MB como mirror-leech
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # Log inicial del bot
        self.info("Bot Started!")
    
    def info(self, message: str):
        """Log de información"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log de advertencia"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log de error"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log de debug"""
        self.logger.debug(message)
    
    def log_url_processing(self, url: str, user_id: int = None):
        """Registra el procesamiento de una URL"""
        user_info = f" from user {user_id}" if user_id else ""
        self.info(f"Processing URL: {url}{user_info}")
    
    def log_download_start(self, url: str, gid: str = None):
        """Registra inicio de descarga"""
        gid_info = f" - Gid: {gid}" if gid else ""
        self.info(f"Download started: {url}{gid_info}")
    
    def log_download_complete(self, filename: str, gid: str = None):
        """Registra descarga completada"""
        gid_info = f" - Gid: {gid}" if gid else ""
        self.info(f"Download completed: {filename}{gid_info}")
    
    def log_direct_link_generated(self, original_url: str, direct_link: str):
        """Registra generación de enlace directo"""
        self.info(f"Generated direct link for: {original_url}")
        self.info(f"Direct link: {direct_link}")
    
    def log_extraction_start(self, filename: str):
        """Registra inicio de extracción"""
        self.info(f"Extracting: {filename}")
    
    def log_extraction_complete(self, filename: str):
        """Registra extracción completada"""
        self.info(f"Extraction completed: {filename}")
    
    def log_upload_start(self, filename: str, destination: str = None):
        """Registra inicio de subida"""
        dest_info = f" to {destination}" if destination else ""
        self.info(f"Upload started: {filename}{dest_info}")
    
    def log_upload_complete(self, filename: str, path: str = None):
        """Registra subida completada"""
        path_info = f". Path: {path}" if path else ""
        self.info(f"Upload completed: {filename}{path_info}")
    
    def log_task_done(self, task_name: str):
        """Registra tarea completada"""
        self.info(f"Task Done: {task_name}")
    
    def log_cleaning(self, directory: str):
        """Registra limpieza de directorio"""
        self.info(f"Cleaning Download: {directory}")
    
    def log_error_with_details(self, error_msg: str, url: str = None, context: str = None):
        """Registra error con detalles"""
        full_msg = f"ERROR: {error_msg}"
        if url:
            full_msg += f" for URL: {url}"
        if context:
            full_msg += f" in {context}"
        self.error(full_msg)
    
    def log_bot_command(self, command: str, user_id: int, args: list = None):
        """Registra comandos del bot"""
        args_str = f" with args: {args}" if args else ""
        self.info(f"Command /{command} executed by user {user_id}{args_str}")
    
    def log_site_detection(self, url: str, site_name: str):
        """Registra detección de sitio"""
        self.info(f"Site detected: {site_name} for URL: {url}")
    
    def log_user_activity(self, user_id: int, action: str, details: str = None):
        """Registra actividad de usuario"""
        detail_str = f": {details}" if details else ""
        self.info(f"User {user_id} {action}{detail_str}")
    
    def log_system_status(self):
        """Registra estado del sistema"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            self.info(f"System Memory: {memory.percent:.1f}% used")
            self.info(f"Bot Memory: {process_memory.rss // 1024 // 1024} MB")
            self.info(f"CPU Usage: {psutil.cpu_percent():.1f}%")
        except Exception as e:
            self.error(f"Error getting system status: {str(e)}")
    
    def log_exception_with_traceback(self, exception: Exception, context: str = ""):
        """Registra excepción con traceback completo"""
        context_str = f" in {context}" if context else ""
        self.error(f"Exception occurred{context_str}: {str(exception)}")
        
        # Registrar traceback completo
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        for line in tb_lines:
            for subline in line.strip().split('\n'):
                if subline.strip():
                    self.error(f"  {subline}")
    
    def log_async_task_start(self, task_name: str, task_id: str = None):
        """Registra inicio de tarea async"""
        id_str = f" (ID: {task_id})" if task_id else ""
        self.info(f"Async task started: {task_name}{id_str}")
    
    def log_async_task_complete(self, task_name: str, task_id: str = None, duration: float = None):
        """Registra completación de tarea async"""
        id_str = f" (ID: {task_id})" if task_id else ""
        duration_str = f" in {duration:.2f}s" if duration else ""
        self.info(f"Async task completed: {task_name}{id_str}{duration_str}")
    
    def log_restart_sequence(self, stage: str, details: str = None):
        """Registra secuencia de reinicio"""
        detail_str = f": {details}" if details else ""
        self.warning(f"RESTART - {stage}{detail_str}")
    
    def log_service_status(self, service: str, status: str, details: str = None):
        """Registra estado de servicios"""
        detail_str = f" - {details}" if details else ""
        self.info(f"Service {service}: {status}{detail_str}")
    
    def get_log_file_content(self, lines: int = None) -> str:
        """Obtiene contenido completo del archivo de log"""
        try:
            if not os.path.exists(self.log_file_path):
                return "Log file not found"
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                if lines:
                    # Leer todas las líneas y tomar las últimas N
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:])
                else:
                    return f.read()
        except Exception as e:
            return f"Error reading log file: {str(e)}"
    
    def get_log_file_bytes(self) -> BytesIO:
        """Obtiene el archivo de log como bytes para envío por Telegram"""
        try:
            if not os.path.exists(self.log_file_path):
                # Crear archivo temporal con mensaje
                content = "Log file not found"
                return BytesIO(content.encode('utf-8'))
            
            with open(self.log_file_path, 'rb') as f:
                return BytesIO(f.read())
        except Exception as e:
            error_content = f"Error reading log file: {str(e)}"
            return BytesIO(error_content.encode('utf-8'))
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del log"""
        try:
            if not os.path.exists(self.log_file_path):
                return {"error": "Log file not found"}
            
            # Obtener información del archivo
            stat_info = os.stat(self.log_file_path)
            file_size = stat_info.st_size
            modified_time = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Contar líneas y tipos de log
            line_count = 0
            info_count = 0
            warning_count = 0
            error_count = 0
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line_count += 1
                    if ' - INFO - ' in line:
                        info_count += 1
                    elif ' - WARNING - ' in line:
                        warning_count += 1
                    elif ' - ERROR - ' in line:
                        error_count += 1
            
            uptime = datetime.now() - self.bot_start_time
            
            return {
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "total_lines": line_count,
                "info_logs": info_count,
                "warning_logs": warning_count,
                "error_logs": error_count,
                "last_modified": modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                "bot_uptime": str(uptime).split('.')[0],
                "log_file_path": self.log_file_path
            }
        except Exception as e:
            return {"error": f"Error getting log stats: {str(e)}"}
    
    def rotate_logs_manually(self):
        """Rota los logs manualmente"""
        try:
            for handler in self.logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    handler.doRollover()
            self.info("Log rotation completed manually")
            return True
        except Exception as e:
            self.error(f"Error rotating logs: {str(e)}")
            return False
    
    def clear_logs(self):
        """Limpia todos los logs (USAR CON PRECAUCIÓN)"""
        try:
            # Cerrar handlers temporalmente
            for handler in self.logger.handlers[:]:
                if isinstance(handler, RotatingFileHandler):
                    handler.close()
                    self.logger.removeHandler(handler)
            
            # Eliminar archivos de log
            if os.path.exists(self.log_file_path):
                os.remove(self.log_file_path)
            
            # Eliminar logs rotados
            for i in range(1, 11):
                rotated_file = f"{self.log_file_path}.{i}"
                if os.path.exists(rotated_file):
                    os.remove(rotated_file)
            
            # Recrear handler
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler = RotatingFileHandler(
                self.log_file_path,
                maxBytes=50*1024*1024,
                backupCount=10,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            self.info("Logs cleared and logger reinitialized")
            return True
        except Exception as e:
            print(f"Error clearing logs: {str(e)}")
            return False

# Instancia global
bot_logger = MirrorLeechBotLogger()