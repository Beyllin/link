import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import html

class BotLogger:
    _logs = []
    _logger = None

    @classmethod
    def setup_logging(cls):
        """Configura el sistema de logging"""
        cls._logger = logging.getLogger('bot_logger')
        cls._logger.setLevel(logging.INFO)

        # Formato del log
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler para archivo (rotativo)
        os.makedirs('logs', exist_ok=True)
        file_handler = RotatingFileHandler(
            'logs/bot.log',
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        cls._logger.addHandler(file_handler)

        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        cls._logger.addHandler(console_handler)

    @classmethod
    def log(cls, message, level='info'):
        """Registra un mensaje en el log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} - {level.upper()} - {message}"
        
        # Mantener un registro en memoria (últimas 1000 entradas)
        cls._logs.append(log_entry)
        if len(cls._logs) > 1000:
            cls._logs.pop(0)
        
        # Registrar usando el logger estándar
        if cls._logger:
            if level.lower() == 'error':
                cls._logger.error(message)
            elif level.lower() == 'warning':
                cls._logger.warning(message)
            else:
                cls._logger.info(message)

    @classmethod
    def get_logs(cls, lines=100):
        """Obtiene los últimos registros del log"""
        # Obtener los últimos 'lines' registros
        recent_logs = cls._logs[-lines:] if lines > 0 else cls._logs.copy()
        
        # Leer también del archivo de log si existe
        try:
            if os.path.exists('logs/bot.log'):
                with open('logs/bot.log', 'r', encoding='utf-8') as f:
                    file_logs = f.readlines()[-lines:]
                # Combinar y eliminar duplicados
                all_logs = list(set(recent_logs + file_logs))
                all_logs.sort()  # Ordenar por timestamp
                return '\n'.join(all_logs[-lines:])
        except Exception as e:
            cls.log(f"Error al leer archivo de log: {str(e)}", 'error')
        
        return '\n'.join(recent_logs)

# Configuración inicial cuando se importa el módulo
BotLogger.setup_logging()
BotLogger.log("Sistema de logging inicializado")