import asyncio
import signal
import os
import sys
import time
import threading
import subprocess
import uuid
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Callable, Any, List
from concurrent.futures import ThreadPoolExecutor
import queue

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    user_id: int
    task_type: str  # 'download', 'command', etc.
    data: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None
    progress: int = 0

class TaskQueue:
    """Sistema de cola de tareas con soporte para concurrencia"""
    
    def __init__(self, max_workers: int = 3):
        self.task_queue = queue.Queue()
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = True
        self.lock = threading.Lock()
        
        # Iniciar workers
        self.workers = []
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker, args=(i,), daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def add_task(self, user_id: int, task_type: str, data: Dict[str, Any]) -> str:
        """Agrega una tarea a la cola"""
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            id=task_id,
            user_id=user_id,
            task_type=task_type,
            data=data,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.task_queue.put(task)
        
        # Loggear
        from advanced_logging import bot_logger
        bot_logger.log_request_start(user_id, data.get('url', 'N/A'), task_id)
        bot_logger.log(
            f"📝 Tarea agregada a la cola: {task_type}",
            "INFO",
            user_id=user_id,
            extra_data={
                'task_id': task_id,
                'task_type': task_type,
                'queue_size': self.task_queue.qsize()
            }
        )
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """Obtiene el estado de una tarea"""
        with self.lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]
            elif task_id in self.completed_tasks:
                return self.completed_tasks[task_id]
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Intenta cancelar una tarea"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.error = "Tarea cancelada por el usuario"
                task.completed_at = datetime.now()
                
                # Mover a completadas
                del self.active_tasks[task_id]
                self.completed_tasks[task_id] = task
                
                from advanced_logging import bot_logger
                bot_logger.log(
                    f"🚫 Tarea cancelada: {task_id}",
                    "WARNING",
                    user_id=task.user_id,
                    extra_data={'task_id': task_id, 'action': 'cancel'}
                )
                return True
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Obtiene estado completo de la cola"""
        with self.lock:
            return {
                'pending': self.task_queue.qsize(),
                'active': len(self.active_tasks),
                'completed': len(self.completed_tasks),
                'active_tasks': list(self.active_tasks.keys()),
                'max_workers': self.max_workers
            }
    
    def _worker(self, worker_id: int):
        """Worker que procesa tareas de la cola"""
        from advanced_logging import bot_logger
        
        bot_logger.log(f"🔧 Worker {worker_id} iniciado", "INFO")
        
        while self.running:
            try:
                # Obtener tarea de la cola (timeout para poder verificar self.running)
                try:
                    task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Mover a tareas activas
                with self.lock:
                    task.status = TaskStatus.PROCESSING
                    task.started_at = datetime.now()
                    self.active_tasks[task.id] = task
                
                bot_logger.log(
                    f"🔄 Worker {worker_id} procesando tarea: {task.task_type}",
                    "INFO",
                    user_id=task.user_id,
                    extra_data={
                        'task_id': task.id,
                        'worker_id': worker_id,
                        'task_type': task.task_type
                    }
                )
                
                # Procesar la tarea
                try:
                    if task.task_type == 'download':
                        result = self._process_download_task(task)
                    elif task.task_type == 'command':
                        result = self._process_command_task(task)
                    else:
                        raise Exception(f"Tipo de tarea no reconocido: {task.task_type}")
                    
                    # Tarea completada exitosamente
                    with self.lock:
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        task.completed_at = datetime.now()
                        
                        # Mover a completadas
                        if task.id in self.active_tasks:
                            del self.active_tasks[task.id]
                        self.completed_tasks[task.id] = task
                    
                    bot_logger.log_request_success(task.id, result)
                    
                except Exception as e:
                    # Tarea falló
                    with self.lock:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        task.completed_at = datetime.now()
                        
                        # Mover a completadas
                        if task.id in self.active_tasks:
                            del self.active_tasks[task.id]
                        self.completed_tasks[task.id] = task
                    
                    bot_logger.log_request_error(task.id, str(e))
                    bot_logger.log_exception(e, f"Worker {worker_id} - Task {task.id}", task.user_id)
                
                finally:
                    self.task_queue.task_done()
            
            except Exception as e:
                bot_logger.log_exception(e, f"Worker {worker_id} main loop")
                time.sleep(1)  # Evitar bucle infinito en caso de error persistente
        
        bot_logger.log(f"🛑 Worker {worker_id} detenido", "INFO")
    
    def _process_download_task(self, task: Task) -> str:
        """Procesa una tarea de descarga"""
        from handlers import get_direct_link
        
        url = task.data.get('url')
        if not url:
            raise Exception("URL no proporcionada")
        
        # Actualizar progreso
        task.progress = 10
        
        # Obtener enlace directo
        direct_link = get_direct_link(url)
        
        task.progress = 100
        return direct_link
    
    def _process_command_task(self, task: Task) -> str:
        """Procesa una tarea de comando"""
        command = task.data.get('command')
        
        if command == 'soporte':
            from commands import generate_support_message
            return generate_support_message()
        elif command == 'ayuda':
            from commands import generate_help_message
            return generate_help_message()
        else:
            raise Exception(f"Comando no reconocido: {command}")
    
    def shutdown(self):
        """Detiene el sistema de colas"""
        from advanced_logging import bot_logger
        bot_logger.log("🛑 Deteniendo sistema de colas...", "INFO")
        
        self.running = False
        
        # Esperar a que terminen los workers
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        self.executor.shutdown(wait=True)
        bot_logger.log("✅ Sistema de colas detenido", "INFO")

class BotRestartManager:
    """Gestor de reinicio del bot con limpieza completa"""
    
    def __init__(self, task_queue: TaskQueue):
        self.task_queue = task_queue
        self.restart_in_progress = False
    
    async def restart_bot(self, user_id: int) -> str:
        """Ejecuta reinicio completo del bot"""
        if self.restart_in_progress:
            return "⚠️ Ya hay un reinicio en progreso..."
        
        self.restart_in_progress = True
        
        from advanced_logging import bot_logger
        bot_logger.log(
            "🔄 INICIANDO REINICIO COMPLETO DEL BOT",
            "WARNING",
            user_id=user_id,
            command="restart"
        )
        
        try:
            # Paso 1: Detener cola de tareas
            bot_logger.log("1️⃣ Deteniendo cola de tareas...", "INFO")
            self.task_queue.shutdown()
            
            # Paso 2: Limpiar procesos Chrome/ChromeDriver
            bot_logger.log("2️⃣ Limpiando procesos del navegador...", "INFO")
            await self._cleanup_browser_processes()
            
            # Paso 3: Limpiar memoria y recursos
            bot_logger.log("3️⃣ Liberando recursos del sistema...", "INFO")
            self._cleanup_resources()
            
            # Paso 4: Ejecutar script de restart si existe
            bot_logger.log("4️⃣ Ejecutando reinicio del script...", "INFO")
            restart_result = await self._execute_restart_script()
            
            bot_logger.log("✅ REINICIO COMPLETADO EXITOSAMENTE", "INFO")
            return f"✅ Bot reiniciado exitosamente\n\n{restart_result}"
            
        except Exception as e:
            bot_logger.log_exception(e, "restart_bot", user_id)
            return f"❌ Error durante el reinicio: {str(e)}"
        
        finally:
            self.restart_in_progress = False
    
    async def _cleanup_browser_processes(self):
        """Limpia procesos de Chrome y ChromeDriver"""
        import psutil
        from advanced_logging import bot_logger
        
        processes_killed = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    cmdline = ' '.join(proc_info.get('cmdline', [])).lower()
                    
                    # Identificar procesos relacionados con Chrome/ChromeDriver
                    if any(keyword in proc_name for keyword in ['chrome', 'chromedriver']):
                        # Verificar que sea del bot (buscar patrones específicos)
                        if any(pattern in cmdline for pattern in ['headless', 'no-sandbox', 'disable-dev-shm-usage']):
                            bot_logger.log(f"Terminando proceso: {proc_name} (PID: {proc_info['pid']})", "DEBUG")
                            proc.terminate()
                            processes_killed += 1
                            
                            # Esperar un poco antes de forzar
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                                bot_logger.log(f"Proceso forzado: {proc_name}", "DEBUG")
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            bot_logger.log(f"Procesos del navegador terminados: {processes_killed}", "INFO")
            
        except Exception as e:
            bot_logger.log_exception(e, "_cleanup_browser_processes")
    
    def _cleanup_resources(self):
        """Limpia recursos del sistema"""
        import gc
        from advanced_logging import bot_logger
        
        try:
            # Forzar recolección de basura
            collected = gc.collect()
            bot_logger.log(f"Objetos recolectados por GC: {collected}", "DEBUG")
            
            # Limpiar cache de ChromeDriver si existe
            import os
            import shutil
            
            cache_dirs = [
                os.path.expanduser("~/.wdm"),
                "/tmp/.com.google.Chrome*",
                "/tmp/chrome*"
            ]
            
            cleaned_dirs = 0
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    try:
                        shutil.rmtree(cache_dir)
                        cleaned_dirs += 1
                        bot_logger.log(f"Cache eliminado: {cache_dir}", "DEBUG")
                    except:
                        pass
            
            bot_logger.log(f"Directorios de cache limpiados: {cleaned_dirs}", "INFO")
            
        except Exception as e:
            bot_logger.log_exception(e, "_cleanup_resources")
    
    async def _execute_restart_script(self) -> str:
        """Ejecuta el script de reinicio si está disponible"""
        from advanced_logging import bot_logger
        
        script_path = "./manage_bot.sh"
        
        if not os.path.exists(script_path):
            bot_logger.log("Script manage_bot.sh no encontrado, reiniciando proceso Python", "WARNING")
            return await self._restart_python_process()
        
        try:
            # Ejecutar el script de restart
            bot_logger.log("Ejecutando: ./manage_bot.sh restart", "INFO")
            
            # Ejecutar en background para que no bloquee
            process = await asyncio.create_subprocess_exec(
                script_path, "restart",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Esperar un poco para ver si inicia correctamente
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
                
                result = stdout.decode() if stdout else "Sin salida"
                if stderr:
                    result += f"\nErrores: {stderr.decode()}"
                
                bot_logger.log(f"Script ejecutado exitosamente", "INFO")
                return result
                
            except asyncio.TimeoutError:
                bot_logger.log("Script ejecutándose en background", "INFO")
                return "Script de reinicio ejecutado en background"
        
        except Exception as e:
            bot_logger.log_exception(e, "_execute_restart_script")
            return await self._restart_python_process()
    
    async def _restart_python_process(self) -> str:
        """Reinicia el proceso Python actual"""
        from advanced_logging import bot_logger
        
        try:
            bot_logger.log("Reiniciando proceso Python...", "INFO")
            
            # Obtener argumentos del proceso actual
            args = sys.argv
            executable = sys.executable
            
            bot_logger.log(f"Ejecutando: {executable} {' '.join(args)}", "DEBUG")
            
            # Reiniciar el proceso
            os.execv(executable, [executable] + args)
            
        except Exception as e:
            bot_logger.log_exception(e, "_restart_python_process")
            return f"Error reiniciando proceso: {str(e)}"

# Instancia global del sistema
task_queue = TaskQueue(max_workers=3)
restart_manager = BotRestartManager(task_queue)