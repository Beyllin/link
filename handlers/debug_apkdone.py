#!/usr/bin/env python3
"""
Script de debug para probar ambos módulos de APKDone por separado
"""

def test_direct_link():
    """Prueba SOLO el módulo de enlace directo"""
    print("=" * 60)
    print("🔗 PROBANDO MÓDULO DE ENLACE DIRECTO")
    print("=" * 60)
    
    try:
        # Import directo sin pasar por __init__.py
        from apkdone import APKDoneHandler
        
        test_url = "https://apkdone.com/creatify/"
        print(f"📱 URL de prueba: {test_url}")
        
        # Verificar si es enlace válido
        if APKDoneHandler.is_apkdone_link(test_url):
            print("✅ Es un enlace de APKDone válido")
            
            # Obtener enlace directo
            print("\n🔄 Obteniendo enlace directo...")
            direct_link = APKDoneHandler.get_direct_link(test_url)
            print(f"✅ ENLACE DIRECTO: {direct_link}")
            
            return True, direct_link
            
        else:
            print("❌ No es un enlace de APKDone válido")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR en módulo de enlace directo: {str(e)}")
        import traceback
        print(f"📊 Traceback:\n{traceback.format_exc()}")
        return False, None

def test_info_extractor():
    """Prueba SOLO el módulo de extracción de información"""
    print("\n" + "=" * 60)
    print("📝 PROBANDO MÓDULO DE EXTRACCIÓN DE INFORMACIÓN")
    print("=" * 60)
    
    try:
        # Import directo sin pasar por __init__.py
        from apkdone_info_extractor import APKDoneInfoExtractor
        
        test_url = "https://apkdone.com/creatify/"
        print(f"📱 URL de prueba: {test_url}")
        
        # Obtener información formateada
        print("\n🔄 Extrayendo información...")
        result = APKDoneInfoExtractor.get_formatted_info(test_url)
        
        print(f"✅ Success: {result.get('success', False)}")
        
        if result.get('success', False):
            print(f"📝 MENSAJE FORMATEADO:\n{result['message']}")
            print(f"\n📊 INFO RAW: {result.get('raw_info', {})}")
            return True, result['message']
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR en módulo de extracción: {str(e)}")
        import traceback
        print(f"📊 Traceback:\n{traceback.format_exc()}")
        return False, None

def test_combined_flow():
    """Prueba el flujo completo como debería funcionar"""
    print("\n" + "=" * 60)
    print("🚀 PROBANDO FLUJO COMPLETO")
    print("=" * 60)
    
    try:
        # Imports directos SIN usar __init__.py
        from apkdone import APKDoneHandler
        from apkdone_info_extractor import APKDoneInfoExtractor
        
        test_url = "https://apkdone.com/creatify/"
        print(f"📱 URL de prueba: {test_url}")
        
        # Paso 1: Obtener enlace directo
        print("\n🔗 PASO 1: Obteniendo enlace directo...")
        try:
            direct_link = APKDoneHandler.get_direct_link(test_url)
            print(f"✅ Enlace directo obtenido: {direct_link}")
        except Exception as e:
            print(f"❌ Error obteniendo enlace: {str(e)}")
            direct_link = None
        
        # Paso 2: Obtener información formateada
        print("\n📝 PASO 2: Obteniendo información formateada...")
        try:
            info_result = APKDoneInfoExtractor.get_formatted_info(test_url)
            print(f"✅ Info result success: {info_result.get('success', False)}")
            
            if info_result.get('success', False):
                print(f"📝 INFORMACIÓN FORMATEADA:\n{info_result['message']}")
            else:
                print(f"❌ Error en información: {info_result.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ Error obteniendo info: {str(e)}")
            info_result = None
        
        # Resultado final
        print("\n" + "=" * 40)
        print("📋 RESULTADO FINAL:")
        print("=" * 40)
        
        if direct_link:
            print(f"✅ ENLACE DIRECTO: {direct_link}")
        else:
            print("❌ NO HAY ENLACE DIRECTO")
            
        if info_result and info_result.get('success', False):
            print(f"✅ INFORMACIÓN EXTRAÍDA:")
            print(info_result['message'])
        else:
            print("❌ NO HAY INFORMACIÓN EXTRAÍDA")
            
        return direct_link, info_result
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en flujo completo: {str(e)}")
        import traceback
        print(f"📊 Traceback:\n{traceback.format_exc()}")
        return None, None

def test_imports():
    """Verifica que todos los imports funcionen"""
    print("=" * 60)
    print("📦 VERIFICANDO IMPORTS")
    print("=" * 60)
    
    imports_ok = True
    
    try:
        # Import directo desde el archivo (estamos en la carpeta handlers/)
        from apkdone import APKDoneHandler
        print("✅ APKDoneHandler importado correctamente")
    except Exception as e:
        print(f"❌ Error importando APKDoneHandler: {e}")
        imports_ok = False
    
    try:
        from apkdone_info_extractor import APKDoneInfoExtractor
        print("✅ APKDoneInfoExtractor importado correctamente")
    except Exception as e:
        print(f"❌ Error importando APKDoneInfoExtractor: {e}")
        imports_ok = False
    
    try:
        # Para el __init__.py necesitamos importar desde el directorio padre
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from handlers import get_direct_link, get_apkdone_formatted_info
        print("✅ Funciones de handlers importadas correctamente")
    except Exception as e:
        print(f"❌ Error importando funciones de handlers: {e}")
        # No es crítico, podemos continuar sin estas funciones
        print("⚠️  Continuando sin las funciones del __init__.py")
    
    return imports_ok

def main():
    """Función principal de testing"""
    print("🧪 INICIANDO TESTS DE DEBUG PARA APKDONE")
    print("=" * 80)
    
    # Test 1: Verificar imports
    if not test_imports():
        print("\n❌ ERROR: Los imports fallan, no se pueden continuar los tests")
        return
    
    # Test 2: Módulo de enlace directo
    direct_success, direct_link = test_direct_link()
    
    # Test 3: Módulo de información
    info_success, info_message = test_info_extractor()
    
    # Test 4: Flujo completo
    final_link, final_info = test_combined_flow()
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL DE TESTS")
    print("=" * 80)
    
    print(f"🔗 Enlace directo individual: {'✅' if direct_success else '❌'}")
    print(f"📝 Extracción info individual: {'✅' if info_success else '❌'}")
    print(f"🚀 Flujo completo: {'✅' if (final_link and final_info) else '❌'}")
    
    if direct_success and not info_success:
        print("\n⚠️  DIAGNÓSTICO: El módulo de enlace funciona pero el de información no")
        print("   - Revisar APKDoneInfoExtractor")
        print("   - Verificar selectores CSS")
        print("   - Comprobar estructura HTML de la página")
        
    elif not direct_success and info_success:
        print("\n⚠️  DIAGNÓSTICO: El módulo de información funciona pero el de enlace no")
        print("   - Revisar APKDoneHandler")
        print("   - Verificar selectores de botones de descarga")
        
    elif not direct_success and not info_success:
        print("\n❌ DIAGNÓSTICO: Ambos módulos fallan")
        print("   - Problema de conectividad o scraping")
        print("   - APKDone podría estar bloqueando requests")
        print("   - Verificar estructura de la página web")
        
    else:
        print("\n✅ DIAGNÓSTICO: Todo funciona correctamente!")

if __name__ == "__main__":
    main()