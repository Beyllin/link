from handlers import is_supported_link

SUPPORTED_SITES = {
    'MediaFire': {
        'ejemplo': 'https://www.mediafire.com/file/ejemplo/file.apk',
        'notas': 'Soporta archivos individuales y carpetas'
    },
    'MegaUp': {
        'ejemplo': 'https://megaup.net/ejemplo',
        'notas': 'Requiere esperar 5 segundos para el captcha'
    },
    'A2ZAPK': {
        'ejemplo': 'https://a2zapk.io/ejemplo',
        'notas': 'Usa estrategia de distracción'
    },
    'APK4Free': {
        'ejemplo': 'https://apk4free.net/ejemplo',
        'notas': 'Descarga directa de APKs modificados'
    }
}

def generate_support_message():
    """Genera el mensaje de sitios soportados"""
    message = "🛠 <b>Sitios soportados actualmente:</b>\n\n"
    for site, info in SUPPORTED_SITES.items():
        message += f"• <b>{site}</b>\n"
        message += f"  🔹 <i>Ejemplo:</i> <code>{info['ejemplo']}</code>\n"
        message += f"  🔹 <i>Notas:</i> {info['notas']}\n\n"
    message += "📌 Envía un enlace de cualquiera de estos sitios para obtener el enlace directo."
    return message

def generate_help_message():
    """Genera el mensaje de ayuda general"""
    return """
📚 <b>Ayuda - Descargas Directas</b>

🔹 <b>Cómo usar:</b>
1. Envía un enlace de descarga
2. Espera a que el bot lo procese
3. Recibe el enlace directo

🔹 <b>Comandos disponibles:</b>
/soporte - Muestra los sitios soportados
/ayuda - Muestra este mensaje

⚠ <i>El bot solo procesa enlaces de los sitios soportados</i>
"""