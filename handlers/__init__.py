from .mediafire import MediaFireHandler
from .megaup import MegaUpHandler
from .a2zapk import A2ZAPKHandler
from .apk4free import APK4FreeHandler
from .apkdone import APKDoneHandler
from .uptodown import UptodownHandler
from .liteapks import LiteAPKsHandler
from .apkdone_info_extractor import APKDoneInfoExtractor
from .FilmAffinity import FilmAffinityHandler


def is_supported_link(url):
    return (MediaFireHandler.is_mediafire_link(url) or 
            MegaUpHandler.is_megaup_link(url) or
            A2ZAPKHandler.is_a2zapk_link(url) or
            APK4FreeHandler.is_apk4free_link(url) or
            APKDoneHandler.is_apkdone_link(url) or
            UptodownHandler.is_uptodown_link(url) or
            LiteAPKsHandler.is_liteapks_link(url) or
            FilmAffinityHandler.is_filmaffinity_link(url))

def get_direct_link(url):
    if MediaFireHandler.is_mediafire_link(url):
        return MediaFireHandler.get_direct_link(url)
    elif MegaUpHandler.is_megaup_link(url):
        return MegaUpHandler.get_direct_link(url)
    elif A2ZAPKHandler.is_a2zapk_link(url):
        return A2ZAPKHandler.get_direct_link(url)
    elif APK4FreeHandler.is_apk4free_link(url):
        return APK4FreeHandler.get_direct_link(url)
    elif APKDoneHandler.is_apkdone_link(url):
        return APKDoneHandler.get_direct_link(url)
    elif UptodownHandler.is_uptodown_link(url):
        return UptodownHandler.get_direct_link(url)
    elif LiteAPKsHandler.is_liteapks_link(url):
        return LiteAPKsHandler.get_direct_link(url)
    elif FilmAffinityHandler.is_filmaffinity_link(url):
        return FilmAffinityHandler.process_url(url)
    raise Exception("Servicio no soportado")

# Función original para carpetas MediaFire
def process_mediafire_folder(url):
    return MediaFireHandler.process_folder(url)

# Función para obtener información formateada de APKDone
def get_apkdone_formatted_info(url):
    return APKDoneInfoExtractor.get_formatted_info(url)

# Función para obtener información formateada de FilmAffinity
def get_filmaffinity_formatted_info(url):
    return FilmAffinityHandler.process_url(url)