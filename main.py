import os
import time
import asyncio
import signal
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
from handlers import get_direct_link, is_supported_link, process_mediafire_folder

# Importar los nuevos sistemas
from advanced_logging import bot_logger
from task_queue_system import task_queue, restart_manager, TaskStatus

TOKEN = os.getenv("BOT_TOKEN")

# Diccionario de sitios soportados
SUPPORTED_SITES = {
    'MediaFire': {
        'ejemplo': 'https://www.mediafire.com/file/ejemplo/file.apk',
        'notas': 'Soporta archivos individuales y carpetas (con /folder/)'
    },
    'MegaUp': {
        'ejemplo': 'https://megaup.net/ejemplo',
        'notas': 'Autodetecta captcha, espera 5 segundos'
    },
    'A2ZAPK': {
        'ejemplo': 'https://a2zapk.io/ejemplo',
        'notas': 'Usa técnica de distracción para evitar bloqueos'
    },
    'APK4Free': {
        'ejemplo': 'https://apk4free.net/ejemplo',
        'notas': 'Descarga directa de APKs modificados'
    },
    'APKDone': {
        'ejemplo': 'https://apkdone.com/spotify-premium',
        'notas': 'Descarga directa de APKs premium/modificados'
    }
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador principal de mensajes con sistema de colas"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    try:
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("Por favor envía una URL válida comenzando con http:// o https://")
            bot_logger.log(
                f"URL inválida recibida: {url[:50]}...",
                "WARNING",
                user_id=user_id,
                extra_data={'invalid_url': url}
            )
            return
        
        # Verificar si el sitio es soportado
        if not is_supported_link(url):
            await update.message.reply_text("Sitio no soportado. Usa /soporte para ver los sitios disponibles.")
            bot_logger.log(
                f"Sitio no soportado: {url}",
                "WARNING",
                user_id=user_id,
                extra_data={'unsupported_url': url}
            )
            return
        
        # Agregar tarea a la cola
        task_id = task_queue.add_task(
            user_id=user_id,
            task_type='download',
            data={'url': url}
        )
        
        # Obtener estado de la cola para mostrar posición
        queue_status = task_queue.get_queue_status()
        position_msg = ""
        if queue_status['pending'] > 0:
            position_msg = f"\nPosición en cola: {queue_status['pending']}"
        elif queue_status['active'] > 0:
            position_msg = f"\nTareas activas: {queue_status['active']}"
        
        processing_msg = await update.message.reply_text(
            f"Procesando enlace... ID: {task_id}{position_msg}\n\n"
            f"Puedes usar /estado {task_id} para verificar el progreso"
        )
        
        # Monitorear la tarea hasta que complete
        await monitor_task(update, context, task_id, processing_msg.message_id)
        
    except Exception as e:
        bot_logger.log_exception(e, "handle_message", user_id)
        await update.message.reply_text(f"Error inesperado: {str(e)}")

async def monitor_task(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: str, processing_msg_id: int):
    """Monitorea una tarea hasta su completación"""
    max_wait_time = 300  # 5 minutos máximo
    check_interval = 2   # Verificar cada 2 segundos
    elapsed_time = 0
    
    while elapsed_time < max_wait_time:
        task = task_queue.get_task_status(task_id)
        
        if not task:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_msg_id,
                text="Error: Tarea no encontrada"
            )
            return
        
        if task.status == TaskStatus.COMPLETED:
            # Tarea completada exitosamente
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=processing_msg_id
                )
            except:
                pass  # No importa si no se puede borrar
            
            await update.message.reply_text(task.result)
            return
        
        elif task.status == TaskStatus.FAILED:
            # Tarea falló
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=processing_msg_id
                )
            except:
                pass
            
            await update.message.reply_text(f"Error: {task.error}")
            return
        
        elif task.status == TaskStatus.CANCELLED:
            # Tarea cancelada
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=processing_msg_id
                )
            except:
                pass
            
            await update.message.reply_text("Tarea cancelada")
            return
        
        # Actualizar mensaje de progreso si hay cambios significativos
        if elapsed_time % 10 == 0:  # Cada 10 segundos
            try:
                queue_status = task_queue.get_queue_status()
                progress_msg = f"Procesando... ID: {task_id}\n"
                progress_msg += f"Estado: {task.status.value}\n"
                
                if task.progress > 0:
                    progress_msg += f"Progreso: {task.progress}%\n"
                
                if task.status == TaskStatus.PENDING:
                    progress_msg += f"Posición en cola: {queue_status['pending']}"
                elif task.status == TaskStatus.PROCESSING:
                    progress_msg += "Procesando enlace..."
                
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=processing_msg_id,
                    text=progress_msg
                )
            except:
                pass  # No importa si no se puede actualizar
        
        await asyncio.sleep(check_interval)
        elapsed_time += check_interval
    
    # Timeout
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=processing_msg_id,
        text=f"Timeout: La tarea {task_id} está tomando demasiado tiempo. Verifica con /estado {task_id}"
    )

async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de logs avanzado"""
    user_id = update.effective_user.id
    
    try:
        # Extraer parámetros del comando
        args = context.args
        lines = 100
        filter_level = None
        
        if args:
            if args[0] == 'errores':
                # Mostrar solo errores
                error_report = bot_logger.get_error_report(24)
                
                # Dividir en múltiples mensajes si es muy largo
                max_length = 4000
                for i in range(0, len(error_report), max_length):
                    part = error_report[i:i+max_length]
                    await update.message.reply_text(f"```\n{part}\n```", parse_mode='MarkdownV2')
                
                return
            
            elif args[0].isdigit():
                lines = min(int(args[0]), 500)  # Máximo 500 líneas
            
            elif args[0].upper() in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                filter_level = args[0].upper()
                if len(args) > 1 and args[1].isdigit():
                    lines = min(int(args[1]), 500)
        
        # Obtener logs formateados
        logs = bot_logger.get_formatted_logs(lines, filter_level)
        
        # Dividir en mensajes de máximo 4000 caracteres
        max_length = 4000
        messages = []
        
        for i in range(0, len(logs), max_length):
            part = logs[i:i+max_length]
            messages.append(part)
        
        # Enviar mensajes
        for i, message in enumerate(messages):
            if i == 0:
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"```\n{message}\n```", parse_mode='MarkdownV2')
        
        bot_logger.log(
            f"Comando /log ejecutado. Líneas: {lines}, Filtro: {filter_level or 'Ninguno'}",
            "INFO",
            user_id=user_id,
            command="log"
        )
        
    except Exception as e:
        bot_logger.log_exception(e, "log_command", user_id)
        await update.message.reply_text(f"Error al obtener logs: {str(e)}")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando de reinicio completo del bot"""
    user_id = update.effective_user.id
    
    try:
        # Mensaje inicial
        restart_msg = await update.message.reply_text(
            "Iniciando reinicio completo del bot...\n"
            "Esto puede tomar hasta 30 segundos."
        )
        
        # Ejecutar reinicio
        result = await restart_manager.restart_bot(user_id)
        
        # Actualizar mensaje con resultado
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=restart_msg.message_id,
            text=result
        )
        
    except Exception as e:
        bot_logger.log_exception(e, "restart_command", user_id)
        await update.message.reply_text(f"Error durante el reinicio: {str(e)}")

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para verificar estado de tareas"""
    user_id = update.effective_user.id
    
    try:
        args = context.args
        
        if not args:
            # Mostrar estado general de la cola
            queue_status = task_queue.get_queue_status()
            
            message = "**Estado de la Cola de Tareas**\n\n"
            message += f"Tareas pendientes: {queue_status['pending']}\n"
            message += f"Tareas activas: {queue_status['active']}\n"
            message += f"Tareas completadas: {queue_status['completed']}\n"
            message += f"Workers máximos: {queue_status['max_workers']}\n"
            
            if queue_status['active_tasks']:
                message += f"\n**Tareas activas:**\n"
                for task_id in queue_status['active_tasks'][:5]:
                    task = task_queue.get_task_status(task_id)
                    if task:
                        elapsed = (time.time() - task.started_at.timestamp()) if task.started_at else 0
                        message += f"• {task_id}: {task.task_type} ({elapsed:.0f}s)\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        else:
            # Mostrar estado de tarea específica
            task_id = args[0]
            task = task_queue.get_task_status(task_id)
            
            if not task:
                await update.message.reply_text(f"Tarea {task_id} no encontrada")
                return
            
            message = f"**Estado de la Tarea {task_id}**\n\n"
            message += f"Usuario: {task.user_id}\n"
            message += f"Tipo: {task.task_type}\n"
            message += f"Estado: {task.status.value}\n"
            message += f"Creada: {task.created_at.strftime('%H:%M:%S')}\n"
            
            if task.started_at:
                message += f"Iniciada: {task.started_at.strftime('%H:%M:%S')}\n"
            
            if task.completed_at:
                message += f"Completada: {task.completed_at.strftime('%H:%M:%S')}\n"
            
            if task.progress > 0:
                message += f"Progreso: {task.progress}%\n"
            
            if task.error:
                message += f"Error: {task.error}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        bot_logger.log(
            f"Comando /estado ejecutado",
            "INFO",
            user_id=user_id,
            command="estado"
        )
        
    except Exception as e:
        bot_logger.log_exception(e, "estado_command", user_id)
        await update.message.reply_text(f"Error: {str(e)}")

async def cancelar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando para cancelar tareas"""
    user_id = update.effective_user.id
    
    try:
        args = context.args
        
        if not args:
            await update.message.reply_text("Uso: /cancelar <task_id>")
            return
        
        task_id = args[0]
        
        if task_queue.cancel_task(task_id):
            await update.message.reply_text(f"Tarea {task_id} cancelada")
            bot_logger.log(
                f"Tarea cancelada por usuario: {task_id}",
                "INFO",
                user_id=user_id,
                command="cancelar"
            )
        else:
            await update.message.reply_text(f"No se pudo cancelar la tarea {task_id}")
            
    except Exception as e:
        bot_logger.log_exception(e, "cancelar_command", user_id)
        await update.message.reply_text(f"Error: {str(e)}")

async def soporte_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los sitios soportados y ejemplos"""
    user_id = update.effective_user.id
    
    message = "**Sitios soportados actualmente:**\n\n"
    for site, info in SUPPORTED_SITES.items():
        message += f"• **{site}**\n"
        message += f"  Ejemplo: `{info['ejemplo']}`\n"
        message += f"  Notas: {info['notas']}\n\n"
    message += "Envía un enlace de cualquiera de estos sitios para obtener el enlace directo."
    
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
    
    bot_logger.log(
        "Comando /soporte ejecutado",
        "INFO",
        user_id=user_id,
        command="soporte"
    )

async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la ayuda general del bot"""
    user_id = update.effective_user.id
    
    help_message = """
**Ayuda - Descargas Directas**

**Como usar:**
1. Envía un enlace de descarga de los sitios soportados
2. El bot lo procesará automáticamente usando el sistema de colas
3. Recibe el enlace directo

**Comandos disponibles:**
/soporte - Muestra los sitios soportados
/ayuda - Muestra este mensaje
/log [líneas] [nivel] - Muestra registros del bot
/log errores - Muestra solo errores recientes
/estado [task_id] - Ver estado de tareas
/cancelar <task_id> - Cancelar una tarea
/restart - Reiniciar bot completamente

**Nuevas características:**
• Sistema de colas: Puedes enviar múltiples enlaces
• Procesamiento en paralelo: Hasta 3 tareas simultáneas
• Monitoreo en tiempo real del progreso
• Logging avanzado para administradores
• Reinicio completo con limpieza de procesos

El bot solo procesa enlaces de los sitios soportados.
"""
    
    await update.message.reply_text(help_message, parse_mode='Markdown')
    
    bot_logger.log(
        "Comando /ayuda ejecutado",
        "INFO",
        user_id=user_id,
        command="ayuda"
    )

def setup_signal_handlers():
    """Configura manejadores de señales para shutdown limpio"""
    def signal_handler(signum, frame):
        bot_logger.log(f"Señal {signum} recibida. Iniciando shutdown...", "WARNING")
        
        # Detener sistema de colas
        task_queue.shutdown()
        
        # Limpiar logs antiguos
        bot_logger.cleanup_old_logs()
        
        bot_logger.log("Shutdown completado", "INFO")
        os._exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    if not TOKEN:
        bot_logger.log("ERROR: No se ha configurado el token del bot", "ERROR")
        print("ERROR: No se ha configurado el token del bot")
        return
    
    try:
        # Configurar manejadores de señales
        setup_signal_handlers()
        
        bot_logger.log("Iniciando bot de Telegram con sistema avanzado...", "INFO")
        print("Iniciando bot de Telegram con sistema avanzado...")
        
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Handlers de mensajes
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Handlers de comandos
        app.add_handler(CommandHandler("log", log_command))
        app.add_handler(CommandHandler("restart", restart_command))
        app.add_handler(CommandHandler("reiniciar", restart_command))
        app.add_handler(CommandHandler("estado", estado_command))
        app.add_handler(CommandHandler("status", estado_command))
        app.add_handler(CommandHandler("cancelar", cancelar_command))
        app.add_handler(CommandHandler("cancel", cancelar_command))
        app.add_handler(CommandHandler("soporte", soporte_command))
        app.add_handler(CommandHandler("ayuda", ayuda_command))
        app.add_handler(CommandHandler("help", ayuda_command))
        
        bot_logger.log("Bot iniciado correctamente. Sistema de colas activo.", "INFO")
        print("Bot iniciado correctamente. Sistema de colas activo.")
        print("Comandos nuevos: /log, /restart, /estado, /cancelar")
        
        app.run_polling()
        
    except Exception as e:
        bot_logger.log_exception(e, "main")
        print(f"Error al iniciar el bot: {str(e)}")
    
    finally:
        # Cleanup al salir
        task_queue.shutdown()
        bot_logger.log("Bot detenido", "INFO")

if __name__ == "__main__":
    main()