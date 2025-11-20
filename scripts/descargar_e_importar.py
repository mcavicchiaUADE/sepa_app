#!/usr/bin/env python
"""
Script combinado para Render: Descarga e importación automática de datos SEPA.

Este script ejecuta el flujo completo:
1. Descarga el archivo SEPA según el día de la semana (hora Argentina)
2. Procesa el ZIP y lo importa a PostgreSQL
3. Limpia archivos temporales

Diseñado para ejecutarse como Cron Job en Render.
"""
import sys
import os
import logging
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Agregar el directorio raíz del proyecto al path
# En Render, el working directory es la raíz del proyecto (render-deploy/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Cambiar al directorio raíz para que los imports y paths relativos funcionen
os.chdir(project_root)

from scripts.descargar_sepa import descargar_archivo_sepa, obtener_ruta_destino
from app.services.importador import procesar_zip_sepa


def limpiar_archivos_temporales(project_root_path):
    """
    Limpia archivos temporales y carpetas de extracción.
    """
    try:
        # Limpiar carpeta data/temp si existe
        temp_dir = os.path.join(project_root_path, 'data', 'temp')
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Directorio temporal eliminado: {temp_dir}")
        
        # Limpiar archivos ZIP temporales en data/
        data_dir = os.path.join(project_root_path, 'data')
        if os.path.exists(data_dir):
            for item in os.listdir(data_dir):
                item_path = os.path.join(data_dir, item)
                # Mantener solo sepa_data.zip
                if item.endswith('.zip') and item != 'sepa_data.zip':
                    try:
                        os.remove(item_path)
                        logger.info(f"Archivo temporal eliminado: {item}")
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar {item}: {e}")
    except Exception as e:
        logger.warning(f"Error al limpiar archivos temporales: {e}")


def main():
    """
    Función principal: ejecuta descarga e importación.
    """
    logger.info("=" * 70)
    logger.info("INICIANDO PROCESO DE ACTUALIZACIÓN DE DATOS SEPA")
    logger.info("=" * 70)
    
    try:
        # Paso 1: Descargar archivo SEPA
        logger.info("\n[PASO 1/2] Descargando archivo SEPA...")
        logger.info("-" * 70)
        
        exito_descarga = descargar_archivo_sepa()
        
        if not exito_descarga:
            logger.error("ERROR: La descarga del archivo SEPA falló")
            sys.exit(1)
        
        # Obtener ruta del archivo descargado
        ruta_archivo = obtener_ruta_destino()
        
        if not os.path.exists(ruta_archivo):
            logger.error(f"ERROR: El archivo descargado no existe: {ruta_archivo}")
            sys.exit(1)
        
        tamaño_mb = os.path.getsize(ruta_archivo) / (1024 * 1024)
        logger.info(f"✓ Archivo descargado exitosamente: {ruta_archivo} ({tamaño_mb:.2f} MB)")
        
        # Paso 2: Importar datos a PostgreSQL
        logger.info("\n[PASO 2/2] Importando datos a PostgreSQL...")
        logger.info("-" * 70)
        
        try:
            procesar_zip_sepa(ruta_archivo)
            logger.info("✓ Importación completada exitosamente")
        except Exception as e:
            logger.error(f"ERROR en la importación: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
        
        # Paso 3: Limpiar archivos temporales
        logger.info("\n[PASO 3/3] Limpiando archivos temporales...")
        logger.info("-" * 70)
        limpiar_archivos_temporales(project_root)
        logger.info("✓ Limpieza completada")
        
        logger.info("\n" + "=" * 70)
        logger.info("PROCESO COMPLETADO EXITOSAMENTE")
        logger.info("=" * 70)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"ERROR CRÍTICO: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

